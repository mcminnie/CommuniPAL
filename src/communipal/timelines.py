'''
Functions for creating timelines for visual analysis of results.
'''


import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.dates as mdates 
import matplotlib.patches as mpatches
# from datetime import timedelta
# import os

font_size = 12
mpl.rcParams['xtick.labelsize'] = font_size
mpl.rcParams['ytick.labelsize'] = font_size
mpl.rcParams['axes.labelsize'] = font_size

epoch_num = mdates.date2num(pd.Timestamp('1970-01-01'))

category_styles = {
    "Home": dict(facecolors='tab:blue'),
    "Community": dict(facecolors='tab:red'),
    # "Non-Wear": dict(facecolors='white', edgecolors='black'),
    "Sleep": dict(facecolors='none', edgecolors='black', hatch='////', linewidth=0),
}

legend_handles = {
    "Home": mpatches.Patch(facecolor='tab:blue', label="Home"),
    "Sleep": mpatches.Patch(facecolor='tab:blue', edgecolor='black', hatch='////', label="Sleep"),
    "Community": mpatches.Patch(facecolor='tab:red', label="Community"),
    # "Non-Wear": mpatches.Patch(facecolor='white', edgecolor='black', label="Non-Wear"),
}

def convert_pal_to_timeline(df):
    '''
    Switches dates and times to to number format for plotting in brokenbarh
    '''
    df['Duration'] = pd.to_datetime(df['Duration (s)'], unit = 's')
    df['Duration'] = mdates.date2num(df['Duration'])
    df['Start_Num'] = mdates.date2num(df['Start'])
    return df


def bars_for_day(intervals, day_start, day_end):
    """
    intervals: list of (start_num, duration_as_abs_date_num)
            where duration_as_abs_date_num = mdates.date2num(pd.to_datetime(seconds))
    returns: list of (x0, width) in mdates units, clipped to [day_start, day_end)
    """
    ds = mdates.date2num(pd.to_datetime(day_start))
    de = mdates.date2num(pd.to_datetime(day_end))
    out = []
    for start_num, duration_abs_num in intervals:
        # Convert your stored "Duration" to a width in days
        width_days = float(duration_abs_num) - epoch_num
        if width_days <= 0:
            continue
        s = max(float(start_num), ds)
        e = min(float(start_num) + width_days, de)
        if e > s:
            out.append((s, e - s))
    return out


def add_default_legend(fig, ncol=3):
    fig.legend(
        handles=list(legend_handles.values()),
        loc='upper center',
        ncol=ncol,
        bbox_to_anchor=(0.5, 1.05),
        frameon=False,
        fontsize = font_size
        )    
    

def stepping_overlay(df, overlay = 'SLS', 
                     csd_threshold = 54.7, sls_threshold = 22.9, 
                     amputee = False,legend = True, sleep_shade = True):
    
    if amputee:
        sleep_shade = False

    temp1 = convert_pal_to_timeline(df) # Convert start time and duration to numbers to plot as horizontal bars

    # Data to input to the timelines - start and duration of each event saved into lists
    classification_list = ['Home', 'Community', 'Non-Wear']
    category_dict = {classification: pd.DataFrame() for classification in classification_list}
    for key,value in category_dict.items():
        value = temp1[temp1['community_classification'] == key]
        category_dict[key] = value[['Start_Num','Duration']].values.tolist()

    # Overlay df - change any events that aren't stepping to have no duration. 
    overlay_df = temp1.copy()
    overlay_df.loc[overlay_df['Event Type'] != 2, ['Duration (s)']] = 0

    nonwear_type = temp1[temp1['Event Type'] == 4]
    nonwear_list = nonwear_type[['Start_Num','Duration']].values.tolist()

    sleeping_type = temp1[temp1['Event Type'] == 3.1] 
    sleeping_list = sleeping_type[['Start_Num','Duration']].values.tolist()

    # Create start and end limits for x-axis
    day0 = pd.to_datetime(temp1['Start']).min().normalize()
    dayn  = pd.to_datetime(temp1['End']).max().ceil('D')

    # A DatetimeIndex of day starts: [day0, day1, ..., last_day-1]
    days = pd.date_range(day0, dayn, freq='D', inclusive='left')
    n_days = len(days)
    # Make that many rows of axes
    fig, ax = plt.subplots(n_days, 1, figsize=(12, max(3, 2*n_days)), squeeze=False)
    ax = ax.ravel()

    # Plotting
    for i, axi in enumerate(ax):
        day_start = days[i]
        # day_end = day_start + pd.Timedelta(minutes = 1439)
        day_end = day_start + pd.Timedelta(days=1)
        axi.set_xlim(day_start, day_end)

        if overlay == 'CSD':
            threshold = csd_threshold
            overlay_col = 'Duration (s)'
            ylabel = 'CSD (s)'
        if overlay == 'SLS':
            threshold = sls_threshold
            overlay_col = 'Longest Straight Line Time (s)'
            ylabel = 'SLS (s)'

        # Home
        hbar = bars_for_day(category_dict.get('Home', []), day_start, day_end)
        if hbar:
            axi.broken_barh(hbar, 
                            (0, threshold), 
                            **category_styles["Home"])

        # Community
        cbar = bars_for_day(category_dict.get('Community', []), day_start, day_end)
        if cbar:
            axi.broken_barh(cbar, 
                            (0, threshold), 
                            **category_styles["Community"])

        # Sleep
        if sleep_shade:
            sbar = bars_for_day(sleeping_list, day_start, day_end)
            if sbar:
                axi.broken_barh(
                        sbar,
                        (0, threshold), 
                        **category_styles["Sleep"])

        # Non-wear
        non_wear_colour = 'white'
        full_day_bar = [(mdates.date2num(day_start), mdates.date2num(day_end) - mdates.date2num(day_start))]
        axi.broken_barh(full_day_bar, (0, threshold), facecolors=non_wear_colour, zorder=0)
    
        nbar = bars_for_day(nonwear_list, day_start, day_end)
        if nbar:
            axi.broken_barh(nbar, 
                            (0, threshold), 
                            facecolors=non_wear_colour)

        nbar1 = bars_for_day(category_dict.get('Non-Wear', []), day_start, day_end)
        if nbar1:
            axi.broken_barh(nbar1, (0, threshold), facecolors=non_wear_colour)
  



        day_overlay = overlay_df[(overlay_df['Start'] >= day_start) & 
                                (overlay_df['Start'] < day_end)]
        if not day_overlay.empty:
            axi.fill_between(
                day_overlay['Start_Num'], 
                day_overlay[overlay_col],
                color='black', alpha=0.6
            )

       
        axi.set_ylabel(ylabel)
        axi.set_ylim(0, 120)
        axi.set_xticklabels([])  # hide ticks for all but bottom
        axi.xaxis_date()
        axi.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
        # axi.set_xlabel('Time of day')
        axi.grid(axis = 'x')

        # Annotation for day of the week 
        current_date = day_start
        axi.text(current_date + pd.Timedelta(hours=0.1), 100,
                current_date.strftime('%A'),
                ha='left', va='center', fontsize = font_size)

    plt.subplots_adjust(hspace=0.5)


    if legend:
        if amputee:
            legend_list = ["Home","Community"]
        else:    
            legend_list = ["Home","Sleep", "Community"]

        fig.canvas.draw()  # ensure positions are finalized (after tight_layout/constrained_layout)
        top = max(ax.get_position().y1 for ax in fig.axes)  
        pad = 0  # gap between axes and legend (in figure coords)
        fig.legend(
            handles=[legend_handles[name] for name in legend_list if name in legend_handles],
            loc="lower center",                  
            bbox_to_anchor=(0.5, top + pad),     
            bbox_transform=fig.transFigure,      
            ncol=3,
            frameon=True,
            fontsize=font_size,
        )

    plt.show()


def simple(df,amputee = False,legend = True, sleep_shade = True):
    
    if amputee:
        sleep_shade = False

    bar_start = 0
    bar_height = 3 
    yaxis_height = bar_start+bar_height+2.5

    temp1 = convert_pal_to_timeline(df) # Convert start time and duration to numbers to plot as horizontal bars

    # Data to input to the timelines - start and duration of each event saved into lists
    classification_list = ['Home', 'Community', 'Non-Wear']
    category_dict = {classification: pd.DataFrame() for classification in classification_list}
    for key,value in category_dict.items():
        value = temp1[temp1['community_classification'] == key]
        category_dict[key] = value[['Start_Num','Duration']].values.tolist()

    nonwear_type = temp1[temp1['Event Type'] == 4]
    nonwear_list = nonwear_type[['Start_Num','Duration']].values.tolist()

    sleeping_type = temp1[temp1['Event Type'] == 3.1] 
    sleeping_list = sleeping_type[['Start_Num','Duration']].values.tolist()

    # Create start and end limits for x-axis
    day0 = pd.to_datetime(temp1['Start']).min().normalize()
    dayn  = pd.to_datetime(temp1['End']).max().ceil('D')

    # A DatetimeIndex of day starts: [day0, day1, ..., last_day-1]
    days = pd.date_range(day0, dayn, freq='D', inclusive='left')
    n_days = len(days)
    # Make that many rows of axes
    fig, ax = plt.subplots(n_days, 1, figsize=(12, max(3, 1*n_days)), squeeze=False)
    ax = ax.ravel()

    # Plotting
    for i, axi in enumerate(ax):
        day_start = days[i]
        day_end = day_start + pd.Timedelta(days=1)
        axi.set_xlim(day_start, day_end)

        # Home
        hbar = bars_for_day(category_dict.get('Home', []), day_start, day_end)
        if hbar:
            axi.broken_barh(hbar, 
                            (bar_start, bar_height), 
                            **category_styles["Home"])

        # Community
        cbar = bars_for_day(category_dict.get('Community', []), day_start, day_end)
        if cbar:
            axi.broken_barh(cbar, 
                            (bar_start, bar_height),
                            **category_styles["Community"])

        # Sleep
        if sleep_shade:
            sbar = bars_for_day(sleeping_list, day_start, day_end)
            if sbar:
                axi.broken_barh(
                        sbar,
                        (bar_start, bar_height),
                        **category_styles["Sleep"])

        # Non-wear
        non_wear_colour = 'white'
        full_day_bar = [(mdates.date2num(day_start), mdates.date2num(day_end) - mdates.date2num(day_start))]
        axi.broken_barh(full_day_bar, 
                        (bar_start, bar_height),
                         facecolors=non_wear_colour, 
                         zorder=0)
    
        nbar = bars_for_day(nonwear_list, day_start, day_end)
        if nbar:
            axi.broken_barh(nbar, 
                            (bar_start, bar_height),
                            facecolors=non_wear_colour)

        nbar1 = bars_for_day(category_dict.get('Non-Wear', []), day_start, day_end)
        if nbar1:
            axi.broken_barh(nbar1,
                            (bar_start, bar_height),
                            facecolors=non_wear_colour)
  

        axi.set_yticks([])             # remove ticks
        axi.set_ylabel("")             # remove axis label
        axi.tick_params(labelleft=False)  # remove tick labels
        axi.set_ylim(0, yaxis_height)
        axi.set_xticklabels([])
        axi.grid(axis="x")
        
        # Annotation for day of the week 
        current_date = day_start
        axi.text(current_date + pd.Timedelta(hours=0.1), bar_height+bar_start+1,
                current_date.strftime('%A'),
                ha='left', va='center', fontsize = font_size)

    # Set x-axis to final subplot only
    axi.xaxis_date()
    # axi.xaxis.set_major_locator(mdates.HourLocator(byhour=[0,3,6,9, 12,15, 18,21, 24]))
    axi.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    axi.set_xlabel('Time of day')
    # Add vertical padding between subplots
    plt.subplots_adjust(hspace=0.5)

    if legend:
        if amputee:
            legend_list = ["Home","Community"]
        else:    
            legend_list = ["Home","Sleep", "Community"]

        fig.canvas.draw()  # ensure positions are finalized (after tight_layout/constrained_layout)
        top = max(ax.get_position().y1 for ax in fig.axes)  
        pad = 0  # gap between axes and legend 
        fig.legend(
            handles=[legend_handles[name] for name in legend_list if name in legend_handles],
            loc="lower center",                  
            bbox_to_anchor=(0.5, top + pad),     
            bbox_transform=fig.transFigure,      
            ncol=3,
            frameon=True,
            fontsize=font_size,
        )

    plt.show()


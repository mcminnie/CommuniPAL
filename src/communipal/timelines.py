'''
Functions for creating timelines for visual analysis of results.
'''


import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.dates as mdates 
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
# from datetime import timedelta
# import os

font_size = 14
mpl.rcParams['xtick.labelsize'] = font_size
mpl.rcParams['ytick.labelsize'] = font_size
mpl.rcParams['axes.labelsize'] = font_size

epoch_num = mdates.date2num(pd.Timestamp('1970-01-01'))

category_styles = {
    "Home": dict(facecolors='tab:blue'),
    "Community": dict(facecolors='tab:red'),
    "Non-Wear": dict(facecolors='white', edgecolor = 'gray'), 
    "Sleep": dict(facecolors='none', edgecolors='black', hatch='////', linewidth=0),
    "Primary": dict(facecolors = 'purple'),
    "Secondary": dict(facecolors = 'orange'),
    "Transition": dict(facecolors = 'orange')
}

legend_handles = {
    "Home": mpatches.Patch(facecolor='tab:blue', label="Home"),
    "Sleep": mpatches.Patch(facecolor='tab:blue', edgecolor='black', hatch='////', label="Sleep"),
    "Community": mpatches.Patch(facecolor='tab:red', label="Community"),
    "Non-Wear": mpatches.Patch(facecolor='white', edgecolor='gray', label="Non-Wear"),
    "Primary": mpatches.Patch(facecolor = 'purple', label = 'Primary'),
    "Secondary": mpatches.Patch(facecolor = 'orange', label = 'Secondary'),
    "Transition": mpatches.Patch(facecolor = 'orange', label = 'Transition'),
    "Primary Marker": Line2D(
        [0], [0],
        marker='x', color='black', linestyle='None',
        markersize=6, label='Transition')
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
                     amputee = False,legend = True, sleep_shade = True, show = True):
    
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
        
        axi.grid(axis = 'x')

        # Annotation for day of the week 
        current_date = day_start
        axi.text(current_date + pd.Timedelta(hours=0.1), 100,
                current_date.strftime('%A'),
                ha='left', va='center', fontsize = font_size)

    plt.subplots_adjust(hspace=0.5)
    axi.set_xlabel('Time of day')

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

    if show:
        plt.show()
    return fig


def simple(df,amputee = False,legend = True, sleep_shade = True, show=True):
    
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
        axi.text(current_date + pd.Timedelta(hours=0.1), 
                 yaxis_height *0.8,
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
            ncol=len(legend_list),
            frameon=True,
            fontsize=font_size,
        )
    if show:
        plt.show()
    return fig


def comparison(dfs, amputee=False, legend=True, sleep_shade=True, labels=None, show = True):
    '''
    Compare any number of PAL-like dataframes on stacked daily timelines.

    Parameters
    ----------
    dfs : list[pd.DataFrame] | dict[str, pd.DataFrame]
        The dataframes to compare. If a dict is provided, its keys are used as labels.
        If a list is provided, you can pass `labels` (same length) to label each track.
    amputee : bool
        If True, disables sleep shading and legend will exclude Sleep.
    legend : bool
        Whether to show category legend (Home, Sleep, Community, Non-wear).
    sleep_shade : bool
        Whether to shade sleep (overridden to False if `amputee=True`).
    labels : list[str] | None
        Optional labels for each DF if `dfs` is a list.
    '''
    if amputee:
        sleep_shade = False

    if isinstance(dfs, dict):
        series = list(dfs.items())
    else:
        if labels is None:
            labels = [f"DF {i+1}" for i in range(len(dfs))]
        series = list(zip(labels, dfs))

    n_series = len(series)
    # Convert to timeline space once per DF and precompute bar lists per category
    classification_list = ['Home', 'Community', 'Non-Wear']
    per_df = []
    for name, df in series:
        temp = convert_pal_to_timeline(df)  # must create Start, End, Start_Num, Duration, community_classification, Event Type

        # Classification -> list[[start_num, duration], ...]
        category_map = {c: [] for c in classification_list}
        for c in classification_list:
            sel = temp[temp['community_classification'] == c]
            if not sel.empty:
                category_map[c] = sel[['Start_Num', 'Duration']].values.tolist()

        # Specific event types
        nonwear_type = temp[temp['Event Type'] == 4]
        nonwear_list = nonwear_type[['Start_Num', 'Duration']].values.tolist()

        sleeping_type = temp[temp['Event Type'] == 3.1]
        sleeping_list = sleeping_type[['Start_Num', 'Duration']].values.tolist()

        per_df.append({
            "name": name,
            "temp": temp,
            "categories": category_map,
            "nonwear_list": nonwear_list,
            "sleeping_list": sleeping_list,
        })

    # Global day range across all DFs
    day0 = min(pd.to_datetime(d['temp']['Start']).min().normalize() for d in per_df)
    dayn = max(pd.to_datetime(d['temp']['End']).max().ceil('D') for d in per_df)

    days = pd.date_range(day0, dayn, freq='D', inclusive='left')
    n_days = len(days)

    # Figure/axes
    # fig, ax = plt.subplots(n_days, 1, figsize=(12, max(3, 1*n_days)), squeeze=False)
    fig, ax = plt.subplots(n_days, 1, figsize=(12, 1.8*n_days), squeeze=False)
    ax = ax.ravel()

    # Total vertical span per subplot
    bar_height=4
    bar_padding=3
    track_span = bar_height + bar_padding
    margin_top = bar_height + 2
    yaxis_height = n_series * track_span + margin_top
    bar_start = 0  # first track starts at 0


    # Plot each day
    for i, axi in enumerate(ax):
        day_start = days[i]
        day_end = day_start + pd.Timedelta(days=1)
        axi.set_xlim(day_start, day_end)

        # Background full-day non-wear (white) per DF track, then overlay category bars
        for s_idx, d in enumerate(per_df):
            y0 = bar_start + s_idx * track_span

            # Full-day base (white) to "clear" background for that track
            full_day_bar = [(mdates.date2num(day_start),
                             mdates.date2num(day_end) - mdates.date2num(day_start))]
            axi.broken_barh(full_day_bar,
                            (y0, bar_height),
                            facecolors='white',
                            zorder=0)

            # Home
            hbar = bars_for_day(d["categories"].get('Home', []), day_start, day_end)
            if hbar:
                axi.broken_barh(hbar,
                                (y0, bar_height),
                                **category_styles["Home"])

            # Community
            cbar = bars_for_day(d["categories"].get('Community', []), day_start, day_end)
            if cbar:
                axi.broken_barh(cbar,
                                (y0, bar_height),
                                **category_styles["Community"])

            # Sleep (optional shade)
            if sleep_shade:
                sbar = bars_for_day(d["sleeping_list"], day_start, day_end)
                if sbar:
                    axi.broken_barh(sbar,
                                    (y0, bar_height),
                                    **category_styles["Sleep"])

            # Non-wear overlays
            nbar_event = bars_for_day(d["nonwear_list"], day_start, day_end)
            if nbar_event:
                axi.broken_barh(nbar_event,
                                (y0, bar_height),
                                facecolors='white')

            nbar_class = bars_for_day(d["categories"].get('Non-Wear', []), day_start, day_end)
            if nbar_class:
                axi.broken_barh(nbar_class,
                                (y0, bar_height),
                                facecolors='white')

            # Left-side label for the track (one per DF)
            axi.text(day_start - pd.Timedelta(minutes=10),
                    #  y0 + bar_height + 0.15,
                     y0,
                     d["name"],
                     ha='right', va='bottom', 
                     fontsize=font_size)

        # Cosmetics per subplot
        axi.set_yticks([])
        axi.set_ylabel("")
        axi.tick_params(labelleft=False)
        axi.set_ylim(0, yaxis_height)
        axi.set_xticklabels([])
        axi.grid(axis="x")

        # Day-of-week annotation (at top of stack)
        axi.text(day_start + pd.Timedelta(hours=0.1),
                yaxis_height * 0.9,
                 day_start.strftime('%A'),
                 ha='left', va='center', fontsize=font_size)

    # Only the final subplot gets the x-axis time labels
    axi.xaxis_date()
    axi.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    axi.set_xlabel('Time of day', fontsize=font_size)

    plt.subplots_adjust(hspace=0.2)

    # Legend
    if legend:
        if amputee or not sleep_shade:
            legend_list = ["Home", "Community", "Non-Wear"]
        else:
            legend_list = ["Home", "Sleep", "Community", "Non-Wear"]

        fig.canvas.draw()
        top = max(ax_i.get_position().y1 for ax_i in fig.axes)
        fig.legend(
            handles=[legend_handles[name] for name in legend_list if name in legend_handles],
            loc="lower center",
            bbox_to_anchor=(0.5, top + 0.0),
            bbox_transform=fig.transFigure,
            ncol=len(legend_list),
            frameon=True,
            fontsize=font_size,
        )

    if show:
        plt.show()
    return fig



def transition_type(df, amputee = False, legend = True, sleep_shade = True, show = True):
    '''
    Plots primary and secondary transitions, with a marker for the primary transitions.
    '''
    if amputee:
        sleep_shade = False

    bar_start = 0
    bar_height = 3 
    bar_spacing = 1.5
    yaxis_height = (bar_start+bar_height)*2+ bar_spacing + 2.5 

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

    primary_type = temp1[temp1['transition'] == 'Primary'].copy()
    primary_list = primary_type[['Start_Num','Duration']].values.tolist()

    # Add markers to leave/return time of the primary transitions
    primary_type['transition_time_num'] = mdates.date2num(primary_type['transition_time'])

    secondary_type = temp1[temp1['transition'] == 'Secondary']
    secondary_list = secondary_type[['Start_Num','Duration']].values.tolist()
    
    # Create start and end limits for x-axis
    day0 = pd.to_datetime(temp1['Start']).min().normalize()
    dayn  = pd.to_datetime(temp1['End']).max().ceil('D')

    # A DatetimeIndex of day starts: [day0, day1, ..., last_day-1]
    days = pd.date_range(day0, dayn, freq='D', inclusive='left')
    n_days = len(days)
    # Make that many rows of axes
    fig, ax = plt.subplots(n_days, 1, figsize=(12,  1.5*n_days), squeeze=False)
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
  
        # Primary transitions
        pbar = bars_for_day(primary_list, day_start, day_end)
        if pbar:
            axi.broken_barh(pbar,
                                (bar_start+bar_height+bar_spacing, bar_height),
                                **category_styles["Primary"])
            axi.scatter(
                primary_type['transition_time_num'],
                [bar_start + bar_height + bar_spacing + bar_height/2] * len(primary_type),
                marker='x', 
                color = 'black', 
                linestyle='None',
                linewidth = 1, 
                s=30
                )
        
        # Secondary transitions    
        sbar = bars_for_day(secondary_list, day_start, day_end)
        if sbar:
            axi.broken_barh(sbar,
                            (bar_start+bar_height+bar_spacing, bar_height),
                            **category_styles["Secondary"])


        # Aesthetics
        axi.set_yticks([])             # remove ticks
        axi.set_ylabel("")             # remove axis label
        axi.tick_params(labelleft=False)  # remove tick labels
        axi.set_ylim(0, yaxis_height)
        axi.set_xticklabels([])
        axi.grid(axis="x")
        
        # Annotation for day of the week 
        current_date = day_start
        axi.text(current_date + pd.Timedelta(hours=0.1), 
                yaxis_height *0.85,
                current_date.strftime('%A'),
                ha='left', va='center', fontsize = font_size)

    # Set x-axis to final subplot only
    axi.xaxis_date()
    # axi.xaxis.set_major_locator(mdates.HourLocator(byhour=[0,3,6,9, 12,15, 18,21, 24]))
    axi.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    axi.set_xlabel('Time of day')
    # Add vertical padding between subplots
    plt.subplots_adjust(hspace=0.2)

    if legend:
        if amputee:
            legend_list = ["Home","Community"]
        else:    
            legend_list = ["Home","Sleep", "Community"]
        transitions_list = [ "Primary", "Secondary", "Primary Marker"]
        fig.canvas.draw()  # ensure positions are finalized (after tight_layout/constrained_layout)
        top = max(ax.get_position().y1 for ax in fig.axes)  
        pad = 0  # gap between axes and legend 
        fig.legend(
            handles=[legend_handles[name] for name in legend_list if name in legend_handles],
            loc="lower left",                  
            bbox_to_anchor=(0.05, top + pad),     
            bbox_transform=fig.transFigure,      
            ncol=len(legend_list),
            title = 'Activity',
            title_fontsize = font_size,
            frameon=True,
            fontsize=font_size,
        )

        fig.legend(
            handles = [legend_handles[name] for name in transitions_list if name in legend_handles],
            loc = "lower right",
            bbox_to_anchor=(0.98, top + pad),     
            bbox_transform=fig.transFigure,      
            ncol=len(legend_list),
            frameon=True,
            title = 'Transition Type',
            title_fontsize = font_size,
            fontsize=font_size,
        )

    plt.show()
    return fig

def transition_cause(df, amputee = False, legend = True, sleep_shade = True, seated_transport = False, algo_type = None,  sls_threshold = None, csd_threshold = None, show = True):
    '''
    Plots primary and secondary transitions, with a marker for the primary transitions.
    '''
    if amputee:
        sleep_shade = False

    bar_start = 0
    bar_height = 3 
    bar_spacing = 2

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

    # --- optional tracks' data
    # transport
    transport = temp1[temp1['Event Type'] == 5]
    transport_list = transport[['Start_Num', 'Duration']].values.tolist()

    # continuous stepping duration
    csd = temp1.loc[(temp1['Event Type'] == 2)]
    if csd_threshold is not None:
        csd = csd[csd['Duration (s)'] > csd_threshold]
    csd_list = csd[['Start_Num', 'Duration']].values.tolist()

    # straight line stepping
    if sls_threshold is not None:
        sls = temp1[temp1['Longest Straight Line Time (s)'] > sls_threshold]
    else:
        sls = temp1.iloc[0:0]  # empty
    sls_list = sls[['Start_Num', 'Duration']].values.tolist()

    # --- determine which optional tracks are enabled
    tracks_enabled = []  # order here determines vertical order
    if algo_type in ['CSDonly', 'CSDorSLS', 'CSDandSLS']:
        tracks_enabled.append('CSD')
    if algo_type in ['SLSonly', 'CSDorSLS', 'CSDandSLS']:
        tracks_enabled.append('SLS')
    if seated_transport:
        tracks_enabled.append('Transport')

    # lane 0 is the base lane (Home/Community/Sleep/Non-wear)
    lanes = ['Base'] + tracks_enabled

    # compute y positions for each lane/track
    # lane i starts at: bar_start + i*(bar_height + bar_spacing)
    y_positions = {lane: bar_start + i*(bar_height + bar_spacing) for i, lane in enumerate(lanes)}
    # dynamic y-axis height based on number of lanes
    yaxis_height = y_positions[lanes[-1]] + bar_height + bar_spacing + bar_height

    # Create start and end limits for x-axis
    day0 = pd.to_datetime(temp1['Start']).min().normalize()
    dayn  = pd.to_datetime(temp1['End']).max().ceil('D')
    days = pd.date_range(day0, dayn, freq='D', inclusive='left')
    n_days = len(days)
    # Make that many rows of axes
    fig, ax = plt.subplots(n_days, 1, figsize=(12,  1.8*n_days), squeeze=False)
    ax = ax.ravel()

    for i, axi in enumerate(ax):
        day_start = days[i]
        day_end = day_start + pd.Timedelta(days=1)
        axi.set_xlim(day_start, day_end)

        # --- BASE lane (always present)
        base_y0 = y_positions['Base']

        # Home
        hbar = bars_for_day(category_dict.get('Home', []), day_start, day_end)
        if hbar:
            axi.broken_barh(hbar, (base_y0, bar_height), **category_styles["Home"])

        # Community
        cbar = bars_for_day(category_dict.get('Community', []), day_start, day_end)
        if cbar:
            axi.broken_barh(cbar, (base_y0, bar_height), **category_styles["Community"])

        # Sleep (optional shading)
        if sleep_shade:
            sbar = bars_for_day(sleeping_list, day_start, day_end)
            if sbar:
                axi.broken_barh(sbar, (base_y0, bar_height), **category_styles["Sleep"])

        # Non-wear: white fill under everything (keep zorder=0)
        non_wear_colour = 'white'
        full_day_bar = [(mdates.date2num(day_start),
                         mdates.date2num(day_end) - mdates.date2num(day_start))]
        axi.broken_barh(full_day_bar, (base_y0, bar_height),
                        facecolors=non_wear_colour, zorder=0)
        nbar = bars_for_day(nonwear_list, day_start, day_end)
        if nbar:
            axi.broken_barh(nbar, (base_y0, bar_height), facecolors=non_wear_colour)
        nbar1 = bars_for_day(category_dict.get('Non-Wear', []), day_start, day_end)
        if nbar1:
            axi.broken_barh(nbar1, (base_y0, bar_height), facecolors=non_wear_colour)

        # --- OPTIONAL LANES (one per enabled track)
        for lane in tracks_enabled:
            lane_y0 = y_positions[lane]
            if lane == 'CSD':
                csd_bar = bars_for_day(csd_list, day_start, day_end)
                if csd_bar:
                    axi.broken_barh(csd_bar, (lane_y0, bar_height), **category_styles["Transition"])
                    axi.text(day_start - pd.Timedelta(minutes=10), 
                                                      y_positions['CSD'],
                                                      "CSD",
                                                      ha='right', va='bottom', 
                                                      fontsize=font_size)
            elif lane == 'SLS':
                sls_bar = bars_for_day(sls_list, day_start, day_end)
                if sls_bar:
                    axi.broken_barh(sls_bar, (lane_y0, bar_height), **category_styles["Transition"])
                    axi.text(day_start - pd.Timedelta(minutes=10),
                                                    y_positions['SLS'],
                                                        "SLS",
                                                        ha='right', va='bottom', fontsize=font_size)
            elif lane == 'Transport':
                transport_bar = bars_for_day(transport_list, day_start, day_end)
                if transport_bar:
                    axi.broken_barh(transport_bar, (lane_y0, bar_height), **category_styles["Transition"])
                    axi.text(day_start - pd.Timedelta(minutes=10),
                                                        y_positions['Transport'],
                                                        "Transport",
                                                        ha='right', va='bottom', 
                                                        fontsize=font_size)

        axi.set_yticks([])             
        axi.set_ylabel("")            
        axi.tick_params(labelleft=False) 
        axi.set_ylim(0, yaxis_height)
        axi.set_xticklabels([])
        axi.grid(axis="x")
        
        # Annotation for day of the week 
        current_date = day_start
        axi.text(current_date + pd.Timedelta(hours=0.1), 
                yaxis_height *0.9,
                current_date.strftime('%A'),
                ha='left', va='center', fontsize = font_size)

    # Set x-axis to final subplot only
    axi.xaxis_date()
    # axi.xaxis.set_major_locator(mdates.HourLocator(byhour=[0,3,6,9, 12,15, 18,21, 24]))
    axi.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    axi.set_xlabel('Time of day')
    # Add vertical padding between subplots
    plt.subplots_adjust(hspace=0.2)

    if legend:
        if amputee:
            legend_list = ["Home","Community", "Transition"]
        else:    
            legend_list = ["Home","Sleep", "Community", "Transition"]
        fig.canvas.draw()  # ensure positions are finalized (after tight_layout/constrained_layout)
        top = max(ax.get_position().y1 for ax in fig.axes)  
        pad = 0  # gap between axes and legend 

        fig.legend(
            handles=[legend_handles[name] for name in legend_list if name in legend_handles],
            loc="lower center",                  
            bbox_to_anchor=(0.5, top + pad),     
            bbox_transform=fig.transFigure,      
            ncol=len(legend_list),
            frameon=True,
            fontsize=font_size,
        )

    if show:
        plt.show()
    return fig


import statistics

def run_algorithm(df, csd = 0,sls = 26,algo_type = 'CSDonly',seated_transport = False, amputee = False):
    ''' 
    input_dict should be the dictionary with key: participant ID and value: activPAL stepping bouts (df)
    Then select all other options e.g.: 
    df = run_algorithm(input_path=input_path,
                    id=1, 
                    csd = 0,
                    sls = 26, 
                    algo_type='CSDonly', 
                    seated_transport=True, 
                    amputee = False)
    '''
    

    algo_type = algo_type
    seated_transport = seated_transport
    amputee = amputee

    temp_df = df.copy()
    from . import identifiers
    algo_df = identifiers.transition_algorithm(
        temp_df, 
        algo_type=algo_type, 
        csd=csd, 
        sls=sls, 
        seated_transport=seated_transport, 
        amputee=amputee
    )

    return algo_df



def community_result(df):
    '''
    Input df should be the result of the run_algorithm function
    '''
    
    days = list(df['day_id'].unique())
    valid_days = []
    cp_days = 0
    active_times = []
    away_times = []

    for day in days: 
        day_df = df[df['day_id'] == day] 
        day_duration = day_df['Duration (s)'].sum()/60/60
        if day_duration >= 20:
            valid_days.append(day)
        
    for day in valid_days:     
        day_df = df[df['day_id'] == day] 
        away = day_df[day_df['community_classification'] == 'Community']
        time_away = away['Duration (s)'].sum()/60/60 # Hours
        away_times.append(time_away)

        active = away[away['Event Type'] == 2] #  | (away['Event Type'] == 2.1)] # Stepping or cycling
        time_active = active['Duration (s)'].sum()/60/60 # Hours
        active_times.append(time_active)

        transitions = day_df[day_df['transition'] == 'Primary']
        if len(transitions) >= 1:
            cp_days += 1

    # active_mean = round(sum(active_times)/len(active_times),2)
    active_std = round(statistics.stdev(active_times),2)
    active_median = round(statistics.median(active_times), 2)

    print(f"Median stepping time whilst away from home each day: {active_median} ± {active_std} hours") 

    # away_mean = round(sum(away_times)/len(away_times),2)
    away_std = round(statistics.stdev(away_times),2)
    away_median = round(statistics.median(away_times), 2)
    away_max = max(away_times)
    print(f"Median time away from home per day: {away_median} ± {away_std} hours") 

    print(f"Days active in Community: {cp_days}")
    cp_percent  = round(cp_days/len(valid_days)*100,2)
    print(f"Percentage of days active in community: {cp_percent}%")

    return 
    # return cp_days, cp_percent, active_times, active_mean, active_std, active_median, away_times, away_mean, away_std, away_median, away_max
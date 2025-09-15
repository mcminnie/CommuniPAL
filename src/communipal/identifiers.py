import numpy as np
import pandas as pd




def identify_event(row, algo_type, csd=None, sls=None, seated_transport=False, amputee=False):
    """
    Function to identify events based on chosen algorithm type and event characteristics.
    
    Args:
        row: DataFrame row with event data
        algo_type: Algorithm type ('CSDorSLS', 'CSDandSLS', 'CSDonly', 'SLSonly', 'STonly')
        sd_threshold: Stepping duration threshold
        sls_threshold: Straight line time threshold  
        seated_transport: Whether to include transport events as transitions
        amputee: Whether to use amputee-specific logic
        
    Returns:
        'lying', 'transition', or np.nan
    """
    
    # Handle amputee case
    if amputee:
        if (row['Event Type'] == 4) | (row['Event Type'] == 3.1):
            return 'sleeping'
        # return np.nan
    else:
        # Standard lying detection (consistent across all algorithms)
        if row['Event Type'] == 3.1:
            return 'sleeping'
        
    # Transport detection (when enabled)
    if seated_transport and row['Event Type'] == 5.0:
        return 'transition'
    
    # Stepping event detection (Event Type == 2)
    if row['Event Type'] == 2:
        if algo_type == 'CSDorSLS':
            if (row['Duration (s)'] > csd) | (row['Longest Straight Line Time (s)'] > sls):
                return 'transition'
        elif algo_type == 'CSDandSLS':
            if (row['Duration (s)'] > csd) & (row['Longest Straight Line Time (s)'] > sls):
                return 'transition'
        elif algo_type == 'CSDonly':
            if row['Duration (s)'] > csd:
                return 'transition'
        elif algo_type == 'SLSonly':
            if row['Longest Straight Line Time (s)'] > sls:
                return 'transition'
    
    # # Transport-only algorithm
    # if algo_type == 'STonly':
    #     # Already handled transport above, only lying remains
    #     return np.nan


    return np.nan

''' 
Used to label the identified transitions as either primary or secondary, according to what happens next. 
(Primary = between home and not)
(Secondary = between not and not) 
'''
def algorithm_transition_type(row, algo_type = None):
    if ((row['identifiers']) == 'transition') & ((row['identifiers']) != (row['next'])):
        return 'Primary'
    elif ((row['identifiers']) == 'transition') & ((row['identifiers']) != (row['previous'])):
        return 'Primary'
    elif ((row['identifiers']) == 'transition'):
        return 'Secondary'
    else:
        return None
    # elif (row['identifiers']) != 'lying':
        # return 'Secondary'

''' 
Used to assign a new column to the df to identify whether they are at home next or away.  
(transition - transition = Community)
(transition - sleeping = Home)
(sleeping - transition = Home) 
'''
def transition_change(row):
    if (row['next']) == 'sleeping':
        return 'Home'
    elif (row['identifiers'] == 'sleeping') & (row['next'] == 'transition'): 
        return 'Home'
    elif (row['identifiers'] == 'transition') & (row['next'] == 'transition'):
        return 'Community'
    
def return_leave(df):
    '''
    Adds return and leave labels to algorithm identified transitions, assigning the correct time based on leave = beginning of event, return = end of event. 
    Must be applied after transition_algorithm function.
    '''
    # Identify transitions. 
    df['algo_previous'] = df['community_classification'].shift(1)
    df['algo_next'] = df['community_classification'].shift(-1)

    df.loc[(df['algo_next'] == 'Home') & ( df['community_classification'] == 'Community') , 'return_leave'] = 'Return'
    df.loc[(df['community_classification'] == 'Community') & ( df['algo_previous'] == 'Home') , 'return_leave'] = 'Leave'

    # Add a column for the time of the transition
    df.loc[(df['return_leave'] == 'Leave'), 'transition_time'] = df['Start']
    df.loc[(df['return_leave'] == 'Return'), 'transition_time'] = (df['Start']) + pd.to_timedelta(df['Duration (s)'], unit='s')

    # Drop temporary columns
    remove_cols = ['algo_previous', 'algo_next']
    df = df.drop(columns=[col for col in remove_cols if col in df.columns])

    return df
    

def transition_algorithm(df, algo_type, csd=None, sls=None, seated_transport=False, amputee=False):
    """
    Unified transition algorithm that works with all algorithm types.
    
    Args:
        df: DataFrame with activPAL data
        algo_type: Algorithm type matching identify_event function ('CSDorSLS', 'CSDandSLS', 'CSDonly', 'SLSonly', 'STonly')
        csd_threshold: Continuous stepping duration threshold
        sls_threshold: Straight line stepping time threshold
        seated_transport: Whether to include transport events, defaults to False
        amputee: Whether to use amputee-specific logic, defaults to False
    """
    # Validate thresholds based on algo
    if algo_type in ('CSDorSLS', 'CSDonly') and csd is None:
        raise ValueError("csd threshold is required for this algo_type")
    if algo_type in ('CSDorSLS', 'SLSonly') and sls is None:
        raise ValueError("sls threshold is required for this algo_type")
    if algo_type == 'CSDandSLS' and (csd is None or sls is None):
        raise ValueError("Both csd and sls thresholds are required for CSDandSLS")
    df = df.copy()
    
    # Initialize identifiers column
    df['identifiers'] = np.nan
    
    # Apply the unified identify_event function
    df['identifiers'] = df.apply(
        lambda row: identify_event(
            row, 
            algo_type=algo_type, 
            csd=csd, 
            sls=sls, 
            seated_transport=seated_transport, 
            amputee=amputee
        ), 
        axis=1
    )
    
    # Create temporary dataframe with only identified events
    temp_transitions = df.dropna(subset='identifiers').copy()
    
    if temp_transitions.empty:
        # If no transitions found, return original dataframe with classification
        df['community_classification'] = 'Home'
        return df
    
    # Create shift columns for transition analysis
    temp_transitions['next'] = temp_transitions['identifiers'].shift(-1)
    temp_transitions['previous'] = temp_transitions['identifiers'].shift(1)
    
    # Apply transition change logic
    temp_transitions['transition_change'] = temp_transitions.apply(transition_change, axis=1)
    
    # Rejoin with original dataframe
    temp = temp_transitions[['next', 'previous', 'transition_change']]
    df = df.join(temp, how='left')  # preserves index alignment

    # df = pd.merge_ordered(df, temp_transitions, how='left')
    
    # Create algorithm classification - including forwards (then backwards) fill anything that isn't a transition. 
    df['community_classification'] = df['transition_change']
    df['community_classification'] = df['community_classification'].ffill()
    df['community_classification'] = df['community_classification'].bfill()
    
    # Mark transitions as 'Community'
    df['community_classification'] = np.where(
        df['identifiers'] == 'transition', 
        'Community', 
        df['community_classification']
    )
    
    # Handle Event Type 4 (non-wear/lying)
    if not amputee:
        df['community_classification'] = np.where(
            df['Event Type'] == 4, 
            'Non-wear', 
            df['community_classification']
        )
    else:
        df['community_classification'] = np.where(
            df['Event Type'] == 4, 
            'Home', 
            df['community_classification']
        )
    
    df['transition'] = df.apply(algorithm_transition_type, axis = 1) # Add primary or secondary transition labels
    df = return_leave(df) # Add return or leave transition labels
    # df['return_leave'] = df.apply(return_leave, axis = 1)


    # Drop temporary columns
    remove_cols = ['identifiers', 'next', 'previous', 'transition_change']
    df = df.drop(columns=[col for col in remove_cols if col in df.columns])
    
    return df




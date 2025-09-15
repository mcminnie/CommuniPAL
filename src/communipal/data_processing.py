import pandas as pd
import os
from tqdm import tqdm

def midnight_stop(df, start_col, end_col):  
    '''
    Correctly labels the days of events that go past midnight by splitting them into two events. 
    '''
    df = df.copy()
    df = df.reset_index(drop=True)
    # Ensure start and end columns are in datetime format
    df[start_col] = pd.to_datetime(df[start_col])
    df[end_col] = pd.to_datetime(df[end_col])


    df['start_date'] = df['Start'].dt.date # create a column that contains the start date without the time. 
    df['end_date'] = df['End'].dt.date # create a column that contains the end date without the time. 
    df['day_id'] = df['ID'].astype(str)+ '_' + df['start_date'].astype(str)
    df['past_midnight'] = df['start_date'] != df['end_date'] # Find the events where the start date is not the same as the end date

    rows_to_add = []  # List to store new rows that need to be inserted

    for index, row in df.iterrows():
        if row['past_midnight'] == True: 
            # Adjust original row end_time to last second of the start day
            original_row = row.copy()
            original_row[end_col] = pd.Timestamp(year=row[start_col].year, 
                                                    month=row[start_col].month, 
                                                    day=row[start_col].day, 
                                                    hour=23, 
                                                    minute=59, 
                                                    second=59)
            
            # Create a new row for the event continuing past midnight
            new_row = row.copy()
            new_row[start_col] = pd.Timestamp(year=row[end_col].year, 
                                                month=row[end_col].month, 
                                                day=row[end_col].day, 
                                                hour=0, 
                                                minute=0, 
                                                second=0)
            new_row['day_id'] = str(row['ID'])+ '_' + str(row['end_date'])
            
            # Update Duration (s) for both rows if necessary
            original_duration = (original_row[end_col] - row[start_col]).total_seconds()
            new_duration = (row[end_col] - new_row[start_col]).total_seconds()
            
            original_row['Duration (s)'] = original_duration
            new_row['Duration (s)'] = new_duration
            
            original_row = original_row.reindex(df.columns)

            # Update the DataFrame
            df.loc[index] = original_row
            rows_to_add.append((new_row.to_dict()))  # Save new row to add later

    # Add all the new rows to the DataFrame
    df = pd.concat([df, pd.DataFrame(rows_to_add)], ignore_index=True)
    # Remove unnecessary columns
    df.drop(['start_date', 
                    'end_date',
                    'past_midnight'],
                    axis=1, 
                    inplace=True)
    df = df.sort_values(by = start_col)

    return df


def import_multiple(path_pal):

    ''' 
    Imports all files in folder (path_pal) and returns a dictionary with ID number as key. 
    This works on stepping bout exports only, as it gives higher resolution than upright bouts. 
    If using upright bouts instead, need to change the 'Duration (s)' column to the stepping time column (Duration of the event is the stepping time in stepping bouts export). 
    '''

    dfs_pal = {}
    
    for file in tqdm(os.listdir(path_pal), desc = 'Importing activPAL files'):
        if file.endswith('.csv'):
            # Remove the file extension to get the dataframe name
            full_df_name = os.path.splitext(file)[0]
            # Use the first 2 characters of the filename as the key
            df_name = full_df_name[:2]
            # Read the CSV file
            df = pd.read_csv(os.path.join(path_pal, file), sep=';', usecols=range(16))
            # Set Date_Time as index to allow for merge with diary data
            df_column_name = df.columns[1]
            df['Date_Time'] = pd.to_datetime(df[df_column_name], format = "%Y-%m-%d %H:%M:%S")
            df = df.set_index(['Date_Time'])

            # Remove unnecessary columns
            df.drop(['Data Count', 
                     'Time(approx)',
                     'Upright Bout Number',
                     'Upright Bout Duration (s)',
                     'Num Steps',
                     'Cadence',
                     'Straight Line Time (s) (>=15s,<30s)',
                     'Straight Line Time (s) (>=30s,<45s)',
                     'Straight Line Time (s) (>=45s,<60s)',
                     'Straight Line Time (s) (>=60s)',
                     'Cumulative Positive Height Change (m)',
                     'Cumulative Negative Height Change (m)'],
                      axis=1, 
                      inplace=True)
            
            # Rename Time column to timestamp
            df.rename(columns={'Time': 'Timestamp'}, inplace=True)
            # Convert the timestamp to date/time format - more accurate than Date_Time.
            timestamp_startdate = '12/30/1899'
            df['Start'] = pd.to_datetime(timestamp_startdate) + (pd.to_timedelta(df['Timestamp'], unit='D'))
            # Add an end time for each event based on its duration.
            df['End'] = (df['Start']) + pd.to_timedelta(df['Duration (s)'], unit='s')
            df['past_midnight'] = df['Start'].dt.date != df['End'].dt.date 
            # Add an ID column with the first two characters of the CSV filename
            id = int(df_name)
            df['ID'] = id
            df['day_id'] = str(id) + '_' + df['Start'].dt.date.astype(str) 

            df = midnight_stop(df, 'Start', 'End')
            # Store the adjusted dataframe in the dictionary
            dfs_pal[id] = df
    
    return dfs_pal



def import_single(path_pal):

    ''' 
    Same as the import_multiple() function, but importing one at a time (so doesn't find the participant ID)
    This works on stepping bout exports only, as it gives higher resolution than upright bouts. 
    If using upright bouts instead, need to change the 'Duration (s)' column to the stepping time column (Duration of the event is the stepping time in stepping bouts export). 
    '''
    df = pd.read_csv(path_pal, sep=';', usecols=range(16))
    
    df_column_name = df.columns[1]
    df['Date_Time'] = pd.to_datetime(df[df_column_name], format = "%Y-%m-%d %H:%M:%S")
    
    df = df.set_index(['Date_Time'])

    # Remove unnecessary columns
    df.drop(['Data Count', 
                'Time(approx)',
                'Upright Bout Number',
                'Upright Bout Duration (s)',
                'Num Steps',
                'Cadence',
                'Straight Line Time (s) (>=15s,<30s)',
                'Straight Line Time (s) (>=30s,<45s)',
                'Straight Line Time (s) (>=45s,<60s)',
                'Straight Line Time (s) (>=60s)',
                'Cumulative Positive Height Change (m)',
                'Cumulative Negative Height Change (m)'],
                axis=1, 
                inplace=True)
    
    # Rename Time column to timestamp
    df.rename(columns={'Time': 'Timestamp'}, inplace=True)
    # Convert the timestamp to date/time format - more accurate than Date_Time.
    timestamp_startdate = '12/30/1899'
    df['Start'] = pd.to_datetime(timestamp_startdate) + (pd.to_timedelta(df['Timestamp'], unit='D'))
    # Add an end time for each event based on its duration.
    df['End'] = (df['Start']) + pd.to_timedelta(df['Duration (s)'], unit='s')
    
    # Stop an event that goes after midnight so it can be correctly attributed to the following day.
    df['ID'] = 0
    df['past_midnight'] = df['Start'].dt.date != df['End'].dt.date 
    df['day_id'] = df['Start'].dt.date.astype(str) 
    df = midnight_stop(df, 'Start', 'End')
    return df

'''
Example of running the classification model on a sample dataset. 
(single vs multiple participants.)
'''
# %%

import pandas as pd 
import communipal.data_processing as dp
import communipal.classification_model as cm
import communipal.timelines as timelines

# Single file import
df = dp.import_single("../sample_data/able_bodied/thigh/07_thigh-AP891502 204atmb 22Jul22 11-00am for 7d-GHLA-PB08110369-SteppingBouts.csv")
results_df = cm.run_algorithm(df, csd = 0, sls = 26, algo_type='SLSonly', seated_transport=False)
cm.community_result(results_df)

# Overlay can be 'CSD' or 'SLS'. 
timelines.stepping_overlay(results_df, overlay= 'SLS') 
timelines.stepping_overlay(results_df, overlay='CSD')
timelines.simple(results_df)


# Multiple file import
group_data = '../sample_data/able_bodied/shank'
group_dict = dp.import_multiple(group_data) # imports all files into dictionary with ID as the key (ID taken from beginning of filename) and csv as the value. 

# chosen_id = [6]
results = {}
for id, df in group_dict.items():
# for id in chosen_id:
    # df = group_dict[id]
    print(f"Participant: {id}")
    results_df = cm.run_algorithm(df, csd = 60, sls = 26, algo_type='CSDorSLS', seated_transport=True, amputee = True)
    cm.community_result(results_df)
    timelines.stepping_overlay(results_df, overlay='SLS', amputee=True)
    results[id] = results_df

# Example: compare between participants (dates must be the same). 
timelines.comparison(
    dfs={"Participant 4": results[4], "Participant 6": results[6]},
    amputee=False
)



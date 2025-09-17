'''
Example of running the classification model on a sample dataset. 
(single vs multiple participants.)
'''
# %%

import pandas as pd 
import communipal.data_processing as dp
import communipal.classification_model as cm
# import communipal.timelines as timelines

import sys
sys.path.append("../src/communipal")
import timelines

algo_type = 'CSDorSLS'
csd = 25
sls = 26
seated_transport = True

# Single file import
df = dp.import_single("../sample_data/able_bodied/thigh/07_thigh-AP891502 204atmb 22Jul22 11-00am for 7d-GHLA-PB08110369-SteppingBouts.csv")
results_df = cm.run_algorithm(df, csd = csd, sls = sls, algo_type=algo_type, seated_transport=seated_transport)
# cm.community_result(results_df)

# Overlay can be 'CSD' or 'SLS'. 
timelines.stepping_overlay(results_df, overlay= 'SLS') 
timelines.stepping_overlay(results_df, overlay='CSD')
timelines.simple(results_df)
timelines.transition_cause(results_df, 
                           algo_type = algo_type, 
                           csd_threshold = csd, 
                           sls_threshold = sls, 
                           seated_transport = seated_transport)

timelines.transition_type(results_df)
# %%
# Multiple file import
group_data = '../sample_data/lower_limb_amputee/shank'
group_dict = dp.import_multiple(group_data) # imports all files into dictionary with ID as the key (ID taken from beginning of filename) and csv as the value. 

# Compare algorithms
results1 = {}
results2 = {}
for id, df in group_dict.items():
    # print(f"Participant: {id}")
    results_df1 = cm.run_algorithm(df, 
                                  csd = 60, 
                                  sls = 26, 
                                  algo_type='CSDorSLS', seated_transport=True, 
                                  amputee = True)
    results_df2 = cm.run_algorithm(df, 
                                  csd = 0, 
                                  sls = 26, 
                                  algo_type='SLSonly', seated_transport=False, 
                                  amputee = True)
    
    # cm.community_result(results_df)
    results1[id] = results_df1
    results2[id] = results_df2

# Example: compare between participants (dates must be the same). 
timelines.comparison(
    dfs={"CSDorSLS": results1[4], 
         "SLSonly": results2[4]},
    amputee=False
)



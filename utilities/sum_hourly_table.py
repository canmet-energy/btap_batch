import os
import pandas as pd

simulation_type = 'parametric'

# Get the output directory and the location of the output file
os.chdir("..")
curr_dir = os.getcwd()
examples_dir = os.path.join(curr_dir, 'examples', simulation_type)

for file_example in os.listdir(examples_dir):
    d = os.path.join(examples_dir, file_example)
    if os.path.isdir(d):
        for folder_datapoint in os.listdir(d):
            dir_datapoint = os.path.join(examples_dir, file_example, folder_datapoint)
            for folder_result in os.listdir(dir_datapoint):
                dir_results = os.path.join(examples_dir, file_example, folder_datapoint, folder_result)
                for folder_hourly in os.listdir(dir_results):
                    dir_hourly = os.path.join(examples_dir, file_example, folder_datapoint, folder_result, folder_hourly)
                    if folder_hourly == 'hourly.csv':

                        datapoint_number = 0.0
                        df_output = []
                        for file_object in os.listdir(dir_hourly):
                            output_file = os.path.join(dir_hourly, "sum_hourly_res.csv")
                            if file_object != 'sum_hourly_res.csv':
                                datapoint = os.path.join(dir_hourly, file_object)
                                datapoint_empty = os.stat(datapoint).st_size == 0

                                if datapoint_empty == False:
                                    df = pd.read_csv(datapoint)
                                    df_columns = df.columns

                                    if datapoint_number == 0.0:
                                        df_output = []
                                        df_output = pd.DataFrame(columns=df_columns)

                                    df_names = df['Name']
                                    df_names = df_names.to_list()
                                    df_names_unique = [i for n, i in enumerate(df_names) if i not in df_names[:n]] # Remove duplicate names from df_names
                                    df_names_duplicate = [i for n, i in enumerate(df_names) if i in df_names[:n]] # Find duplicate items in df_names
                                    df_names_duplicate = [i for n, i in enumerate(df_names_duplicate) if i in df_names_duplicate[:n]] # Remove duplicate names from df_names_duplicate
                                    df_names_unique = new_list = [x for x in df_names_unique if (x not in df_names_duplicate)] # Remove whatever has a duplicate from df_names_unique

                                    for count_name, value_name in enumerate(df_names_unique):
                                        df_output = df_output.append(df.loc[df['Name']==value_name], True)

                                    for count_name, value_name in enumerate(df_names_duplicate):
                                        z = df.loc[df['Name'] == value_name]
                                        value_sum = z.sum()
                                        value_sum['datapoint_id'] = z['datapoint_id'].iloc[0]
                                        value_sum['Name'] = z['Name'].iloc[0]
                                        value_sum['KeyValue'] = ""
                                        value_sum['Units'] = z['Units'].iloc[0]
                                        df_output = df_output.append(value_sum, True)

                                    datapoint_number += 1.0

                        if len(df_output) > 0.0:
                            df_output.to_csv(output_file, index=False)
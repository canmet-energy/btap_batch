import logging
import os
import pathlib
import pandas as pd
import boto3
import botocore
import tqdm
import csv
from functools import partial
from concurrent.futures import ThreadPoolExecutor, as_completed
import shutil
import re
from src.btap.aws_credentials import AWSCredentials
from src.btap.aws_dynamodb import AWSResultsTable
from src.btap.aws_s3 import S3
from src.btap.constants import BASELINE_RESULTS
from icecream import ic

# This class processes the btap_batch file to add columns as needed. This is a separate class as this can be applied
# independant of simulation runs.

class PostProcessResults():
    def __init__(self,
                 baseline_results=BASELINE_RESULTS, #dataframe of reference runs
                 database_folder=None, # Path to location of analysis csv simulation results.. ie output/optimization/results/database
                 results_folder=None,  # Path to result folder ie output/optimization/results/ probably should be removed as redundant.
                 compute_environment=None, # where the analysis was run.
                 output_variables=None, # Custom E+ output varialbles.
                 username=None # username, usually aws username.
                 ):

        # ic(baseline_results)
        # ic(database_folder)
        # ic(results_folder)
        # ic(compute_environment)
        # ic(output_variables)
        # ic(username)



        logging.info(f'PostProcessResults(database_folder=r"{database_folder}", results_folder=r"{results_folder}, compute_environment ="{compute_environment}", output_variables="{output_variables}", username="{username}")')

        filepaths = [os.path.join(database_folder, f) for f in os.listdir(database_folder) if f.endswith('.csv')]
        btap_data_df = pd.concat(map(pd.read_csv, filepaths))
        btap_data_df.reset_index()

        # the primary fuel type should be set to the correct baseline if a HP is set in the :ecm_system_name
        def primary_fuel(row):
            if isinstance(row[':ecm_system_name'],str):
                if row[':primary_heating_fuel'] == "NaturalGas" and 'HP' in row[':ecm_system_name'] :
                    return 'NaturalGasHPGasBackup'
                if row[':primary_heating_fuel'] == "Electricity" and 'HP' in row[':ecm_system_name'] :
                    return 'ElectricityHPElecBackup'
            return row[':primary_heating_fuel']
        btap_data_df['orig_fuel_type'] = btap_data_df[':primary_heating_fuel']
        btap_data_df[':primary_heating_fuel'] = btap_data_df.apply(primary_fuel, axis=1)


        if isinstance(btap_data_df, pd.DataFrame):
            self.btap_data_df = btap_data_df
        else:
            self.btap_data_df = pd.read_excel(open(str(btap_data_df), 'rb'), sheet_name='btap_data')
        self.baseline_results = baseline_results
        self.results_folder = results_folder
        self.compute_environment = compute_environment
        self.output_variables = output_variables
        self.username = username

        #paths


    def run(self):
        self.reference_comparisons()
        self.get_files(file_paths=['run_dir/run/in.osm',
                                   'run_dir/run/eplustbl.htm',
                                   'hourly.csv',
                                   'run_dir/run/eplusout.sql'])
        self.save_excel_output()
        if self.compute_environment == 'aws_batch':
            self.save_dynamodb()
        self.operation_on_hourly_output()
        return self.btap_data_df

    # This method gets files from the run folders into the results folders.  This is both for S3 and local analyses.
    # This is all done serially...if this is too slow, we should implement a parallel method using threads.. While probably
    # Not an issue for local analyses, it may be needed for large run. Here is an example of somebody with an example of parallel
    # downloads from S3 using threads.  https://emasquil.github.io/posts/multithreading-boto3/
    def get_files(self, file_paths=['run_dir/run/in.osm',
                                   'run_dir/run/eplustbl.htm',
                                   'hourly.csv',
                                   'run_dir/run/eplusout.sql']):
        for file_path in file_paths:
            pathlib.Path(os.path.dirname(self.results_folder)).mkdir(parents=True, exist_ok=True)
            filename = os.path.basename(file_path)
            extension = pathlib.Path(filename).suffix
            message = f"Getting {filename} files"
            logging.info(message)
            bin_folder = os.path.join(self.results_folder, filename)
            os.makedirs(bin_folder, exist_ok=True)
            s3 = boto3.resource('s3')
            func = partial(self.download_file, bin_folder, extension, file_path, s3)
            files = self.btap_data_df['datapoint_output_url'].tolist()
            failed_downloads = []

            with tqdm.tqdm(desc=f"Downloading {filename} files", total=len(self.btap_data_df.index),
                           colour='green') as pbar:
                with ThreadPoolExecutor(max_workers=32) as executor:
                    # Using a dict for preserving the downloaded file for each future, to store it as a failure if we need that
                    futures = {
                        executor.submit(func, row): row for index, row in self.btap_data_df.iterrows()
                    }
                    for future in as_completed(futures):
                        if future.exception():
                            failed_downloads.append(futures[future])
                        pbar.update(1)
            if len(failed_downloads) > 0:
                failed_csv_list = os.path.join(self.results_folder, "failed_downloads.csv")
                message = f"Some downloads have failed. Saving ids to csv here: {failed_csv_list}"
                logging.error(message)
                print(message)
                with open(
                        os.path.join(self.results_folder, "failed_downloads.csv"), "w", newline=""
                ) as csvfile:
                    wr = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
                    wr.writerow(failed_downloads)

    def download_file(self, bin_folder, extension, file_path, s3, row):
        # If files are local
        if row['datapoint_output_url'].startswith('file:///'):
            # This is a local file. use system copy. First remove prefix
            local_file_path = os.path.join(row['datapoint_output_url'][len('file:///'):], file_path)
            if os.path.isfile(local_file_path):
                shutil.copyfile(local_file_path, os.path.join(bin_folder, row[':datapoint_id'] + extension))

        # If files are on S3
        elif row['datapoint_output_url'].startswith('https://s3'):
            p = re.compile(
                "https://s3\.console\.aws\.amazon\.com/s3/buckets/(\d*)\?region=(.*)&prefix=(.*)")
            m = p.match(row['datapoint_output_url'])
            bucket = m.group(1)
            region = m.group(2)
            prefix = m.group(3)
            s3_file_path = prefix + file_path
            target_on_local = os.path.join(bin_folder, row[':datapoint_id'] + extension)
            message = f"Getting file from S3 bucket {bucket} at path {s3_file_path} to {target_on_local}"
            logging.info(message)
            try:
                s3.Bucket(bucket).download_file(s3_file_path, target_on_local)
            except botocore.exceptions.ClientError as e:
                if e.response['Error']['Code'] == "404":
                    print("The object does not exist.")
                else:
                    raise
            # Copy output files ('run_dir/run/in.osm', 'run_dir/run/eplustbl.htm', 'hourly.csv') to s3 for storage.

            target_path_on_aws = os.path.join("/".join(s3_file_path.split("/")[:3]), 'results', os.path.basename(file_path),
                                              row[':datapoint_id'] + extension)
            target_path_on_aws = target_path_on_aws.replace('\\', '/')  # s3 likes forward slashes.
            message = "Uploading %s..." % target_path_on_aws
            logging.info(message)
            S3().upload_file(target_on_local, AWSCredentials().account_id, target_path_on_aws)

    def save_excel_output(self):
        # Create excel object
        excel_path = os.path.join(self.results_folder, 'output.xlsx')
        with pd.ExcelWriter(excel_path) as writer:
            if isinstance(self.btap_data_df, pd.DataFrame):
                self.btap_data_df.to_excel(writer, index=False, sheet_name='btap_data')
                message = f'Saved Excel Output: {excel_path}'
                logging.info(message)
                print(message)
            else:
                message = 'No simulations completed.'
                logging.error(message)

    def save_dynamodb(self):
        AWSResultsTable().save_results(dataframe=self.btap_data_df)



    # The below operation_on_hourly_output method is for performing operations on hourly output; for instance, sum of hourly data
    def operation_on_hourly_output(self):

        # Go through each folder in the results folder.
        for folder_in_results_name in os.listdir(self.results_folder):
            # Find path of the results folder
            folder_in_results_path = os.path.join(self.results_folder, folder_in_results_name)
            if folder_in_results_name == 'hourly.csv':
                # Get variables specified in the :output_variables variable
                output_var = self.output_variables
                # Get number of variables specified in the :output_variables variable
                output_var_length = len(output_var)

                datapoint_number = 0.0
                df_output = []
                output_file = None
                for file_object in os.listdir(folder_in_results_path):
                    # Set path of the output file that will be generated by the operation_on_hourly_output method
                    output_file = os.path.join(folder_in_results_path, "sum_hourly_res.csv")

                    if file_object != 'sum_hourly_res.csv':
                        # Find path of the datapoint in the hourly.csv folder of the results folder
                        datapoint_path = os.path.join(folder_in_results_path, file_object)

                        # Check if the datapoint is empty or not
                        if os.stat(datapoint_path).st_size == 0:
                            datapoint_empty = True
                        else:
                            datapoint_empty = False

                        # Go through datapoint if it is not empty
                        if datapoint_empty == False:

                            # Read the datapoint csv file
                            df = pd.read_csv(datapoint_path)

                            # Get column headers of the df
                            df_columns = df.columns

                            # Create an empty dataframe with the 'df_columns' column headers
                            if datapoint_number == 0.0:
                                df_output = pd.DataFrame(columns=df_columns)

                            # Go through each variable of output_var; Do below items for only the ones that their value for 'operation' in the .yml file is not '*'
                            for count_operation_var in range(0, output_var_length):
                                operation_var = output_var[count_operation_var]['variable']
                                operation_case = output_var[count_operation_var]['operation']
                                operation_unit = output_var[count_operation_var]['unit']
                                if operation_var not in df_output['Name']:
                                    list_data = []
                                    df_operation_var = df.loc[df['Name'] == operation_var]
                                    if operation_case == 'sum':
                                        if operation_unit == 'GJ':
                                            list_data.append(df_operation_var.iloc[:, 4:].sum(axis=0) / 10 ** 9)
                                        elif operation_unit == 'kWh':
                                            list_data.append(277.778 * df_operation_var.iloc[:, 4:].sum(axis=0) / 10 ** 9)
                                        elif operation_unit != '*':
                                            message = f"Unknown unit for the sum operation on hourly outputs. Allowed units are GJ and kWh."
                                            logging.error(message)

                                        value_sum = pd.DataFrame(list_data, columns=df_columns)
                                        value_sum['datapoint_id'] = df_operation_var['datapoint_id'].iloc[0]
                                        value_sum['Name'] = df_operation_var['Name'].iloc[0]
                                        value_sum['KeyValue'] = ""
                                        value_sum['Units'] = operation_unit

                                        df_output = pd.concat([value_sum, df_output])
                                    elif operation_case != '*':
                                        message = f"Unknown operation type on hourly outputs. Allowed operation type is sum."
                                        logging.error(message)

                            # Go to the next datapoint
                            datapoint_number += 1.0
                if len(df_output) > 0.0:

                    # Save the df_output as the output_file
                    df_output.to_csv(output_file, index=False)

                    # Copy sum_hourly_res.csv to s3 for storage if run on AWS.
                    if self.compute_environment == "aws_batch":
                        sum_hourly_res_path = os.path.join(self.results_folder, 'hourly.csv', 'sum_hourly_res.csv')
                        target_path_on_aws = os.path.join(self.username,
                                                          "\\".join(sum_hourly_res_path.split("\\")[-5:])).replace('\\', '/')

                        message = "Uploading %s..." % target_path_on_aws
                        print(message)
                        logging.info(message)
                        S3().upload_file(file=sum_hourly_res_path, bucket_name=AWSCredentials().account_id, target_path=target_path_on_aws)


    def reference_comparisons(self):
        self.baseline_df = self.baseline_results
        if isinstance(self.baseline_df, pd.DataFrame):
            merge_columns = [':building_type', ':template', ':primary_heating_fuel', ':epw_file']
            df = pd.merge(self.btap_data_df, self.baseline_df, how='left', left_on=merge_columns,
                          right_on=merge_columns).reset_index()  # Note: in this case, the 'x' suffix stands for the proposed building; and 'y' stands for the baseline (reference) building

            if (('cost_utility_neb_total_cost_per_m_sq_y' in df.columns) and (
                    'cost_utility_neb_total_cost_per_m_sq_x' in df.columns)):
                self.btap_data_df['baseline_savings_energy_cost_per_m_sq'] = round(
                    (df['cost_utility_neb_total_cost_per_m_sq_y'] - df[
                        'cost_utility_neb_total_cost_per_m_sq_x']), 1).values

            self.btap_data_df['baseline_difference_energy_eui_electricity_gj_per_m_sq'] = round(
                (df['energy_eui_electricity_gj_per_m_sq_y'] - df[
                    'energy_eui_electricity_gj_per_m_sq_x']), 1).values

            self.btap_data_df['baseline_difference_energy_eui_natural_gas_gj_per_m_sq'] = round(
                (df['energy_eui_natural_gas_gj_per_m_sq_y'] - df[
                    'energy_eui_natural_gas_gj_per_m_sq_x']), 1).values

            self.btap_data_df['baseline_difference_energy_eui_additional_fuel_gj_per_m_sq'] = round(
                (df['energy_eui_additional_fuel_gj_per_m_sq_y'] - df[
                    'energy_eui_additional_fuel_gj_per_m_sq_x']), 1).values

            costing_columns = [
                'cost_equipment_envelope_total_cost_per_m_sq',
                'cost_equipment_heating_and_cooling_total_cost_per_m_sq',
                'cost_equipment_lighting_total_cost_per_m_sq',
                'cost_equipment_renewables_total_cost_per_m_sq',
                'cost_equipment_shw_total_cost_per_m_sq',
                'cost_equipment_thermal_bridging_total_cost_per_m_sq',
                'cost_equipment_ventilation_total_cost_per_m_sq']
            for name in costing_columns:
                self.add_baseline_diff(df, name)



            if (('cost_equipment_total_cost_per_m_sq_y' in df.columns) and (
                    'cost_equipment_total_cost_per_m_sq_x' in df.columns)):
                self.btap_data_df['baseline_difference_cost_equipment_total_cost_per_m_sq'] = round(
                    (df['cost_equipment_total_cost_per_m_sq_y'] - df[
                        'cost_equipment_total_cost_per_m_sq_x']), 1).values

            if (('baseline_difference_cost_equipment_total_cost_per_m_sq' in df.columns) and (
                    'baseline_savings_energy_cost_per_m_sq' in df.columns)):
                self.btap_data_df['baseline_simple_payback_years'] = round(
                    (self.btap_data_df['baseline_difference_cost_equipment_total_cost_per_m_sq'] / self.btap_data_df[
                        'baseline_savings_energy_cost_per_m_sq']), 1).values

            self.btap_data_df['baseline_peak_electric_percent_better'] = round(
                ((df['energy_peak_electric_w_per_m_sq_y'] - df[
                    'energy_peak_electric_w_per_m_sq_x']) * 100.0 / df['energy_peak_electric_w_per_m_sq_y']), 1).values

            self.btap_data_df['baseline_energy_percent_better'] = round(((df['energy_eui_total_gj_per_m_sq_y'] - df[
                'energy_eui_total_gj_per_m_sq_x']) * 100 / df['energy_eui_total_gj_per_m_sq_y']), 1).values

            self.btap_data_df['baseline_necb_tier'] = pd.cut(self.btap_data_df['baseline_energy_percent_better'],
                                                             bins=[-1000.0, -0.001, 25.00, 50.00, 60.00, 1000.0],
                                                             labels=['non_compliant', 'tier_1', 'tier_2', 'tier_3',
                                                                     'tier_4']).values

            self.btap_data_df['baseline_ghg_percent_better'] = round(((df['cost_utility_ghg_total_kg_per_m_sq_y'] - df[
                'cost_utility_ghg_total_kg_per_m_sq_x']) * 100 / df['cost_utility_ghg_total_kg_per_m_sq_y']), 1).values

            if (('npv_total_per_m_sq_y' in df.columns) and ('npv_total_per_m_sq_x' in df.columns)):
                self.btap_data_df['baseline_difference_npv_total_per_m_sq'] = round(
                    (df['npv_total_per_m_sq_y'] - df[
                        'npv_total_per_m_sq_x']), 1).values

                # Unmet cooling hours of the reference building
                self.btap_data_df['baseline_unmet_hours_cooling'] = df['unmet_hours_cooling_y']
                self.btap_data_df['baseline_unmet_hours_cooling_during_occupied'] = df[
                    'unmet_hours_cooling_during_occupied_y']

                # Outdoor-air-related outputs of the reference building
                self.btap_data_df['baseline_airloops_total_outdoor_air_mechanical_ventilation_ach_1_per_hr'] = df[
                    'airloops_total_outdoor_air_mechanical_ventilation_ach_1_per_hr_y']
                self.btap_data_df[
                    'baseline_airloops_total_outdoor_air_mechanical_ventilation_flow_per_conditioned_floor_area_m3_per_s_m2'] = df['airloops_total_outdoor_air_mechanical_ventilation_flow_per_conditioned_floor_area_m3_per_s_m2_y']
                self.btap_data_df[
                    'baseline_airloops_total_outdoor_air_mechanical_ventilation_flow_per_exterior_area_m3_per_s_m2'] = df['airloops_total_outdoor_air_mechanical_ventilation_flow_per_exterior_area_m3_per_s_m2_y']
                self.btap_data_df['baseline_airloops_total_outdoor_air_mechanical_ventilation_m3'] = df[
                    'airloops_total_outdoor_air_mechanical_ventilation_m3_y']
                self.btap_data_df['baseline_airloops_total_outdoor_air_natural_ventilation_ach_1_per_hr'] = df[
                    'airloops_total_outdoor_air_natural_ventilation_ach_1_per_hr_y']
                self.btap_data_df[
                    'baseline_airloops_total_outdoor_air_natural_ventilation_flow_per_conditioned_floor_area_m3_per_s_m2'] = df['airloops_total_outdoor_air_natural_ventilation_flow_per_conditioned_floor_area_m3_per_s_m2_y']
                self.btap_data_df[
                    'baseline_airloops_total_outdoor_air_natural_ventilation_flow_per_exterior_area_m3_per_s_m2'] = df[
                    'airloops_total_outdoor_air_natural_ventilation_flow_per_exterior_area_m3_per_s_m2_y']
                self.btap_data_df['baseline_airloops_total_outdoor_air_natural_ventilation_m3'] = df[
                    'airloops_total_outdoor_air_natural_ventilation_m3_y']
                self.btap_data_df['baseline_zones_total_outdoor_air_infiltration_ach_1_per_hr'] = df[
                    'zones_total_outdoor_air_infiltration_ach_1_per_hr_y']
                self.btap_data_df[
                    'baseline_zones_total_outdoor_air_infiltration_flow_per_conditioned_floor_area_m3_per_s_m2'] = df[
                    'zones_total_outdoor_air_infiltration_flow_per_conditioned_floor_area_m3_per_s_m2_y']
                self.btap_data_df['baseline_zones_total_outdoor_air_infiltration_flow_per_exterior_area_m3_per_s_m2'] = df['zones_total_outdoor_air_infiltration_flow_per_exterior_area_m3_per_s_m2_y']
                self.btap_data_df['baseline_zones_total_outdoor_air_infiltration_m3'] = df[
                    'zones_total_outdoor_air_infiltration_m3_y']
                self.btap_data_df['baseline_zones_total_outdoor_air_mechanical_ventilation_ach_1_per_hr'] = df[
                    'zones_total_outdoor_air_mechanical_ventilation_ach_1_per_hr_y']
                self.btap_data_df[
                    'baseline_zones_total_outdoor_air_mechanical_ventilation_flow_per_conditioned_floor_area_m3_per_s_m2'] = df['zones_total_outdoor_air_mechanical_ventilation_flow_per_conditioned_floor_area_m3_per_s_m2_y']
                self.btap_data_df[
                    'baseline_zones_total_outdoor_air_mechanical_ventilation_flow_per_exterior_area_m3_per_s_m2'] = df[
                    'zones_total_outdoor_air_mechanical_ventilation_flow_per_exterior_area_m3_per_s_m2_y']
                self.btap_data_df['baseline_zones_total_outdoor_air_mechanical_ventilation_m3'] = df[
                    'zones_total_outdoor_air_mechanical_ventilation_m3_y']
                self.btap_data_df['baseline_zones_total_outdoor_air_natural_ventilation_ach_1_per_hr'] = df[
                    'zones_total_outdoor_air_natural_ventilation_ach_1_per_hr_y']
                self.btap_data_df[
                    'baseline_zones_total_outdoor_air_natural_ventilation_flow_per_conditioned_floor_area_m3_per_s_m2'] = df['zones_total_outdoor_air_natural_ventilation_flow_per_conditioned_floor_area_m3_per_s_m2_y']
                self.btap_data_df[
                    'baseline_zones_total_outdoor_air_natural_ventilation_flow_per_exterior_area_m3_per_s_m2'] = df[
                    'zones_total_outdoor_air_natural_ventilation_flow_per_exterior_area_m3_per_s_m2_y']
                self.btap_data_df['baseline_zones_total_outdoor_air_natural_ventilation_m3'] = df[
                    'zones_total_outdoor_air_natural_ventilation_m3_y']

    def add_baseline_percent_diff(self, df, name):
        if ((name + '_y' in df.columns) and (
                name + '_x' in df.columns)):
            self.btap_data_df['baseline_percent_difference_'+ name] = round(
                ((df[name + '_y'] - df[
                    name + '_x' ]) * 100.0 / df[name + '_y']), 1).values

    def add_baseline_diff(self, df, name):
        if ((name + '_y' in df.columns) and (
                name + '_x' in df.columns)):
            self.btap_data_df['baseline_difference_'+name ] = round(
                (df[name + '_y'] - df[name + '_x' ]), 1).values


# PostProcessResults(baseline_results=None,
#                    database_folder=r"C:\Users\plopez\btap_batch\output\parametric_example\parametric\results\database",
#                    results_folder=r"C:\Users\plopez\btap_batch\output\parametric_example\parametric\results",
#                    compute_environment="aws_batch",
#                    output_variables=[],
#                    username="phylroy_lopez")

#
# PostProcessResults(baseline_results=None,
#                    database_folder=r"/home/plopez/btap_batch/output/parametric_example/reference/results/database",
#                    results_folder=r"/home/plopez/btap_batch/output/parametric_example/reference/results",
#                    compute_environment ="local_docker",
#                    output_variables=[], username="lowrise_apartment").run()
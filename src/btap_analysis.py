import openstudio
import logging
import os
import pathlib
import docker
import uuid
import time
import yaml
import pandas as pd
import boto3,botocore
import tqdm
import csv
from functools import partial
from concurrent.futures import ThreadPoolExecutor, as_completed
import shutil
import re

from sklearn import preprocessing
from .exceptions import OSMErrorException
from docker.errors import DockerException
from .aws_batch import AWSCredentials,S3
from .helper import batch_factory
from .constants import BASELINE_RESULTS, NECB2011_SPACETYPE_PATH, BTAP_BATCH_VERSION
from .btap_engine import BTAPEngine

# This class processes the btap_batch file to add columns as needed. This is a separate class as this can be applied
# independant of simulation runs.
class PostProcessResults():
    def __init__(self,
                 baseline_results=BASELINE_RESULTS,
                 database_folder=None,
                 results_folder=None
                 ):

        filepaths = [os.path.join(database_folder, f) for f in os.listdir(database_folder) if f.endswith('.csv')]
        btap_data_df = pd.concat(map(pd.read_csv, filepaths))
        btap_data_df.reset_index()

        if isinstance(btap_data_df, pd.DataFrame):
            self.btap_data_df = btap_data_df
        else:
            self.btap_data_df = pd.read_excel(open(str(btap_data_df), 'rb'), sheet_name='btap_data')
        self.baseline_results = baseline_results
        self.results_folder = results_folder

    def run(self):
        self.reference_comparisons()
        self.get_files(file_paths=['run_dir/run/in.osm', 'run_dir/run/eplustbl.htm', 'hourly.csv'])
        self.save_excel_output()
        self.operation_on_hourly_output()
        return self.btap_data_df

    # This method gets files from the run folders into the results folders.  This is both for S3 and local analyses.
    # This is all done serially...if this is too slow, we should implement a parallel method using threads.. While probably
    # Not an issue for local analyses, it may be needed for large run. Here is an example of somebody with an example of parallel
    # downloads from S3 using threads.  https://emasquil.github.io/posts/multithreading-boto3/
    def get_files(self, file_paths=None):
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
            self.credentials = AWSCredentials()
            target_path_on_aws = os.path.join("/".join(s3_file_path.split("/")[:3]), 'results', file_path,
                                              row[':datapoint_id'] + extension)
            target_path_on_aws = target_path_on_aws.replace('\\', '/')  # s3 likes forward slashes.
            message = "Uploading %s..." % target_path_on_aws
            logging.info(message)
            S3().upload_file(target_on_local, self.credentials.account_id, target_path_on_aws)

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

    # The below operation_on_hourly_output method is for performing operations on hourly output; for instance, sum of hourly data
    def operation_on_hourly_output(self):
        # Find the directory of results
        dir_results = self.results_folder

        # Go through each folder in the results folder.
        for folder_in_results_name in os.listdir(dir_results):
            # Find path of the results folder
            folder_in_results_path = os.path.join(self.results_folder, folder_in_results_name)
            if folder_in_results_name == 'hourly.csv':
                # Find path of the folder where the .yml file is
                yml_file_folder_path = "\\".join(folder_in_results_path.split("\\")[:-4])
                # Find path of the .yml file
                yml_file_path = os.path.join(yml_file_folder_path, 'input.yml')
                # Get inputs in the .yml file
                engine = BTAPEngine(analysis_config_file=yml_file_path)
                analysis_config = engine.analysis_config
                # Get variables specified in the :output_variables variable
                output_var = analysis_config[':output_variables']
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
                                df_output = []
                                df_output = pd.DataFrame(columns=df_columns)

                            # Go through each variable of output_var; Do below items for only the ones that their value for 'operation' in the .yml file is not '*'
                            for count_operation_var in range(0, output_var_length):
                                operation_var = output_var[count_operation_var]['variable']
                                operation_case = output_var[count_operation_var]['operation']
                                operation_unit = output_var[count_operation_var]['unit']
                                if operation_var not in df_output['Name']:
                                    value_sum = None
                                    df_operation_var = df.loc[df['Name'] == operation_var]
                                    if operation_case == 'sum':
                                        if operation_unit == 'GJ':
                                            value_sum = df_operation_var.iloc[:, 4:].sum(axis=0) / 10 ** 9
                                            value_sum['Units'] = 'GJ'
                                        elif operation_unit == 'kWh':
                                            value_sum = 277.778 * df_operation_var.iloc[:, 4:].sum(axis=0) / 10 ** 9
                                            value_sum['Units'] = 'kWh'
                                        elif operation_unit != '*':
                                            message = f"Unknown unit for the sum operation on hourly outputs. Allowed units are GJ and kWh."
                                            logging.error(message)
                                        value_sum['datapoint_id'] = df_operation_var['datapoint_id'].iloc[0]
                                        value_sum['Name'] = df_operation_var['Name'].iloc[0]
                                        value_sum['KeyValue'] = ""
                                        df_output = df_output.append(value_sum, True)
                                        #df_output = pd.concat([df_output, value_sum], ignore_index=True)
                                    elif operation_case != '*':
                                        message = f"Unknown operation type on hourly outputs. Allowed operation type is sum."
                                        logging.error(message)
                            # Go to the next datapoint
                            datapoint_number += 1.0

                if len(df_output) > 0.0:

                    # Save the df_output as the output_file
                    df_output.to_csv(output_file, index=False)

                    # Copy sum_hourly_res.csv to s3 for storage if run on AWS.
                    try:
                        sum_hourly_res_path = os.path.join(self.results_folder, 'hourly.csv', 'sum_hourly_res.csv')
                        self.credentials = AWSCredentials()
                        target_path_on_aws = os.path.join(self.credentials.user_name,
                                                          "\\".join(sum_hourly_res_path.split("\\")[-5:]))
                        target_path_on_aws = target_path_on_aws.replace('\\', '/')  # s3 likes forward slashes.
                        message = "Uploading %s..." % target_path_on_aws
                        logging.info(message)
                        S3().upload_file(sum_hourly_res_path, self.credentials.account_id, target_path_on_aws)
                    except:
                        print('Run locally. No need to copy sum_hourly_res.csv to s3')

    def reference_comparisons(self):
        if self.baseline_results != None:
            file = open(self.baseline_results, 'rb')
            self.baseline_df = pd.read_excel(file, sheet_name='btap_data')
            file.close()
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


# Parent Analysis class from with all analysis inherit
class BTAPAnalysis():
    # This does some simple check on the osm file to ensure that it has the required inputs for btap.
    def check_list(self, osm_file):
        print("Preflight check of local osm file.")
        # filepath = r"C:\Users\plopez\PycharmProjects\btap_batch\examples\idp\idp_example_elim\b6056cd4-e4f5-44eb-ae57-73b624faa5ce\output\0fba95bd-455a-44f4-8532-2e167a95cffa\sizing_folder\autozone_systems\run\in.osm"
        version_translator = openstudio.osversion.VersionTranslator()
        model = version_translator.loadModel(openstudio.path(osm_file)).get()
        necb_lib = openstudio.osversion.VersionTranslator().loadModel(openstudio.path(NECB2011_SPACETYPE_PATH)).get()

        messages = ''
        if not model.getBuilding().standardsBuildingType().is_initialized():
            messages += f"OS:Building, you have not defined the standardsBuildingType\n"

        if not model.getBuilding().standardsNumberOfAboveGroundStories().is_initialized():
            messages += f"OS:Building, you have not defined the standardsNumberOfAboveGroundStories\n"

        if not model.getBuilding().standardsNumberOfStories().is_initialized():
            messages += f"OS:Building, you have not defined the standardsNumberOfStories\n"

        for space in model.getSpaces():
            if not space.spaceType().is_initialized():
                messages += f"OS:Space {space.name().get()} does not have a spacetype defined.\n"

            if not space.thermalZone().is_initialized():
                messages += f"OS:Space {space.name().get()} is not associated with a zone.\n"
        model_spacetypes = []
        for spacetype in model.getSpaceTypes():
            if not spacetype.standardsBuildingType().is_initialized():
                messages += f"OS:SpaceType {spacetype.name().get()} does not have a standardBuildingType defined.\n"
            if not spacetype.standardsSpaceType().is_initialized():
                messages += f"OS:SpaceType {spacetype.name().get()} does not have a standardsSpaceType defined.\n"

            if spacetype.standardsSpaceType().is_initialized() and spacetype.standardsBuildingType().is_initialized():
                model_spacetypes.append(spacetype.standardsBuildingType().get() + spacetype.standardsSpaceType().get())

        # Check if we are using NECB2011 spacetypes
        necb_spacetypes = list(
            map(lambda spacetype: spacetype.standardsBuildingType().get() + spacetype.standardsSpaceType().get(),
                necb_lib.getSpaceTypes()))
        for st in model_spacetypes:
            if not st in necb_spacetypes:
                messages += f"OS:SpaceType {st} is not associated a valid NECB2011 spacetype.\n"

        if len(messages) > 0:
            logging.error(f"The errors below need to be fixed in your osm file.\n{messages}\n")
            raise OSMErrorException(f"The osm file {osm_file} is misconfigured.. Analysis aborted.\n")

    def get_local_osm_files(self):
        osm_list = {}
        osm_folder = os.path.join(self.engine.project_root, 'osm_folder')
        if pathlib.Path(osm_folder).is_dir():
            for file in os.listdir(osm_folder):
                if file.endswith(".osm"):
                    osm_list[os.path.splitext(file)[0]] = os.path.join(osm_folder, file)
        return osm_list

    # Constructor will
    def __init__(self,
                 engine=None,
                 batch=None):
        self.credentials = None
        self.batch = batch
        self.btap_data_df = []
        self.failed_df = []
        self.engine = engine


        # Making sure that used installed docker.
        find_docker = os.system("docker -v")
        if find_docker != 0:
            logging.exception("Docker is not installed on this system")

        # Try to access the docker daemon. If we cannot.. ask user to turn it on and then exit.
        try:
            docker.from_env()
        except DockerException as err:
            logging.error(
                f"Could not access Docker Daemon. Either it is not running, or you do not have permissions to run docker. {err}")
            exit(1)

        # Create required paths and folders for analysis
        self.create_paths_folders()

        # If batch object has not been pass/created.. make one.
        # This really should be replaced with a https://en.wikipedia.org/wiki/Factory_method_pattern.
        if self.batch is None:
            self.batch = batch_factory(engine=self.engine)


    def get_num_of_runs_failed(self):
        if os.path.isdir(self.failures_folder):
            return len([name for name in os.listdir(self.failures_folder) if
                        os.path.isfile(os.path.join(self.failures_folder, name))])
        else:
            return 0

    def get_num_of_runs_completed(self):

        if os.path.isdir(self.database_folder):
            return len([name for name in os.listdir(self.database_folder) if
                        os.path.isfile(os.path.join(self.database_folder, name))])
        else:
            return 0

    # This methods sets the pathnames and creates the input and output folders for the analysis. It also initilizes the
    # sql database.
    def create_paths_folders(self):

        # Create analysis folder
        os.makedirs(self.engine.project_root, exist_ok=True)

        # Create unique id for the analysis if not given.
        if self.engine.analysis_config[':analysis_id'] is None:
            self.engine.analysis_config[':analysis_id'] = str(uuid.uuid4())

        # Tell user and logger id and names
        print(f'analysis_id is: {self.engine.analysis_config[":analysis_id"]}')
        print(f'analysis_name is: {self.engine.analysis_config[":analysis_name"]}')
        print(f'analysis type is: {self.engine.analysis_config[":algorithm"][":type"]}')
        logging.info(f'analysis_id:{self.engine.analysis_config[":analysis_id"]}')
        logging.info(f'analysis_name:{self.engine.analysis_config[":analysis_name"]}')
        logging.info(f'analysis type is: {self.engine.analysis_config[":algorithm"][":type"]}')

        # Set analysis name folder.
        self.analysis_name_folder = os.path.join(self.engine.project_root, self.engine.analysis_config[':analysis_name'])
        logging.info(f'analysis_folder:{self.analysis_name_folder}')
        self.analysis_id_folder = os.path.join(self.analysis_name_folder,
                                               self.engine.analysis_config[':analysis_id'])
        logging.info(f'analysis_id_folder:{self.analysis_id_folder}')

        # Tell log we are deleting previous runs.
        message = f'Deleting previous runs from: {self.analysis_name_folder}'
        logging.info(message)
        print(message)
        # Check if folder exists
        if os.path.isdir(self.analysis_name_folder):
            # Remove old folder
            try:
                shutil.rmtree(self.analysis_name_folder)
            except PermissionError as err:
                message = f'Could not delete {self.analysis_name_folder}. Do you have a file open in that folder? Exiting'
                print(message)
                logging.error(message)
                exit(1)

        message = f'Creating new folders for analysis'
        logging.info(message)
        print(message)
        # create local input and output folders
        self.input_folder = os.path.join(self.analysis_id_folder,
                                         'input')
        self.output_folder = os.path.join(self.analysis_id_folder,
                                          'output')
        self.results_folder = os.path.join(self.analysis_id_folder,
                                           'results')
        self.database_folder = os.path.join(self.results_folder,
                                            'database')
        self.failures_folder = os.path.join(self.results_folder,
                                            'failures')

        # Make input / output folder for mounting to container.
        os.makedirs(self.input_folder, exist_ok=True)
        os.makedirs(self.output_folder, exist_ok=True)
        os.makedirs(self.results_folder, exist_ok=True)
        os.makedirs(self.database_folder, exist_ok=True)
        os.makedirs(self.failures_folder, exist_ok=True)
        logging.info(f"local mounted input folder:{self.input_folder}")
        logging.info(f"local mounted output folder:{self.output_folder}")
        logging.info(f"local mounted results_folder folder:{self.results_folder}")
        logging.info(f"local mounted database_folder folder:{self.database_folder}")
        logging.info(f"local mounted failures_folder folder:{self.failures_folder}")

    def run_datapoint(self, run_options):
        # Start timer to track simulation time.
        start = time.time()

        # Save run options to a unique folder. Run options is modified to contain datapoint id, analysis_id and
        # other run information.
        # Create datapoint id and path to folder where input file should be saved.
        run_options[':datapoint_id'] = str(uuid.uuid4())
        run_options[':analysis_id'] = self.engine.analysis_config[':analysis_id']
        run_options[':analysis_name'] = self.engine.analysis_config[':analysis_name']
        run_options[':run_annual_simulation'] = self.engine.analysis_config[':run_annual_simulation']
        run_options[':enable_costing'] = self.engine.analysis_config[':enable_costing']
        run_options[':compute_environment'] = self.engine.compute_environment
        run_options[':output_variables'] = self.engine.analysis_config[':output_variables']
        run_options[':output_meters'] = self.engine.analysis_config[':output_meters']
        run_options[':algorithm_type'] = self.engine.analysis_config[':algorithm'][':type']

        # Local Paths
        local_datapoint_input_folder = os.path.join(self.input_folder, run_options[':datapoint_id'])
        local_datapoint_output_folder = os.path.join(self.output_folder, run_options[':datapoint_id'])
        local_run_option_file = os.path.join(local_datapoint_input_folder, 'run_options.yml')
        # Create path to btap_data.json file.
        local_btap_data_path = os.path.join(self.output_folder, run_options[':datapoint_id'], 'btap_data.json')

        # Save run_option file for this simulation.
        os.makedirs(local_datapoint_input_folder, exist_ok=True)
        logging.info(f'saving simulation input file here:{local_run_option_file}')
        with open(local_run_option_file, 'w') as outfile:
            yaml.dump(run_options, outfile, encoding=('utf-8'))

        # Save custom osm file if required.
        local_osm_dict = self.get_local_osm_files()
        if run_options[':building_type'] in local_osm_dict:
            shutil.copy(local_osm_dict[run_options[':building_type']], local_datapoint_input_folder)
            logging.info(
                f"Copying osm file from {local_osm_dict[run_options[':building_type']]} to {local_datapoint_input_folder}")

        # Submit Job to batch
        return self.batch.submit_job(local_btap_data_path=local_btap_data_path,
                                     local_datapoint_input_folder=local_datapoint_input_folder,
                                     local_datapoint_output_folder=local_datapoint_output_folder,
                                     run_options=run_options)

    def save_results_to_database(self, results):
        if results['success'] == True:
            # If container completed with success don't save container output.
            results['container_output'] = None
            if results['eplus_fatals'] > 0:
                # If we had fatal errors..the run was not successful after all.
                results['success'] = False
        # This method organizes the data structure of the dataframe to fit into a report table.
        df = self.sort_results(results)

        # Save datapoint row information to disc in case of catastrophic failure or when C.K. likes to hit Ctrl-C

        pathlib.Path(self.database_folder).mkdir(parents=True, exist_ok=True)
        df.to_csv(os.path.join(self.database_folder, f"{results[':datapoint_id']}.csv"))

        # Save failures to a folder as well.

        if results['success'] == False:
            df.to_csv(os.path.join(self.failures_folder, f"{results[':datapoint_id']}.csv"))
        return results

    def sort_results(self, results):
        # Set up dict for top/high level data from btap_data.json output
        dp_values = {}
        # Set up arrays for tabular information contained in btap_date.json
        dp_tables = []
        # Set up arrays for dicts information contained in btap_data.json
        dp_dicts = []
        # interate through all btap_data top level keys.
        for key in results:
            if isinstance(results[key], list):
                # if the value is a list.. it is probably a table.. so put it in the tables array. Nothing will be done with this
                # at the moment.
                dp_tables.append(results[key])
            elif isinstance(results[key], dict):
                # if the value is a dict.. it is probably a configuration information.. so put it in array. Nothing will be done with this
                dp_tables.append(results[key])
            else:
                # otherwise store the key.
                dp_values[key] = results[key]
        # Convert dp_values to dataframe and add to sql table named 'btap_data'
        logging.info(f'obtained dp_values= {dp_values}')
        df = pd.DataFrame([dp_values])
        return df

    def shutdown_analysis(self):
        self.generate_output_file(baseline_results=self.engine.baseline_results)

    # This method creates a encoder and decoder of the simulation options to integers.  The ML and AI routines use float,
    # conventionally for optimization problems. Since most of the analysis that we do are discrete options for designers
    # we need to convert all inputs, string, float or int, into  to enumerated integer representations for the optimizer to
    # work.
    def create_options_encoder(self):
        # Determine options the users defined and constants and variable for the analysis. Options / lists that the user
        # provided only one options (a list of size 1) in the analysis input file are to be consider constants in the simulation.
        # this may simplify the calculations that the optimizer has to conduct.

        # Create a dict of the constants.
        self.constants = {}
        # Create a dict of encoders/decoders.
        self.option_encoder = {}

        # Keep track of total possible scenarios to tell user.
        self.number_of_possible_designs = 1
        # Interate through all the building_options contained in the analysis input yml file.
        for key, value in self.engine.building_options.items():
            # If the options for that building charecteristic are > 1 it is a variable to be take part in optimization.
            if isinstance(value, list) and len(value) > 1:
                self.number_of_possible_designs *= len(value)
                # Create the encoder for the building option / key.
                self.option_encoder[key] = {}
                self.option_encoder[key]['encoder'] = preprocessing.LabelEncoder().fit(value)
            elif isinstance(value, list) and len(value) == 1:
                # add the constant to the constant hash.
                self.constants[key] = value[0]
            else:
                # Otherwise warn user that nothing was provided.
                raise (f"building option {key} was set to empty. Pleace enter a value for it.")

        # Return the variables.. but the return value is not really use since these are access via the object variable self anyways.
        return self.constants, self.option_encoder

    # convieniance interface to get number of variables.
    def number_of_variables(self):
        # Returns the number of variables Note this is not a class variable self like the others. That is because this method is used in the
        # problem definition and we need to avoid thread variable issues.
        return len(self.option_encoder)

    # Convience variable to get the upper limit integers of all the variable as an ordered list.
    def x_u(self):
        # Set up return list.
        x_u = []
        # iterage throug each key in the encoder list.
        for key in self.option_encoder:
            # get the max value, which is the length minus 1 since the enumeration starts at 0.
            x_u.append(len(self.option_encoder[key]['encoder'].classes_) - 1)
        # Returns the list of max values.. Note this is not a class variable self like the others. That is because this method is used in the
        # problem definition and we need to avoid thread variable issues.
        return x_u

    # This method takes an ordered list of ints and converts it to a run_options input file.
    def generate_run_option_file(self, x):
        # Create dict that will be the basis of the run_options.yml file.
        run_options = {}
        # Make sure options are the same length as the encoder.
        if len(x) != len(self.option_encoder):
            raise ('input is larger than the encoder was set to.')

        # interate though both the encoder key and x input list at the same time
        for key_name, x_option in zip(self.option_encoder.keys(), x):
            # encoder/decoder for the building option key.
            encoder = self.option_encoder[key_name]['encoder']
            # get the actual value for the run_options
            run_options[key_name] = str(encoder.inverse_transform([x_option])[0])
        # Tell user the options through std out.
        run_options[':scenario'] = 'optimize'
        run_options[':algorithm_type'] = self.engine.analysis_config[':algorithm'][':type']
        run_options[':output_variables'] = self.engine.analysis_config[':output_variables']
        run_options[':output_meters'] = self.engine.analysis_config[':output_meters']
        message = f"Running Option Variables {run_options}"
        logging.info(message)
        # Add the constants to the run options dict.
        run_options.update(self.constants)
        # Add the analysis setting to the run options dict.
        run_options.update(self.engine.analysis_config)
        # Returns the dict.. Note this is not a class variable self like the others. That is because this method is used in the
        # problem definition and we need to avoid thread variable issues.
        return run_options

    def generate_output_file(self, baseline_results=None):

        # Process csv file to create single dataframe with all simulation results
        PostProcessResults(baseline_results=baseline_results,
                           database_folder=self.database_folder,
                           results_folder=self.results_folder).run()
        excel_path = os.path.join(self.results_folder, 'output.xlsx')

        # If this is an aws_batch run, copy the excel file to s3 for storage.
        if self.engine.compute_environment == 'aws_batch':
            self.credentials = AWSCredentials()
            target_path = os.path.join(self.credentials.user_name, self.engine.analysis_config[':analysis_name'],
                                       self.engine.analysis_config[':analysis_id'], 'results', 'output.xlsx')
            # s3 likes forward slashes.
            target_path = target_path.replace('\\', '/')
            message = "Uploading %s..." % target_path
            logging.info(message)
            S3().upload_file(excel_path, self.credentials.account_id, target_path)
        return


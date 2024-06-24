import openstudio
import logging
import os
import pathlib
import uuid
import yaml
import pandas as pd
import shutil
from sklearn import preprocessing
from src.btap.exceptions import OSMErrorException
from src.btap.aws_credentials import AWSCredentials
from src.btap.aws_s3 import S3
from src.btap.constants import NECB2011_SPACETYPE_PATH
from src.btap.btap_postprocess_analysis import PostProcessResults
from src.btap.docker_image_manager import DockerImageManager
from src.btap.aws_image_manager import AWSImageManager
from src.btap.common_paths import CommonPaths
from src.btap.aws_compute_environment import AWSComputeEnvironment
from src.btap.common_paths  import SCHEMA_FOLDER
import jsonschema
from src.btap.aws_dynamodb import AWSResultsTable
from icecream import ic


# Parent Analysis class from with all analysis inherit
class BTAPAnalysis():
    # This does some simple check on the osm file to ensure that it has the required inputs for btap.
    @staticmethod
    def check_list(osm_file):
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
        necb_space_types = list(
            map(lambda
                    space_type_temp: space_type_temp.standardsBuildingType().get() + space_type_temp.standardsSpaceType().get(),
                necb_lib.getSpaceTypes()))
        for st in model_spacetypes:
            if st not in necb_space_types:
                messages += f"OS:SpaceType {st} is not associated a valid NECB2011 spacetype.\n"

        if len(messages) > 0:
            logging.error(f"The errors below need to be fixed in your osm file.\n{messages}\n")
            raise OSMErrorException(f"The osm file {osm_file} is misconfigured.. Analysis aborted.\n")

    def get_local_osm_files(self):
        osm_list = {}
        osm_folder = os.path.join(self.analysis_input_folder, 'osm_folder')
        if pathlib.Path(osm_folder).is_dir():
            for file in os.listdir(osm_folder):
                if file.endswith(".osm"):
                    osm_list[os.path.splitext(file)[0]] = os.path.join(osm_folder, file)
        return osm_list

    # Constructor will
    def __init__(self,
                 analysis_config=None,
                 output_folder=None,
                 analysis_input_folder=None,
                 reference_run_df=None,
                 include_files=None):

        # Will always use the btap_cli image that run the ruby code.
        self.image_name = 'btap_cli'
        self.analysis_config = analysis_config
        self.analysis_input_folder = analysis_input_folder
        self.output_folder = output_folder
        self.reference_run_df = reference_run_df
        self.include_files = include_files

        # Get analysis information for runs.

        self.analysis_id = str(uuid.uuid4())
        self.analysis_name = self.analysis_config[':analysis_name']
        self.algorithm_type = self.analysis_config[':algorithm_type']
        self.algorithm_nsga_population = self.analysis_config.get(':algorithm_nsga_population')
        self.algorithm_nsga_n_generations = self.analysis_config.get(':algorithm_nsga_n_generations')
        self.algorithm_nsga_prob = self.analysis_config.get(':algorithm_nsga_prob')
        self.algorithm_nsga_eta = self.analysis_config.get(':algorithm_nsga_eta')
        self.algorithm_nsga_minimize_objectives = self.analysis_config.get(':algorithm_nsga_minimize_objectives')
        self.algorithm_lhs_n_samples = self.analysis_config.get(':algorithm_lhs_n_samples')
        self.algorithm_lhs_type = self.analysis_config.get(':algorithm_lhs_type')
        self.algorithm_lhs_random_seed = self.analysis_config.get(':algorithm_lhs_random_seed')
        self.compute_environment = self.analysis_config.get(':compute_environment')
        self.options = self.analysis_config.get(':options')

        # Set common paths singleton.
        self.cp = CommonPaths()
        # Setting paths to current context.
        self.cp.set_analysis_info(analysis_id=self.analysis_id,
                                  analysis_name=self.analysis_name,
                                  local_output_folder=self.output_folder,
                                  project_input_folder=self.analysis_input_folder,
                                  algorithm_type=self.algorithm_type)

        # btap specific.
        self.output_variables = self.analysis_config[':output_variables']
        self.output_meters = self.analysis_config[':output_meters']
        self.run_annual_simulation = True

        if self.compute_environment == 'local':
            print(f"running on {self.compute_environment}")
            self.image_manager = DockerImageManager(image_name=self.image_name)


        elif self.compute_environment == 'local_managed_aws_workers':
            print(f"running on {self.compute_environment}")

            self.image_manager = AWSImageManager(image_name=self.image_name,
                                                 compute_environment=AWSComputeEnvironment())
            self.credentials = AWSCredentials()
        else:
            logging.error(f"Unknown image {self.image_name}")
            exit(1)
        # Get instance of aws batch that has already been created in the build process.
        self.batch = self.image_manager.get_batch()

        # Storage items
        self.btap_data_df = []
        self.failed_df = []



    def create_paths_folders(self):

        # Create analysis folder
        print(f'analyses_folder is:{self.cp.output_folder()}')
        os.makedirs(self.cp.output_folder(), exist_ok=True)

        # Tell user and logger id and names
        print(f'analysis_id is: {self.analysis_id}')
        print(f'analysis_name is: {self.analysis_name}')
        logging.info(f'analysis_id:{self.analysis_id}')
        logging.info(f'analysis_name:{self.analysis_name}')

        # Set analysis name folder.
        logging.info(f'analysis_folder:{self.analysis_name_folder()}')
        logging.info(f'analysis_output_folder:{self.analysis_output_folder()}')

        # Tell log we are deleting previous runs.
        message = f'Deleting previous runs from: {self.cp.algorithm_folder()}'
        logging.info(message)
        print(message)
        # Check if folder exists
        if os.path.isdir(self.cp.algorithm_folder()):
            # Remove old folder
            try:
                shutil.rmtree(self.cp.algorithm_folder())
            except PermissionError:
                message = f'Could not delete {self.analysis_name_folder()}. Do you have a file open in that folder? Exiting'
                print(message)
                logging.error(message)
                exit(1)

        message = f'Creating new folders for analysis'
        logging.info(message)
        print(message)
        # create local input and output folders

        # Make input / output folder for mounting to container.
        os.makedirs(self.cp.algorithm_folder(), exist_ok=True)
        os.makedirs(self.cp.analysis_results_folder(), exist_ok=True)
        os.makedirs(self.cp.analysis_database_folder(), exist_ok=True)
        os.makedirs(self.cp.analysis_failures_folder(), exist_ok=True)
        logging.info(f"local mounted input folder:{self.cp.algorithm_folder()}")
        logging.info(f"local mounted output folder:{self.cp.algorithm_folder()}")
        logging.info(f"local mounted results_folder folder:{self.cp.analysis_results_folder()}")
        logging.info(f"local mounted database_folder folder:{self.cp.analysis_database_folder()}")
        logging.info(f"local mounted failures_folder folder:{self.cp.analysis_failures_folder()}")

    def algorithm_folder(self):
        return self.cp.algorithm_folder()

    def analysis_name_folder(self):
        return self.cp.project_output_folder()

    def analysis_output_folder(self):
        return self.cp.algorithm_folder()

    def analysis_results_folder(self):
        return self.cp.analysis_results_folder()

    def analysis_excel_results_path(self):
        return self.cp.analysis_excel_results_path()

    def analysis_failures_folder(self):
        return self.cp.analysis_failures_folder()

    def analysis_database_folder(self):
        return self.cp.analysis_database_folder()

    @staticmethod
    def load_analysis_input_file(analysis_config_file=None):
        # Load Analysis File into variable
        if not os.path.isfile(analysis_config_file):
            logging.error(f"could not find analysis input file at {analysis_config_file}. Exiting")
        # Open the yaml in analysis dict.
        with open(analysis_config_file, 'r') as stream:
            analysis_config = yaml.safe_load(stream)
        analyses_folder = os.path.dirname(os.path.realpath(analysis_config_file))
        analysis_input_folder = os.path.dirname(os.path.realpath(analysis_config_file))

        try:
            schema_file = os.path.join(f'{SCHEMA_FOLDER}/analysis_config_schema.yml')
            with open(schema_file) as f:
                schema = yaml.load(f, Loader=yaml.FullLoader)
        except FileNotFoundError:
            print(f'Error: The schema file does not exist {schema_file}')
            exit(1)

        try:
            jsonschema.validate(analysis_config, schema)
        except yaml.parser.ParserError as e:
            print(f"ERROR: input.yml contains an invalid YAML format. Please check your YAML format.")
            print(e.message)
            exit(1)

        return analysis_config, analysis_input_folder, analyses_folder

    def get_num_of_runs_failed(self):
        if os.path.isdir(self.analysis_failures_folder()):
            return len([name for name in os.listdir(self.analysis_failures_folder()) if
                        os.path.isfile(os.path.join(self.analysis_failures_folder(), name))])
        else:
            return 0

    def get_num_of_runs_completed(self):

        if os.path.isdir(self.analysis_database_folder()):
            return len([name for name in os.listdir(self.analysis_database_folder()) if
                        os.path.isfile(os.path.join(self.analysis_database_folder(), name))])
        else:
            return 0

    # This methods sets the pathnames and creates the input and output folders for the analysis. It also initilizes the
    # sql database.

    def run_datapoint(self, run_options):

        # Save run options to a unique folder. Run options is modified to contain datapoint id, analysis_id and
        # other run information.
        # Create datapoint id and path to folder where input file should be saved.
        job_id = str(uuid.uuid4())
        run_options[':datapoint_id'] = job_id
        run_options[':analysis_id'] = self.analysis_id
        run_options[':analysis_name'] = self.analysis_name
        run_options[':compute_environment'] = self.compute_environment
        run_options[':algorithm_type'] = self.algorithm_type
        # BTAP specific.
        run_options[':run_annual_simulation'] = True
        run_options[':output_variables'] = self.output_variables
        run_options[':output_meters'] = self.output_meters

        # Local Paths

        # In AWS the runs folder is named slightly differently.
        run_folder = 'runs/' if self.compute_environment == 'local' else 'run/'

        local_datapoint_input_folder = os.path.join(self.cp.algorithm_folder(), run_folder, job_id)
        local_run_option_file = os.path.join(self.cp.analysis_job_id_folder(job_id=job_id), 'run_options.yml')

        # Save run_option file for this simulation.
        os.makedirs(self.cp.analysis_job_id_folder(job_id=job_id), exist_ok=True)
        logging.info(f'saving simulation input file here:{local_run_option_file}')
        with open(local_run_option_file, 'w') as outfile:
            yaml.dump(run_options, outfile, encoding=('utf-8'))

        # Save custom osm file if required.
        local_osm_dict = self.get_local_osm_files()
        if run_options[':building_type'] in local_osm_dict:
            shutil.copy(local_osm_dict[run_options[':building_type']],
                        self.cp.analysis_job_id_folder(job_id=job_id))
            logging.info(
                f"Copying osm file from {local_osm_dict[run_options[':building_type']]} to {self.cp.analysis_job_id_folder(job_id=job_id)}")

        # Submit Job to batch
        job = self.batch.create_job(job_id=job_id)
        job_data = job.submit_job(run_options=run_options)

        # If the include_files list isn't empty and the job is a success, delete the files:
        if self.include_files and job_data['status'] == 'SUCCEEDED':
            self.delete_unwanted_files(local_datapoint_input_folder)

        return job_data

    # This method deletes the unspecified files as per the :include_files input parameter

    def delete_unwanted_files(self, job_folder):

        datapoint_folder = pathlib.Path(job_folder)  # Make the datapoint folder a Path object
        keep_files = set()   # List of wanted files to match against the unwanted ones
        parent_dirs = set()  # List of parent directories so they aren't deleted

        # Compile a list of paths to keep from the inputs specified
        for pattern in self.include_files:
            keep_files |= set(datapoint_folder.rglob(pattern))

        # Get each of the parent directories of the kept files to not indirectly delete them
        for file in keep_files:
            i = 0
            curr_parent_dir = file.parents[i]
            while curr_parent_dir != datapoint_folder or curr_parent_dir in parent_dirs:
                parent_dirs.add(curr_parent_dir)
                i += 1
                curr_parent_dir = file.parents[i]

        keep_files |= parent_dirs

        # Delete the files which don't match the patterns
        rm_files = set(filter(lambda f: f not in keep_files, datapoint_folder.rglob('*')))
        for file in rm_files:
            if file.is_file():
                file.unlink()
            elif file.is_dir():
                rm_files -= set(file.rglob('*'))
                shutil.rmtree(file)


    def save_results_to_database(self, job_data):
        if job_data['status'] == 'SUCCEEDED':
            # If container completed with success don't save container output.
            job_data['container_output'] = None
            if job_data['eplus_fatals'] > 0:
                # If we had fatal errors..the run was not successful after all.
                job_data['status'] = 'FAILED'
        # This method organizes the data structure of the dataframe to fit into a report table.
        df = self.sort_results(job_data)
        # Save job_data
        # to csv file.
        pathlib.Path(self.cp.analysis_database_folder()).mkdir(parents=True, exist_ok=True)
        df.to_csv(os.path.join(self.cp.analysis_database_folder(), f"{job_data[':datapoint_id']}.csv"))

        # Save failures to a folder as well.

        if job_data['status'] != 'SUCCEEDED':
            df.to_csv(os.path.join(self.cp.analysis_failures_folder(), f"{job_data[':datapoint_id']}.csv"))
        return job_data

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
        self.generate_output_file(baseline_results=self.reference_run_df)

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
        for key, value in self.options.items():
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
        run_options[':scenario'] = 'optimize'  # todo remove.

        message = f"Running Option Variables {run_options}"
        logging.info(message)
        # Add the constants to the run options dict.
        run_options.update(self.constants)
        # Returns the dict.. Note this is not a class variable self like the others. That is because this method is used in the
        # problem definition and we need to avoid thread variable issues.
        return run_options

    def generate_output_file(self, baseline_results=None):
        # Process csv file to create single dataframe with all simulation results
        ppr = PostProcessResults(baseline_results=baseline_results,
                                 database_folder=self.cp.analysis_database_folder(),
                                 results_folder=self.cp.analysis_results_folder(),
                                 compute_environment=self.compute_environment,
                                 output_variables=self.output_variables,
                                 username=self.cp.get_build_env_name(),
                                 include_files=self.include_files)
        # Store post process run into analysis object. Will need it later.
        self.btap_data_df = ppr.run()

        folders = ['in.osm',
                   'eplustbl.htm',
                   'hourly.csv',
                   'eplusout.sql']


        if self.compute_environment != 'local':
            #Create Zip Files.
            for folder in folders:
                print(f"Zipping {folder} to S3 results zipfile")
                source_folder = os.path.join(self.analysis_results_folder(), folder)
                source_zip = os.path.join(self.analysis_results_folder(), 'zips',  folder)
                # Delete file if it exists.
                pathlib.Path(source_zip).unlink(missing_ok=True)
                # Create zip
                shutil.make_archive(source_zip, 'zip', source_folder)








        # If this is an local_managed_aws_workers run, copy the excel file to s3 for storage.
        if self.compute_environment == 'local_managed_aws_workers':
            self.credentials = AWSCredentials()
            message = "Uploading %s..." % self.cp.s3_analysis_excel_output_path()
            logging.info(message)
            S3().upload_file(self.cp.analysis_excel_results_path(),
                             self.credentials.account_id,
                             self.cp.s3_analysis_excel_output_path())

            # now copy results to s3

            for folder in folders:
                print(f"Uploading {folder} to S3 results")
                source_folder = os.path.join(self.analysis_results_folder(), folder)
                target_folder = os.path.join(self.cp.s3_analysis_results_folder(),folder).replace('\\', '/')
                S3().copy_folder_to_s3(bucket_name=self.credentials.account_id,
                                       source_folder=source_folder,
                                       target_folder=target_folder)
                # Upload Zip files of results.
                source_zip = os.path.join(self.analysis_results_folder(), 'zips', folder + '.zip' )
                s3_target_zip = os.path.join(self.cp.s3_analysis_results_folder(), 'zips', folder + '.zip').replace('\\', '/')
                S3().upload_file(source_zip, self.credentials.account_id, s3_target_zip)


            print("Data upload to S3 Complete")




        return

    @staticmethod
    def generate_pdf_report(df=None,
                            pdf_output=None):
        return None

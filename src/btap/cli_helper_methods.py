import pip_system_certs.wrapt_requests
from src.btap.constants import WORKER_CONTAINER_MEMORY, WORKER_CONTAINER_VCPU
from src.btap.constants import MANAGER_CONTAINER_VCPU, MANAGER_CONTAINER_MEMORY
from src.btap.constants import MAX_AWS_VCPUS
from src.btap.aws_batch import AWSBatch
from src.btap.aws_credentials import AWSCredentials
from src.btap.aws_compute_environment import AWSComputeEnvironment
from src.btap.aws_image_manager import AWSImageManager
from src.btap.docker_image_manager import DockerImageManager
from src.btap.aws_iam_roles import IAMBatchJobRole, IAMBatchServiceRole, IAMCodeBuildRole
from src.btap.btap_analysis import BTAPAnalysis
from src.btap.btap_reference import BTAPReference
from src.btap.btap_optimization import BTAPOptimization
from src.btap.btap_parametric import BTAPParametric
from src.btap.btap_elimination import BTAPElimination
from src.btap.btap_lhs import BTAPSamplingLHS
from src.btap.btap_sensitivity import BTAPSensitivity
from src.btap.btap_batch_analysis import BTAPBatchAnalysis
from src.btap.reports import generate_btap_reports
from src.btap.aws_s3 import S3
from src.btap.common_paths import CommonPaths, SCHEMA_FOLDER, HISTORIC_WEATHER_LIST, \
    FUTURE_WEATHER_LIST, HISTORIC_WEATHER_REPO, FUTURE_WEATHER_REPO, HISTORIC_WEATHER_LIST_BTAP, \
    FUTURE_WEATHER_LIST_BTAP, HISTORIC_WEATHER_REPO_BTAP, FUTURE_WEATHER_REPO_BTAP, USER, \
    CLIMATE_ONEBUILDING_FOLDER, CLIMATE_ONEBUILDING_MAP, CLIMATE_ONEBUILDING_URL, PROJECT_FOLDER
import os
import pandas as pd
from src.btap.aws_s3 import S3
import zipfile
import pathlib
import re

import json
import requests
import shutil
import time
import copy
import os
from pathlib import Path
import uuid
import numpy as np
from icecream import ic
from src.btap.aws_dynamodb import AWSResultsTable
import math
import yaml




def load_config(build_config_path):
    from src.btap.cli_helper_methods import generate_build_config
    import jsonschema
    import yaml
    try:
        schema_file = os.path.join(SCHEMA_FOLDER, 'build_config_schema.yml')
        with open(schema_file) as f:
            schema = yaml.load(f, Loader=yaml.FullLoader)
    except FileNotFoundError:
        print(f'Error: The schema file does not exist {schema_file}')
        exit(1)
    try:
        with open(build_config_path) as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
        # Validate against schema
    except FileNotFoundError:
        print(
            f'The file does not exist. Creating a template at location {build_config_path}. Please edit it with your information.')
        generate_build_config(build_config_path)
        exit(1)
    try:
        jsonschema.validate(config, schema)
    except yaml.parser.ParserError as e:
        print(f"ERROR: {build_config_path} contains an invalid YAML format. Please check your YAML format.")
        print(e.message)
        exit(1)


    except jsonschema.exceptions.ValidationError as e:
        print(f"ERROR: {build_config_path} does not contain valid data. Please fix the error below and try again.")
        print(e.message)
        exit(1)
    return config



def get_pareto_points(costs, return_mask=True):
    """
    Find the pareto-efficient points
    :param costs: An (n_points, n_costs) array
    :param return_mask: True to return a mask
    :return: An array of indices of pareto-efficient points.
        If return_mask is True, this will be an (n_points, ) boolean array
        Otherwise it will be a (n_efficient_points, ) integer array of indices.
    """
    is_efficient = np.arange(costs.shape[0])
    n_points = costs.shape[0]
    next_point_index = 0  # Next index in the is_efficient array to search for
    while next_point_index < len(costs):
        nondominated_point_mask = np.any(costs < costs[next_point_index], axis=1)
        nondominated_point_mask[next_point_index] = True
        is_efficient = is_efficient[nondominated_point_mask]  # Remove dominated points
        costs = costs[nondominated_point_mask]
        next_point_index = np.sum(nondominated_point_mask[:next_point_index]) + 1
    if return_mask:
        is_efficient_mask = np.zeros(n_points, dtype=bool)
        is_efficient_mask[is_efficient] = True
        return is_efficient_mask
    else:
        return is_efficient

def get_weather_locations(btap_weather: bool, weather_locations=[]) -> str:

    # Helper function for building download links for Climate.OneBuilding.Org.
    def build_link(data, zip_file):
        return CLIMATE_ONEBUILDING_URL + data["region"] + data["country"] + \
               data["province_map"][zip_file[4 : 6]] + zip_file

    default_weather_locations =  [
        'CAN_QC_Montreal-Trudeau.Intl.AP.716270_CWEC2016.epw',
        'CAN_NS_Halifax.Dockyard.713280_CWEC2016.epw',
        'CAN_AB_Edmonton.Intl.AP.711230_CWEC2016.epw',
        'CAN_BC_Vancouver.Intl.AP.718920_CWEC2016.epw',
        'CAN_AB_Calgary.Intl.AP.718770_CWEC2016.epw',
        'CAN_ON_Toronto.Pearson.Intl.AP.716240_CWEC2016.epw',
        'CAN_NT_Yellowknife.AP.719360_CWEC2016.epw',
        'CAN_AB_Fort.McMurray.AP.716890_CWEC2016.epw',
        # 2020 versions
        'CAN_QC_Montreal.Intl.AP.716270_CWEC2020.epw',
        'CAN_NS_Halifax.Dockyard.713280_CWEC2020.epw',
        'CAN_AB_Edmonton.Intl.AP.711230_CWEC2020.epw',
        'CAN_BC_Vancouver.Intl.AP.718920_CWEC2020.epw',
        'CAN_AB_Calgary.Intl.AP.718770_CWEC2020.epw',
        'CAN_ON_Toronto.Intl.AP.716240_CWEC2020.epw',
        'CAN_NT_Yellowknife.AP.719360_CWEC2020.epw',
        'CAN_AB_Fort.Mcmurray.AP.716890_CWEC2020.epw'
    ]

    if btap_weather: # Download from btap_weather
        # Get list of historic and future weather files available from git repo. See definitions for URLs
        historic_list = set(requests.get(HISTORIC_WEATHER_LIST_BTAP, allow_redirects=True).json())
        future_list   = set(requests.get(FUTURE_WEATHER_LIST_BTAP, allow_redirects=True).json())

        # Check if any weather locations on the weather file list are not default weather locations.
        custom_weather_locs = {
            re.sub(r'\.epw$', '.zip', x) # Replace .epw for .zip as this is the basename 
            for x in weather_locations   # used in the weatherfile repository.
            if x not in default_weather_locations
        }

        # Check if any of the weather files are not part of historical or future files.
        non_existant_files = (custom_weather_locs - historic_list) - future_list 

        if len(non_existant_files) > 0:
            print(
                f"Could not find the weather files {non_existant_files} in the list of BTAP "
                "weather files from your build_conf.yml file. Please check if it is spelled "
                "correctly and check whether it is in:"
                f"\n  The historic list: {HISTORIC_WEATHER_LIST_BTAP}"
                f"\n  The future list: {FUTURE_WEATHER_LIST_BTAP}")
            exit(1)

        # prefix custom_weather with correct URL for fut or hist.  
        # Already filtered for one or the other above.. so the else works implicitly for future.
        custom_weather_list = [
            HISTORIC_WEATHER_REPO_BTAP + loc 
            if loc in historic_list 
            else FUTURE_WEATHER_REPO_BTAP + loc  
            for loc in custom_weather_locs
        ]

    else: # Download from Climate.OneBuilding.Org.
        custom_weather_list = []
        weather_groups      = {}
        non_existant_files  = {} # Maps missing files to their associated file list.
        
        # Group weather files by country to avoid reopening files where unnessecary.
        for weather_file in weather_locations:
            prefix = weather_file[0 : 3]

            if prefix not in weather_groups:
                weather_groups[prefix] = []

            weather_groups[prefix].append(re.sub(r'\.epw$', '.zip', weather_file))

        for prefix in weather_groups:
            if prefix == 'CAN': # Search historic and future files if this is a Canadian file.
                historic_data = json.load(open(HISTORIC_WEATHER_LIST))
                future_data   = json.load(open(FUTURE_WEATHER_LIST))
                for zip_file in weather_groups[prefix]:
                    if zip_file in set(future_data["file_list"]):
                        custom_weather_list.append(build_link(future_data, zip_file))

                    elif zip_file in set(historic_data["file_list"]):
                        custom_weather_list.append(build_link(historic_data, zip_file))

                    else:
                        non_existant_files[zip_file] = f"{HISTORIC_WEATHER_LIST} or {FUTURE_WEATHER_LIST}"

            else: # Other files not in canada.
                file_map = json.load(open(CLIMATE_ONEBUILDING_MAP))

                # Contains the list of weather files for a given country as well as other 
                # information needed for building the download link.
                weather_data_file = os.path.join(CLIMATE_ONEBUILDING_FOLDER, file_map[prefix])

                # Try to load the weather file list for the country based on the 3-character 
                # country code.
                try: 
                    weather_data = json.load(open(weather_data_file))
                except FileNotFoundError as error:
                    print(
                        f"Error: Couldn't resolve country code {prefix} for file {weather_file}"
                        f"Full error description: {error}")
                    exit(1)
                except Exception as error:
                    print(f"Unknown error: {error}")
                    exit(1)
                
                for zip_file in weather_groups[prefix]:
                    if zip_file in set(weather_data["file_list"]):
                        # Build the download link and append it to the list of locations.
                        custom_weather_list.append(build_link(weather_data, zip_file))
                    else:
                        non_existant_files[weather_file] = weather_data_file
        
        if len(non_existant_files) > 0:
            print(
                "Could not find the weather files in the list of weather files from "
                "ClimateOneBuilding.Org from your build_conf.yml file. The following weather files "
                "could not be found in their appropriate weather lists:")
            for file, file_list in non_existant_files.items():
                print(file, ':', file_list)
                
            exit(1)

    # Return a single string from the list separated by a space.
    return  " ".join(custom_weather_list)

def build_and_configure_docker_and_aws(btap_batch_branch=None,
                                       enable_rsmeans=False,
                                       local_costing_path='',
                                       local_factors_path='',
                                       compute_environment=None,
                                       openstudio_version=None,
                                       os_standards_org=None,
                                       os_standards_branch=None,
                                       build_btap_cli=None,
                                       build_btap_batch=None,
                                       btap_weather=None,
                                       weather_list=None,
                                       local_nrcan=None):



    # Get the weather locations from the weather list
    weather_locations = get_weather_locations(btap_weather, weather_list)

    # Check if the local_costing_path file exists and convert to absolute path if relative
    dockerfile_costing_path = 'do_not_delete.txt'  # Dummy path relative to the Dockerfile build context
    dockerfile_factors_path = 'do_not_delete.txt'  # Dummy path relative to the Dockerfile build context
    copy_costing_file = False  # Do not use the costing file in the Docker build by default
    if local_costing_path != '':
        copy_costing_file = True  # Default to copying the costing file

    if local_factors_path != '':
        copy_factors_file = True  # Default to copying the factors file

    # Copy custom costing file to the Dockerfile build context if it exists
    if copy_costing_file:
        # If path is relative, make it absolute
        if not os.path.isabs(local_costing_path):
            local_costing_path = os.path.join(PROJECT_FOLDER, local_costing_path)
        
        # Check if the file actually exists, has a size greater than 0, and is readable
        if os.path.isfile(local_costing_path) and os.path.getsize(local_costing_path) > 0 and os.access(local_costing_path, os.R_OK):
            # Copy the costing file to the Dockerfile build context
            dockerfile_folder = os.path.join(PROJECT_FOLDER, 'src', 'Dockerfiles', 'btap_cli')
            dockerfile_costing_path = 'costs.csv'  # Relative path in build context
            target_path = os.path.join(dockerfile_folder, dockerfile_costing_path)
            
            try:
                shutil.copy2(local_costing_path, target_path)
                copy_costing_file = True  # Use the costing file in the Docker build
                print(f"Copied costing file from {local_costing_path} to {target_path}")
            except Exception as e:
                print(f"Warning: Could not copy costing file: {e}")
                dockerfile_costing_path = 'do_not_delete.txt'  # Placeholder if copy fails
                copy_costing_file = False  # Do not use the costing file in the Docker build if copy fails
        else:
            print(f"Warning: Local costing file not found at {local_costing_path}")
            dockerfile_costing_path = 'do_not_delete.txt'  # Placeholder if file does not exist
            copy_costing_file = False  # Do not use the costing file in the Docker build if the costing file does not exist

    # Copy custom costing localization factors file to the Dockerfile build context if it exists
    if copy_factors_file:
        # If path is relative, make it absolute
        if not os.path.isabs(local_factors_path):
            local_factors_path = os.path.join(PROJECT_FOLDER, local_factors_path)

        # Check if the file actually exists, has a size greater than 0, and is readable
        if os.path.isfile(local_factors_path) and os.path.getsize(local_factors_path) > 0 and os.access(local_factors_path, os.R_OK):
            # Copy the factors file to the Dockerfile build context
            dockerfile_folder = os.path.join(PROJECT_FOLDER, 'src', 'Dockerfiles', 'btap_cli')
            dockerfile_factors_path = 'costs_local_factors.csv'  # Relative path in build context
            target_path = os.path.join(dockerfile_folder, dockerfile_factors_path)

            try:
                shutil.copy2(local_factors_path, target_path)
                copy_factors_file = True  # Use the factors file in the Docker build
                print(f"Copied costing localization factors file from {local_factors_path} to {target_path}")
            except Exception as e:
                print(f"Warning: Could not copy factors file: {e}")
                dockerfile_factors_path = 'do_not_delete.txt'  # Placeholder if copy fails
                copy_factors_file = False  # Do not use the factors file in the Docker build if copy fails
        else:
            print(f"Warning: Local factors file not found at {local_factors_path}")
            dockerfile_factors_path = 'do_not_delete.txt'  # Placeholder if file does not exist
            copy_factors_file = False  # Do not use the factors file in the Docker build if the factors file does not exist

    # Set os_standards_org to NREL if not provided
    if os_standards_org == '':
        os_standards_org = 'NREL'

    # build args for aws and btap_cli container.
    build_args_btap_cli = {'OPENSTUDIO_VERSION': openstudio_version,
                           'ENABLE_RSMEANS' : 'True' if enable_rsmeans == True else '',
                           'OS_STANDARDS_ORG': os_standards_org,
                           'OS_STANDARDS_BRANCH': os_standards_branch,
                           'WEATHER_FILES': weather_locations,
                           'LOCAL_COSTING_PATH': dockerfile_costing_path,  # Use the relative path in build context
                           'COPY_COSTING_FILE': 'True' if copy_costing_file == True else '',
                           'LOCAL_FACTORS_PATH': dockerfile_factors_path,  # Use the relative path in build context
                           'COPY_FACTORS_FILE': 'True' if copy_factors_file == True else '',
                           'LOCALNRCAN': ''}
    # build args for btap_batch container.
    build_args_btap_batch = {'BTAP_BATCH_BRANCH': btap_batch_branch}



    if compute_environment in ['local_managed_aws_workers', 'aws']:
        delete_aws_build_env(os.environ['BUILD_ENV_NAME'])

        # # Create new
        ace_worker = AWSComputeEnvironment(name='btap_cli')
        ace_manager = AWSComputeEnvironment(name='btap_batch')
        image_worker = AWSImageManager(image_name='btap_cli')
        image_manager = AWSImageManager(image_name='btap_batch', compute_environment=ace_worker)
        IAMBatchJobRole().create_role()
        IAMCodeBuildRole().create_role()
        IAMBatchServiceRole().create_role()
        time.sleep(30)  # Give a few seconds for role to apply.

        # Create Compute Environment for workers
        ace_worker = AWSComputeEnvironment(name='btap_cli')
        ace_worker.setup(maxvCpus=math.floor(MAX_AWS_VCPUS * 0.95))



        if build_btap_cli:
            print('Building btap_cli on aws..')
            image_worker.build_image(build_args=build_args_btap_cli)
            
            # Clean up: Remove the copied costing file from the build context
            if copy_costing_file == True and dockerfile_costing_path != 'do_not_delete.txt':
                dockerfile_folder = os.path.join(PROJECT_FOLDER, 'src', 'Dockerfiles', 'btap_cli')
                target_path = os.path.join(dockerfile_folder, dockerfile_costing_path)
                try:
                    if os.path.exists(target_path):
                        os.remove(target_path)
                        print(f"Cleaned up costing file from build context: {target_path}")
                except Exception as e:
                    print(f"Warning: Could not clean up costing file: {e}")

            if copy_factors_file == True and dockerfile_factors_path != 'do_not_delete.txt':
                dockerfile_folder = os.path.join(PROJECT_FOLDER, 'src', 'Dockerfiles', 'btap_cli')
                target_path = os.path.join(dockerfile_folder, dockerfile_factors_path)
                try:
                    if os.path.exists(target_path):
                        os.remove(target_path)
                        print(f"Cleaned up costing factors file from build context: {target_path}")
                except Exception as e:
                    print(f"Warning: Could not clean up costing factors file: {e}")

        # Create Job description and queues for workers.
        batch_cli = AWSBatch(image_manager=image_worker,
                             compute_environment=ace_worker
                             )
        batch_cli.setup(container_vcpu=WORKER_CONTAINER_VCPU,
                        container_memory=WORKER_CONTAINER_MEMORY)

        # Create compute environment for analysis managers, which is a 10% of MAXVCPU

        ace_manager.setup(maxvCpus=math.floor(MAX_AWS_VCPUS * 0.05))

        # Build image for btap_batch manager
        if build_btap_batch:
            print('Building AWS batch manager image')
            image_manager.build_image(build_args=build_args_btap_batch)

        # Create Job description and queues for analysis manager.
        batch_manager = AWSBatch(image_manager=image_manager,
                                 compute_environment=ace_manager
                                 )
        batch_manager.setup(container_vcpu=MANAGER_CONTAINER_VCPU,
                            container_memory=MANAGER_CONTAINER_MEMORY)

        # Create AWS database for results if it does not already exist.
        AWSResultsTable().create_table()

    if compute_environment in ['local']:
        # Build btap_cli image
        # Add local_nrcan argument to build_args_btap_cli dictionary.  This argument is only used when building a
        # btap_cli image locally
        if local_nrcan:
            build_args_btap_cli["LOCALNRCAN"] = str(local_nrcan)

        image_worker = DockerImageManager(image_name='btap_cli')
        if build_btap_cli:
            print('Building btap_cli image')
            image_worker.build_image(build_args=build_args_btap_cli)
            
            # Clean up: Remove the copied costing file from the build context
            if copy_costing_file == True and dockerfile_costing_path != 'do_not_delete.txt':
                dockerfile_folder = os.path.join(PROJECT_FOLDER, 'src', 'Dockerfiles', 'btap_cli')
                target_path = os.path.join(dockerfile_folder, dockerfile_costing_path)
                try:
                    if os.path.exists(target_path):
                        os.remove(target_path)
                        print(f"Cleaned up costing file from build context: {target_path}")
                except Exception as e:
                    print(f"Warning: Could not clean up costing file: {e}")

            if copy_factors_file == True and dockerfile_factors_path != 'do_not_delete.txt':
                dockerfile_folder = os.path.join(PROJECT_FOLDER, 'src', 'Dockerfiles', 'btap_cli')
                target_path = os.path.join(dockerfile_folder, dockerfile_factors_path)
                try:
                    if os.path.exists(target_path):
                        os.remove(target_path)
                        print(f"Cleaned up costing factors file from build context: {target_path}")
                except Exception as e:
                    print(f"Warning: Could not clean up costing factors file: {e}")

        else:
            print("Skipping building btap_cli image at users request.")


def delete_aws_build_env(build_env_name = None):
    os.environ['BUILD_ENV_NAME'] = build_env_name
    # Tear down
    ace_worker = AWSComputeEnvironment(build_env_name=build_env_name, name='btap_cli')
    ace_manager = AWSComputeEnvironment(build_env_name=build_env_name,name='btap_batch')
    image_worker = AWSImageManager(build_env_name=build_env_name, image_name='btap_cli')
    image_manager = AWSImageManager(build_env_name=build_env_name, image_name='btap_batch', compute_environment=ace_worker)
    # tear down aws_btap_cli batch framework.
    batch_cli = AWSBatch(build_env_name=build_env_name, image_manager=image_worker, compute_environment=ace_worker)
    batch_cli.tear_down()
    # tear down aws_btap_batch batch framework.
    batch_manager = AWSBatch(build_env_name=build_env_name, image_manager=image_manager, compute_environment=ace_manager)
    batch_manager.tear_down()
    # tear down compute resources.
    ace_worker.tear_down()
    ace_manager.tear_down()
    # Delete user role permissions.
    IAMBatchJobRole(build_env_name=build_env_name).delete()
    IAMCodeBuildRole(build_env_name=build_env_name).delete()
    IAMBatchServiceRole(build_env_name=build_env_name).delete()
    # Delete repositories/images from AWS
    image_manager.delete_image()
    image_worker.delete_image()




def analysis(project_input_folder=None,
             build_config=None,
             output_folder=None):

    compute_environment = None
    # If build_env is available in the build config use it.
    if build_config != None:
        if 'build_env_name' in build_config:
            os.environ['BUILD_ENV_NAME'] = build_config['build_env_name']
        if 'compute_environment' in build_config:
            compute_environment = build_config['compute_environment']


    # If project folder is on S3.  Download the folder to work on it locally.
    if project_input_folder.startswith('s3:'):
        # download project to local temp folder.
        local_dir = os.path.join(str(Path.home()), 'temp_analysis_folder')
        # Check if folder exists
        if os.path.isdir(local_dir):
            # Remove old folder
            try:
                shutil.rmtree(local_dir)
            except PermissionError:
                message = f'Could not delete {local_dir}. Do you have a file open in that folder? Exiting'
                print(message)
                exit(1)
        S3().download_s3_folder(s3_folder=project_input_folder, local_dir=local_dir)
        project_input_folder = local_dir


        # Set compute_environment to local_managed_aws_workers.
        path_to_yml = os.path.join(project_input_folder, 'input.yml')
        with Path(path_to_yml).open() as fp:
            config = yaml.safe_load(fp)
        # If this was taken from S3. Force it to be locally managed analysis.
        config['compute_environment'] = 'local_managed_aws_workers'

        with open(path_to_yml, 'w') as outfile:
            yaml.dump(config, outfile, default_flow_style=False)




    # path of analysis input.yml
    analysis_config_file = os.path.join(project_input_folder, 'input.yml')

    if not os.path.isfile(analysis_config_file):
        print(f"input.yml file does not exist at path {analysis_config_file}")
        exit(1)
    if not os.path.isdir(project_input_folder):
        print(f"Folder does not exist at path {analysis_config_file}")
        exit(1)
    analysis_config, analysis_input_folder, analyses_folder = BTAPAnalysis.load_analysis_input_file(
        analysis_config_file=analysis_config_file)
    
    if 'build_env_name' in analysis_config: # input.yml has priority.
        os.environ['BUILD_ENV_NAME'] = config['build_env_name']

    # Set compute Environment
    if 'compute_environment' in analysis_config:
        compute_environment = analysis_config['compute_environment']

    if compute_environment == None:
        raise("Computer environment was not defined")

    reference_run = analysis_config[':reference_run']
    # delete output from previous run if present locally
    project_folder = os.path.join(output_folder,analysis_config[':analysis_name'])
    # Check if folder exists
    if os.path.isdir(project_folder):
        # Remove old folder
        try:
            shutil.rmtree(project_folder)
        except PermissionError:
            message = f'Could not delete {project_folder}. Do you have a file open in that folder or permissions to delete that folder? When running locally docker sometimes runs as another user requiring you to be admin to delete files. Exiting'
            print(message)
            exit(1)

    # delete output from previous run if present on s3
    if compute_environment == 'local_managed_aws_workers' or compute_environment == 'aws':
        bucket = AWSCredentials().account_id
        user_name = os.environ.get('BUILD_ENV_NAME').replace('.', '_')
        # Check if aws build_env_name exists
        if not user_name in AWSImageManager.get_existing_build_env_names():
            print(f"build_env_name '{user_name}' does not exist on aws. Have you built it using the build command yet?")

        prefix = os.path.join(user_name, analysis_config[':analysis_name'] + '/')
        print(f"Deleting old files in S3 folder {prefix}")
        S3().bulk_del_with_pbar(bucket=bucket, prefix=prefix)

        print("")
        print("#########################################################################")
        print("################## compute_environment pre: {} ##################".format(compute_environment))
        print("#########################################################################")
        print("")

    if compute_environment == 'local' or compute_environment == 'local_managed_aws_workers':
        print("")
        print("#########################################################################")
        print("################## compute_environment post: {} ##################".format(compute_environment))
        print("#########################################################################")
        print("")
        analysis_config[':compute_environment'] = compute_environment

        # Don't run a reference run on a reference analysis
        if analysis_config[':algorithm_type'] == 'reference':
            reference_run = False

        reference_run_df = None
        if reference_run == True:
            if analysis_config[':algorithm_type'] != 'batch':
                # Run reference
                print("")
                print("#########################################################################")
                print("################## Running reference case for analysis ##################")
                print("#########################################################################")
                print("")
                ref_analysis_config = copy.deepcopy(analysis_config)
                ref_analysis_config[':algorithm_type'] = 'reference'
                br = BTAPReference(analysis_config=ref_analysis_config,
                                   analysis_input_folder=analysis_input_folder,
                                   output_folder=os.path.join(output_folder))

                br.run()
                reference_run_df = br.btap_data_df
                print("")
                print("#########################################################################")
                print("#################### Finished running reference case ####################")
                print("#########################################################################")
                print("")

        # BTAP analysis placeholder.
        ba = None

        # nsga2
        if analysis_config[':algorithm_type'] == 'nsga2':
            print("")
            print("#########################################################################")
            print("#################### Creating optimization analysis #####################")
            print("#########################################################################")
            print("")
            ba = BTAPOptimization(analysis_config=analysis_config,
                                  analysis_input_folder=analysis_input_folder,
                                  output_folder=output_folder,
                                  reference_run_df=reference_run_df)
            print("")
            print("#########################################################################")
            print("################# Finished creating optimization analysis ###############")
            print("#########################################################################")
            print("")
        # parametric
        elif analysis_config[':algorithm_type'] == 'parametric':
            ba = BTAPParametric(analysis_config=analysis_config,
                                analysis_input_folder=analysis_input_folder,
                                output_folder=os.path.join(output_folder),
                                reference_run_df=reference_run_df)

        # parametric
        elif analysis_config[':algorithm_type'] == 'elimination':
            ba = BTAPElimination(analysis_config=analysis_config,
                                 analysis_input_folder=analysis_input_folder,
                                 output_folder=output_folder,
                                 reference_run_df=reference_run_df)

        elif analysis_config[':algorithm_type'] == 'sampling-lhs':
            ba = BTAPSamplingLHS(analysis_config=analysis_config,
                                 analysis_input_folder=analysis_input_folder,
                                 output_folder=output_folder,
                                 reference_run_df=reference_run_df)

        elif analysis_config[':algorithm_type'] == 'sensitivity':
            ba = BTAPSensitivity(analysis_config=analysis_config,
                                 analysis_input_folder=analysis_input_folder,
                                 output_folder=output_folder,
                                 reference_run_df=reference_run_df)

        elif analysis_config[':algorithm_type'] == 'reference':
            ba = BTAPReference(analysis_config=analysis_config,
                               analysis_input_folder=analysis_input_folder,
                               output_folder=output_folder)

        elif analysis_config[':algorithm_type'] == 'batch':
            ba = BTAPBatchAnalysis(analysis_config=analysis_config,
                                   analysis_input_folder=analysis_input_folder,
                                   output_folder=output_folder)


        else:
            print(f"Error:Analysis type {analysis_config[':algorithm_type']} not supported. Exiting.")
            exit(1)

        print("")
        print("#########################################################################")
        print("#################### Starting optimization analysis #####################")
        print("#########################################################################")
        print("")
        ba.run()
        print("")
        print("#########################################################################")
        print("#################### Finished optimization analysis #####################")
        print("#########################################################################")
        print("")
        print(f"Excel results file {ba.analysis_excel_results_path()}")
        if compute_environment == 'local':
            generate_btap_reports(data_file=ba.analysis_excel_results_path(), pdf_output_folder=ba.analysis_results_folder())


    elif compute_environment == 'aws':
        analysis_name = analysis_config[':analysis_name']
        # Set common paths singleton.
        cp = CommonPaths()
        # Setting paths to current context.
        cp.set_analysis_info(analysis_id=str(uuid.uuid4()),
                             analysis_name=analysis_name,
                             local_output_folder=output_folder,
                             project_input_folder=analysis_input_folder)
        # Gets an AWSAnalysisJob from AWSBatch
        batch = AWSBatch(image_manager=AWSImageManager(image_name='btap_batch'),
                         compute_environment=AWSComputeEnvironment(name='btap_batch')
                         )
        # Submit analysis job to aws.
        job = batch.create_job(job_id=analysis_name, reference_run=reference_run)
        return job.submit_job()


def list_active_analyses():
    # Gets an AWSBatch analyses object.
    ace = AWSComputeEnvironment(name='btap_batch')
    analysis_queue = AWSBatch(image_manager=AWSImageManager(image_name='btap_batch'),
                              compute_environment=ace
                              )
    return analysis_queue.get_active_jobs()


def terminate_aws_analyses():
    # Gets an AWSBatch analyses object.
    ace = AWSComputeEnvironment(name='btap_batch')
    analysis_queue = AWSBatch(image_manager=AWSImageManager(image_name='btap_batch'),
                              compute_environment=ace
                              )
    analysis_queue.clear_queue()

    ace = AWSComputeEnvironment(name='btap_cli')
    batch_cli = AWSBatch(image_manager=AWSImageManager(image_name='btap_cli'), compute_environment=ace)
    batch_cli.clear_queue()


def sensitivity_chart(data_file='/home/plopez/btap_batch/downloads/master.parquet', pdf_output_folder=r"/home/plopez/btap_batch/test"):
    import pandas as pd
    import numpy as np
    import seaborn as sns
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    from icecream import ic
    import dataframe_image as dfi

    import time


    # Get the file extension
    ext = os.path.splitext(data_file)[1]

    if ext == '.csv':
        df = pd.read_csv(data_file)
    elif ext == '.xlsx':
        df = pd.read_excel(data_file)
    elif ext == '.parquet':
        df = pd.read_parquet(data_file)
    else:
        raise RuntimeError('File extension not recognized')

    # Gets all unique values in the scenario column.
    scenarios = df[':scenario'].unique()
    analysis_names = df[':analysis_name'].unique()

    for analysis_name in analysis_names:
        pdf_output_file = os.path.join(pdf_output_folder, analysis_name + ".pdf")
        filtered_df = df.loc[df[':analysis_name'] == 'analysis_name']
        algorithm_type = df[':algorithm_type'].unique()[0]

        if algorithm_type == 'sensitivity':

            # This is a pdf writer.. This will save all our charts to a PDF.
            with PdfPages(pdf_output_file) as pdf:
                # Order Measures that had the biggest impact.
                # https: // stackoverflow.com / questions / 32791911 / fast - calculation - of - pareto - front - in -python
                ranked_df = df.copy()
                # Remove rows where energy savings are negative.
                ranked_df.drop(ranked_df[ranked_df['baseline_energy_percent_better'] <= 0].index, inplace=True)

                # Use only columns for ranking.

                ranked_df["scenario_value"] = ranked_df.values[
                    ranked_df.index.get_indexer(ranked_df[':scenario'].index), ranked_df.columns.get_indexer(
                        ranked_df[':scenario'])]
                ranked_df["energy_savings_per_cost"] = ranked_df['baseline_energy_percent_better'] / ranked_df[
                    "cost_equipment_total_cost_per_m_sq"]
                ranked_df['energy_savings_rank'] = ranked_df['energy_savings_per_cost'].rank(ascending=False)
                ranked_df = ranked_df.sort_values(by=['energy_savings_rank'])
                ranked_df['ECM'] = ranked_df[':scenario'] + "=" + ranked_df["scenario_value"].astype(str)
                # Use only columns for ranking.
                ranked_df = ranked_df[['ECM', ':scenario', 'scenario_value', 'energy_savings_per_cost']]

                ranked_df.plot.barh(x='ECM', y='energy_savings_per_cost')
                plt.tight_layout()
                pdf.savefig()
                plt.close()

                # Apply styling to dataframe and save
                styled_df = ranked_df.style.format({'energy_savings_per_cost': "{:.4f}"}).hide(axis="index").bar(
                    subset=["energy_savings_per_cost", ], color='lightgreen')
                dfi.export(styled_df, 'ecm_ranked.png')

                # Iterate through all scenarios.
                for scenario in scenarios:

                    # Scatter plot

                    sns.scatterplot(
                        x="baseline_energy_percent_better",
                        y="cost_equipment_total_cost_per_m_sq",
                        hue=scenario,
                        data=df.loc[df[':scenario'] == scenario].reset_index())

                    pdf.savefig()
                    plt.close('all')

                    ## Stacked EUI chart.
                    # Filter Table rows by scenario. Save it to a new df named filtered_df.
                    filtered_df = df.loc[df[':scenario'] == scenario].reset_index()
                    # Filter the table to contain only these columns.
                    # List of columns to use for EUI sensitivity.
                    columns_to_use = [
                        scenario,
                        'energy_eui_cooling_gj_per_m_sq',
                        'energy_eui_heating_gj_per_m_sq',
                        'energy_eui_fans_gj_per_m_sq',
                        'energy_eui_heat recovery_gj_per_m_sq',
                        'energy_eui_interior lighting_gj_per_m_sq',
                        'energy_eui_interior equipment_gj_per_m_sq',
                        'energy_eui_water systems_gj_per_m_sq',
                        'energy_eui_pumps_gj_per_m_sq'
                    ]
                    filtered_df = filtered_df[columns_to_use]
                    # Set Scenario Col as String. This makes it easier to plot on the x-axis of the stacked bar chart.
                    filtered_df[scenario] = filtered_df[scenario].astype(str)
                    # Sort order of Scenarios in accending order.
                    filtered_df = filtered_df.sort_values(scenario)
                    # Plot EUI stacked chart.
                    ax = filtered_df.plot(
                        x=scenario,  # The column name used as the x component of the chart.
                        kind='bar',
                        stacked=True,
                        title=f"Sensitivity of {scenario} by EUI ",
                        figsize=(16, 12),
                        rot=0,
                        xlabel=scenario,  # Use the column name as the X label.
                        ylabel='GJ/M2')
                    # Have the amount for each stack in chart.
                    for c in ax.containers:
                        # if the segment is small or 0, do not report zero.remove the labels parameter if it's not needed for customized labels
                        labels = [round(v.get_height(), 3) if v.get_height() > 0 else '' for v in c]
                        ax.bar_label(c, labels=labels, label_type='center')
                    pdf.savefig()
                    plt.close()

                    ## Stacked Costing Chart.
                    # Filter Table rows by scenario. Save it to a new df named filtered_df.
                    filtered_df = df.loc[df[':scenario'] == scenario].reset_index()
                    # Filter the table to contain only these columns.
                    # List of columns that make up costing stacked totals.
                    columns_to_use = [
                        scenario,
                        'cost_equipment_heating_and_cooling_total_cost_per_m_sq',
                        'cost_equipment_lighting_total_cost_per_m_sq',
                        'cost_equipment_shw_total_cost_per_m_sq',
                        'cost_equipment_ventilation_total_cost_per_m_sq',
                        'cost_equipment_thermal_bridging_total_cost_per_m_sq',
                        'cost_equipment_envelope_total_cost_per_m_sq'

                    ]
                    filtered_df = filtered_df[columns_to_use]
                    # Set Scenario Col as String. This makes it easier to plot on the x-axis of the stacked bar.
                    filtered_df[scenario] = filtered_df[scenario].astype(str)
                    # Sort order of Scenarios in accending order.
                    filtered_df = filtered_df.sort_values(scenario)
                    # Plot chart.
                    ax = filtered_df.plot(
                        x=scenario,
                        kind='bar',
                        stacked=True,
                        title=f"Sensitivity of {scenario} by Costing ",
                        figsize=(16, 12),
                        rot=0,
                        xlabel=scenario,
                        ylabel='$/M2')
                    # Have the amount for each stack in chart.
                    for c in ax.containers:
                        # if the segment is small or 0, do not report zero.remove the labels parameter if it's not needed for customized labels
                        labels = [round(v.get_height(), 3) if v.get_height() > 0 else '' for v in c]
                        ax.bar_label(c, labels=labels, label_type='center')
                    pdf.savefig()
                    plt.close()
                    pdf.output()

        elif algorithm_type == "nsga2":
            print("No charting support for optimization yet.")
            # # https: // stackoverflow.com / questions / 32791911 / fast - calculation - of - pareto - front - in -python
            #
            # # 'baseline_necb_tier','cost_equipment_total_cost_per_m_sq'
            # optimization_column_names = ['baseline_energy_percent_better', 'cost_equipment_total_cost_per_m_sq']
            # # Add column to dataframe to indicate optimal datapoints.
            # df['is_on_pareto'] = get_pareto_points(np.array(df[optimization_column_names].values.tolist()))
            #
            # # Filter by pareto curve.
            # pareto_df = df.loc[df['is_on_pareto'] == True].reset_index()
            # bins = [-100, 0, 25, 50, 60, 1000]
            # labels = ["Non-Compliant", "Tier-1", "Tier-2", "Tier-3", "Tier-4"]
            # pareto_df['binned'] = pd.cut(pareto_df['baseline_energy_percent_better'], bins=bins, labels=labels)
            # sns.scatterplot(x="baseline_energy_percent_better",
            #                 y="cost_equipment_total_cost_per_m_sq",
            #                 hue="binned",
            #                 data=pareto_df)
            #
            # plt.show()

        elif algorithm_type == "elimination":
            print("No charting support for Elimination yet.")

        elif algorithm_type == "parametric":
            print("No charting support for parametric yet.")

        elif algorithm_type == "sampling-lhs":
            print("No charting support for sampling-lhs yet.")

        elif algorithm_type == "reference":
            print("No charting support for reference yet.")

        else:
            print(f"Unsupported analysis type {algorithm_type}")


def get_number_of_failures(job_queue_name='btap_cli'):
    # Gets an AWSBatch analyses object.
    analysis_queue = AWSBatch(image_manager=AWSImageManager(image_name=job_queue_name),
                              compute_environment=AWSComputeEnvironment(name=job_queue_name)
                              )
    # Connect to AWS Batch
    client = AWSCredentials().batch_client

    # Initialize the object count
    object_count = 0

    # Use the list_objects_v2 API to retrieve the objects in the folder
    paginator = client.get_paginator('list_jobs')
    response_iterator = paginator.paginate( jobQueue=analysis_queue.job_queue_name,
                                            jobStatus='FAILED')

    # Iterate through the paginated responses
    for response in response_iterator:
        if 'jobSummaryList' in response:
            object_count += len(response['jobSummaryList'])
    return object_count

def generate_build_config(build_config_path = None):
    import yaml

    config = f"""
# This is the name of the build environment. This will prefix all images, s3 folders, and resources created on aws. Please ensure that it is 24 characters long or less, only uses numbers and lowercase letters, and includes no spaces or special characters aside from underscore. Use the underscore character instead of spaces.
build_env_name: {USER.lower()}

# Github Token. This must be set to build and run analyses. See the enable_rsmeans section below if you are NRCan staff and would to access RSMeans costing data. 
git_api_token: null

# Compute Environment used to build and run analyses. Options are
#  local: Will run everything on your own computer. Recommended for running small analysis and testing ahead of using aws.
#  aws: Run everything on Amazon infrastructure. You can turn off your computer after the analyses are all sent to Amazon. Recommended for large analyses.
#  local_managed_aws_workers: Analysis is managed on your local computer but simulations are done on Amazon.. Used by the aws process above.
compute_environment: local

# Branch of btap_batch to be used in aws compute_environment runs on AWS.
btap_batch_branch: dev

# Branch of openstudio-standards used in environment
os_standards_branch: nrcan

# OpenStudio version used by analyses and built into the container environment. The E+ version used for simulations is determined by the OpenStudio version.
openstudio_version: 3.9.0

# Location of weather files to download. 
# If true, downloads from btap_weather. Else, downloads from Climate.OneBuilding.Org. 
# The other locations that you can use can be found in their respective locations here: 
# btap_weather:
#   {HISTORIC_WEATHER_REPO_BTAP}
#   {FUTURE_WEATHER_REPO_BTAP}
# Climate.OneBuilding.Org:
#   {HISTORIC_WEATHER_REPO}
#   {FUTURE_WEATHER_REPO}
btap_weather: True 

# List of Weather files to build included in the build environment. 
# Only .epw files , and <100 files. Other weather locations are available. 
# However, you have to define the ones you want to use when creating your environment.  
weather_list:
  - CAN_QC_Montreal.Intl.AP.716270_CWEC2020.epw
  - CAN_NS_Halifax.Dockyard.713280_CWEC2020.epw
  - CAN_AB_Edmonton.Intl.AP.711230_CWEC2020.epw
  - CAN_BC_Vancouver.Intl.AP.718920_CWEC2020.epw
  - CAN_AB_Calgary.Intl.AP.718770_CWEC2020.epw
  - CAN_ON_Toronto.Intl.AP.716240_CWEC2020.epw
  - CAN_NT_Yellowknife.AP.719360_CWEC2020.epw
  - CAN_AB_Fort.Mcmurray.AP.716890_CWEC2020.epw

# Path to the local costs.csv costing file.  The default is 'resources\costing\costs.csv'. If you are using a custom costing file, you can set the path here.
# All relative paths are relative to the root of the btap_batch repository you are using. Ignore this if you are not using costing or are content with the default costs.csv costing file."
local_costing_path: resources\costing\costs.csv

# Path to the local costs_local_factors.csv costing localization factors file.  The default is 'resources\costing\costs_local_factors.csv'. If you are using a custom costing localization factors file, you can set the path here.
# All relative paths are relative to the root of the btap_batch repository you are using. Ignore this if you are not using local costing localization factors or content with the default costs_local_factors.csv costing localization factors file."
local_factors_path: resources\costing\costs_local_factors.csv

# Rebuild btap_cli image
build_btap_cli: True

# Rebuild btap_batch image
build_btap_batch: True

# Set this to True if you intend to build your environment locally on a computer connected to the NRCan network.
# Otherwise leave it as False.
local_nrcan: False

    """

    output_file = Path(build_config_path)
    output_file.parent.mkdir(exist_ok=True, parents=True)
    output_file.write_text(config)


# This method will a single analysis present in a given S3 path. It will only download the zips and output
# excel files.  It will rename the files with the analysis_name/parent folder name.
# bucket is the s3 bucket.
# prefix is the s3 analysis folder to parse. Note the trailing / is important. It denoted that it is a folder to S3.
# target path is the path on this machine where the files will be stored.
# hourly_csv, eplusout_sql, in_osm, eplustbl_htm are bools that indicate to download those zipfiles. It will always download
# the output.xlsx file.
def download_analysis(key='phylroy_lopez_1/parametric_example/',
                      bucket='834599497928',
                      target_path='/home/plopez/btap_batch/downloads',
                      hourly_csv=False,
                      in_osm=False,
                      eplusout_sql=False,
                      eplustbl_htm=False,
                      unzip_and_delete=True,
                      ):
    filetype = 'output.xlsx'
    source_zip_file = os.path.join(key, 'results', filetype).replace('\\', '/')
    target_zip_basename = os.path.join(target_path, os.path.basename(os.path.dirname(key)) + "_" + filetype)
    S3().download_file(s3_file=source_zip_file, bucket_name=bucket, target_path=target_zip_basename)

    if hourly_csv:
        filetype = 'hourly.csv.zip'
        source_zip_file = os.path.join(key, 'results', 'zips', filetype).replace('\\', '/')
        target_zip_basename = os.path.join(target_path, os.path.basename(os.path.dirname(key)) + "_" + filetype)
        is_downloaded = S3().download_file(s3_file=source_zip_file, bucket_name=bucket, target_path=target_zip_basename)
        if unzip_and_delete and is_downloaded:
            extraction_folder_suffix = 'hourly.csv'
            extraction_folder = os.path.join(target_path, extraction_folder_suffix)
            pathlib.Path(extraction_folder).mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(target_zip_basename, 'r') as zip_ref:
                zip_ref.extractall(extraction_folder)
            pathlib.Path(target_zip_basename).unlink(missing_ok=True)

    if in_osm:
        filetype = 'in.osm.zip'
        source_zip_file = os.path.join(key, 'results', 'zips', filetype).replace('\\', '/')
        target_zip_basename = os.path.join(target_path, os.path.basename(os.path.dirname(key)) + "_" + filetype)
        is_downloaded = S3().download_file(s3_file=source_zip_file, bucket_name=bucket, target_path=target_zip_basename)
        if unzip_and_delete and is_downloaded:
            extraction_folder_suffix = 'in.osm'
            extraction_folder = os.path.join(target_path, extraction_folder_suffix)
            pathlib.Path(extraction_folder).mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(target_zip_basename, 'r') as zip_ref:
                zip_ref.extractall(extraction_folder)
            pathlib.Path(target_zip_basename).unlink(missing_ok=True)

    if eplusout_sql:
        filetype = 'eplusout.sql.zip'
        source_zip_file = os.path.join(key, 'results', 'zips', filetype).replace('\\', '/')
        target_zip_basename = os.path.join(target_path, os.path.basename(os.path.dirname(key)) + "_" + filetype)
        is_downloaded = S3().download_file(s3_file=source_zip_file, bucket_name=bucket, target_path=target_zip_basename)
        if unzip_and_delete and is_downloaded:
            extraction_folder_suffix = 'eplusout.sql'
            extraction_folder = os.path.join(target_path, extraction_folder_suffix)
            pathlib.Path(extraction_folder).mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(target_zip_basename, 'r') as zip_ref:
                zip_ref.extractall(extraction_folder)
            pathlib.Path(target_zip_basename).unlink(missing_ok=True)

    if eplustbl_htm:
        filetype = 'eplustbl.htm.zip'
        source_zip_file = os.path.join(key, 'results', 'zips', filetype).replace('\\', '/')
        target_zip_basename = os.path.join(target_path, os.path.basename(os.path.dirname(key)) + "_" + filetype)
        is_downloaded = S3().download_file(s3_file=source_zip_file, bucket_name=bucket, target_path=target_zip_basename)
        if unzip_and_delete and is_downloaded:
            extraction_folder_suffix = 'eplustbl.htm'
            extraction_folder = os.path.join(target_path, extraction_folder_suffix)
            pathlib.Path(extraction_folder).mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(target_zip_basename, 'r') as zip_ref:
                zip_ref.extractall(extraction_folder)
            pathlib.Path(target_zip_basename).unlink(missing_ok=True)


# This method will download all the analysis present in a given S3 path. It will only download the zips and output
# excel files.  It will rename the files with the analysis_name/parent folder name.
# bucket is the s3 bucket.
# prefix is the s3 folder to parse. Note the trailing / is important. It denoted that it is a folder to S3.
# target path is the path on this machine where the files will be stored.

def download_analyses(bucket='834599497928',
                      build_env_name='solution_sets/',
                      output_path='/home/plopez/btap_batch/downloads',
                      hourly_csv=True,
                      in_osm=True,
                      eplusout_sql=True,
                      eplustbl_htm=True,
                      concat_excel_files=True,
                      analysis_name='vin.*YUL.*',
                      unzip_and_delete=True,
                      dry_run=True
                      ):
    folders = S3().s3_get_list_of_folders_in_folder(bucket=bucket, prefix=build_env_name)
    if build_env_name + 'btap_cli/' in folders:
        folders.remove(build_env_name + 'btap_cli/')

    if build_env_name + 'btap_batch/' in folders:
        folders.remove(build_env_name + 'btap_batch/')

    for folder in folders:

        if re.search(analysis_name, folder) != None:
            print(f"Processing {folder}")
        if re.search(analysis_name, folder) and not dry_run:
            download_analysis(key=folder,
                              bucket=bucket,
                              target_path=output_path,
                              hourly_csv=hourly_csv,
                              in_osm=in_osm,
                              eplusout_sql=eplusout_sql,
                              eplustbl_htm=eplustbl_htm,
                              unzip_and_delete=unzip_and_delete
                              )
    if concat_excel_files and not dry_run:
        print(f"Creating master csv and parquet results file.")
        all_files = os.listdir(output_path)
        xlsx_files = [f for f in all_files if f.endswith('.xlsx')]
        df_list = []
        for xlsx in xlsx_files:
            try:
                df = pd.read_excel(os.path.join(output_path, xlsx))
                print(f"Appending {xlsx} to master csv file.")
                df_list.append(df)
            except Exception as e:
                print(f"Could not read file {xlsx} because of error: {e}")
        # Concatenate all data into one DataFrame
        big_df = pd.concat(df_list, ignore_index=True)

        # Save the final result to a new CSV file
        master_csv_path = os.path.join(output_path, 'master.csv')
        big_df.to_csv(master_csv_path, index=False)

        # Create parquet file.
        master_parquet_file = os.path.join(output_path, 'master.parquet')

        # Horrible workaround to deal with non-uniform datatypes in columns.
        big_df = pd.read_csv(master_csv_path, dtype='unicode')
        big_df.to_parquet(master_parquet_file)
        generate_btap_reports(data_file=master_csv_path,
                              pdf_output_folder=os.path.join(output_path,'pdf'))

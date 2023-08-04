import pip_system_certs.wrapt_requests
from src.btap.constants import WORKER_CONTAINER_MEMORY, WORKER_CONTAINER_STORAGE, WORKER_CONTAINER_VCPU
from src.btap.constants import MANAGER_CONTAINER_VCPU, MANAGER_CONTAINER_MEMORY, MANAGER_CONTAINER_STORAGE
from src.btap.aws_batch import AWSBatch
from src.btap.aws_compute_environment import AWSComputeEnvironment
from src.btap.aws_image_manager import AWSImageManager
from src.btap.docker_image_manager import DockerImageManager
from src.btap.aws_iam_roles import IAMBatchJobRole, IAMBatchServiceRole, IAMCodeBuildRole
#from src.btap.btap_analysis import BTAPAnalysis
from src.btap.btap_reference import BTAPReference
from src.btap.btap_optimization import BTAPOptimization
from src.btap.btap_parametric import BTAPParametric
from src.btap.btap_elimination import BTAPElimination
from src.btap.btap_lhs import BTAPSamplingLHS
from src.btap.btap_sensitivity import BTAPSensitivity
from src.btap.aws_s3 import S3
from src.btap.common_paths import CommonPaths

# Stuff we need
from src.btap.aws_s3 import S3
from src.btap.btap_analysis import BTAPAnalysis
from zipfile import ZipFile
import requests
import logging
import shutil

import time
import copy
import os
from pathlib import Path
import uuid
from icecream import ic
from src.btap.aws_dynamodb import AWSResultsTable

HISTORIC_WEATHER_LIST = "https://github.com/canmet-energy/btap_weather/raw/main/historic_weather_filenames.json"
FUTURE_WEATHER_LIST = "https://github.com/canmet-energy/btap_weather/raw/main/future_weather_filenames.json"
HISTORIC_WEATHER_REPO = "https://github.com/canmet-energy/btap_weather/raw/main/historic/"
FUTURE_WEATHER_REPO = "https://github.com/canmet-energy/btap_weather/raw/main/future/"

def download_weather_files(cust_weather_loc=None, cust_weather_dir=None, hist_files=None, fut_files=None):
    # Set the zip file name
    weather_file = cust_weather_loc + (".zip")
    # Check if the zip file is a historic file, a future data file, or not in the btap_weather repository
    future_file = False
    if weather_file in hist_files:
        repo_url = HISTORIC_WEATHER_REPO
    if weather_file in fut_files:
        repo_url = FUTURE_WEATHER_REPO
        future_file = True
    else:
        # If not in the repository produce an error
        logging.error(f"Could not fine epw file {weather_file} in the btap_weather repository. Exiting")
    # Download the file and write it to the custom weather folder directory
    download_url = repo_url + weather_file
    download_name = os.path.join(cust_weather_dir, weather_file)
    r = requests.get(download_url, allow_redirects=True)
    open(download_name, 'wb').write(r.content)
    # loading the zip and creating a zip object
    with ZipFile(download_name, 'r') as zObject:
        # Extracting all files in the zip into a specific location.
        zObject.extractall(path=cust_weather_dir)
    zObject.close()
    # If future weather data is used, copy the _ASHRAE.ddy file to be the .ddy file to avoid simulation issues.
    if future_file:
        init_name = cust_weather_loc + ".ddy"
        rev_name = cust_weather_loc + "_orig.ddy"
        ashrae_name = cust_weather_loc + "_ASHRAE.ddy"
        init_name = os.path.join(cust_weather_dir, init_name)
        rev_name = os.path.join(cust_weather_dir, rev_name)
        ashrae_name = os.path.join(cust_weather_dir, ashrae_name)
        shutil.copy(init_name, rev_name)
        shutil.copy(ashrae_name, init_name)

def define_weather_library(compute_environment=None, weather_folder=None, weather_dict=None):
    # Get the default weather locations from the default_weather_locs.yml file.
    def_weather_dir = os.getcwd()
    def_weather_file = os.path.join(def_weather_dir, 'default_weather_locs.yml')
    def_weather_config, def_weather_folder, def_weather_analyses_folder = BTAPAnalysis.load_analysis_input_file(
        analysis_config_file=def_weather_file)
    def_weather_locs = def_weather_config[':weather_locations']

    # Set default custom weather folder location
    cust_weather_dir = os.path.join(def_weather_dir, '..', '..', 'weather_library')
    # Set default custom weather yml file location
    cust_weather_file = os.path.join(cust_weather_dir, 'weather_locs.yml')

    # Check if a custom weather folder was defined.  If not then use the default folder defined above.
    if weather_folder is not None:
        if not os.path.isdir(weather_folder):
            logging.error(f"could not find folder {weather_folder}. Exiting")
        cust_weather_dir = weather_folder

    # Check if a custom weather yml file was defined.  If not then use the default file defined above.
    if weather_dict is not None:
        if not os.path.isfile(weather_dict):
            logging.error(f"could not find weather file list at {weather_dict}. Exiting")
        else:
            cust_weather_config, cust_weather_folder, cust_weather_analyses_folder = BTAPAnalysis.load_analysis_input_file(
                analysis_config_file=weather_dict)
    else:
        cust_weather_file = os.path.join(cust_weather_dir, 'weather_locs.yml')
        cust_weather_config, cust_weather_folder, cust_weather_analyses_folder = BTAPAnalysis.load_analysis_input_file(
            analysis_config_file=cust_weather_file)


    init_cust_weather_locs = cust_weather_config[':weather_locations']

    # Check if any of the custom weather locations are actually default weather locations
    cust_weather_locs = []
    for weather_loc in init_cust_weather_locs:
        is_default_loc = weather_loc in def_weather_locs
        if not is_default_loc:
            cust_weather_locs.append(weather_loc)

    # If custom weather locations were found then download and extract them
    if len(cust_weather_locs) > 0:
        # Get the lists of historic and future weather files from btap_weather
        r = requests.get(HISTORIC_WEATHER_LIST, allow_redirects=True)
        hist_files = r.json()
        r = requests.get(FUTURE_WEATHER_LIST, allow_redirects=True)
        fut_files = r.json()
        # Cycle through the weather files we want to get and download and extract them
        for cust_weather_loc in cust_weather_locs:
            # Remove the extension from the file name since the zip file contains many files with different extensions but
            # the same initial name.
            ext_ind = cust_weather_loc.rindex('.')
            cust_weather_pre = cust_weather_loc[0:ext_ind]
            download_weather_files(cust_weather_loc=cust_weather_pre, cust_weather_dir=cust_weather_dir,
                                   hist_files=hist_files, fut_files=fut_files)

    # Check weather library folder for epw, ddy, and stat files.
    cust_weather_files = os.listdir(cust_weather_dir)
    cust_weather_files_pre = []

    # Go through each weather file in the custom weather folder and make sure an epw, ddy, and stat file with the same
    # name are present.
    for cust_weather_file in cust_weather_files:
        # Get the file name with the file extension
        ext_ind = cust_weather_file.rindex('.')
        cust_weather_pre = cust_weather_file[0:ext_ind]
        ext_type = cust_weather_file[(ext_ind+1):len(cust_weather_file)]
        # Check if the file is one we care about:
        if (ext_type == 'epw') or (ext_type == 'ddy') or (ext_type == 'stat'):
            # Check if you already looked for the files
            in_weather_list = cust_weather_pre in cust_weather_files_pre
            if not in_weather_list:
                # If you didn't make sure each file type is present
                epw_file = cust_weather_pre + ".epw"
                ddy_file = cust_weather_pre + ".ddy"
                stat_file = cust_weather_pre + ".stat"
                epw_loc = os.path.join(cust_weather_dir, epw_file)
                ddy_loc = os.path.join(cust_weather_dir, ddy_file)
                stat_file = os.path.join(cust_weather_dir, stat_file)
                if not os.path.isfile(epw_loc):
                    logging.error(f"Missing epw file {epw_file}. Exiting")
                if not os.path.isfile(ddy_loc):
                    logging.error(f"Missing ddy file {epw_file}. Exiting")
                if not os.path.isfile(epw_loc):
                    logging.error(f"Missing stat file {stat_file}. Exiting")
                cust_weather_files_pre.append(cust_weather_pre)

    # If this is an AWS run copy the weather files to an S3 weather library
    if compute_environment == 'aws_batch_analysis':
        destination_folder = 'weather_library'
        #S3.copy_folder_to_s3(bucket, cust_weather_folder, s3.get_username() + '/' + destination_folder)

    analysis_input_folder = os.path.dirname(os.path.realpath(analysis_config_file))
    def_weather_config_file = current_dir

    def_weather_config, def_weather_folder, def_wetaher_analyses_folder = BTAPAnalysis.load_analysis_input_file(
        analysis_config_file=analysis_config_file)


    # build args for aws and btap_cli container.
    build_args_btap_cli = {'OPENSTUDIO_VERSION': openstudio_version,
                           'BTAP_COSTING_BRANCH': btap_costing_branch,
                           'OS_STANDARDS_BRANCH': os_standards_branch}
    # build args for btap_batch container.
    build_args_btap_batch = {'BTAP_BATCH_BRANCH': btap_batch_branch}
    if compute_environment == 'aws_batch' or compute_environment == 'all':
        # Tear down
        ace = AWSComputeEnvironment()
        image_cli = AWSImageManager(image_name='btap_cli')
        image_btap_batch = AWSImageManager(image_name='btap_batch', compute_environment=ace)

        # tear down aws_btap_cli batch framework.
        batch_cli = AWSBatch(image_manager=image_cli, compute_environment=ace)
        batch_cli.tear_down()

        # tear down aws_btap_batch batch framework.
        batch_batch = AWSBatch(image_manager=image_btap_batch, compute_environment=ace)
        batch_batch.tear_down()

        # tear down compute resources.
        ace.tear_down()

        # Delete user role permissions.
        IAMBatchJobRole().delete()
        IAMCodeBuildRole().delete()
        IAMBatchServiceRole().delete()

        # # Create new
        IAMBatchJobRole().create_role()
        IAMCodeBuildRole().create_role()
        IAMBatchServiceRole().create_role()
        time.sleep(30)  # Give a few seconds for role to apply.
        ace = AWSComputeEnvironment()
        ace.setup()
        image_cli = AWSImageManager(image_name='btap_cli')
        print('Building AWS btap_cli image')
        image_cli.build_image(build_args=build_args_btap_cli)

        image_batch = AWSImageManager(image_name='btap_batch')
        print('Building AWS btap_batch image')
        image_batch.build_image(build_args=build_args_btap_batch)

        # create aws_btap_cli batch framework.
        batch_cli = AWSBatch(image_manager=image_cli,
                             compute_environment=ace
                             )
        batch_cli.setup(container_vcpu=WORKER_CONTAINER_VCPU,
                        container_memory=WORKER_CONTAINER_MEMORY)
        # create aws_btap_batch batch framework.
        batch_batch = AWSBatch(image_manager=image_batch,
                               compute_environment=ace
                               )
        batch_batch.setup(container_vcpu=MANAGER_CONTAINER_VCPU,
                          container_memory=MANAGER_CONTAINER_MEMORY)

        # Create AWS database for results if it does not already exist.
        AWSResultsTable().create_table()

    if compute_environment == 'all' or compute_environment == 'local_docker':
        # Build btap_batch image
        image_cli = DockerImageManager(image_name='btap_cli')
        print('Building btap_cli image')
        image_cli.build_image(build_args=build_args_btap_cli)

        # # Build batch image
        # image_batch = DockerImageManager(image_name='btap_batch')
        # print('Building btap_batch image')
        # image_batch.build_image(build_args=build_args_btap_batch)
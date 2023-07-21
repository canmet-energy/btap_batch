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

from src.btap.btap_analysis import BTAPAnalysis
import requests

import shutil
import time
import copy
import os
from pathlib import Path
import uuid
from icecream import ic
from src.btap.aws_dynamodb import AWSResultsTable

def define_weather_library(compute_environment=None,):
    # Get the default weather locations from the default_weather_locs.yml file.
    def_weather_dir = os.getcwd()
    def_weather_file = os.path.join(def_weather_dir, 'default_weather_locs.yml')
    def_weather_config, def_weather_folder, def_weather_analyses_folder = BTAPAnalysis.load_analysis_input_file(
        analysis_config_file=def_weather_file)
    def_weather_locs = def_weather_config[':weather_locations']

    # Set custom weather file location
    cust_weather_dir = os.path.join(def_weather_dir, '..', '..', 'weather_library')

    # Read weather locations from the custom weather location yml file
    cust_weather_file = os.path.join(cust_weather_dir, 'weather_locs.yml')
    cust_weather_config, cust_weather_folder, cust_weather_analyses_folder = BTAPAnalysis.load_analysis_input_file(
        analysis_config_file=def_weather_file)
    init_cust_weather_locs = cust_weather_config[':weather_locations']

    # Check if any of the custom weather locations are actually default weather locations
    cust_weather_locs = []
    for weather_loc in init_cust_weather_locs:
        is_default_loc = weather_loc in def_weather_locs
        if not is_default_loc:
            cust_weather_locs.append(weather_loc)

    # Check weather library folder for epw, ddy, and stat files.
    cust_weather_files = os.listdir(cust_weather_dir)


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
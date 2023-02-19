from src.btap.aws_batch import AWSBatch
from src.btap.aws_compute_environment import AWSComputeEnvironment
from src.btap.aws_image_manager import AWSImageManager
from src.btap.docker_image_manager import DockerImageManager
from src.btap.aws_iam_roles import IAMBatchJobRole, IAMBatchServiceRole, IAMCloudBuildRole
from src.btap.btap_analysis import BTAPAnalysis
from src.btap.btap_reference import BTAPReference
from src.btap.btap_optimization import BTAPOptimization
from src.btap.btap_parametric import BTAPParametric
from src.btap.btap_elimination import BTAPElimination
from src.btap.btap_lhs import BTAPSamplingLHS
from src.btap.btap_sensitivity import BTAPSensitivity
from src.btap.aws_s3 import S3
from src.btap.common_paths import CommonPaths
import shutil
import time
import copy
import os
from pathlib import Path
import uuid
from icecream import ic
from src.btap.aws_dynamodb import AWSResultsTable

def build_and_configure_docker_and_aws(btap_batch_branch=None,
                                       btap_costing_branch=None,
                                       compute_environment=None,
                                       openstudio_version=None,
                                       os_standards_branch=None):
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
        IAMCloudBuildRole().delete()
        IAMBatchServiceRole().delete()

        # # Create new
        IAMBatchJobRole().create_role()
        IAMCloudBuildRole().create_role()
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
        batch_cli = AWSBatch(image_manager=image_cli, compute_environment=ace)
        batch_cli.setup()
        # create aws_btap_batch batch framework.
        batch_batch = AWSBatch(image_manager=image_batch, compute_environment=ace)
        batch_batch.setup()

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

def analysis(project_input_folder=None,
             compute_environment=None,
             reference_run=None,
             output_folder=None):
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
    #path of analysis input.yml
    analysis_config_file = os.path.join(project_input_folder, 'input.yml')

    if not os.path.isfile(analysis_config_file):
        print(f"input.yml file does not exist at path {analysis_config_file}")
        exit(1)
    if not os.path.isdir(project_input_folder):
        print(f"Folder does not exist at path {analysis_config_file}")
        exit(1)
    analysis_config, analysis_input_folder, analyses_folder = BTAPAnalysis.load_analysis_input_file(
        analysis_config_file=analysis_config_file)

    if compute_environment == 'local_docker' or compute_environment == 'aws_batch':
        analysis_config[':compute_environment'] = compute_environment

        reference_run_data_path = None
        if reference_run:
            # Run reference
            ref_analysis_config = copy.deepcopy(analysis_config)
            ref_analysis_config[':algorithm_type'] = 'reference'
            br = BTAPReference(analysis_config=ref_analysis_config,
                               analysis_input_folder=analysis_input_folder,
                               analyses_folder=os.path.join(output_folder))
            br.run()



            reference_run_data_path = br.analysis_excel_results_path()

        #ic(reference_run_data_path)

        # BTAP analysis placeholder.
        ba = None

        # nsga2
        if analysis_config[':algorithm_type'] == 'nsga2':
            ba = BTAPOptimization(analysis_config=analysis_config,
                                  analysis_input_folder=analysis_input_folder,
                                  analyses_folder=output_folder,
                                  reference_run_data_path=reference_run_data_path)
        # parametric
        elif analysis_config[':algorithm_type'] == 'parametric':
            ba = BTAPParametric(analysis_config=analysis_config,
                                analysis_input_folder=analysis_input_folder,
                                analyses_folder=output_folder,
                                reference_run_data_path=reference_run_data_path)

        # parametric
        elif analysis_config[':algorithm_type'] == 'elimination':
            ba = BTAPElimination(analysis_config=analysis_config,
                                 analysis_input_folder=analysis_input_folder,
                                 analyses_folder=output_folder,
                                 reference_run_data_path=reference_run_data_path)

        elif analysis_config[':algorithm_type'] == 'sampling-lhs':
            ba = BTAPSamplingLHS(analysis_config=analysis_config,
                                 analysis_input_folder=analysis_input_folder,
                                 analyses_folder=output_folder,
                                 reference_run_data_path=reference_run_data_path)

        elif analysis_config[':algorithm_type'] == 'sensitivity':
            ba = BTAPSensitivity(analysis_config=analysis_config,
                                 analysis_input_folder=analysis_input_folder,
                                 analyses_folder=output_folder,
                                 reference_run_data_path=reference_run_data_path)

        elif analysis_config[':algorithm_type'] == 'reference':
            ba = BTAPReference(analysis_config=analysis_config,
                                 analysis_input_folder=analysis_input_folder,
                                 analyses_folder=output_folder)

        else:
            print(f"Error:Analysis type {analysis_config[':algorithm_type']} not supported. Exiting.")
            exit(1)

        ba.run()
        print(f"Excel results file {ba.analysis_excel_results_path()}")

    if compute_environment == 'aws_batch_analysis':
        analysis_name = analysis_config[':analysis_name']
        analyses_folder = analysis_config[':analysis_name']
        # Set common paths singleton.
        cp = CommonPaths()
        # Setting paths to current context.
        cp.set_analysis_info(analysis_id=str(uuid.uuid4()),
                             analysis_name=analysis_name,
                             local_output_folder=output_folder,
                             project_input_folder=analysis_input_folder)
        # Gets an AWSAnalysisJob from AWSBatch
        batch = AWSBatch(image_manager=AWSImageManager(image_name='btap_batch'),
                         compute_environment=AWSComputeEnvironment())
        # Submit analysis job to aws.
        job = batch.create_job(job_id=analysis_name)
        return job.submit_job()




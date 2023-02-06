import click
import logging
import time
from src.compute_resources.aws_batch import AWSBatch
from src.compute_resources.aws_compute_environment import AWSComputeEnvironment
from src.compute_resources.aws_image_manager import AWSImageManager
from src.compute_resources.docker_image_manager import DockerImageManager
from src.compute_resources.aws_iam_roles import IAMBatchJobRole, IAMBatchServiceRole, IAMCloudBuildRole
from src.compute_resources.btap_analysis import BTAPAnalysis
from src.compute_resources.btap_reference import BTAPReference
from src.compute_resources.btap_optimization import BTAPOptimization
from src.compute_resources.btap_parametric import BTAPParametric
from src.compute_resources.btap_elimination import BTAPElimination
from src.compute_resources.btap_lhs import BTAPSamplingLHS
from src.compute_resources.btap_sensitivity import BTAPSensitivity
from src.compute_resources.aws_s3 import S3
from src.compute_resources.common_paths import CommonPaths
import shutil
from colorama import Fore, Style
import time
import copy
import os
from pathlib import Path
import uuid
import pyfiglet
import random
from icecream import ic
from src.compute_resources.aws_dynamodb import AWSDynamodb

PROJECT_FOLDER = os.path.join(Path(os.path.dirname(os.path.realpath(__file__))).parent.absolute())
OUTPUT_FOLDER = os.path.join(PROJECT_FOLDER, "output")
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(version='1.0.0')
def btap():
    pass


@btap.command()
def credits():
    print(Fore.GREEN +"CanmetENERGY Building Technology Assessment Platform Team (BTAP)" + Style.RESET_ALL)
    colors = [Fore.RED,
              Fore.GREEN,
              Fore.MAGENTA,
              Fore.CYAN,
              Fore.YELLOW,
              Fore.BLUE
              ]
    for x in [
                 'Meli Stylianou\n'
                 "Sara Gilani\n",
                 "Kamel Haddad\n",
                 "Chris Kirney\n",
                 "Mike Lubun\n",
                 "Phylroy Lopez\n",
                 "Ali Syed\n"
    ]:
        print(random.choice(colors) + pyfiglet.figlet_format(x) + Fore.RESET)


@btap.command()
@click.option('--compute_environment', default='local_docker', help='configure local_docker, aws_batch or all')
@click.option('--btap_batch_branch',   default='remove_anaconda', help='branch to use for btap_batch. Default = master')
@click.option('--os_standards_branch', default='nrcan', help='branch to use for openstudio-standards branch')
@click.option('--btap_costing_branch', default='master', help='branch to use for btap_costing branch')
@click.option('--openstudio_version', default='3.2.1', help='version of openstudio to use.. Do not change.')
def build_environment(**kwargs):
    compute_environment = kwargs['compute_environment']
    btap_batch_branch = kwargs['btap_batch_branch']
    os_standards_branch = kwargs['os_standards_branch']
    btap_costing_branch = kwargs['btap_costing_branch']
    openstudio_version = kwargs['openstudio_version']
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
        # Create AWS database for results
        AWSDynamodb().create_results_table()


    if compute_environment == 'all' or compute_environment == 'local_docker':
        # Build btap_cli image
        image_batch = DockerImageManager(image_name='btap_batch')
        print('Building btap_batch image')
        image_batch.build_image(build_args=build_args_btap_batch)
        # Build btap_batch image
        image_cli = DockerImageManager(image_name='btap_cli')
        print('Building btap_cli image')
        image_cli.build_image(build_args=build_args_btap_cli)


@btap.command()
@click.option('--compute_environment', default='local_docker',
              help='Environment to run analysis either local_docker or aws_batch')
@click.option('--project_folder',
              help='location of folder containing input.yml file and optionally support folder such as osm_files folder. ')
@click.option('--reference_run', is_flag=True,
              help='Run reference. Required for baseline comparisons')
@click.option('--output_folder', default=r"C:\Users\plopez\btap_batch\output",
              help='Run reference. Required for baseline comparisons')

def run_analysis_project(**kwargs):
    # Input folder name
    analysis_project_folder = kwargs['project_folder']
    compute_environment = kwargs['compute_environment']
    reference_run = kwargs['reference_run']
    output_folder = kwargs['output_folder']
    analysis(analysis_project_folder, compute_environment, reference_run, output_folder)


def analysis(project_input_folder, compute_environment, reference_run, output_folder):
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

        print("analysis")
        ic(reference_run_data_path)

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


@btap.command()
def result_data_reset(**kwargs):
    AWSDynamodb().delete_results_table()
    AWSDynamodb().create_results_table()

@btap.command()
@click.option('--type', default="csv", help='format type to dump entire results information. Choices are pickle or csv')
@click.option('--folder_path', default=OUTPUT_FOLDER, help='folder path to save database file dump. Defaults to projects output folder. ')
def result_data_dump(**kwargs):
    type = kwargs['type']
    folder_path = kwargs['folder_path']
    AWSDynamodb().dump_results_table(folder_path=folder_path, type=type)


@btap.command()
@click.option('--compute_environment', default='local_docker',
              help='Environment to run analysis either local_docker or aws_batch')
def parallel_test_examples(**kwargs):
    start = time.time()
    examples_folder = os.path.join(PROJECT_FOLDER,'examples')
    example_folders = ['custom_osm',
                      'elimination',
                      'optimization',
                      'parametric',
                      'sample-lhs',
                      'sensitivity']

    for folder in example_folders:
        project_input_folder = os.path.join(examples_folder,folder)
        print(project_input_folder)
        analysis(project_input_folder, kwargs['compute_environment'], True, OUTPUT_FOLDER)
    end = time.time()
    print(f"Time elapsed: {end-start}")


if __name__ == '__main__':
    btap()

# Sample commands.
# set PYTHONPATH=C:\Users\plopez\btap_batch &&  python ./bin/btap_batch.py run-analysis-project --compute_environment aws_batch_analysis --project_folder C:\Users\plopez\btap_batch\examples\optimization
# set PYTHONPATH=C:\Users\plopez\btap_batch &&  python ./bin/btap_batch.py run-analysis-project --compute_environment local_docker --project_folder C:\Users\plopez\btap_batch\examples\parametric --run_reference

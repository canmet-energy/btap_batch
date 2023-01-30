import click
from src.compute_resources.aws_batch import AWSBatch
from src.compute_resources.aws_compute_environment import AWSComputeEnvironment
from src.compute_resources.aws_image_manager import AWSImageManager
from src.compute_resources.docker_image_manager import DockerImageManager
from src.compute_resources.aws_iam_roles import IAMBatchJobRole, IAMBatchServiceRole, IAMCloudBuildRole
from src.compute_resources.btap_analysis import BTAPAnalysis
from src.compute_resources.btap_reference import BTAPReference
from src.compute_resources.btap_optimization import BTAPOptimization
from src.compute_resources.btap_parametric import BTAPParametric

import time
import copy
import os


def get_analysis(analysis_config=None,
                 analysis_input_folder=None,
                 analyses_folder=None,
                 reference_run_data_path=None):
    analysis = None

    # nsga2
    if analysis_config[':algorithm_type'] == 'nsga2':
        analysis = BTAPOptimization(analysis_config=analysis_config,
                                    analysis_input_folder=analysis_input_folder,
                                    analyses_folder=analyses_folder,
                                    reference_run_data_path=reference_run_data_path)
    # parametric
    elif analysis_config[':algorithm_type'] == 'parametric':
        analysis = BTAPParametric(analysis_config=analysis_config,
                                  analysis_input_folder=analysis_input_folder,
                                  analyses_folder=analyses_folder,
                                  reference_run_data_path=reference_run_data_path)


    return analysis



CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(version='1.0.0')
def btap():
    pass


@btap.command()
@click.option('--compute_environment', default='local_docker', help='configure local_docker, aws_batch or all')
@click.option('--btap_batch_branch', default='remove_anaconda', help='branch to use for btap_batch. Default = master')
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
@click.option('--compute_environment', default='local_docker', help='Environment to run analysis either local_docker or aws_batch')
@click.option('--project_folder',
              help='location of folder containing input.yml file and optionally support folder such as osm_files folder. ')
def run_analysis_project(**kwargs):
    # Input folder name
    analysis_project_folder = kwargs['project_folder']
    compute_environment = kwargs['compute_environment']
    analysis(analysis_project_folder, compute_environment)


def analysis(analysis_project_folder, compute_environment):
    analysis_config_file = os.path.join(analysis_project_folder, 'input.yml')
    if not os.path.isfile(analysis_config_file):
        print(f"input.yml file does not exist at path {analysis_config_file}")
        exit(1)
    if not os.path.isdir(analysis_project_folder):
        print(f"Folder does not exist at path {analysis_config_file}")
        exit(1)
    analysis_config, analysis_input_folder, analyses_folder = BTAPAnalysis.load_analysis_input_file(
        analysis_config_file=analysis_config_file)
    analysis_config[':compute_environment'] = compute_environment
    # Run reference
    ref_analysis_config = copy.deepcopy(analysis_config)
    ref_analysis_config[':algorithm_type'] = 'reference'
    ref_analysis_config[':analysis_name'] = 'reference_runs'
    br = BTAPReference(analysis_config=ref_analysis_config,
                       analysis_input_folder=analysis_input_folder,
                       analyses_folder=analyses_folder)
    br.run()
    bb = get_analysis(analysis_config=analysis_config,
                      analysis_input_folder=analysis_input_folder,
                      analyses_folder=analyses_folder,
                      reference_run_data_path=br.analysis_excel_results_path())
    bb.run()
    print(f"Excel results file {bb.analysis_excel_results_path()}")


if __name__ == '__main__':
    btap()




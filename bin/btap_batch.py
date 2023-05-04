from pathlib import Path
import click
import os
import sys
#from icecream import ic


# Avoid having to add PYTHONPATH to env.
PROJECT_ROOT = str(Path(os.path.dirname(os.path.realpath(__file__))).parent.absolute())
sys.path.append(PROJECT_ROOT)

PROJECT_FOLDER = os.path.join(Path(os.path.dirname(os.path.realpath(__file__))).parent.absolute())
EXAMPLE_FOLDER = os.path.join(PROJECT_FOLDER, 'examples')
OUTPUT_FOLDER = os.path.join(PROJECT_FOLDER, "output")
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


def check_environment_vars_are_defined(compute_environment=None):
    failed = False
    if os.environ.get('AWS_USERNAME') is None and (
            compute_environment == 'aws_batch' or compute_environment == 'aws_batch_analysis'):
        print(
            'Please set AWS_USERNAME environment variable to your aws username. See https://github.com/canmet-energy/btap_batch/blob/main/README.md#requirements to ensure all requirements are met before running. ')
        failed = True
    if os.environ.get('GIT_API_TOKEN') is None:
        print(
            'Please set GIT_API_TOKEN environment variable to your aws username. See https://github.com/canmet-energy/btap_batch/blob/main/README.md#requirements')
        failed = True
    if failed:
        exit(1)


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(version='1.0.0')
def btap():
    pass


@btap.command()
def credits():
    from colorama import Fore, Style
    import pyfiglet
    import random
    print(Fore.GREEN + "CanmetENERGY Building Technology Assessment Platform Team (BTAP)" + Style.RESET_ALL)
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
@click.option('--compute_environment', default='local_docker',
              help='local_docker for local computer, aws_batch to configure aws, or all. Default=local_docker.')
@click.option('--btap_batch_branch', default='dev', help='btap_batch branch. Default = dev.')
@click.option('--os_standards_branch', default='nrcan', help='openstudio-standards branch. Default=nrcan.')
@click.option('--btap_costing_branch', default='master', help='btap_costing branch.Default=master.')
@click.option('--openstudio_version', default='3.5.1', help='OpenStudio version. Default=3.5.1')
@click.option('--disable_costing', is_flag=True,
              help='Disable costing. Choose this if you do not have an RSMeans licence and access to the BTAPCosting repo.')
@click.option('--aws_max_vcpus', default=500, help='Expert Only: Sets maximum number of vcpus to use. Default is 500')
@click.option('--aws_instance_types', multiple=True, default=['optimal'],
              help='Expert Only: Set the EC2 instances type to use. Default to "optimal" to allow AWS ML to decide. To add more than one instance type use multiple switches')
@click.option('--aws_worker_vcpus', default=1, help='Expert Only: Number of CPUs to run simulation. Default is 1')
@click.option('--aws_worker_mem', default=2000,
              help='Expert Only: Amount of ram to run a simulation in MB. Default is 2000')
@click.option('--aws_manager_vcpus', default=16,
              help='Expert Only: Sets maximum number of vcpus to use to manage analysis. Default is 16')
@click.option('--aws_manager_mem', default=32000,
              help='Expert Only: Amount of ram to run to manage analysis in MB. Default is 32000')
def build_environment(**kwargs):
    from src.btap.cli_helper_methods import build_and_configure_docker_and_aws
    """
    This command will build the supporting permissions, databases, on aws and local docker. This optionally will allow
    you to choose experimental development branches to use.
    For 'local_docker' as compute_environment, it will simply build the btap_cli image on your local computer. This
    image is responsible for running openstudio/Energyplus.

    For 'aws_batch' this will configure the correct IAM roles required to run BTAP on AWS. This includes
    CloudBuildRole, BatchJobRole, and BatchServiceRole. These roles will appear with a suffix of your AWS_USERNAME that
    you have provided in your system variables.

    It will also create an aws compute resource, an aws job description, a btap job queue and an analysis job queue..
    These are also suffixed with your provided AWS_USERNAME.

    Similarly to local_docker, it will create btap_cli image, but on the Amazon Container Registery. It will also build
    the btap_batch image to run the analysis completely remotely.

    It will also create a dynamodb table to store results and status of running submitted analysis jobs and btap_cli
    jobs.

    The reason for all components of aws to have your username as a suffix ensures that your setting will not effect
    others on a federated account, which is the type of account the government of canada uses.

    Subsequent executions of this command will tear down and rebuild the configuration based on the latest branches
    that you have selected or chosen to default.

    The branch switches are for developer use only. Use at your peril.

    Examples:
        # without costing
        python ./bin/btap_batch.py build-environment --compute_environment local_docker --disable_costing

        python ./bin/btap_batch.py build-environment --compute_environment aws_batch 
        
        # most powerful (and expensive!) aws configuration with costing implicitly enabled.
        
        python ./bin/btap_batch.py build-environment --compute_environment aws_batch  --aws_instance_types c6g.16xlarge --aws_max_vcpus 1000 
        

    """
    compute_environment = kwargs['compute_environment']
    btap_batch_branch = kwargs['btap_batch_branch']
    os_standards_branch = kwargs['os_standards_branch']
    btap_costing_branch = kwargs['btap_costing_branch']
    openstudio_version = kwargs['openstudio_version']
    disable_costing = kwargs['disable_costing']

    ce_maxvCpus = kwargs['aws_max_vcpus']
    ce_instanceTypes = list(kwargs['aws_instance_types'])  # convert tuple to list.
    worker_container_cpu = kwargs['aws_worker_vcpus']
    worker_container_mem = kwargs['aws_worker_mem']
    manager_container_cpu = kwargs['aws_manager_vcpus']
    manage_container_mem = kwargs['aws_manager_mem']


    if disable_costing:
        # Setting the costing branch to an empty string will force the docker file to not use costing.
        btap_costing_branch = ''

    check_environment_vars_are_defined(compute_environment=compute_environment)
    build_and_configure_docker_and_aws(btap_batch_branch=btap_batch_branch,
                                       btap_costing_branch=btap_costing_branch,
                                       compute_environment=compute_environment,
                                       openstudio_version=openstudio_version,
                                       os_standards_branch=os_standards_branch,
                                       ce_maxvCpus=ce_maxvCpus,
                                       ce_instanceTypes=ce_instanceTypes,
                                       worker_container_cpu=worker_container_cpu,
                                       worker_container_mem=worker_container_mem,
                                       manager_container_cpu=manager_container_cpu,
                                       manage_container_mem=manage_container_mem
                                       )
    print(
        "Build Complete. Please wait at least 5 minutes before running on AWS. This is to give time the amazon changes to propogate on their servers. Local docker runs can start immediately.")


@btap.command()
@click.option('--compute_environment', default='local_docker',
              help='Environment to run analysis. Either local_docker, which runs on your computer, or aws_batch_analysis which runs completely on AWS. The default is local_docker')
@click.option('--project_folder', default=os.path.join(EXAMPLE_FOLDER, 'optimization'),
              help='location of folder containing input.yml file and optionally support folders such as osm_files folder for custom models. Default is the optimization example folder.')
@click.option('--reference_run', is_flag=True,
              help='Run reference. Required for baseline comparisons')
@click.option('--output_folder', default=OUTPUT_FOLDER,
              help='Path to output results. Defaulted to this projects output folder ./btap_batch/output')
def run_analysis_project(**kwargs):
    from src.btap.cli_helper_methods import analysis
    """
    This command will invoke an analysis, a set of simulations based on the input.yml contained in your project_folder.
    Please see the 'examples' folder for examples of how to run different types of analyses. Note: The build_environment
    command must have been invoked at least once.

    Examples.

        python ./bin/btap_batch.py run-analysis-project --compute_environment local_docker  --project_folder examples\optimization --reference_run

        python ./bin/btap_batch.py run-analysis-project --compute_environment aws_batch_analysis --project_folder examples\parametric --reference_run
    """

    # Input folder name
    analysis_project_folder = kwargs['project_folder']
    compute_environment = kwargs['compute_environment']
    reference_run = kwargs['reference_run']
    output_folder = kwargs['output_folder']
    # Function to run analysis.
    check_environment_vars_are_defined(compute_environment=compute_environment)
    analysis(analysis_project_folder, compute_environment, reference_run, output_folder)


@btap.command()
def aws_db_reset(**kwargs):
    from src.btap.aws_dynamodb import AWSResultsTable
    """
    This command will clear all data contained in the AWS DynamoDB database.

    Example:

       python ./bin/btap_batch.py aws_db_reset

    """
    AWSResultsTable().delete_table()
    AWSResultsTable().create_table()


@btap.command()
@click.option('--type', default="csv", help='format type to dump entire results information. Choices are pickle or csv')
@click.option('--folder_path', default=OUTPUT_FOLDER,
              help='folder path to save database file dump. Defaults to projects output folder. ')
@click.option('--analysis_name', default=None, help='Filter by analysis name given. Default shows all.')
def aws_db_dump(**kwargs):
    from src.btap.aws_dynamodb import AWSResultsTable
    """
    This command will dump all data contained in the AWS (DynamoDB) database to a local file.

        Example:

        python ./bin/btap_batch.py aws_db_dump --folder_path C:/output_folder/
    """
    type = kwargs['type']
    folder_path = kwargs['folder_path']
    analysis_name = kwargs['analysis_name']
    check_environment_vars_are_defined(compute_environment='aws_batch')

    AWSResultsTable().dump_table(folder_path=folder_path, type=type, analysis_name=analysis_name)


@btap.command()
def aws_db_analyses_status(**kwargs):
    import pandas
    from src.btap.aws_dynamodb import AWSResultsTable
    """
    This command will show the state of each analysis that has been, and that is currently running.

        Example:

        python ./bin/btap_batch.py aws_db_analyses_status
    """
    pandas.set_option('display.max_colwidth', None)
    pandas.set_option('display.max_columns', None)
    check_environment_vars_are_defined(compute_environment='aws_batch')
    print(AWSResultsTable().aws_db_analyses_status())


@btap.command()
@click.option('--analysis_name', default=None, help='Filter by analysis name given. Default shows all.')
def aws_db_failures(**kwargs):
    from src.btap.aws_dynamodb import AWSResultsTable
    import pandas
    """
    This will print a dataframe of all the failed runs, if any. You may filter this by the --analysis_name switch. It will provide
    The analysis name, datapoint_id,container_error if available, and the url to the failed run on s3.

    Example:
        python ./bin/btap_batch.py aws_db_failures
    """
    pandas.set_option('display.max_colwidth', None)
    pandas.set_option('display.max_columns', None)
    check_environment_vars_are_defined(compute_environment='aws_batch')
    print(AWSResultsTable().aws_db_failures(analysis_name=kwargs['analysis_name']))


#
# @btap.command()
# @click.option('--analysis_name', default=None, help='Filter by analysis name given. Default shows all.')
# @click.option('--x_data', default='energy_eui_total_gj_per_m_sq', help='X-data for chart. Default is energy_eui_total_gj_per_m_sq ')
# @click.option('--y_data', default='cost_equipment_total_cost_per_m_sq', help='Y-data for chart. Default is cost_equipment_total_cost_per_m_sq')
# @click.option('--color', default=':scenario', help='color of points. Default is :scenario')
# @click.option('--size', default=None, help='Filter by analysis name given. Default is none')
# def aws_db_chart(**kwargs):
#     """
#     This command will generate a plotly scatter chart based on the initial data collected during an analysis run on aws. This can be used
#     to monitor the progress of an analysis while it is still being completed.
#
#     Example:
#
#     python ./bin/btap_batch.py aws-db-chart --analysis_name optimization_example --x energy_eui_total_gj_per_m_sq --y cost_equipment_total_cost_per_m_sq
#
#     """
#     x = kwargs['x_data']
#     y = kwargs['y_data']
#     color = kwargs['color']
#     size = kwargs['size']
#     analysis_name = kwargs['analysis_name']
#     pandas.set_option('display.max_colwidth', None)
#     pandas.set_option('display.max_columns', None)
#     check_environment_vars_are_defined(compute_environment='aws_batch')
#     AWSResultsTable().aws_db_analyses_chart_scatter(x=x,
#                                                     y=y,
#                                                     color=color,
#                                                     size=size,
#                                                     analysis_name=analysis_name)
#

@btap.command(help="This will run all the analysis projects in the examples file. Locally or on AWS.")
@click.option('--compute_environment', default='local_docker',
              help='Environment to run analysis either local_docker, or aws_batch_analysis')
def parallel_test_examples(**kwargs):
    import time
    from src.btap.cli_helper_methods import analysis
    """
    This command will self test btap_batch by performing example analyses locally or on aws. This test is simply to see if it will run.

    Example:

    # To run test locally....
    python ./bin/btap_batch.py parallel_test_examples --compute_environment local_docker

    # To run test on aws.
    python ./bin/btap_batch.py parallel_test_examples --compute_environment aws_batch_analysis

    """
    check_environment_vars_are_defined(compute_environment=kwargs['compute_environment'])
    start = time.time()
    examples_folder = os.path.join(PROJECT_FOLDER, 'examples')
    example_folders = [
        'custom_osm',
        'elimination',
        'optimization',
        'parametric',
        'sample-lhs',
        'sensitivity',
        'reference_only'
    ]

    for folder in example_folders:
        project_input_folder = os.path.join(examples_folder, folder)
        print(project_input_folder)
        analysis(project_input_folder=project_input_folder, compute_environment=kwargs['compute_environment'],
                 reference_run=True, output_folder=OUTPUT_FOLDER)
    end = time.time()
    print(f"Time elapsed: {end - start}")


if __name__ == '__main__':
    btap()

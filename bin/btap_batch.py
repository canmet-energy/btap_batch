from pathlib import Path
import click
import os
import sys

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
@click.option('--compute_environment', '-c', default='local_docker',
              help='local_docker for local computer, aws_batch to configure aws, or all. Default=local_docker.')
@click.option('--btap_batch_branch', default='dev', help='btap_batch branch. Default = dev.')
@click.option('--os_standards_branch', default='nrcan', help='openstudio-standards branch. Default=nrcan.')
@click.option('--btap_costing_branch', default='master', help='btap_costing branch.Default=master.')
@click.option('--openstudio_version', default='3.5.1', help='OpenStudio version. Default=3.5.1')
@click.option('--disable_costing', is_flag=True,
              help='Disable costing. Choose this if you do not have an RSMeans licence and access to the BTAPCosting repo.')
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

        python ./bin/btap_batch.py build-environment --compute_environment local_docker --disable_costing

        python ./bin/btap_batch.py build-environment --compute_environment aws_batch --disable_costing

    """
    compute_environment = kwargs['compute_environment']
    btap_batch_branch = kwargs['btap_batch_branch']
    os_standards_branch = kwargs['os_standards_branch']
    btap_costing_branch = kwargs['btap_costing_branch']
    openstudio_version = kwargs['openstudio_version']
    disable_costing = kwargs['disable_costing']

    if disable_costing:
        # Setting the costing branch to an empty string will force the docker file to not use costing.
        btap_costing_branch = ''

    check_environment_vars_are_defined(compute_environment=compute_environment)
    build_and_configure_docker_and_aws(btap_batch_branch=btap_batch_branch,
                                       btap_costing_branch=btap_costing_branch,
                                       compute_environment=compute_environment,
                                       openstudio_version=openstudio_version,
                                       os_standards_branch=os_standards_branch)


@btap.command()
@click.option('--compute_environment', '-c', default='local_docker',
              help='Environment to run analysis. Either local_docker, which runs on your computer, or aws_batch_analysis which runs completely on AWS. The default is local_docker')
@click.option('--project_folder', '-p', default=os.path.join(EXAMPLE_FOLDER, 'optimization'),
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


@btap.command(
    help="This will run an NECB 2020 optimization solution set run on a given building type and location for all fueltypes. Will optimize for Total Energy and Net Present Value.")
@click.option('--compute_environment', '-c', default='local_docker',
              help='Environment to run analysis either local_docker, aws_batch or aws_batch_analysis')
@click.option('--building_types', '-b', default=['SmallOffice'], multiple=True,
              help='NECB prototype building to use. Must be only Offices, Apartment/Condos and Schools types')
@click.option('--epw_files', '-e',
              default=[
                  'CAN_BC_Vancouver.Intl.AP.718920_CWEC2016.epw'],
              multiple=True,
              help='Environment to run analysis either local_docker, aws_batch or aws_batch_analysis')
@click.option('--hvac_fuel_types_list', '-h',
              multiple=True,
              help='This is the FuelSet combination to use. ',
              default=['NECB_Default-NaturalGas']
              )
@click.option('--population', '-p', default=35, help='Population to use in NSGAII optimization')
@click.option('--generations', '-g', default=2, help='Generations to use in NSGAII optimization')
@click.option('--working_folder', '-w', default=os.path.join(PROJECT_FOLDER, 'solution_sets'), help='location to output results')
def optimized_solution_sets(**kwargs):
    from src.btap.solution_sets import generate_solution_sets
    import time
    import shutil
    """
    This will run an NECB 2020 optimization solution set run on a given building type and location. This will examine 
    all possible fueltypes and use the correct reference fuel accordingly. The optimization will be based on the total EUI
    and the Net Present value."

    Example:

    # To run locally.... This will create a solutions set folder with all the project yaml files, with the  the simulation and results with the given building type, locations, and FuelType 
    python ./bin/btap_batch.py optimized-solution-sets -c local_docker -b SmallOffice -e CAN_QC_Montreal-Trudeau.Intl.AP.716270_CWEC2016.epw -h NECB_Default-NaturalGas -h NECB_Default-Electricity

    # To run test on aws. This will run 
    python ./bin/btap_batch.py optimized-solution-sets -c aws_batch_analysis 

    """
    check_environment_vars_are_defined(compute_environment=kwargs['compute_environment'])
    start = time.time()
    # Check if analyses folder exists
    if os.path.isdir(kwargs['working_folder']):
        # Remove old folder
        try:
            shutil.rmtree(kwargs['working_folder'])
        except PermissionError:
            message = f'Could not delete {kwargs["working_folder"]}. Do you have a file open in that folder? Exiting'
            print(message)
            exit(1)

    supported_fuel_types = ['NECB_Default-NaturalGas',
                            'NECB_Default-Electricity',
                            'HS09_CCASHP_Baseboard-NaturalGasHPGasBackup',
                            'HS09_CCASHP_Baseboard-ElectricityHPElecBackup',
                            'HS08_CCASHP_VRF-NaturalGasHPGasBackup',
                            'HS08_CCASHP_VRF-ElectricityHPElecBackup',
                            'HS11_ASHP_PTHP-NaturalGasHPGasBackup',
                            'HS11_ASHP_PTHP-ElectricityHPElecBackup',
                            'HS13_ASHP_VRF-NaturalGasHPGasBackup',
                            'HS13_ASHP_VRF-ElectricityHPElecBackup']

    supported_building_types = [
        'MediumOffice',
        'LargeOffice',
        'SmallOffice',
        'PrimarySchool',
        'SecondarySchool',
        'LowriseApartment',
        'MidriseApartment',
        'HighriseApartment'
    ]

    if not (set(kwargs['hvac_fuel_types_list']).issubset(set(supported_fuel_types))):
        print("Invalid fueltype system mix. Please use only the following:")
        print(supported_fuel_types)
        exit(1)

    if not (set(kwargs['building_types']).issubset(set(supported_building_types))):
        print("Invalid building types detected. Please use only the following:")
        print(supported_fuel_types)
        exit(1)

    generate_solution_sets(
        compute_environment=kwargs['compute_environment'],  # local_docker, aws_batch, aws_batch_analysis...
        building_types_list=kwargs['building_types'],  # a list of the building_types to look at.
        epw_files=kwargs['epw_files'],  # a list of the epw files.
        hvac_fuel_types_list=[x.split('-') for x in kwargs['hvac_fuel_types_list']],
        working_folder=os.path.join(kwargs['working_folder']),
        pop=kwargs['population'],
        generations=kwargs['generations'],
        run_analyses=True
    )


@btap.command(
    help="This will perform the post-processing on the results to use in Tableau or other analyses.")
@click.option('--solution_sets_projects_results_folder', '-r', default=os.path.join(PROJECT_FOLDER, 'solution_sets','projects_results'),
              help='Folder containing btap project results. Not required for AWS runs.')
@click.option('--aws_database', '-a', is_flag=True, help='Gather all results from AWS database.')
def post_process_solution_sets(**kwargs):
    """
    This command will self test btap_batch by performing example analyses locally or on aws. This test is simply to see if it will run.

    Example:

    # To postprocess a local simulation....
    python ./bin/btap_batch.py post-process-solution-sets

    # To postprocess an aws simulation. Warning. This will pull all simulation that are present in your Dynamo
    python ./bin/btap_batch.py post-process-solution-sets -a

    """
    from src.btap.solution_sets import post_process_analyses



    post_process_analyses(solution_sets_raw_results_folder=kwargs["solution_sets_projects_results_folder"],
                          # Only required if runs were done with local_docker. Must contain nsga results.
                          aws_database=kwargs["aws_database"],  # use aws database will download all results nsga or not,
                          )


if __name__ == '__main__':
    btap()

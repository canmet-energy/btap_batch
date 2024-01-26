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
SCHEMA_FOLDER = os.path.join(PROJECT_FOLDER, "schemas")
CONFIG_FOLDER = os.path.join(PROJECT_FOLDER, 'config')
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


def check_environment_vars_are_defined(compute_environment=None):
    print("not checking env vars!")


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
@click.option('--build_config_path', '-p', default=os.path.join(CONFIG_FOLDER, 'build_config.yml'),
              help=f'location of Location of build_config.yml file.  Default location is {CONFIG_FOLDER}')

def build_environment(**kwargs):
    from src.btap.cli_helper_methods import build_and_configure_docker_and_aws
    from src.btap.cli_helper_methods import generate_build_config
    import jsonschema
    import yaml
    """


    It will also create an aws compute resource, an aws job description, a btap job queue and an analysis job queue..

    Similarly to local, it will create btap_cli image, but on the Amazon Container Registery. It will also build
    the btap_batch image to run the analysis completely remotely.

    It will also create a dynamodb table to store results and status of running submitted analysis jobs and btap_cli
    jobs.

    The reason for all components of aws to have your username as a suffix ensures that your setting will not effect
    others on a federated account, which is the type of account the government of canada uses.

    Subsequent executions of this command will tear down and rebuild the configuration based on the latest branches
    that you have selected or chosen to default.

    The branch switches are for developer use only. Use at your peril.

    Examples:

        python ./bin/btap_batch.py build-environment

        python ./bin/btap_batch.py build-environment 

    """

    build_config_path = kwargs['build_config_path']
    config = load_config(build_config_path)

    btap_batch_branch = config['btap_batch_branch']
    os_standards_branch = config['os_standards_branch']
    btap_costing_branch = config['btap_costing_branch']
    openstudio_version = config['openstudio_version']
    disable_costing = config['disable_costing']
    weather_list = config['weather_list']
    build_btap_cli = config['build_btap_cli']
    build_btap_batch = config['build_btap_batch']
    os.environ['BUILD_ENV_NAME'] = config['build_env_name']
    os.environ['GIT_API_TOKEN'] = config['git_api_token']
    compute_environment = config['compute_environment']


    if disable_costing:
        # Setting the costing branch to an empty string will force the docker file to not use costing.
        btap_costing_branch = ''

    check_environment_vars_are_defined(compute_environment=compute_environment)
    build_and_configure_docker_and_aws(btap_batch_branch=btap_batch_branch,
                                       btap_costing_branch=btap_costing_branch,
                                       compute_environment=compute_environment,
                                       openstudio_version=openstudio_version,
                                       weather_list=weather_list,
                                       os_standards_branch=os_standards_branch,
                                       build_btap_batch=build_btap_batch,
                                       build_btap_cli=build_btap_cli)


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


@btap.command()
@click.option('--project_folder', '-p', default=os.path.join(EXAMPLE_FOLDER, 'optimization'),
              help='location of folder containing input.yml file and optionally support folders such as osm_folder folder for custom models. Default is the optimization example folder.')
@click.option('--output_folder', default=OUTPUT_FOLDER,
              help='Path to output results. Defaulted to this projects output folder ./btap_batch/output')
@click.option('--build_config_path', '-c', default=os.path.join(CONFIG_FOLDER, 'build_config.yml'),
              help=f'location of Location of build_config.yml file.  Default location is {CONFIG_FOLDER}')
@click.option('--compute_environment', default=None,
              help=f'location of Location of build_config.yml file.  Default location is {CONFIG_FOLDER}')
def run_analysis_project(**kwargs):
    from src.btap.cli_helper_methods import analysis
    from cloudpathlib import CloudPath
    import yaml
    """
    This command will invoke an analysis, a set of simulations based on the input.yml contained in your project_folder.
    Please see the 'examples' folder for examples of how to run different types of analyses. Note: The build_environment
    command must have been invoked at least once.

    Examples.

        python ./bin/btap_batch.py run-analysis-project --compute_environment local  --project_folder examples\optimization

        python ./bin/btap_batch.py run-analysis-project --compute_environment aws --project_folder examples\parametric
    """

    build_config_path = kwargs['build_config_path']

    if kwargs['compute_environment'] != None:
        compute_environment = kwargs['compute_environment']

    # Input folder name
    analysis_project_folder = kwargs['project_folder']

    build_config = None


    if  os.path.exists(build_config_path):
        build_config = load_config(build_config_path)
        print(f"Using build_env_name from build_config.yml: {build_config['build_env_name']}")
    else:
        print(f"No build_config.yml found in {build_config_path}, trying to continue.")

    output_folder = kwargs['output_folder']





    analysis(project_input_folder= analysis_project_folder,
             build_config=build_config,
             output_folder=output_folder)


@btap.command()
def aws_db_reset(**kwargs):
    from src.btap.aws_dynamodb import AWSResultsTable
    """
    This command will clear all data contained in the AWS DynamoDB database.

    Example:

       python ./bin/btap_batch.py aws-db-reset

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
    check_environment_vars_are_defined(compute_environment='local_managed_aws_workers')
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
    check_environment_vars_are_defined(compute_environment='local_managed_aws_workers')
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
    check_environment_vars_are_defined(compute_environment='local_managed_aws_workers')
    print(AWSResultsTable().aws_db_failures(analysis_name=kwargs['analysis_name']))


@btap.command(help="This will run all the analysis projects in the examples file. Locally or on AWS.")
@click.option('--compute_environment', default='local',
              help='Environment to run analysis either local, or aws')
def parallel_test_examples(**kwargs):
    import time
    from src.btap.cli_helper_methods import analysis
    """
    This command will self test btap_batch by performing example analyses locally or on aws. This test is simply to see if it will run.

    Example:

    # To run test locally....
    python ./bin/btap_batch.py parallel_test_examples --compute_environment local

    # To run test on aws.
    python ./bin/btap_batch.py parallel_test_examples --compute_environment aws

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


@btap.command(help="This will run all the analysis projects in a given folder path. Locally or on AWS.")
@click.option('--compute_environment','-c', default='local',
              help='Environment to run analysis either local, or aws')
@click.option('--analyses_folder_path', default=os.path.join(PROJECT_FOLDER, 'examples'),
              help='folder containing multiple project analysis folders to run.')
@click.option('--output_folder', default=OUTPUT_FOLDER,
              help='Path to output results. Defaulted to this projects output folder ./btap_batch/output')
def batch_analyses(**kwargs):
    import time
    from src.btap.cli_helper_methods import analysis
    """
    This command will self test btap_batch by performing example analyses locally or on aws. This test is simply to see if it will run.

    Example:

    # To run test locally....
    python ./bin/btap_batch.py batch-analyses --compute_environment local --analyses_folder_path

    # To run test on aws.
    python ./bin/btap_batch.py batch-analyses --compute_environment aws --analyses_folder_path

    """
    check_environment_vars_are_defined(compute_environment=kwargs['compute_environment'])
    start = time.time()
    analyses_folder_path = kwargs['analyses_folder_path']
    folders = [os.path.abspath(os.path.join(analyses_folder_path,name)) for name in os.listdir(analyses_folder_path) if os.path.isdir(os.path.join(analyses_folder_path,name))]

    for project_input_folder in folders:
        print(project_input_folder)
        analysis(project_input_folder=project_input_folder, compute_environment=kwargs['compute_environment'],
                 reference_run=True, output_folder=kwargs['output_folder'])
    end = time.time()
    print(f"Time elapsed: {end - start}")


@btap.command(
    help="This will run an NECB 2020 optimization solution set run on a given building type and location for all fueltypes. Will optimize for Total Energy and Net Present Value.")
@click.option('--compute_environment', '-c', default='local',
              help='Environment to run analysis either local, local_managed_aws_workers or aws')
@click.option('--building_types', '-b', default=['SmallOffice'], multiple=True,
              help='NECB prototype building to use. Must be only Offices, Apartment/Condos and Schools types')
@click.option('--epw_files', '-e',
              default=[
                  'CAN_BC_Vancouver.Intl.AP.718920_CWEC2016.epw'],
              multiple=True,
              help='Environment to run analysis either local, local_managed_aws_workers or aws')
@click.option('--hvac_fuel_types_list', '-f',
              multiple=True,
              help='This is the FuelSet combination to use. ',
              default=['NECB_Default-NaturalGas']
              )
@click.option('--population', '-p', default=35, help='Population to use in NSGAII optimization')
@click.option('--generations', '-g', default=2, help='Generations to use in NSGAII optimization')
@click.option('--working_folder', '-w', default=os.path.join(PROJECT_FOLDER, 'solution_sets'), help='location to output results')
def optimized_solution_sets(**kwargs):
    from src.btap.solution_sets import generate_solution_sets
    """
    This will run an NECB 2020 optimization solution set run on a given building type and location. This will examine 
    all possible fueltypes and use the correct reference fuel accordingly. The optimization will be based on the total EUI
    and the Net Present value."

    Example:

    # To run locally.... This will create a solutions set folder with all the project yaml files, with the  the simulation and results with the given building type, locations, and FuelType 
    python ./bin/btap_batch.py optimized-solution-sets -c local -b SmallOffice -e CAN_QC_Montreal-Trudeau.Intl.AP.716270_CWEC2016.epw -f NECB_Default-NaturalGas -f NECB_Default-Electricity

    # To run test on aws. This will run 
    python ./bin/btap_batch.py optimized-solution-sets -c aws 

    """
    check_environment_vars_are_defined(compute_environment=kwargs['compute_environment'])
    working_folder = kwargs['working_folder']
    hvac_fuel_types_list = kwargs['hvac_fuel_types_list']
    compute_environment = kwargs['compute_environment']
    building_types = kwargs['building_types']
    epw_files = kwargs['epw_files']
    nsga_population = kwargs['population']
    nsga_generations = kwargs['generations']


    generate_solution_sets(
        compute_environment=compute_environment,  # local, local_managed_aws_workers, aws...
        building_types_list=building_types,  # a list of the building_types to look at.
        epw_files=epw_files,  # a list of the epw files.
        hvac_fuel_types_list=hvac_fuel_types_list,
        working_folder=os.path.join(working_folder),
        pop=nsga_population,
        generations=nsga_generations,
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
                          # Only required if runs were done with local. Must contain nsga results.
                          aws_database=kwargs["aws_database"],  # use aws database will download all results nsga or not,
                          )

@btap.command(
    help="This will terminate all aws analyses. It will not delete anything fron S3.")
def terminate_aws_analyses(**kwargs):
    from src.btap.cli_helper_methods import terminate_aws_analyses
    terminate_aws_analyses()

@btap.command(help="This will list active analyses")
def list_active_analyses():
    import pandas
    from src.btap.cli_helper_methods import list_active_analyses

    if list_active_analyses() != None:
        df = pandas.json_normalize(list_active_analyses())
        print(df)



@btap.command(
    help="This will generate charts from a sensitivity run output.xlsx file.")
@click.option('--excel_file', '-e',  help='location to output results from a sensitivity analysis.')
@click.option('--pdf_output_file', '-p', default="./", help='location to output pdf charts')
def sensitivity_report(**kwargs):
    from src.btap.btap_sensitivity import BTAPSensitivity
    import pandas as pd
    # Generate PDF
    df = pd.read_excel(kwargs['excel_file'], index_col=0)
    BTAPSensitivity.generate_pdf_report( df=df,
                                         pdf_output=os.path.join(kwargs['pdf_output_file'], 'results.pdf'))




if __name__ == '__main__':
    btap()

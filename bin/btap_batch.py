from pathlib import Path
import click
import os
import sys

# Avoid having to add PYTHONPATH to env.
PROJECT_ROOT = str(Path(os.path.dirname(os.path.realpath(__file__))).parent.absolute())
sys.path.append(PROJECT_ROOT)
from src.btap.cli_helper_methods import build_and_configure_docker_and_aws, load_config
from src.btap.common_paths import PROJECT_FOLDER, EXAMPLE_FOLDER, OUTPUT_FOLDER, CONFIG_FOLDER,HOME
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(version='0.1.0')
def btap():
    pass


@btap.command(help=f"People that worked on this.")
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


@btap.command(help=f"This will build the environment required to run an analysis. If running for the first time. A template configuration will be placed in your home folder here:{CONFIG_FOLDER} ")
@click.option('--build_config_path', '-p', default=os.path.join(CONFIG_FOLDER, 'build_config.yml'),
              help=f'For advanced users. Define location of the build_config.yml file.  Default location is {CONFIG_FOLDER}')

def build(**kwargs):
    """


    It will create an aws compute resource, an aws job description, a btap job queue and an analysis job queue..

    Similarly to local, it will create btap_cli image, but on the Amazon Container Registery. It will also build
    the btap_batch image to run the analysis completely remotely.

    It will also create a dynamodb table to store results and status of running submitted analysis jobs and btap_cli
    jobs.

    The reason for all components of aws to have your username as a suffix ensures that your setting will not effect
    others on a federated account, which is the type of account the government of canada uses.

    Subsequent executions of this command will tear down and rebuild the configuration based on the latest branches
    that you have selected or chosen to default.

    Examples:

        python ./bin/btap_batch.py build-environment

    """

    build_config_path = kwargs['build_config_path']
    config = load_config(build_config_path)

    btap_batch_branch = config['btap_batch_branch']
    enable_rsmeans = config.get('enable_rsmeans', None)
    os_standards_org = config.get('os_standards_org', None)
    os_standards_branch = config['os_standards_branch']
    openstudio_version = config['openstudio_version']
    btap_weather = config['btap_weather']
    weather_list = config['weather_list']
    local_costing_path = config.get('local_costing_path', None)
    build_btap_cli = config['build_btap_cli']
    build_btap_batch = config['build_btap_batch']
    os.environ['BUILD_ENV_NAME'] = config['build_env_name']
    os.environ['GIT_API_TOKEN'] = config['git_api_token']
    compute_environment = config['compute_environment']
    local_nrcan = config['local_nrcan']
    
    build_and_configure_docker_and_aws(btap_batch_branch=btap_batch_branch,
                                       enable_rsmeans=enable_rsmeans,
                                       compute_environment=compute_environment,
                                       openstudio_version=openstudio_version,
                                       btap_weather=btap_weather,
                                       weather_list=weather_list,
                                       os_standards_org=os_standards_org,
                                       os_standards_branch=os_standards_branch,
                                       local_costing_path=local_costing_path,
                                       build_btap_batch=build_btap_batch,
                                       build_btap_cli=build_btap_cli,
                                       local_nrcan=local_nrcan)





@btap.command(help="This will run an analysis project. You must specify a project folder.")
@click.option('--project_folder', '-p', default=os.path.join(EXAMPLE_FOLDER, 'optimization'),
              help='location of folder containing input.yml file and optionally support folders such as osm_folder folder for custom models. Default is the optimization example folder.')
@click.option('--output_folder','-o', default=OUTPUT_FOLDER,
              help='Path to output results. Defaulted to this projects output folder ./btap_batch/output')
@click.option('--build_config_path', '-b', default=os.path.join(CONFIG_FOLDER, 'build_config.yml'),
              help=f'For advanced users. Define location of the build_config.yml file.  Default location is {CONFIG_FOLDER}')
@click.option('--compute_environment', '-c', default=None,
              help=f'For advanced users. Override the computer environment in the build_config.yml.')
def run(**kwargs):
    from src.btap.cli_helper_methods import analysis, load_config
    """
    This command will invoke an analysis, a set of simulations based on the input.yml contained in your project_folder.
    Please see the 'examples' folder for examples of how to run different types of analyses. Note: The build_environment
    command must have been invoked at least once.

    Examples.

        python ./bin/btap_batch.py run-analysis-project  --project_folder examples\optimization

        python ./bin/btap_batch.py run-analysis-project  --project_folder examples\parametric
    """

    build_config_path = kwargs['build_config_path']
    analysis_project_folder = kwargs['project_folder']
    output_folder = kwargs['output_folder']

    #load run information from build_config if possible.
    build_config = get_build_config(build_config_path)

    analysis(project_input_folder= analysis_project_folder,
             build_config=build_config,
             output_folder=output_folder)


def get_build_config(build_config_path):
    build_config = None
    if os.path.exists(build_config_path):
        build_config = load_config(build_config_path)
        print(f"Using build_env_name from build_config.yml: {build_config['build_env_name']}")
    else:
        print(f"No build_config.yml found in {build_config_path}, trying to continue.")
    return build_config


# @btap.command()
# def aws_db_analyses_status(**kwargs):
#     import pandas
#     from src.btap.aws_dynamodb import AWSResultsTable
#     """
#     This command will show the state of each analysis that has been, and that is currently running.
#         Example:
#         python ./bin/btap_batch.py aws_db_analyses_status
#     """
#     pandas.set_option('display.max_colwidth', None)
#     pandas.set_option('display.max_columns', None)
#     print(AWSResultsTable().aws_db_analyses_status())


# @btap.command()
# @click.option('--analysis_name', default=None, help='Filter by analysis name given. Default shows all.')
# def aws_db_failures(**kwargs):
#     from src.btap.aws_dynamodb import AWSResultsTable
#     import pandas
#     """
#     This will print a dataframe of all the failed runs, if any. You may filter this by the --analysis_name switch. It will provide
#     The analysis name, datapoint_id,container_error if available, and the url to the failed run on s3.
#
#     Example:
#         python ./bin/btap_batch.py aws_db_failures
#     """
#     pandas.set_option('display.max_colwidth', None)
#     pandas.set_option('display.max_columns', None)
#     print(AWSResultsTable().aws_db_failures(analysis_name=kwargs['analysis_name']))
#

@btap.command(help="This will run all the analysis projects in the examples file. Locally or on AWS.")
@click.option('--build_config_path', '-c', default=os.path.join(CONFIG_FOLDER, 'build_config.yml'),
              help=f'For advanced users.  Define location of the build_config.yml file.  Default location is {CONFIG_FOLDER}')
@click.option('--output_folder', default=OUTPUT_FOLDER,
              help='Path to output results. Defaulted to this projects output folder ./btap_batch/output')
def run_examples(**kwargs):
    import time
    from src.btap.cli_helper_methods import analysis
    """
    This command will self test btap_batch by performing example analyses locally or on aws. This test is simply to see if it will run.

    Example:

    # To run test locally....
    python ./bin/btap_batch.py run_examples

    # To run test on aws.
    python ./bin/btap_batch.py run_examples

    """
    start = time.time()
    examples_folder = os.path.join(PROJECT_FOLDER, 'examples')
    example_folders = [
        'custom_osm',
        'elimination',
        'optimization',
        'parametric',
        'sample-lhs',
        'sensitivity'
    ]

    for folder in example_folders:
        analysis_project_folder = os.path.join(examples_folder, folder)
        print(analysis_project_folder)
        analysis(project_input_folder=analysis_project_folder,
                 build_config=get_build_config(kwargs["build_config_path"]),
                 output_folder=kwargs["output_folder"])
    end = time.time()
    print(f"Time elapsed: {end - start}")


#@btap.command(help="This will run all the analysis projects in a given folder path. Locally or on AWS.")
#@click.option('--compute_environment','-c', default='local',
#              help='Environment to run analysis either local, or aws')
#@click.option('--analyses_folder_path', default=os.path.join(PROJECT_FOLDER, 'examples'),
#              help='folder containing multiple project analysis folders to run.')
#@click.option('--output_folder', default=OUTPUT_FOLDER,
#              help='Path to output results. Defaulted to this projects output folder ./btap_batch/output')
#def batch(**kwargs):
#    import time
#    from src.btap.cli_helper_methods import analysis
#    """
#    This command will self test btap_batch by performing example analyses locally or on aws. This test is simply to see if it will run.
#
#    Example:
#
#    # To run test locally....
#    python ./bin/btap_batch.py batch-analyses --compute_environment local --analyses_folder_path
#
#    # To run test on aws.
#    python ./bin/btap_batch.py batch-analyses --compute_environment aws --analyses_folder_path
#
#    """
#    start = time.time()
#    analyses_folder_path = kwargs['analyses_folder_path']
#    folders = [os.path.abspath(os.path.join(analyses_folder_path,name)) for name in os.listdir(analyses_folder_path) if os.path.isdir(os.path.join(analyses_folder_path,name))]

#    for project_input_folder in folders:
#        print(project_input_folder)
#        analysis(project_input_folder=project_input_folder, compute_environment=kwargs['compute_environment'],
#                 reference_run=True, output_folder=kwargs['output_folder'])
#    end = time.time()
#    print(f"Time elapsed: {end - start}")


# @btap.command(
#     help="This will run an NECB 2020 optimization solution set run on a given building type and location for all fueltypes. Will optimize for Total Energy and Net Present Value.")
# @click.option('--compute_environment', '-c', default='local',
#               help='Environment to run analysis either local, local_managed_aws_workers or aws')
# @click.option('--building_types', '-b', default=['SmallOffice'], multiple=True,
#               help='NECB prototype building to use. Must be only Offices, Apartment/Condos and Schools types')
# @click.option('--epw_files', '-e',
#               default=[
#                   'CAN_BC_Vancouver.Intl.AP.718920_CWEC2016.epw'],
#               multiple=True,
#               help='Environment to run analysis either local, local_managed_aws_workers or aws')
# @click.option('--hvac_fuel_types_list', '-f',
#               multiple=True,
#               help='This is the FuelSet combination to use. ',
#               default=['NECB_Default-NaturalGas']
#               )
# @click.option('--population', '-p', default=35, help='Population to use in NSGAII optimization')
# @click.option('--generations', '-g', default=2, help='Generations to use in NSGAII optimization')
# @click.option('--working_folder', '-w', default=os.path.join(PROJECT_FOLDER, 'solution_sets'), help='location to output results')
# def optimized_solution_sets(**kwargs):
#     from src.btap.solution_sets import generate_solution_sets
#     """
#     This will run an NECB 2020 optimization solution set run on a given building type and location. This will examine
#     all possible fueltypes and use the correct reference fuel accordingly. The optimization will be based on the total EUI
#     and the Net Present value."
#
#     Example:
#
#     # To run locally.... This will create a solutions set folder with all the project yaml files, with the  the simulation and results with the given building type, locations, and FuelType
#     python ./bin/btap_batch.py optimized-solution-sets -c local -b SmallOffice -e CAN_QC_Montreal-Trudeau.Intl.AP.716270_CWEC2016.epw -f NECB_Default-NaturalGas -f NECB_Default-Electricity
#
#     # To run test on aws. This will run
#     python ./bin/btap_batch.py optimized-solution-sets -c aws
#
#     """
#     working_folder = kwargs['working_folder']
#     hvac_fuel_types_list = kwargs['hvac_fuel_types_list']
#     compute_environment = kwargs['compute_environment']
#     building_types = kwargs['building_types']
#     epw_files = kwargs['epw_files']
#     nsga_population = kwargs['population']
#     nsga_generations = kwargs['generations']
#
#
#     generate_solution_sets(
#         compute_environment=compute_environment,  # local, local_managed_aws_workers, aws...
#         building_types_list=building_types,  # a list of the building_types to look at.
#         epw_files=epw_files,  # a list of the epw files.
#         hvac_fuel_types_list=hvac_fuel_types_list,
#         working_folder=os.path.join(working_folder),
#         pop=nsga_population,
#         generations=nsga_generations,
#         run_analyses=True
#     )

#
# @btap.command(
#     help="This will perform the post-processing on the results to use in Tableau or other analyses.")
# @click.option('--solution_sets_projects_results_folder', '-r', default=os.path.join(PROJECT_FOLDER, 'solution_sets','projects_results'),
#               help='Folder containing btap project results. Not required for AWS runs.')
# @click.option('--aws_database', '-a', is_flag=True, help='Gather all results from AWS database.')
# def post_process_solution_sets(**kwargs):
#     """
#     This command will self test btap_batch by performing example analyses locally or on aws. This test is simply to see if it will run.
#
#     Example:
#
#     # To postprocess a local simulation....
#     python ./bin/btap_batch.py post-process-solution-sets
#
#     # To postprocess an aws simulation. Warning. This will pull all simulation that are present in your Dynamo
#     python ./bin/btap_batch.py post-process-solution-sets -a
#
#     """
#     from src.btap.solution_sets import post_process_analyses
#
#
#
#     post_process_analyses(solution_sets_raw_results_folder=kwargs["solution_sets_projects_results_folder"],
#                           # Only required if runs were done with local. Must contain nsga results.
#                           aws_database=kwargs["aws_database"],  # use aws database will download all results nsga or not,
#                           )

@btap.command(
    help="This will terminate all aws analyses. It will not delete anything fron S3.")
@click.option('--build_config_path', '-c', default=os.path.join(CONFIG_FOLDER, 'build_config.yml'),
              help=f'location of Location of build_config.yml file.  Default location is {CONFIG_FOLDER}')
def aws_kill(**kwargs):
    from src.btap.cli_helper_methods import load_config
    from src.btap.cli_helper_methods import terminate_aws_analyses

    config = load_config(build_config_path=kwargs["build_config_path"])
    os.environ['BUILD_ENV_NAME'] = config['build_env_name']

    terminate_aws_analyses()

@btap.command(
    help="This delete all resources on aws for the given build_env_name")
@click.option('--build_config_path', '-c', default=os.path.join(CONFIG_FOLDER, 'build_config.yml'),
              help=f'location of Location of build_config.yml file.  Default location is {CONFIG_FOLDER}')
@click.option('--build_env_name', '-n',  help='name of aws build_environment to delete, if not set, it will use the '
                                              'build_env_name in your build_cofig.yml file', default='none')
def aws_rm_build(**kwargs):
    from src.btap.cli_helper_methods import delete_aws_build_env
    if kwargs['build_env_name'] == 'none':
        config = load_config(build_config_path=kwargs["build_config_path"])
        name = config['build_env_name']
    else:
        name = kwargs['build_env_name']
    delete_aws_build_env(build_env_name=name)


@btap.command(
    help="Download results from 1 or more analyses performed on Amazon's S3 bucket.")
@click.option('--s3_bucket',   help='Bucket where build environment exists and analyses were run. ', show_default=True, default='834599497928')
@click.option('--build_env_name',  help='name of aws build_environment simulation was run with.',show_default = True, default='solution_sets')
@click.option('--analysis_name',  help='name of analysis or you can use regex to get any or all analyses performed under a build environment name', show_default=True, default='LowriseApartment.*$')
@click.option('--output_path',  help='Path to save downloaded data to.', show_default = True, default=f'{HOME}/btap_batch/downloads')
@click.option('--download',   help='By default, will not download and just show the folders it finds on S3. This is used to make sure your regex is working as intended before you add this flag to set to true. ', is_flag = True, show_default=True, default=False)
@click.option('--osm',   help='Download OSM files', is_flag = True, show_default=True, default=False)
@click.option('--hourly',   help='Download Hourly data', is_flag = True, show_default=True, default=False)
@click.option('--eplussql',   help='Download EnergyPlus SQLite output data', is_flag = True, show_default=True, default=False)
@click.option('--eplushtm',   help='Download EnergyPlus HTM output data', is_flag = True, show_default=True, default=False)
@click.option('--unzip',   help='Unzip all files', is_flag = True, show_default=True, default=False)


def aws_download(**kwargs):
    from src.btap.cli_helper_methods import download_analyses
    download_analyses(bucket='834599497928',
                      build_env_name=kwargs['build_env_name']+'/',  # S3 prefix MUST have a trailing /
                      analysis_name=kwargs['analysis_name'],
                      output_path= kwargs['output_path'],
                      hourly_csv=kwargs['hourly'],
                      in_osm=kwargs['osm'],
                      eplusout_sql=kwargs['eplussql'],
                      eplustbl_htm=kwargs['eplushtm'],
                      concat_excel_files=True,  # concat all output.xlsx files to a master.csv and parquet file
                      unzip_and_delete=kwargs['unzip'],  # This will unzip the zip files of all the above into a folder and delete the original zip file.
                      dry_run=not kwargs['download']  # If set to true.. will do a dry run and not download anything. This is used to make sure your regex is working as intended.
                      )


if __name__ == '__main__':
    btap()

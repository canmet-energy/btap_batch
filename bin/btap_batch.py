from pathlib import Path
import click
import os
import sys

# Avoid having to add PYTHONPATH to env.
PROJECT_ROOT = str(Path(os.path.dirname(os.path.realpath(__file__))).parent.absolute())
sys.path.append(PROJECT_ROOT)
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
@click.option('--use_proprietary_data', is_flag=True,
              help='Fetch and decrypt proprietary RSMeans and carbon files from AWS CodeCommit before building btap_cli.')

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

    from src.btap.cli_helper_methods import build_and_configure_docker_and_aws, load_config
    build_config_path = kwargs['build_config_path']
    use_proprietary_data = kwargs['use_proprietary_data']
    config = load_config(build_config_path)

    btap_batch_branch = config['btap_batch_branch']
    btap_decryption_key = config.get('btap_decryption_key', '')
    rsmeans_year = config.get('rsmeans_year', None)
    os_standards_org = config.get('os_standards_org', '')
    os_standards_branch = config['os_standards_branch']
    openstudio_version = config['openstudio_version']
    btap_weather = config['btap_weather']
    weather_list = config['weather_list']
    local_costing_path = config.get('local_costing_path', '')
    local_factors_path = config.get('local_factors_path', '')
    local_carbon_opaque_path = config.get('local_carbon_opaque_path', '')
    local_carbon_glazing_path = config.get('local_carbon_glazing_path', '')
    local_carbon_frame_path = config.get('local_carbon_frame_path', '')
    build_btap_cli = config['build_btap_cli']
    build_btap_batch = config['build_btap_batch']
    os.environ['BUILD_ENV_NAME'] = config['build_env_name']
    compute_environment = config['compute_environment']
    
    build_and_configure_docker_and_aws(btap_batch_branch=btap_batch_branch,
                                       btap_decryption_key=btap_decryption_key,
                                       use_proprietary_data=use_proprietary_data,
                                       rsmeans_year=rsmeans_year,
                                       compute_environment=compute_environment,
                                       openstudio_version=openstudio_version,
                                       btap_weather=btap_weather,
                                       weather_list=weather_list,
                                       os_standards_org=os_standards_org,
                                       os_standards_branch=os_standards_branch,
                                       local_costing_path=local_costing_path,
                                       local_factors_path=local_factors_path,
                                       local_carbon_opaque_path=local_carbon_opaque_path,
                                       local_carbon_glazing_path=local_carbon_glazing_path,
                                       local_carbon_frame_path=local_carbon_frame_path,
                                       build_btap_batch=build_btap_batch,
                                       build_btap_cli=build_btap_cli)





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

        python ./bin/btap_batch.py run-analysis-project  --project_folder examples\\optimization

        python ./bin/btap_batch.py run-analysis-project  --project_folder examples\\parametric
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
    from src.btap.cli_helper_methods import load_config
    build_config = None
    if os.path.exists(build_config_path):
        build_config = load_config(build_config_path)
        print(f"Using build_env_name from build_config.yml: {build_config['build_env_name']}")
    else:
        print(f"No build_config.yml found in {build_config_path}, trying to continue.")
    return build_config


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
    from src.btap.cli_helper_methods import delete_aws_build_env, load_config
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

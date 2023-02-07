import click
from colorama import Fore, Style
import time
import os
from pathlib import Path
import pyfiglet
import random
from src.compute_resources.aws_dynamodb import AWSDynamodb
from src.compute_resources.cli_helper_methods import analysis, build_and_configure_docker_and_aws

PROJECT_FOLDER = os.path.join(Path(os.path.dirname(os.path.realpath(__file__))).parent.absolute())
OUTPUT_FOLDER = os.path.join(PROJECT_FOLDER, "output")
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(version='1.0.0')
def btap():
    pass


@btap.command()
def credits():
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
    build_and_configure_docker_and_aws(btap_batch_branch=btap_batch_branch,
                                       btap_costing_branch=btap_costing_branch,
                                       compute_environment=compute_environment,
                                       openstudio_version=openstudio_version,
                                       os_standards_branch=os_standards_branch)


@btap.command()
@click.option('--compute_environment', default='local_docker',
              help='Environment to run analysis either local_docker or aws_batch')
@click.option('--project_folder',
              help='location of folder containing input.yml file and optionally support folder such as osm_files folder. ')
@click.option('--reference_run', is_flag=True,
              help='Run reference. Required for baseline comparisons')
@click.option('--output_folder', default=OUTPUT_FOLDER,
              help='Path to output results. Defaulted to this projects output folder ./btap_batch/output')
def run_analysis_project(**kwargs):
    # Input folder name
    analysis_project_folder = kwargs['project_folder']
    compute_environment = kwargs['compute_environment']
    reference_run = kwargs['reference_run']
    output_folder = kwargs['output_folder']
    # Function to run analysis.
    analysis(analysis_project_folder, compute_environment, reference_run, output_folder)


@btap.command()
def result_data_reset(**kwargs):
    AWSDynamodb().delete_results_table()
    AWSDynamodb().create_results_table()


@btap.command()
@click.option('--type', default="csv", help='format type to dump entire results information. Choices are pickle or csv')
@click.option('--folder_path', default=OUTPUT_FOLDER,
              help='folder path to save database file dump. Defaults to projects output folder. ')
def result_data_dump(**kwargs):
    type = kwargs['type']
    folder_path = kwargs['folder_path']
    AWSDynamodb().dump_results_table(folder_path=folder_path, type=type)


@btap.command()
@click.option('--compute_environment', default='local_docker',
              help='Environment to run analysis either local_docker or aws_batch')
def parallel_test_examples(**kwargs):
    start = time.time()
    examples_folder = os.path.join(PROJECT_FOLDER, 'examples')
    example_folders = [
        'custom_osm'
        # 'elimination',
        # 'optimization',
        # 'parametric',
        # 'sample-lhs',
        # 'sensitivity'
    ]

    for folder in example_folders:
        project_input_folder = os.path.join(examples_folder, folder)
        print(project_input_folder)
        analysis(project_input_folder, kwargs['compute_environment'], True, OUTPUT_FOLDER)
    end = time.time()
    print(f"Time elapsed: {end - start}")
    print("You will need to review aws batch for progress of analyses.")


if __name__ == '__main__':
    btap()

# Sample commands.
# set PYTHONPATH=C:\Users\plopez\btap_batch &&  python ./bin/btap_batch.py run-analysis-project --compute_environment aws_batch_analysis --project_folder C:\Users\plopez\btap_batch\examples\optimization
# set PYTHONPATH=C:\Users\plopez\btap_batch &&  python ./bin/btap_batch.py run-analysis-project --compute_environment local_docker --project_folder C:\Users\plopez\btap_batch\examples\parametric --run_reference

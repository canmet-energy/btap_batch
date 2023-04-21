from pathlib import Path
import os
import sys

# PROJECT_ROOT = str(Path(os.path.dirname(os.path.realpath(__file__))).parent.absolute().parent.absolute())
PROJECT_ROOT = str(Path(os.path.dirname(os.path.realpath(__file__))).parent.parent)

print('PROJECT_ROOT is ', PROJECT_ROOT)
# print(Path(os.path.dirname(os.path.realpath(__file__))))
# print(Path(os.path.dirname(os.path.realpath(__file__))).parent)
# print(Path(os.path.dirname(os.path.realpath(__file__))).parent.absolute())
# print(Path(os.path.dirname(os.path.realpath(__file__))).parent.absolute().parent)
# print(Path(os.path.dirname(os.path.realpath(__file__))).parent.absolute().parent.absolute())
sys.path.append(PROJECT_ROOT)

print(sys.path.append(PROJECT_ROOT))

from src.btap.cli_helper_methods import build_and_configure_docker_and_aws
from src.btap.cli_helper_methods import analysis
from src.btap.cli_helper_methods import generate_yml

#=======================================================================================================================
##### Set assumptions for solutions sets
compute_environment='local_docker'
solution_set_input_folder=r"C:\btap_batch\SaraGilani\inputs"
solution_set_output_folder=r"C:\btap_batch\SaraGilani\outputs"
optimization_population=40
optimization_generations=20

building_types_list = [
    # 'MediumOffice',
    # 'LargeOffice',
    'SmallOffice',
    # 'PrimarySchool',
    # 'SecondarySchool',
    # 'LowriseApartment',
    # 'MidriseApartment',
    # 'HighriseApartment'
]

locations_dict = {
    'Vancouver': 'CAN_BC_Vancouver.Intl.AP.718920_CWEC2016.epw',
    # 'Montreal': 'CAN_QC_Montreal-Trudeau.Intl.AP.716270_CWEC2016.epw',
    # 'Edmonton': 'CAN_AB_Edmonton.Intl.AP.711230_CWEC2016.epw'
}

hvac_fuel_types_list = [
    ['NECB_Default','NaturalGas'],
    # ['NECB_Default','Electricity'],
    ['HS09_CCASHP_Baseboard','NaturalGasHPGasBackup'],
    # ['HS09_CCASHP_Baseboard','ElectricityHPElecBackup'],
    # ['HS08_CCASHP_VRF','NaturalGasHPGasBackup'],
    # ['HS08_CCASHP_VRF','ElectricityHPElecBackup'],
    # ['HS11_ASHP_PTHP','NaturalGasHPGasBackup'],
    # ['HS11_ASHP_PTHP','ElectricityHPElecBackup'],
    # ['HS13_ASHP_VRF','NaturalGasHPGasBackup'],
    # ['HS13_ASHP_VRF','ElectricityHPElecBackup']
]
#=======================================================================================================================
##### The below method creates all .yml files and run them
def generate_solution_sets(
    compute_environment=compute_environment,
    building_types_list=building_types_list,
    locations_dict=locations_dict,
    hvac_fuel_types_list=hvac_fuel_types_list,
    solution_set_input_folder=solution_set_input_folder,
    pop=optimization_population,
    generations=optimization_generations,
    solution_set_output_folder=solution_set_output_folder
):

    # What are locations and their associated weather files
    # locations_name_list = []
    # locations_weatherfile_list = []
    # for location_name in locations_dict.keys():
    #     locations_name_list.append(location_name)
    #     locations_weatherfile_list.append(locations_dict[location_name])

    # 1. A function that creates all the analyses project folders and input.yml files.. Returns a list that contains the analyses_folders.
    # folders = generate_yml(solution_set_generated_input_folder)
    generate_yml(
        building_types_list=building_types_list, # a list of the building_types to look at.
        locations_dict=locations_dict, # a dictionary of the locations and associated epw files.
        hvac_fuel_types_list=hvac_fuel_types_list,
        project_input_folder=solution_set_input_folder,
        pop=pop,
        generations=generations,
    )

    ##### Do 'analysis' for each input.yml file in each folder under the 'solution_sets_folder' folder under the 'analysis_project_folder' folder
    for filename in os.listdir(Path(solution_set_input_folder)):
        print('filename is', filename)
        project_input_folder = os.path.join(Path(solution_set_input_folder), filename)
        output_folder = os.path.join(Path(solution_set_output_folder))
        print('project_input_folder is', project_input_folder)
        print('output_folder is', output_folder)
        print('compute_environment is', compute_environment)
        analysis(
            project_input_folder=project_input_folder,
            compute_environment=compute_environment,
            reference_run=True,
            output_folder=output_folder
        )

#=======================================================================================================================
##### Create all .yml files and run them
generate_solution_sets(
    compute_environment=compute_environment, #local_docker, aws_batch, aws_batch_analysis...
    building_types_list=building_types_list, # a list of the building_types to look at.
    locations_dict=locations_dict, # an list of the epw files.
    hvac_fuel_types_list=hvac_fuel_types_list,
    solution_set_input_folder=solution_set_input_folder, # "C:/sara_stuff
    pop=optimization_population,
    generations=optimization_generations,
    solution_set_output_folder=solution_set_output_folder
)
#=======================================================================================================================
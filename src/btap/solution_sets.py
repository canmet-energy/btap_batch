from pathlib import Path
import os
import sys
import pandas as pd

PROJECT_ROOT = str(Path(os.path.dirname(os.path.realpath(__file__))).parent.parent)

sys.path.append(PROJECT_ROOT)

from src.btap.cli_helper_methods import build_and_configure_docker_and_aws
from src.btap.cli_helper_methods import analysis
from src.btap.cli_helper_methods import generate_yml

#=======================================================================================================================
##### Set assumptions for solutions sets
compute_environment='local_docker' #'aws_batch'  'aws_batch_analysis'
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

    # Call the function that creates all the analyses project folders and input.yml file associated with each folder
    generate_yml(
        building_types_list=building_types_list, # a list of the building_types to look at.
        locations_dict=locations_dict, # a dictionary of the locations and associated epw files.
        hvac_fuel_types_list=hvac_fuel_types_list,
        project_input_folder=solution_set_input_folder,
        pop=pop,
        generations=generations,
    )

    ##### Do 'analysis' for each input.yml file under the 'solution_set_input_folder' folder
    for filename in os.listdir(Path(solution_set_input_folder)):
        # print('filename is', filename)
        project_input_folder = os.path.join(Path(solution_set_input_folder), filename)
        output_folder = os.path.join(Path(solution_set_output_folder))
        # print('project_input_folder is', project_input_folder)
        # print('output_folder is', output_folder)
        # print('compute_environment is', compute_environment)
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
##### Postprocess output files START
# postprocess_outputs_solutionsets(
#
# ):

solution_set_output_folder = os.path.join(Path(solution_set_output_folder))
# print('solution_set_output_folder is', solution_set_output_folder)

output_folder_names_list = []
for output_folder_name in os.listdir(Path(solution_set_input_folder)):
    output_folder_names_list.append(output_folder_name)
# print('list_ref_files is', output_folder_names_list)

for output_folder_name in output_folder_names_list:
    # ==================================================================================================================
    ### Read output results file of reference building of the folder
    file_name_ref = os.path.join(Path(solution_set_output_folder), output_folder_name, 'reference', 'results', 'output.xlsx')
    # print('file_name_ref is', file_name_ref)
    df_ref = pd.read_excel(file_name_ref)
    # print('df_ref_unmet_hours_cooling is', df_ref['unmet_hours_cooling'])
    # ==================================================================================================================
    ### Read output results file of proposed buildings of the folder
    file_name_prop = os.path.join(Path(solution_set_output_folder), output_folder_name, 'nsga2', 'results', 'output.xlsx')
    # print('file_name_prop is', file_name_prop)
    df_prop = pd.read_excel(file_name_prop)
    # print('df_prop_unmet_hours_cooling is', df_prop['unmet_hours_cooling'])
    # ==================================================================================================================
    ### Find which datapoints meet NECB's requirement for cooling unmet hours
    unmet_hours_cooling_threshold = df_ref['unmet_hours_cooling'] + df_ref['unmet_hours_cooling'] * 0.10
    unmet_hours_cooling_threshold = unmet_hours_cooling_threshold.values
    # print('unmet_hours_cooling_threshold is', unmet_hours_cooling_threshold[0])
    df_prop['MetCoolingUnmetRequirement'] = False
    df_prop.loc[(df_prop['unmet_hours_cooling']<unmet_hours_cooling_threshold[0]),'MetCoolingUnmetRequirement'] = True
    # print(df_prop['MetCoolingUnmetRequirement'])
    # ==================================================================================================================
    ### Remove duplicates
    # First remove extra columns
    df_prop = df_prop.drop(columns=['Unnamed: 0',
                                    'datapoint_output_url',
                                    'simulation_time',
                                    ':analysis_id',
                                    ':datapoint_id',
                                    'simulation_date',
                                    'run_options'])
    # Second, remove the index column
    df_prop.reset_index(drop=True, inplace=True)
    # Then, remove duplicates
    df_prop = df_prop.drop_duplicates()

    # # save as .xlsx file
    # df_prop.to_excel(os.path.join(Path(solution_set_output_folder), output_folder_name, 'nsga2', 'results', 'output_POSTPROCESS.xlsx'), index=False)
    #===================================================================================================================
    ### Find pareto fronts for datapoints that meet NECB's requirement for cooling unmet hours
    # Define bins
    # df_prop = df_prop.loc[(df_prop['MetCoolingUnmetRequirement'] == True)]
    bins = list(range(0, 101, 1))
    # print('bins are', bins)
    df_prop['bin_baseline_energy_percent_better'] = pd.cut(df_prop['baseline_energy_percent_better'], bins)
    # print(df_prop['bin_baseline_energy_percent_better'])

    # Find minimum NPV in each bin
    min_npv_each_bin = df_prop.groupby('bin_baseline_energy_percent_better')['npv_total_per_m_sq'].min().values
    # print('min_npv_each_bin are', min_npv_each_bin)

    # Gather solutions sets associated with minimum NPVs in each bin
    packages_list = []

    for i_bin in range(0, len(min_npv_each_bin)):
        # print('bin ', bins[i_bin])
        # print('min_npv_each_bin ', min_npv_each_bin[i_bin])
        df_handle = []
        df_handle_list = []
        df_handle = df_prop.loc[(df_prop['npv_total_per_m_sq'] == min_npv_each_bin[i_bin])]
        df_handle_idx = df_handle.index.to_list()
        # print('df_handle_idx are ', df_handle_idx)
        # print('type df_handle_idx are ', type(df_handle_idx))
        if len(df_handle_idx) > 0.0:
            for df_handle_list_index in range(0, len(df_handle_idx)):
                # print(df_handle.iloc[df_handle_list_index])
                packages_list.append(df_handle.iloc[df_handle_list_index])

    # ==============================================================================================================
    packages = pd.DataFrame(packages_list, columns=df_prop.keys())
    packages['IsOptimalPackage?'] = True
    # ==============================================================================================================
    # Remove duplicates
    # First, remove the index column
    packages.reset_index(drop=True, inplace=True)
    # Second, remove duplicates
    packages = packages.drop_duplicates()
    # ==============================================================================================================
    # Calculate number of packages and then save it
    packages['Number_of_packages_Total'] = len(packages)
    # ==============================================================================================================
    # Merge all optimization outputs with pareto fronts for using in Tableau
    df_merged = pd.concat([df_prop, packages], ignore_index=True)
    # df_merged = df_merged.drop(columns=['Unnamed: 0'])
    df_merged.to_excel(file_name_prop.replace('.xlsx', '_postprocess.xlsx'), index=False)
#=======================================================================================================================
##### Postprocess output files END
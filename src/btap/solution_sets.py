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
compute_environment='local_docker'
solution_set_input_folder=r"C:\btap_batch\SaraGilani\inputs"
solution_set_output_folder=r"C:\btap_batch\SaraGilani\outputs"
optimization_population=40
optimization_generations=20

building_types_list = [
    'MediumOffice',
    'LargeOffice',
    'SmallOffice',
    'PrimarySchool',
    'SecondarySchool',
    'LowriseApartment',
    'MidriseApartment',
    'HighriseApartment'
]

locations_dict = {
    'Vancouver': 'CAN_BC_Vancouver.Intl.AP.718920_CWEC2016.epw',
    'Montreal': 'CAN_QC_Montreal-Trudeau.Intl.AP.716270_CWEC2016.epw',
    'Edmonton': 'CAN_AB_Edmonton.Intl.AP.711230_CWEC2016.epw'
}

hvac_fuel_types_list = [
    ['NECB_Default','NaturalGas'],
    ['NECB_Default','Electricity'],
    ['HS09_CCASHP_Baseboard','NaturalGasHPGasBackup'],
    ['HS09_CCASHP_Baseboard','ElectricityHPElecBackup'],
    ['HS08_CCASHP_VRF','NaturalGasHPGasBackup'],
    ['HS08_CCASHP_VRF','ElectricityHPElecBackup'],
    ['HS11_ASHP_PTHP','NaturalGasHPGasBackup'],
    ['HS11_ASHP_PTHP','ElectricityHPElecBackup'],
    ['HS13_ASHP_VRF','NaturalGasHPGasBackup'],
    ['HS13_ASHP_VRF','ElectricityHPElecBackup']
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
solution_set_output_folder = os.path.join(Path(solution_set_output_folder))
# print('solution_set_output_folder is', solution_set_output_folder)

output_folder_names_list = []
for output_folder_name in os.listdir(Path(solution_set_input_folder)):
    output_folder_names_list.append(output_folder_name)
# print('list_ref_files is', output_folder_names_list)

for output_folder_name in output_folder_names_list:
    # print('output_folder_name is', output_folder_name)
    df_prop = []
    # ==================================================================================================================
    ### Read output results file of proposed buildings of the folder
    file_name_prop = os.path.join(Path(solution_set_output_folder), output_folder_name, 'nsga2', 'results', 'output.xlsx')
    # print('file_name_prop is', file_name_prop)
    df_prop = pd.read_excel(file_name_prop)
    # print('df_prop_unmet_hours_cooling is', df_prop['unmet_hours_cooling'])
    # ==================================================================================================================
    ### Find which datapoints meet NECB's requirement for cooling unmet hours
    unmet_hours_cooling_threshold = df_prop['baseline_unmet_hours_cooling'] + df_prop['baseline_unmet_hours_cooling'] * 0.10
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

    #===================================================================================================================
    ### Find pareto fronts for datapoints that meet NECB's requirement for cooling unmet hours
    # Remove datapoints that did not meet NECB's requirement for cooling unmet hours
    # df_prop = df_prop.loc[(df_prop['MetCoolingUnmetRequirement'] == True)]
    # Define bins
    bins = list(range(0, 101, 1))
    # print('bins are', bins)
    df_prop['bin_baseline_energy_percent_better'] = pd.cut(df_prop['baseline_energy_percent_better'], bins)
    # print(df_prop['bin_baseline_energy_percent_better'])
    # print(type(df_prop['bin_baseline_energy_percent_better'][0]))

    # save as .xlsx file
    df_prop.to_excel(
        os.path.join(Path(solution_set_output_folder), output_folder_name, 'nsga2', 'results', 'output_processed.xlsx'),
        index=False)

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
    ### Below are packages in each bin of 'baseline_energy_percent_better' with minimum 'npv_total_per_m_sq'
    ### regardless of whether they meet NECB's requirement for cooling unmet hours
    packages = []
    packages = pd.DataFrame(packages_list, columns=df_prop.keys())
    packages['IsOptimalPackage?'] = True
    # ==============================================================================================================
    ### Remove duplicates from packages
    # First, remove the index column
    packages.reset_index(drop=True, inplace=True)
    # Second, remove duplicates
    packages = packages.drop_duplicates()
    # print(packages['bin_baseline_energy_percent_better'])
    # print(type(packages['bin_baseline_energy_percent_better'][0]))
    # ==============================================================================================================
    ### Calculate number of packages regardless of whether they meet NECB's requirement for cooling unmet hours
    packages['Number_of_packages_Total'] = len(packages)
    packages.to_excel(os.path.join(Path(solution_set_output_folder), output_folder_name, 'nsga2', 'results','output_packages.xlsx'), index=False)
    # ==============================================================================================================
    ### Merge all optimization outputs with packages (pareto fronts regardless of whether they meet NECB's requirements for unmet cooling hours)
    ### Note that in the 'output_postprocess.xlsx' file that is created below, number of rows are more than the number
    ### of the optimization output datapoints. This is because 'packages' have been added to them without removing the
    ### datapoints that are packages.
    ### In other words, each package has a duplicate in the 'output_postprocess.xlsx', however it is not marked as
    ### 'True' for 'IsOptimalPackage'.
    # df_merged = pd.concat([df_prop, packages],axis=1)
    df_merged = pd.concat(map(pd.read_excel, [file_name_prop.replace('.xlsx','_processed.xlsx'),
                                              file_name_prop.replace('.xlsx','_packages.xlsx')]),
                          ignore_index=True)

    df_merged.to_excel(file_name_prop.replace('.xlsx', '_postprocess.xlsx'), index=False)

    # Delete .xlsx files that were created for postprocessing
    os.remove(os.path.join(Path(solution_set_output_folder), output_folder_name, 'nsga2', 'results','output_processed.xlsx'))
    os.remove(os.path.join(Path(solution_set_output_folder), output_folder_name, 'nsga2', 'results','output_packages.xlsx'))

##### Postprocess output files END
#=======================================================================================================================
##### Merge all processed output files of all folders START
# Delete output_processed_all_cases.xlsx if it is there
if os.path.isfile(os.path.join(Path(solution_set_output_folder), 'output_processed_all_cases.xlsx'))==True:
    os.remove(os.path.join(Path(solution_set_output_folder), 'output_processed_all_cases.xlsx'))

# Make a list of all output folders' names
output_folder_names_list = []
for output_folder_name in os.listdir(Path(solution_set_output_folder)):
    output_folder_names_list.append(output_folder_name)
# print('output_folder_names_list is', output_folder_names_list)

file_number = 0.0
for output_folder_name in output_folder_names_list:
    # print('output_folder_name is', output_folder_name)
    ### Read output_processed.xlsx file of proposed buildings of 'output_folder_name' folder
    df = []
    file_name = os.path.join(Path(solution_set_output_folder), output_folder_name, 'nsga2', 'results', 'output_postprocess.xlsx')
    df = pd.read_excel(file_name)

    # Create an empty dataframe
    if file_number == 0.0:
        # Get column headers of the df
        df_columns = df.columns
        # Create an empty dataframe
        df_output = pd.DataFrame(columns=df_columns)

    df_output = pd.concat([df_output, df], ignore_index=True, sort=False)

    file_number += 1.0

df_output['MetCoolingUnmetRequirement'] = df_output['MetCoolingUnmetRequirement'].astype('boolean')
df_output['IsOptimalPackage?'] = df_output['IsOptimalPackage?'].astype('boolean')
df_output[':run_annual_simulation'] = df_output[':run_annual_simulation'].astype('boolean')
df_output['phius_necb_meet_cooling_demand'] = df_output['phius_necb_meet_cooling_demand'].astype('boolean')
df_output['phius_necb_meet_cooling_peak_load'] = df_output['phius_necb_meet_cooling_peak_load'].astype('boolean')
df_output['phius_necb_meet_heating_demand'] = df_output['phius_necb_meet_heating_demand'].astype('boolean')
df_output['phius_necb_meet_heating_peak_load'] = df_output['phius_necb_meet_heating_peak_load'].astype('boolean')
# print(df_output.dtypes)
# print(df_output.dtypes[df_output.dtypes == 'object'])
df_output.to_excel(os.path.join(Path(solution_set_output_folder), 'output_processed_all_cases.xlsx'), index=False)

##### Merge all processed output files of all folders END
# =======================================================================================================================
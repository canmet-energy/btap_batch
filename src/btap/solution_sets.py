from pathlib import Path
import os
import sys
import pandas as pd
import copy
import re
import logging
import yaml
import json
from icecream import ic
from src.btap.cli_helper_methods import analysis
import time
import shutil

PROJECT_ROOT = str(Path(os.path.dirname(os.path.realpath(__file__))).parent.parent)

sys.path.append(PROJECT_ROOT)


def generate_yml(
        building_type=None,
        location_name=None,
        hvac_fuel_type=None,
        yaml_project_generation_folder=None,
        pop=None,
        generations=None,
        analysis_config_file = None,
        eta = 0.85
):
    # load template .yml file for creating all other .yml files
    if not os.path.isfile(analysis_config_file):
        logging.error(f"could not find template input file at {analysis_config_file}. Exiting")
    # Open the yaml in analysis dict.
    with open(analysis_config_file, 'r') as stream:
        analysis_config = yaml.safe_load(stream)

    # Json options_filter  file for filtering options based on fuel, building and
    option_filters_file = os.path.join(Path(os.path.dirname(os.path.realpath(__file__))).parent.parent, 'resources',
                                       'option_filters.json')
    if not os.path.isfile(option_filters_file):
        logging.error(f"could not find template input file at {option_filters_file}. Exiting")
    # Open the yaml in analysis dict.
    with open(option_filters_file, encoding='utf-8') as json_file:
        option_filters = json.load(json_file)


    hvac_type = hvac_fuel_type[0]
    fuel_type = hvac_fuel_type[1]


    # Look up available options from options_filters.json for this type.
    result = list(filter(lambda options_filter: (
            options_filter['hvac_type'] == hvac_type and
            options_filter['fuel_type'] == fuel_type and
            building_type in options_filter['building_types']),
                         option_filters))

    # Error checking.
    if len(result) == 0:
        print("no matching filter found. Exiting.")
        exit(1)
    if len(result) > 1:
        print("Too many filters found. Check options_filter.json logic. Exiting.")
        exit(1)

    # Get options to remove and set to default.
    remove_building_options = result[0]["remove_building_options"]

    # Make a copy of anaylsis_config and use it as template to create all other .yml files
    template_yml = copy.deepcopy(analysis_config)
    # Optimization parameters
    template_yml[':algorithm_nsga_eta'] = eta
    template_yml[':algorithm_nsga_population'] = pop
    template_yml[':algorithm_nsga_n_generations'] = generations
    # Building and location.
    template_yml[':options'][':building_type'] = [building_type]
    template_yml[':options'][':epw_file'] = [location_name]
    # hvac system and fuelset.
    template_yml[':options'][':ecm_system_name'] = [ hvac_type ]
    template_yml[':options'][':primary_heating_fuel'] = [fuel_type]
    # analysis name
    epw_short = re.search(r"CAN_(\w*_\w*).*", location_name).group(1)
    analysis_name = f"opt_necb_{building_type}_{fuel_type}_{hvac_type}_{epw_short}"
    # :analysis_name
    template_yml[':analysis_name'] = analysis_name


    # removes options that do not apply to building type and fuel/hvac combinations.
    for option in remove_building_options:
        # ic(option)
        template_yml[':options'][option] = [i for i in template_yml[':options'][option] if
                                            i in ['NECB_Default']]


    # yml file path
    yaml_folder_path = Path(os.path.join(Path(yaml_project_generation_folder), analysis_name))
    yml_file_path = os.path.join(yaml_folder_path, 'input.yml')
    Path(os.path.join(yaml_folder_path)).mkdir(parents=True, exist_ok=True)
    file = open(yml_file_path, "w")
    yaml.dump(template_yml, file)
    file.close()
    return yaml_folder_path


# =======================================================================================================================


##### The below method creates all .yml files and run them
def generate_solution_sets(
        compute_environment=None,
        building_types_list=None,
        epw_files=None,
        hvac_fuel_types_list=None,
        working_folder=None,
        output_folder=None,
        pop=None,
        generations=None,
        run_analyses=True,
        analysis_config_file = os.path.join( Path(os.path.dirname(
            os.path.realpath(__file__))).parent.parent,
                                             'resources',
                                          'solutionsets_optimization_template_input.yml'),
        eta = 0.85
):
    start = time.time()
    # Check if analyses folder exists if not create it.
    Path(os.path.join(working_folder)).mkdir(parents=True, exist_ok=True)


    supported_fuel_types = ['NECB_Default-NaturalGas',
                            'NECB_Default-Electricity',
                            'HS08_CCASHP_VRF-NaturalGasHPGasBackup',
                            'HS08_CCASHP_VRF-ElectricityHPElecBackup',
                            'HS09_CCASHP_Baseboard-NaturalGasHPGasBackup',
                            'HS09_CCASHP_Baseboard-ElectricityHPElecBackup',
                            'HS11_ASHP_PTHP-NaturalGasHPGasBackup',
                            'HS11_ASHP_PTHP-ElectricityHPElecBackup',
                            'HS12_ASHP_Baseboard-NaturalGasHPGasBackup',
                            'HS12_ASHP_Baseboard-ElectricityHPElecBackup',
                            'HS13_ASHP_VRF-NaturalGasHPGasBackup',
                            'HS13_ASHP_VRF-ElectricityHPElecBackup',
                            'HS14_CGSHP_FanCoils-NaturalGasHPGasBackup',
                            'HS14_CGSHP_FanCoils-ElectricityHPElecBackup']

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


    if not (set(hvac_fuel_types_list).issubset(set(supported_fuel_types))):
        print(f"Invalid fueltype system mix #{hvac_fuel_types_list}. Please use only the following:")
        print(supported_fuel_types)
        raise("hell")

    if not (set(building_types_list).issubset(set(supported_building_types))):
        print("Invalid building types detected. Please use only the following:")
        print(supported_fuel_types)
        exit(1)

    hvac_fuel_types_list = [x.split('-') for x in hvac_fuel_types_list]

    yaml_project_generation_folder = os.path.join(working_folder)
    simulation_results_folder = os.path.join(output_folder)

    for building_type in building_types_list:
        for epw_file in epw_files:
            for hvac_fuel_type in hvac_fuel_types_list:
                # Call the function that creates all the analyses project folders and input.yml file associated with each folder
                project_folder = generate_yml(
                    building_type=building_type,  # a list of the building_types to look at.
                    location_name=epw_file,  # a dictionary of the locations and associated epw files.
                    hvac_fuel_type=hvac_fuel_type,
                    yaml_project_generation_folder=yaml_project_generation_folder,
                    pop=pop,
                    generations=generations,
                    analysis_config_file=analysis_config_file,
                    eta = eta
                )
                if run_analyses:
                    output_folder = os.path.join(Path(simulation_results_folder))
                    project_folder = os.path.join(Path(project_folder))
                    analysis(
                        project_input_folder=project_folder,
                        compute_environment=compute_environment,
                        reference_run=True,
                        output_folder=output_folder
                    )

def post_process_analyses(solution_sets_raw_results_folder="",
                          aws_database=True):
    post_processed_output_folder = solution_sets_raw_results_folder
    # Need error checking on paths.
    if aws_database == False and solution_sets_raw_results_folder == "":
        print("solution sets local folder does not exists")
        exit(1)

    solution_set_output_folder = os.path.join(solution_sets_raw_results_folder)
    from src.btap.aws_dynamodb import AWSResultsTable
    ##### Postprocess output files START

    analysis_names = []

    # Get list of :analysis_name performed.
    # If using AWS database
    if aws_database == True:
        from src.btap.aws_dynamodb import AWSResultsTable
        results_df = AWSResultsTable().dump_table(folder_path=post_processed_output_folder, type='csv',
                                                  analysis_name=None, save_output=True)
        analysis_names = (sorted(results_df[':analysis_name'].unique()))

    # If using local_docker
    else:
        for output_folder_name in os.listdir(Path(solution_sets_raw_results_folder)):
            analysis_names.append(output_folder_name)

    for output_folder_name in analysis_names:
        df_prop = []
        output_xlsx_path = os.path.join(Path(solution_set_output_folder), output_folder_name, 'nsga2', 'results',
                                        'output.xlsx')

        if aws_database == True:
            # ==================================================================================================================
            ### Read output results file of proposed buildings of the folder

            df_prop = results_df.loc[results_df[':analysis_name'] == output_folder_name]
            df_prop = df_prop.dropna(subset=['baseline_energy_percent_better'],
                                     how='all')  # This removes rows with null 'baseline_energy_percent_better' from df_prop as that row is the reference building when running on aws
        else:

            df_prop = pd.read_excel(output_xlsx_path)

        # print('df_prop_unmet_hours_cooling is', df_prop['unmet_hours_cooling'])
        # ==================================================================================================================
        ### Find which datapoints meet NECB's requirement for cooling unmet hours
        from decimal import Decimal
        if aws_database == True:
            unmet_hours_cooling_threshold = df_prop['baseline_unmet_hours_cooling'] + df_prop[
                'baseline_unmet_hours_cooling'] * Decimal(0.10)
        else:
            unmet_hours_cooling_threshold = df_prop['baseline_unmet_hours_cooling'] + df_prop[
                'baseline_unmet_hours_cooling'] * 0.10

        unmet_hours_cooling_threshold = unmet_hours_cooling_threshold.values
        # print('unmet_hours_cooling_threshold is', unmet_hours_cooling_threshold[0])
        df_prop['MetCoolingUnmetRequirement'] = False
        df_prop.loc[
            (df_prop['unmet_hours_cooling'] < unmet_hours_cooling_threshold[0]), 'MetCoolingUnmetRequirement'] = True
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
        # Then, remove duplicates. Keep lists intacts
        df_prop = df_prop.loc[df_prop.astype(str).drop_duplicates().index]

        # ===================================================================================================================
        ### Find pareto fronts for datapoints that meet NECB's requirement for cooling unmet hours
        # Remove datapoints that did not meet NECB's requirement for cooling unmet hours
        # df_prop = df_prop.loc[(df_prop['MetCoolingUnmetRequirement'] == True)]
        # Define bins
        bins = [float(i) for i in list(range(0, 101, 1))]

        df_prop['bin_baseline_energy_percent_better'] = pd.cut(df_prop['baseline_energy_percent_better'], bins)
        # print(df_prop['bin_baseline_energy_percent_better'])
        # print(type(df_prop['bin_baseline_energy_percent_better'][0]))

        # save as .xlsx file
        excel_path = Path(os.path.join(Path(solution_set_output_folder), output_folder_name, 'nsga2', 'results',
                                       'output_processed.xlsx'))
        excel_path.parent.absolute().mkdir(parents=True, exist_ok=True)
        df_prop.to_excel(excel_path, index=False)

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
        packages.to_excel(os.path.join(Path(solution_set_output_folder), output_folder_name, 'nsga2', 'results',
                                       'output_packages.xlsx'), index=False)
        # ==============================================================================================================
        ### Merge all optimization outputs with packages (pareto fronts regardless of whether they meet NECB's requirements for unmet cooling hours)
        ### Note that in the 'output_postprocess.xlsx' file that is created below, number of rows are more than the number
        ### of the optimization output datapoints. This is because 'packages' have been added to them without removing the
        ### datapoints that are packages.
        ### In other words, each package has a duplicate in the 'output_postprocess.xlsx', however it is not marked as
        ### 'True' for 'IsOptimalPackage'.
        # df_merged = pd.concat([df_prop, packages],axis=1)
        df_merged = pd.concat(map(pd.read_excel, [output_xlsx_path.replace('.xlsx', '_processed.xlsx'),
                                                  output_xlsx_path.replace('.xlsx', '_packages.xlsx')]),
                              ignore_index=True)

        df_merged.to_excel(output_xlsx_path.replace('.xlsx', '_postprocess.xlsx'), index=False)

        # Delete .xlsx files that were created for postprocessing
        os.remove(os.path.join(Path(solution_set_output_folder), output_folder_name, 'nsga2', 'results',
                               'output_processed.xlsx'))
        os.remove(os.path.join(Path(solution_set_output_folder), output_folder_name, 'nsga2', 'results',
                               'output_packages.xlsx'))
    ##### Postprocess output files END
    # =======================================================================================================================
    ##### Merge all processed output files of all folders START
    # Delete output_processed_all_cases.xlsx if it is there
    if os.path.isfile(os.path.join(Path(solution_set_output_folder), 'output_processed_all_cases.xlsx')) == True:
        os.remove(os.path.join(Path(solution_set_output_folder), 'output_processed_all_cases.xlsx'))
    # Make a list of all output folders' names
    analysis_names = []

    # If using AWS database
    if aws_database == True:
        from src.btap.aws_dynamodb import AWSResultsTable
        results_df = AWSResultsTable().dump_table(folder_path=post_processed_output_folder, type='csv',
                                                  analysis_name=None, save_output=True)
        analysis_names = (sorted(results_df[':analysis_name'].unique()))

    # If using local_docker
    else:
        for output_folder_name in os.listdir(Path(solution_set_output_folder)):
            analysis_names.append(output_folder_name)

    # print('analysis_names is', analysis_names)

    file_number = 0.0
    for output_folder_name in analysis_names:
        # print('output_folder_name is', output_folder_name)
        ### Read output_processed.xlsx file of proposed buildings of 'output_folder_name' folder
        df = []
        file_name = os.path.join(Path(solution_set_output_folder), output_folder_name, 'nsga2', 'results',
                                 'output_postprocess.xlsx')

        df = pd.read_excel(file_name)

        # Cast columns to bool type, where applicable
        df['MetCoolingUnmetRequirement'] = df['MetCoolingUnmetRequirement'].astype('boolean')
        df['IsOptimalPackage?'] = df['IsOptimalPackage?'].astype('boolean')
        df[':run_annual_simulation'] = df[':run_annual_simulation'].astype('boolean')
        df['phius_necb_meet_cooling_demand'] = df['phius_necb_meet_cooling_demand'].astype('boolean')
        df['phius_necb_meet_cooling_peak_load'] = df['phius_necb_meet_cooling_peak_load'].astype(
            'boolean')
        df['phius_necb_meet_heating_demand'] = df['phius_necb_meet_heating_demand'].astype('boolean')
        df['phius_necb_meet_heating_peak_load'] = df['phius_necb_meet_heating_peak_load'].astype(
            'boolean')

        # Create an empty dataframe
        if file_number == 0.0:
            # Get column headers of the df
            df_columns = df.columns
            # Create an empty dataframe
            df_output = pd.DataFrame(columns=df_columns)

        df_output = pd.concat([df_output, df], ignore_index=True, sort=False)

        # Cast columns to bool type, where applicable
        df_output['MetCoolingUnmetRequirement'] = df_output['MetCoolingUnmetRequirement'].astype('boolean')
        df_output['IsOptimalPackage?'] = df_output['IsOptimalPackage?'].astype('boolean')
        df_output[':run_annual_simulation'] = df_output[':run_annual_simulation'].astype('boolean')
        df_output['phius_necb_meet_cooling_demand'] = df_output['phius_necb_meet_cooling_demand'].astype('boolean')
        df_output['phius_necb_meet_cooling_peak_load'] = df_output['phius_necb_meet_cooling_peak_load'].astype(
            'boolean')
        df_output['phius_necb_meet_heating_demand'] = df_output['phius_necb_meet_heating_demand'].astype('boolean')
        df_output['phius_necb_meet_heating_peak_load'] = df_output['phius_necb_meet_heating_peak_load'].astype(
            'boolean')
        # print(df_output.dtypes)
        # print(df_output.dtypes[df_output.dtypes == 'object'])

        file_number += 1.0

    df_output.to_excel(os.path.join(Path(solution_set_output_folder), 'output_processed_all_cases.xlsx'), index=False)
    ##### Merge all processed output files of all folders END

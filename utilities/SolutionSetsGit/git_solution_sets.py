import copy
import os
import yaml
import pathlib
from src.btap.cli_helper_methods import analysis
from src.btap.cli_helper_methods import get_number_of_failures

def git_solution_sets():

    os.environ['BUILD_ENV_NAME'] = 'reference_runs_370'

    # 2710 runs per building (6)  per location (6)  is 97,000 simulations.
    VINTAGE_RUNS = False  # 4 runs (1)
    REFERENCE_RUNS = True  # 16 Runs (1)
    SENSITIVITY_RUNS = False  # 190 runs (2)
    OPTIMIZATION_RUNS = False  # 500 runs. (1)
    LHS_RUNS = False  # 2000 runs (1)

    # So 6*6*6 = 216 Analyses for solution sets.

    building_types = [
         'LowriseApartment',
         # 'MidriseApartment',
         # 'HighriseApartment',
         # 'SmallOffice',
         # 'MediumOffice',
         # 'LargeOffice',
         # 'RetailStandalone',
         # 'PrimarySchool',
         # 'SecondarySchool'


        # "SecondarySchool",
        # "PrimarySchool",
        # "SmallOffice",
        # "MediumOffice",
        # "LargeOffice",
        # "SmallHotel",
        # "LargeHotel",
        # "Warehouse",
        # "RetailStandalone",
        # "RetailStripmall",
        # "QuickServiceRestaurant",
        # "FullServiceRestaurant",
        # "MidriseApartment",
        # "HighriseApartment",
        # "LowriseApartment",
        # "Hospital",
        # "Outpatient"
        # 'LEEPMidriseApartment',
        # 'LEEPMultiTower',
        # 'LEEPPointTower',
        # 'LEEPTownHouse'
    ]

# Using airport codes to identify the locations.  Much easier if sometimes slightly inaccurate.
    epw_files = [
        # ['CAN_BC_Vancouver.Intl.AP.718920_CWEC2016.epw', 'YVR'],  # CZ 4
        # ['CAN_ON_Toronto.Pearson.Intl.AP.716240_CWEC2016.epw', 'YYZ'],  # CZ 5
        # ['CAN_QC_Montreal-Trudeau.Intl.AP.716270_CWEC2016.epw', 'YUL'],  # CZ 6
        # ['CAN_AB_Edmonton.Intl.AP.711230_CWEC2016.epw', 'YEG'],  # CZ 7A
        # ['CAN_AB_Fort.McMurray.AP.716890_CWEC2016.epw', 'YMM'],  # CZ 7B
        # ['CAN_NT_Yellowknife.AP.719360_CWEC2016.epw', 'YZF']  # CZ 8

        ['CAN_BC_Vancouver.Intl.AP.718920_CWEC2020.epw', 'YVR'],
        ['CAN_AB_Calgary.Intl.AP.718770_CWEC2020.epw', 'YYC'],
         ['CAN_SK_Regina.Intl.AP.715140_CWEC2020.epw', 'YQR'],
         ['CAN_MB_Winnipeg.Intl.AP.718520_CWEC2020.epw', 'YWG'],
         ['CAN_ON_Toronto.Intl.AP.716240_CWEC2020.epw', 'YYZ'],
         ['CAN_QC_Montreal.Intl.AP.716270_CWEC2020.epw', 'YUL'],
         ['CAN_NB_Fredericton.717000_CWEC2020.epw', 'YFC'],
         ['CAN_NS_Halifax.Intl.AP.713950_CWEC2020.epw', 'YHZ'],
         ['CAN_PE_Charlottetown.AP.717060_CWEC2020.epw', 'YYG'],
         ['CAN_NL_St.Johns.Intl.AP.718010_CWEC2020.epw', 'YYT'],
         ['CAN_YT_Whitehorse.AP.719640_CWEC2020.epw', 'YXY'],
         ['CAN_NT_Yellowknife.AP.719360_CWEC2020.epw', 'YZF'],
         ['CAN_NU_Iqaluit.AP.719090_CWEC2020.epw', 'YFB']
    ]



    compute_environment = 'local_managed_aws_workers'

    if compute_environment != 'local':
        print(f"Current Analysis Failures: {get_number_of_failures(job_queue_name='btap_batch')}")
        print(f"Current Worker Failures: {get_number_of_failures(job_queue_name='btap_cli')}")


        # LHS constants
    algorithm_lhs_n_samples = 2000

    # Optimization
    algorithm_nsga_population = 50
    algorithm_nsga_n_generations = 10
    algorithm_nsga_minimize_objectives = [
        'energy_eui_total_gj_per_m_sq',
        'npv_total_per_m_sq'
    ]

    output_meters = [
        # Utility
        {'name': 'NaturalGas:Facility', 'frequency': 'hourly'},
        {'name': 'Electricity:Facility', 'frequency': 'hourly'},
        {'name': 'FuelOilNo2:Facility', 'frequency': 'hourly'},
        # End Uses
        {'name': 'InteriorLights:Electricity', 'frequency': 'hourly'},
        {'name': 'Heating:Electricity', 'frequency': 'hourly'},
        {'name': 'Heating:NaturalGas', 'frequency': 'hourly'},
        {'name': 'Heating:FuelOilNo2', 'frequency': 'hourly'},
        {'name': 'Heating:DistrictHeating', 'frequency': 'hourly'},
        {'name': 'Cooling:Electricity', 'frequency': 'hourly'},
        {'name': 'Heating:DistrictCooling', 'frequency': 'hourly'},
        {'name': 'Fans:Electricity', 'frequency': 'hourly'},
        {'name': 'Pumps:Electricity', 'frequency': 'hourly'},
        {'name': 'InteriorEquipment:Electricity', 'frequency': 'hourly'},
        {'name': 'WaterSystems:Electricity', 'frequency': 'hourly'},
        {'name': 'WaterSystems:NaturalGas', 'frequency': 'hourly'},
    ]

    # Not used yet may run again once
    output_variables = [
        {'key': '*', 'variable': 'Zone Predicted Sensible Load to Setpoint Heat Transfer Rate', 'frequency': 'hourly',
         'operation': '*', 'unit': '*'},
        {'key': '*', 'variable': 'Zone Predicted Sensible Load to Heating Setpoint Heat Transfer Rate',
         'frequency': 'hourly', 'operation': '*', 'unit': '*'},
        {'key': '*', 'variable': 'Zone Predicted Sensible Load to Cooling Setpoint Heat Transfer Rate',
         'frequency': 'hourly', 'operation': '*', 'unit': '*'},
        {'key': '*', 'variable': 'Zone Predicted Moisture Load Moisture Transfer Rate', 'frequency': 'hourly',
         'operation': '*', 'unit': '*'},
        {'key': '*', 'variable': 'Zone Predicted Moisture Load to Humidifying Setpoint Moisture Transfer Rate',
         'frequency': 'hourly', 'operation': '*', 'unit': '*'},
        {'key': '*', 'variable': 'Zone Predicted Moisture Load to Dehumidifying Setpoint Moisture Transfer Rate',
         'frequency': 'hourly', 'operation': '*', 'unit': '*'},
    ]

    pwd = (os.path.dirname(os.path.realpath(__file__)))
    output_folder = os.path.join(pwd, 'output')
    pathlib.Path(output_folder).mkdir(parents=True, exist_ok=True)

    projects_folder = os.path.join(pwd, 'projects')
    pathlib.Path(projects_folder).mkdir(parents=True, exist_ok=True)

    # Load ymls file into memory adjust to ensure consistency and then save
    sensitivity_template_file = pathlib.Path(os.path.join(pwd, 'sensitivity.yml'))
    sensitivity_template = yaml.safe_load(sensitivity_template_file.read_text())
    sensitivity_template[':output_meters'] = output_meters
    sensitivity_template[':output_variables'] = output_variables
    with open(sensitivity_template_file, 'w') as outfile:
        yaml.dump(sensitivity_template, outfile, default_flow_style=False)

    optimization_template_file = pathlib.Path(os.path.join(pwd, 'optimization.yml'))
    optimization_template = yaml.safe_load(optimization_template_file.read_text())
    optimization_template[':output_meters'] = output_meters
    optimization_template[':output_variables'] = output_variables
    with open(optimization_template_file, 'w') as outfile:
        yaml.dump(optimization_template, outfile, default_flow_style=False)

    # Iterage through building_type
    for building_type in building_types:
        for epw_file in epw_files:

            # Reference Runs
            if REFERENCE_RUNS:
                analysis_configuration = copy.deepcopy(sensitivity_template)
                analysis_configuration[':algorithm_type'] = 'reference'
                analysis_configuration[':reference_run'] = True
                analysis_configuration[':options'][':building_type'] = [building_type]
                analysis_configuration[':options'][':epw_file'] = [epw_file[0]]
                analysis_configuration[':output_meters'] = output_meters
                analysis_configuration[':options'][':primary_heating_fuel'] = [
                    'Electricity',
                    # 'ElectricityHPElecBackup',
                    # 'NaturalGas',
                    # 'NaturalGasHPGasBackup'
                ]
                analysis_configuration[':template'] = [
                    'BTAP1980TO2010',
                    'BTAPPRE1980',
                    # 'NECB2011',
                    'NECB2015',
                    # 'NECB2017',
                    # 'NECB2020'
                    #
                    ]

                analysis_configuration[':analysis_name'] = f"{building_type}_{epw_file[1]}_ref"
                analysis_folder = os.path.join(projects_folder, analysis_configuration[':analysis_name'])
                pathlib.Path(analysis_folder).mkdir(parents=True, exist_ok=True)
                f = open(os.path.join(analysis_folder, "input.yml"), 'w')
                yaml.dump(analysis_configuration, f)
                # Submit analysis
                print(f"Running  {analysis_configuration[':analysis_name']}")
                analysis(project_input_folder=analysis_folder,
                         compute_environment=compute_environment,
                         output_folder=output_folder)

            # Vintage Runs
            if VINTAGE_RUNS:
                analysis_configuration = copy.deepcopy(sensitivity_template)
                analysis_configuration[':algorithm_type'] = 'reference'
                analysis_configuration[':reference_run'] = True
                analysis_configuration[':options'][':building_type'] = [building_type]
                analysis_configuration[':options'][':epw_file'] = [epw_file[0]]
                analysis_configuration[':output_meters'] = output_meters
                analysis_configuration[':options'][':primary_heating_fuel'] = [
                    'Electricity',
                    'NaturalGas',
                ]
                analysis_configuration[':template'] = [
                    'BTAP1980TO2010',
                    'BTAPPRE1980']

                analysis_configuration[':analysis_name'] = f"{building_type}_{epw_file[1]}_vin"
                analysis_folder = os.path.join(projects_folder, analysis_configuration[':analysis_name'])
                pathlib.Path(analysis_folder).mkdir(parents=True, exist_ok=True)
                f = open(os.path.join(analysis_folder, "input.yml"), 'w')
                yaml.dump(analysis_configuration, f)
                # Submit analysis
                print(f"Running  {analysis_configuration[':analysis_name']}")
                analysis(project_input_folder=analysis_folder,
                         compute_environment=compute_environment,
                         output_folder=output_folder)

            if SENSITIVITY_RUNS:
                # Sensitivity Analysis
                for primary_heating_fuel in ['Electricity', 'NaturalGas']:
                    analysis_configuration = copy.deepcopy(sensitivity_template)
                    analysis_configuration[':options'][':building_type'] = [building_type]
                    analysis_configuration[':options'][':primary_heating_fuel'] = [primary_heating_fuel]
                    analysis_configuration[':options'][':epw_file'] = [epw_file[0]]
                    analysis_configuration[':algorithm_type'] = 'sensitivity'
                    analysis_configuration[':reference_run'] = True
                    analysis_configuration[':output_meters'] = output_meters

                    analysis_configuration[
                        ':analysis_name'] = f"{building_type}_{primary_heating_fuel}_{epw_file[1]}_sens"
                    analysis_folder = os.path.join(projects_folder, analysis_configuration[':analysis_name'])
                    pathlib.Path(analysis_folder).mkdir(parents=True, exist_ok=True)
                    f = open(os.path.join(analysis_folder, "input.yml"), 'w')
                    yaml.dump(analysis_configuration, f)
                    # Submit analysis
                    print(f"Running {analysis_configuration[':analysis_name']}")
                    analysis(project_input_folder=analysis_folder,
                             compute_environment=compute_environment,
                             output_folder=output_folder)

            if LHS_RUNS:
                # LHS Analysis

                analysis_configuration = copy.deepcopy(optimization_template)

                analysis_configuration[':options'][':building_type'] = [building_type]
                analysis_configuration[':options'][':epw_file'] = [epw_file[0]]
                analysis_configuration[':output_meters'] = output_meters

                analysis_configuration[':algorithm_type'] = 'sampling-lhs'
                analysis_configuration[':reference_run'] = True
                analysis_configuration[':algorithm_lhs_n_samples'] = algorithm_lhs_n_samples
                analysis_configuration[':algorithm_lhs_type'] = 'classic'
                analysis_configuration[':algorithm_lhs_random_seed'] = 1

                analysis_configuration[':options'][':primary_heating_fuel'] = [
                    'Electricity',
                    'ElectricityHPElecBackup',
                    'NaturalGas',
                    'NaturalGasHPGasBackup']

                analysis_configuration[':analysis_name'] = f"{building_type}_{epw_file[1]}_lhs"
                analysis_folder = os.path.join(projects_folder, analysis_configuration[':analysis_name'])
                pathlib.Path(analysis_folder).mkdir(parents=True, exist_ok=True)
                f = open(os.path.join(analysis_folder, "input.yml"), 'w')
                yaml.dump(analysis_configuration, f)
                # Submit analysis
                print(f"Running {analysis_configuration[':analysis_name']}")
                analysis(project_input_folder=analysis_folder,
                         compute_environment=compute_environment,
                         output_folder=output_folder)

            # General Optimization
            if OPTIMIZATION_RUNS:
                analysis_configuration = copy.deepcopy(sensitivity_template)
                analysis_configuration[':options'][':building_type'] = [building_type]
                analysis_configuration[':options'][':epw_file'] = [epw_file[0]]
                analysis_configuration[':options'][':primary_heating_fuel'] = [
                    'NaturalGas',
                    'Electricity',
                    'ElectricityHPElecBackup',
                    'NaturalGasHPGasBackup'
                ]
                analysis_configuration[':output_meters'] = output_meters
                analysis_configuration[':algorithm_type'] = 'nsga2'
                analysis_configuration[':reference_run'] = True
                analysis_configuration[':algorithm_nsga_population'] = algorithm_nsga_population
                analysis_configuration[':algorithm_nsga_n_generations'] = algorithm_nsga_n_generations
                analysis_configuration[':algorithm_nsga_prob'] = 0.85
                analysis_configuration[':algorithm_nsga_eta'] = 3.0
                analysis_configuration[':algorithm_nsga_minimize_objectives'] = algorithm_nsga_minimize_objectives

                analysis_configuration[
                    ':analysis_name'] = f"{building_type}_{epw_file[1]}_opt"
                analysis_folder = os.path.join(projects_folder, analysis_configuration[':analysis_name'])
                pathlib.Path(analysis_folder).mkdir(parents=True, exist_ok=True)
                f = open(os.path.join(analysis_folder, "input.yml"), 'w')
                yaml.dump(analysis_configuration, f)
                # Submit analysis
                print(f"Running  {analysis_configuration[':analysis_name']}")
                analysis(project_input_folder=analysis_folder,
                         compute_environment=compute_environment,
                         output_folder=output_folder)

git_solution_sets()
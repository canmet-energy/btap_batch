import copy
import os
import yaml
import pathlib
from src.btap.cli_helper_methods import analysis, load_config
from src.btap.cli_helper_methods import get_number_of_failures
from src.btap.common_paths import CONFIG_FOLDER

def git_solution_sets():


    build_config = load_config(os.path.join(CONFIG_FOLDER, 'build_config.yml'))
    os.environ['BUILD_ENV_NAME'] =build_config['build_env_name']

    LEEP = False
    HOURLY = True
    SENSITIVITY_RUNS = True
    SENSITIVITY_PRIMARY_FUELS_PIVOT = [
        'Electricity',
        'NaturalGas',
        'ElectricityHPElecBackup',
        'NaturalGasHPGasBackup',
        'ElectricityHPGasBackupMixed',
        'NaturalGasHPElecBackupMixed'
        ]
    OPTIMIZATION_RUNS = True
    OPTIMIZATION_PRIMARY_FUELS_PIVOT = [
        'Electricity',
        'NaturalGas',
        'ElectricityHPElecBackup',
        'NaturalGasHPGasBackup',
        'ElectricityHPGasBackupMixed',
        'NaturalGasHPElecBackupMixed'
    ]
    algorithm_nsga_population = 50
    algorithm_nsga_n_generations = 5
    algorithm_nsga_minimize_objectives = [
        'energy_eui_total_gj_per_m_sq',
        'npv_total_per_m_sq'
    ]
    LHS_RUNS = False  # 2000 runs (1)
    LHS_PRIMARY_FUELS =[
        'Electricity',
        'ElectricityHPElecBackup',
        'NaturalGas',
        'NaturalGasHPGasBackup',
        'ElectricityHPGasBackupMixed',
        'NaturalGasHPElecBackupMixed'
    ]
    algorithm_lhs_n_samples = 2000

    building_types = [
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
        "HighriseApartment",
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
         ['CAN_BC_Vancouver.Intl.AP.718920_CWEC2016.epw', 'YVR'],  # CZ 4
         ['CAN_ON_Toronto.Pearson.Intl.AP.716240_CWEC2016.epw', 'YYZ'],  # CZ 5
         ['CAN_QC_Montreal-Trudeau.Intl.AP.716270_CWEC2016.epw', 'YUL'],  # CZ 6
         ['CAN_AB_Edmonton.Intl.AP.711230_CWEC2016.epw', 'YEG'],  # CZ 7A
         ['CAN_AB_Fort.McMurray.AP.716890_CWEC2016.epw', 'YMM'],  # CZ 7B
         ['CAN_NT_Yellowknife.AP.719360_CWEC2016.epw', 'YZF']  # CZ 8
    ]

    if build_config['compute_environment'] != 'local':
        print(f"Current Analysis Failures: {get_number_of_failures(job_queue_name='btap_batch')}")
        print(f"Current Worker Failures: {get_number_of_failures(job_queue_name='btap_cli')}")


    HOURLY_OUTPUT_METERS = [
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
    HOURLY_OUTPUT_VARIABLES = [
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
    optimization_template_file = pathlib.Path(os.path.join(pwd, 'optimization.yml'))
    optimization_template = yaml.safe_load(optimization_template_file.read_text())


    if HOURLY:
        optimization_template[':output_meters'] = HOURLY_OUTPUT_METERS
        #optimization_template[':output_variables'] = HOURLY_OUTPUT_VARIABLES
        sensitivity_template[':output_meters'] = HOURLY_OUTPUT_METERS
        #sensitivity_template[':output_variables'] = HOURLY_OUTPUT_VARIABLES
    else: # turn off hourly output. Faster runs.
        optimization_template[':output_meters'] = []
        optimization_template[':output_variables'] = []
        sensitivity_template[':output_meters'] = []
        sensitivity_template[':output_variables'] = []

    lhs_template = copy.deepcopy(optimization_template)

    #LEEP Custom Options Overides
    if LEEP:
        building_types = [
            'LEEPMidriseApartment',
            # 'LEEPMultiTower',
            'LEEPPointTower',
            'LEEPTownHouse'
        ]

        epw_files = [
            ['CAN_ON_Toronto.Pearson.Intl.AP.716240_CWEC2016.epw', 'YYZ'],  # CZ 5
        ]

        # LHS
        lhs_template[':options'][':fdwr_set'] = [0.40, 0.20, 0.60, 0.80]
        lhs_template[':options'][':primary_heating_fuel'] = LHS_PRIMARY_FUELS
        lhs_template[':options'][':ecm_system_name'] = [
            'NECB_Default',
            'HS09_CCASHP_Baseboard',
            'HS11_ASHP_PTHP',
            'HS14_CGSHP_FanCoils'
        ]
        # Sensitivity
        SENSITIVITY_PRIMARY_FUELS_PIVOT = [
            'NaturalGas'
            ]
        sensitivity_template[':options'][':fdwr_set'] = [0.40, 0.20, 0.60, 0.80] # Order is important..First value is base case.
        sensitivity_template[':options'][':ecm_system_name'] = [
            'NECB_Default',
            'HS09_CCASHP_Baseboard',
            'HS11_ASHP_PTHP',
            'HS14_CGSHP_FanCoils'
        ]
        # Optimization
        OPTIMIZATION_PRIMARY_FUELS_PIVOT = [
            'Electricity',
            'NaturalGas',
            'ElectricityHPElecBackup',
            'ElectricityHPGasBackupMixed'
        ]
        optimization_template[':options'][':fdwr_set']  = [0.40]
        optimization_template[':options'][':ecm_system_name'] = [
            'NECB_Default',
            'HS09_CCASHP_Baseboard',
            'HS11_ASHP_PTHP',
            'HS14_CGSHP_FanCoils'
        ]


    with open(sensitivity_template_file, 'w') as outfile:
        yaml.dump(sensitivity_template, outfile, default_flow_style=False)

    with open(optimization_template_file, 'w') as outfile:
        yaml.dump(optimization_template, outfile, default_flow_style=False)

    # Iterage through building_type
    for building_type in building_types:
        for epw_file in epw_files:

            if SENSITIVITY_RUNS:
                # Sensitivity Analysis
                for primary_heating_fuel in SENSITIVITY_PRIMARY_FUELS_PIVOT:
                    analysis_configuration = copy.deepcopy(sensitivity_template)
                    analysis_configuration[':options'][':building_type'] = [building_type]
                    analysis_configuration[':options'][':primary_heating_fuel'] = [primary_heating_fuel]
                    analysis_configuration[':options'][':epw_file'] = [epw_file[0]]
                    analysis_configuration[':algorithm_type'] = 'sensitivity'
                    analysis_configuration[':reference_run'] = True
                    analysis_configuration[':output_meters'] = HOURLY_OUTPUT_METERS

                    analysis_configuration[
                        ':analysis_name'] = f"{building_type}_{primary_heating_fuel}_{epw_file[1]}_sens"
                    analysis_folder = os.path.join(projects_folder, analysis_configuration[':analysis_name'])
                    pathlib.Path(analysis_folder).mkdir(parents=True, exist_ok=True)
                    f = open(os.path.join(analysis_folder, "input.yml"), 'w')
                    yaml.dump(analysis_configuration, f)
                    # Submit analysis
                    print(f"Running {analysis_configuration[':analysis_name']}")
                    analysis(project_input_folder=analysis_folder,
                             build_config=build_config,
                             output_folder=output_folder)

            if LHS_RUNS:
                # LHS Analysis
                analysis_configuration = copy.deepcopy(lhs_template)
                analysis_configuration[':options'][':building_type'] = [building_type]
                analysis_configuration[':options'][':epw_file'] = [epw_file[0]]
                analysis_configuration[':algorithm_type'] = 'sampling-lhs'
                analysis_configuration[':reference_run'] = True
                analysis_configuration[':algorithm_lhs_n_samples'] = algorithm_lhs_n_samples
                analysis_configuration[':algorithm_lhs_type'] = 'classic'
                analysis_configuration[':algorithm_lhs_random_seed'] = 1
                analysis_configuration[':options'][':primary_heating_fuel'] = LHS_PRIMARY_FUELS
                analysis_configuration[':analysis_name'] = f"{building_type}_{epw_file[1]}_lhs"
                analysis_folder = os.path.join(projects_folder, analysis_configuration[':analysis_name'])
                pathlib.Path(analysis_folder).mkdir(parents=True, exist_ok=True)
                f = open(os.path.join(analysis_folder, "input.yml"), 'w')
                yaml.dump(analysis_configuration, f)
                # Submit analysis
                print(f"Running {analysis_configuration[':analysis_name']}")
                analysis(project_input_folder=analysis_folder,
                         build_config=build_config,
                         output_folder=output_folder)

            # General Optimization
            if OPTIMIZATION_RUNS:
                for primary_heating_fuel in OPTIMIZATION_PRIMARY_FUELS_PIVOT:
                    analysis_configuration = copy.deepcopy(sensitivity_template)
                    analysis_configuration[':options'][':building_type'] = [building_type]
                    analysis_configuration[':options'][':epw_file'] = [epw_file[0]]
                    analysis_configuration[':options'][':primary_heating_fuel'] = [primary_heating_fuel]
                    analysis_configuration[':algorithm_type'] = 'nsga2'
                    analysis_configuration[':reference_run'] = True
                    analysis_configuration[':algorithm_nsga_population'] = algorithm_nsga_population
                    analysis_configuration[':algorithm_nsga_n_generations'] = algorithm_nsga_n_generations
                    analysis_configuration[':algorithm_nsga_prob'] = 0.85
                    analysis_configuration[':algorithm_nsga_eta'] = 3.0
                    analysis_configuration[':algorithm_nsga_minimize_objectives'] = algorithm_nsga_minimize_objectives

                    analysis_configuration[
                        ':analysis_name'] = f"{building_type}_{primary_heating_fuel}_{epw_file[1]}_opt"
                    analysis_folder = os.path.join(projects_folder, analysis_configuration[':analysis_name'])
                    pathlib.Path(analysis_folder).mkdir(parents=True, exist_ok=True)
                    f = open(os.path.join(analysis_folder, "input.yml"), 'w')
                    yaml.dump(analysis_configuration, f)
                    # Submit analysis
                    print(f"Running  {analysis_configuration[':analysis_name']}")
                    analysis(project_input_folder=analysis_folder,
                             build_config=build_config,
                             output_folder=output_folder)

git_solution_sets()
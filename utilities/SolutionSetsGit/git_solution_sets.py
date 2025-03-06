import copy
import os
import yaml
import pathlib
from src.btap.cli_helper_methods import analysis, load_config
from src.btap.cli_helper_methods import get_number_of_failures
from src.btap.common_paths import CONFIG_FOLDER
import json

def git_solution_sets():


    build_config = load_config(os.path.join(CONFIG_FOLDER, 'build_config.yml'))
    os.environ['BUILD_ENV_NAME'] =build_config['build_env_name']

    OEE = True
    LEEP = False
    HOURLY = False
    CLIMATE_ZONES = [
        'CZ_4',
        # 'CZ_5',
        # 'CZ_6',
        # 'CZ_7A'
    ]
    ENVELOPE = [
        # 'env_necb',
        # 'env_necb_15',
        'env_necb_30'
    ]
    ELECsystems_OEE = [ #TODO: exclude CAWHP and AWASHP as costing is under development
        # 'MURBElec_ElecResWH',
        # 'MURBMixed_ElecResWH',
        # 'MURBASHPElec_ElecResWH',
        # 'MURBASHPMixed_ElecResWH',
        # 'SchoolElec_ElecResWH',
        # 'SchoolMixed_ElecResWH',
        # 'SchoolASHPElec_ElecResWH',
        # 'SchoolASHPMixed_ElecResWH',
        # 'CAWHPElec_ElecResWH',
        # 'CAWHPMixed_ElecResWH',
        # 'CAWASHPElec_ElecResWH',
        # 'CAWASHPMixed_ElecResWH',
        # 'CGSHPElec_ElecResWH',
        # 'CGSHPMixed_ElecResWH',
        # 'VRFElecBoiler_ElecResWH',
        # 'VRFMixedBoiler_ElecResWH',
        # 'VRFElecResBackup_ElecResWH',

        # 'MURBElec_HPWH',
        # 'MURBMixed_HPWH',
        # 'MURBASHPElec_HPWH',
        # 'MURBASHPMixed_HPWH',
        # 'SchoolElec_HPWH',
        # 'SchoolMixed_HPWH',
        # 'SchoolASHPElec_HPWH',
        # 'SchoolASHPMixed_HPWH',
        # 'CAWHPElec_HPWH',
        # 'CAWHPMixed_HPWH',
        # 'CAWASHPElec_HPWH',
        # 'CAWASHPMixed_HPWH',
        # 'CGSHPElec_HPWH',
        # 'CGSHPMixed_HPWH',
        # 'VRFElecBoiler_HPWH',
        # 'VRFMixedBoiler_HPWH',
        # 'VRFElecResBackup_HPWH',

        # 'MURBMixed_ElecResWH_0199',
        # 'MURBASHPMixed_ElecResWH_0199',
        # 'SchoolMixed_ElecResWH_0199',
        # 'SchoolASHPMixed_ElecResWH_0199',
        # 'CGSHPMixed_ElecResWH_0199',
        # 'VRFMixedBoiler_ElecResWH_0199',

        # 'MURBMixed_ElecResWH_5050',
        # 'MURBASHPMixed_ElecResWH_5050',
        # 'SchoolMixed_ElecResWH_5050',
        # 'SchoolASHPMixed_ElecResWH_5050',
        # 'CAWHPMixed_ElecResWH_5050',
        # 'CAWASHPMixed_ElecResWH_5050',
        # 'CGSHPMixed_ElecResWH_5050',
        # 'VRFMixedBoiler_ElecResWH_5050',
        # 'MURBMixed_HPWH_5050',
        # 'MURBASHPMixed_HPWH_5050',
        # 'SchoolMixed_HPWH_5050',
        # 'SchoolASHPMixed_HPWH_5050',
        # 'CAWHPMixed_HPWH_5050',
        # 'CAWASHPMixed_HPWH_5050',
        # 'CGSHPMixed_HPWH_5050',
        # 'VRFMixedBoiler_HPWH_5050',

    ]
    SENSITIVITY_RUNS = False
    SENSITIVITY_PRIMARY_FUELS_PIVOT = [
        'Electricity',
        'NaturalGas',
        'ElectricityHPElecBackup',
        'NaturalGasHPGasBackup',
        'ElectricityHPGasBackupMixed',
        'NaturalGasHPElecBackupMixed'
        ]
    PARAMETRIC_RUNS_OEE = False
    PARAMETRIC_PRIMARY_FUELS_PIVOT_OEE = [
        'NaturalGas'
        ]
    SENSITIVITY_RUNS_OEE = False
    SENSITIVITY_PRIMARY_FUELS_PIVOT_OEE = [
        'NaturalGas'
        ]
    SCENARIO_RUNS_OEE = True
    Baseline_RUNS_OEE = False
    OPTIMIZATION_RUNS = False
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
        "SecondarySchool",
        "PrimarySchool",
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
        "MidriseApartment",
        "HighriseApartment",
        "LowriseApartment",
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
         ['CAN_NT_Yellowknife.AP.719360_CWEC2016.epw', 'YZF'],  # CZ 8
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
        {'name': 'Cooling:DistrictCooling', 'frequency': 'hourly'},
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

    if OEE:
        epw_files_cz4 = [
            ['CAN_BC_Vancouver.Intl.AP.718920_NRCv12022_TMY_GW1.5.epw', 'YVR'],  # CZ 4
        ]

        epw_files_cz5 = [
            ['CAN_BC_Kelowna.Intl.AP.712030_NRCv12022_TMY_GW1.5.epw', 'YLW'],  # CZ 5
            ['CAN_ON_Toronto-Pearson.Intl.AP.716240_NRCv12022_TMY_GW1.5.epw', 'YYZ'],  # CZ 5
        ]

        epw_files_cz6 = [
            ['CAN_ON_Ottawa-Macdonald-Cartier.Intl.AP.716280_NRCv12022_TMY_GW1.5.epw', 'YOW'],  # CZ 6
            ['CAN_QC_Montreal-Trudeau.Intl.AP.716270_NRCv12022_TMY_GW1.5.epw', 'YUL'],  # CZ 6
            ['CAN_NS_Halifax-Stanfield.Intl.AP.713950_NRCv12022_TMY_GW1.5.epw', 'YHZ'],  # CZ 6
            ['CAN_NL_St.Johns.Intl.AP.718010_NRCv12022_TMY_GW1.5.epw', 'YYT'],  # CZ 6
            ['CAN_PE_Charlottetown.AP.717060_NRCv12022_TMY_GW1.5.epw', 'YYG'],  # CZ 6
            ['CAN_NB_Fredericton.Intl.AP.717000_NRCv12022_TMY_GW1.5.epw', 'YFC'],  # CZ 6
        ]

        epw_files_cz7A = [
            ['CAN_AB_Calgary.Intl.AP.718770_NRCv12022_TMY_GW1.5.epw', 'YYC'],  # CZ 7A
            ['CAN_AB_Edmonton.Intl.CS.711550_NRCv12022_TMY_GW1.5.epw', 'YEG'],  # CZ 7A
            ['CAN_SK_Saskatoon-Diefenbaker.Intl.AP.718660_NRCv12022_TMY_GW1.5.epw', 'YXE'],  # CZ 7A
            ['CAN_MB_Winnipeg-Richardson.Intl.AP.718520_NRCv12022_TMY_GW1.5.epw', 'YWG'],  # CZ 7A
        ]

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

    # Iterage through building_type
    for building_type in building_types:

        if PARAMETRIC_RUNS_OEE:
        # Parametric Analysis
            for envelope in ENVELOPE:
                for climate_zone in CLIMATE_ZONES:
                    if climate_zone == 'CZ_4':
                        if envelope == 'env_necb':
                            parametric_template_file = pathlib.Path(os.path.join(pwd, 'parametric_cz4_env_necb.yml'))
                        elif envelope == 'env_necb_15':
                            parametric_template_file = pathlib.Path(os.path.join(pwd, 'parametric_cz4_env_necb_less15.yml'))
                        elif envelope == 'env_necb_30':
                            parametric_template_file = pathlib.Path(os.path.join(pwd, 'parametric_cz4_env_necb_less30.yml'))

                        epw_files = epw_files_cz4

                    elif climate_zone == 'CZ_5':
                        if envelope == 'env_necb':
                            parametric_template_file = pathlib.Path(os.path.join(pwd, 'parametric_cz5_env_necb.yml'))
                        elif envelope == 'env_necb_15':
                            parametric_template_file = pathlib.Path(os.path.join(pwd, 'parametric_cz5_env_necb_less15.yml'))
                        elif envelope == 'env_necb_30':
                            parametric_template_file = pathlib.Path(os.path.join(pwd, 'parametric_cz5_env_necb_less30.yml'))

                        epw_files = epw_files_cz5

                    elif climate_zone == 'CZ_6':
                        if envelope == 'env_necb':
                            parametric_template_file = pathlib.Path(os.path.join(pwd, 'parametric_cz6_env_necb.yml'))
                        elif envelope == 'env_necb_15':
                            parametric_template_file = pathlib.Path(os.path.join(pwd, 'parametric_cz6_env_necb_less15.yml'))
                        elif envelope == 'env_necb_30':
                            parametric_template_file = pathlib.Path(os.path.join(pwd, 'parametric_cz6_env_necb_less30.yml'))

                        epw_files = epw_files_cz6

                    elif climate_zone == 'CZ_7A':
                        if envelope == 'env_necb':
                            parametric_template_file = pathlib.Path(os.path.join(pwd, 'parametric_cz7A_env_necb.yml'))
                        elif envelope == 'env_necb_15':
                            parametric_template_file = pathlib.Path(os.path.join(pwd, 'parametric_cz7A_env_necb_less15.yml'))
                        elif envelope == 'env_necb_30':
                            parametric_template_file = pathlib.Path(os.path.join(pwd, 'parametric_cz7A_env_necb_less30.yml'))

                        epw_files = epw_files_cz7A

                    parametric_template = yaml.safe_load(parametric_template_file.read_text())

                    if HOURLY:
                        parametric_template[':output_meters'] = HOURLY_OUTPUT_METERS
                        # parametric_template[':output_variables'] = HOURLY_OUTPUT_VARIABLES
                    else:  # turn off hourly output. Faster runs.
                        parametric_template[':output_meters'] = []
                        parametric_template[':output_variables'] = []

                    with open(parametric_template_file, 'w') as outfile:
                        yaml.dump(parametric_template, outfile, default_flow_style=False)

                    for epw_file in epw_files:
                        for primary_heating_fuel in PARAMETRIC_PRIMARY_FUELS_PIVOT_OEE:
                            analysis_configuration = copy.deepcopy(parametric_template)
                            analysis_configuration[':options'][':building_type'] = [building_type]
                            analysis_configuration[':options'][':primary_heating_fuel'] = [primary_heating_fuel]
                            analysis_configuration[':options'][':epw_file'] = [epw_file[0]]
                            analysis_configuration[':algorithm_type'] = 'parametric'
                            analysis_configuration[':reference_run'] = True
                            analysis_configuration[':output_meters'] = HOURLY_OUTPUT_METERS

                            analysis_configuration[':analysis_name'] = f"OEEelec_BL_par_{building_type}_{primary_heating_fuel}_{epw_file[1]}_{envelope}"
                            analysis_folder = os.path.join(projects_folder, analysis_configuration[':analysis_name'])
                            pathlib.Path(analysis_folder).mkdir(parents=True, exist_ok=True)
                            f = open(os.path.join(analysis_folder, "input.yml"), 'w')
                            yaml.dump(analysis_configuration, f)
                            # Submit analysis
                            print(f"Running {analysis_configuration[':analysis_name']}")
                            analysis(project_input_folder=analysis_folder,
                                     build_config=build_config,
                                     output_folder=output_folder)

        if SENSITIVITY_RUNS_OEE:
        # Sensitivity Analysis
            for climate_zone in CLIMATE_ZONES:
                if climate_zone == 'CZ_4':
                    sensitivity_template_file = pathlib.Path(os.path.join(pwd, 'sensitivity_cz4.yml'))

                    epw_files = epw_files_cz4

                elif climate_zone == 'CZ_5':
                    sensitivity_template_file = pathlib.Path(os.path.join(pwd, 'sensitivity_cz5.yml'))

                    epw_files = epw_files_cz5

                elif climate_zone == 'CZ_6':
                    sensitivity_template_file = pathlib.Path(os.path.join(pwd, 'sensitivity_cz6.yml'))

                    epw_files = epw_files_cz6

                elif climate_zone == 'CZ_7A':
                    sensitivity_template_file = pathlib.Path(os.path.join(pwd, 'sensitivity_cz7A.yml'))

                    epw_files = epw_files_cz7A

                sensitivity_template = yaml.safe_load(sensitivity_template_file.read_text())

                if HOURLY:
                    sensitivity_template[':output_meters'] = HOURLY_OUTPUT_METERS
                    # sensitivity_template[':output_variables'] = HOURLY_OUTPUT_VARIABLES
                else:  # turn off hourly output. Faster runs.
                    sensitivity_template[':output_meters'] = []
                    sensitivity_template[':output_variables'] = []

                with open(sensitivity_template_file, 'w') as outfile:
                    yaml.dump(sensitivity_template, outfile, default_flow_style=False)

                for epw_file in epw_files:
                    for primary_heating_fuel in SENSITIVITY_PRIMARY_FUELS_PIVOT_OEE:
                        analysis_configuration = copy.deepcopy(sensitivity_template)
                        analysis_configuration[':options'][':building_type'] = [building_type]
                        analysis_configuration[':options'][':primary_heating_fuel'] = [primary_heating_fuel]
                        analysis_configuration[':options'][':epw_file'] = [epw_file[0]]
                        analysis_configuration[':algorithm_type'] = 'sensitivity'
                        analysis_configuration[':reference_run'] = True
                        analysis_configuration[':output_meters'] = HOURLY_OUTPUT_METERS

                        analysis_configuration[':analysis_name'] = f"OEEelec_BL_sen_{building_type}_{primary_heating_fuel}_{epw_file[1]}"
                        analysis_folder = os.path.join(projects_folder, analysis_configuration[':analysis_name'])
                        pathlib.Path(analysis_folder).mkdir(parents=True, exist_ok=True)
                        f = open(os.path.join(analysis_folder, "input.yml"), 'w')
                        yaml.dump(analysis_configuration, f)
                        # Submit analysis
                        print(f"Running {analysis_configuration[':analysis_name']}")
                        analysis(project_input_folder=analysis_folder,
                                 build_config=build_config,
                                 output_folder=output_folder)




    if SCENARIO_RUNS_OEE:

        OEE_scenario_template_file = pathlib.Path(os.path.join(pwd, 'OEE_scenario_yml_template.yml'))

        # json OEE_scenario_system_filters  file for filtering options
        OEE_scenario_system_filters_file = pathlib.Path(os.path.join(pwd, 'OEE_scenario_system_filters.json'))
        # Open the yaml in analysis dict.
        with open(OEE_scenario_system_filters_file, encoding='utf-8') as json_file:
            OEE_scenario_system_filters = json.load(json_file)

        # json OEE_scenario_envelope_filters  file for filtering options
        OEE_scenario_envelope_filters_file = pathlib.Path(os.path.join(pwd, 'OEE_scenario_envelope_filters.json'))
        # Open the yaml in analysis dict.
        with open(OEE_scenario_envelope_filters_file, encoding='utf-8') as json_file:
            OEE_scenario_envelope_filters = json.load(json_file)


        for climate_zone in CLIMATE_ZONES:
            for scenario in ELECsystems_OEE:
                print('scenario is ', scenario)
                if climate_zone == 'CZ_4':
                    epw_files = epw_files_cz4

                elif climate_zone == 'CZ_5':
                    epw_files = epw_files_cz5

                elif climate_zone == 'CZ_6':
                    epw_files = epw_files_cz6

                elif climate_zone == 'CZ_7A':
                    epw_files = epw_files_cz7A

                OEE_scenario_template = yaml.safe_load(OEE_scenario_template_file.read_text())

                if HOURLY:
                    OEE_scenario_template[':output_meters'] = HOURLY_OUTPUT_METERS
                else:  # turn off hourly output. Faster runs.
                    OEE_scenario_template[':output_meters'] = []
                    OEE_scenario_template[':output_variables'] = []

                with open(OEE_scenario_template_file, 'w') as outfile:
                    yaml.dump(OEE_scenario_template, outfile, default_flow_style=False)

                for epw_file in epw_files:
                    if scenario.startswith("School"):
                        list_building_type = [
                            'PrimarySchool',
                            # 'SecondarySchool'
                        ]
                    elif scenario.startswith("MURB"):
                        list_building_type = [
                            'LowriseApartment',
                            # 'MidriseApartment',
                            # 'HighriseApartment'
                        ]
                    else:
                        list_building_type = [
                            'LowriseApartment',
                            # 'MidriseApartment',
                            # 'HighriseApartment',
                            # 'PrimarySchool',
                            # 'SecondarySchool'
                        ]

                    for building_type in list_building_type:
                        if building_type.endswith("School"):
                            building_name = building_type.replace('School','')
                        elif building_type.endswith("Apartment"):
                            building_name = building_type.replace('Apartment','')

                        for envelope in ENVELOPE:
                            # Look up available options from OEE_scenario_system_filters.json for this type.
                            result_system = list(filter(lambda OEE_scenario_system_filter: (
                                    OEE_scenario_system_filter['scenario'] == scenario
                            ),OEE_scenario_system_filters))

                            # Look up available options from OEE_scenario_envelope_filters.json for this type.
                            result_envelope = list(filter(lambda OEE_scenario_envelope_filter: (
                                    OEE_scenario_envelope_filter['envelope'] == envelope and
                                    OEE_scenario_envelope_filter['climate_zone'] == climate_zone
                            ),OEE_scenario_envelope_filters))

                            analysis_configuration = copy.deepcopy(OEE_scenario_template)

                            analysis_configuration[':options'][':ecm_system_name'] = [result_system[0][":ecm_system_name"]]
                            analysis_configuration[':options'][':primary_heating_fuel'] = [result_system[0][":primary_heating_fuel"]]
                            analysis_configuration[':options'][':boiler_fuel'] = [result_system[0][":boiler_fuel"]]
                            analysis_configuration[':options'][':swh_fuel'] = [result_system[0][":swh_fuel"]]
                            analysis_configuration[':options'][':airloop_fancoils_heating'] = [result_system[0][":airloop_fancoils_heating"]]
                            analysis_configuration[':options'][':boiler_cap_ratio'] = [result_system[0][":boiler_cap_ratio"]]

                            analysis_configuration[':options'][':ext_roof_cond'] = [result_envelope[0][":ext_roof_cond"]]
                            analysis_configuration[':options'][':ext_wall_cond'] = [result_envelope[0][":ext_wall_cond"]]
                            analysis_configuration[':options'][':fixed_window_cond'] = [result_envelope[0][":fixed_window_cond"]]
                            analysis_configuration[':options'][':ground_floor_cond'] = [result_envelope[0][":ground_floor_cond"]]
                            analysis_configuration[':options'][':skylight_cond'] = [result_envelope[0][":skylight_cond"]]

                            analysis_configuration[':options'][':building_type'] = [building_type]
                            analysis_configuration[':options'][':epw_file'] = [epw_file[0]]
                            analysis_configuration[':algorithm_type'] = 'parametric'
                            analysis_configuration[':reference_run'] = False
                            analysis_configuration[':output_meters'] = HOURLY_OUTPUT_METERS

                            if (scenario.endswith("_0199")) | (scenario.endswith("_5050")):
                                if building_type.endswith("School"):
                                    if building_name == "Primary":
                                        building_name = building_name.replace('Primary', 'Pri')
                                    elif building_name == "Secondary":
                                        building_name = building_name.replace('Secondary', 'Sec')
                                elif building_type.endswith("Apartment"):
                                    building_name = building_name.replace('rise', '')
                                analysis_configuration[':analysis_name'] = f"OEEelec_SC_{scenario}_{building_name}_{epw_file[1]}_{envelope}"
                            else:
                                analysis_configuration[':analysis_name'] = f"OEEelec_SC_{scenario}_{building_name}_{epw_file[1]}_{envelope}"

                            analysis_folder = os.path.join(projects_folder, analysis_configuration[':analysis_name'])
                            pathlib.Path(analysis_folder).mkdir(parents=True, exist_ok=True)
                            f = open(os.path.join(analysis_folder, "input.yml"), 'w')
                            yaml.dump(analysis_configuration, f)

                            # Submit analysis
                            print(f"Running {analysis_configuration[':analysis_name']}")
                            analysis(project_input_folder=analysis_folder,
                                     build_config=build_config,
                                     output_folder=output_folder)




    if Baseline_RUNS_OEE:

        OEE_baseline_template_file = pathlib.Path(os.path.join(pwd, 'OEE_baseline_yml_template.yml'))

        # json OEE_baseline_filters  file for filtering options
        OEE_baseline_filters_file = pathlib.Path(os.path.join(pwd, 'OEE_baseline_filters.json'))
        # Open the yaml in analysis dict.
        with open(OEE_baseline_filters_file, encoding='utf-8') as json_file:
            OEE_baseline_filters = json.load(json_file)

        for climate_zone in CLIMATE_ZONES:
            if climate_zone == 'CZ_4':
                epw_files = epw_files_cz4
            elif climate_zone == 'CZ_5':
                epw_files = epw_files_cz5
            elif climate_zone == 'CZ_6':
                epw_files = epw_files_cz6
            elif climate_zone == 'CZ_7A':
                epw_files = epw_files_cz7A

            OEE_baseline_template = yaml.safe_load(OEE_baseline_template_file.read_text())

            if HOURLY:
                OEE_baseline_template[':output_meters'] = HOURLY_OUTPUT_METERS
            else:  # turn off hourly output. Faster runs.
                OEE_baseline_template[':output_meters'] = []
                OEE_baseline_template[':output_variables'] = []

            with open(OEE_baseline_template_file, 'w') as outfile:
                yaml.dump(OEE_baseline_template, outfile, default_flow_style=False)

            for epw_file in epw_files:
                list_building_type = [
                    'PrimarySchool',
                    'SecondarySchool',
                    'LowriseApartment',
                    'MidriseApartment',
                    'HighriseApartment'
                ]

                for building_type in list_building_type:

                    for envelope in ENVELOPE:
                        # Look up available options from OEE_baseline_filters.json for this type.
                        result = list(filter(lambda OEE_baseline_filter: (
                                OEE_baseline_filter['envelope'] == envelope and
                                OEE_baseline_filter['climate_zone'] == climate_zone
                        ), OEE_baseline_filters))

                        analysis_configuration = copy.deepcopy(OEE_baseline_template)
                        analysis_configuration[':options'][':building_type'] = [building_type]
                        analysis_configuration[':options'][':primary_heating_fuel'] = [result[0][":primary_heating_fuel"]]
                        analysis_configuration[':options'][':ext_roof_cond'] = [result[0][":ext_roof_cond"]]
                        analysis_configuration[':options'][':ext_wall_cond'] = [result[0][":ext_wall_cond"]]
                        analysis_configuration[':options'][':fixed_window_cond'] = [result[0][":fixed_window_cond"]]
                        analysis_configuration[':options'][':ground_floor_cond'] = [result[0][":ground_floor_cond"]]
                        analysis_configuration[':options'][':skylight_cond'] = [result[0][":skylight_cond"]]
                        analysis_configuration[':options'][':erv_package'] = [result[0][":erv_package"]]
                        analysis_configuration[':options'][':epw_file'] = [epw_file[0]]
                        analysis_configuration[':algorithm_type'] = 'parametric'
                        analysis_configuration[':reference_run'] = False
                        analysis_configuration[':output_meters'] = HOURLY_OUTPUT_METERS

                        analysis_configuration[':analysis_name'] = f"OEEelec_BL_{building_type}_{epw_file[1]}_{envelope}"
                        analysis_folder = os.path.join(projects_folder, analysis_configuration[':analysis_name'])
                        pathlib.Path(analysis_folder).mkdir(parents=True, exist_ok=True)
                        f = open(os.path.join(analysis_folder, "input.yml"), 'w')
                        yaml.dump(analysis_configuration, f)

                        # Submit analysis
                        print(f"Running {analysis_configuration[':analysis_name']}")
                        analysis(project_input_folder=analysis_folder,
                                 build_config=build_config,
                                 output_folder=output_folder)

git_solution_sets()
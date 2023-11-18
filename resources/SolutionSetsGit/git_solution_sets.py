import copy
import os
import yaml
import re
import pathlib
from src.btap.cli_helper_methods import analysis
from src.btap.solution_sets import generate_solution_sets

REFERENCE_RUNS = True
SENSITIVITY_RUNS = False #x2
LHS_RUNS = False
OPTIMIZATION_RUNS = False

building_types = [
    'LowriseApartment',
    # 'MidriseApartment',
    # 'HighriseApartment',
    # 'SmallOffice',
    # 'MediumOffice',
    # 'LargeOffice',
]

epw_files = [
    ['CAN_BC_Vancouver.Intl.AP.718920_CWEC2016.epw','YVR'],  # CZ 4
    # ['CAN_QC_Montreal-Trudeau.Intl.AP.716270_CWEC2016.epw','YUL'],  # CZ 5
    # ['CAN_ON_Toronto.Pearson.Intl.AP.716240_CWEC2016.epw', 'YYZ'],  # CZ 6
    # ['CAN_AB_Edmonton.Intl.AP.711230_CWEC2016.epw', 'YEG'], # CZ 7A
    # ['CAN_AB_Fort.McMurray.AP.716890_CWEC2016.epw', 'YMM'],  # CZ 7B
    # ['CAN_NT_Yellowknife.AP.719360_CWEC2016.epw', 'YZF']  # CZ 8
]

compute_environment = 'aws_batch_analysis'

# LHS constants
algorithm_lhs_n_samples = 10

# Optimization
algorithm_nsga_population = 20
algorithm_nsga_n_generations = 2
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

# Not used yet
output_variables = [
    {'key': '*', 'variable': 'Zone Predicted Sensible Load to Setpoint Heat Transfer Rate', 'frequency': 'hourly',
     'operation': 'average', 'unit': 'W'},
    {'key': '*', 'variable': 'Zone Predicted Sensible Load to Heating Setpoint Heat Transfer Rate',
     'frequency': 'hourly', 'operation': 'average', 'unit': 'W'},
    {'key': '*', 'variable': 'Zone Predicted Sensible Load to Cooling Setpoint Heat Transfer Rate',
     'frequency': 'hourly', 'operation': 'average', 'unit': 'W'},
    {'key': '*', 'variable': 'Zone Predicted Moisture Load Moisture Transfer Rate', 'frequency': 'hourly',
     'operation': 'average', 'unit': 'W'},
    {'key': '*', 'variable': 'Zone Predicted Moisture Load to Humidifying Setpoint Moisture Transfer Rate',
     'frequency': 'hourly', 'operation': 'average', 'unit': 'W'},
    {'key': '*', 'variable': 'Zone Predicted Moisture Load to Dehumidifying Setpoint Moisture Transfer Rate',
     'frequency': 'hourly', 'operation': 'average', 'unit': 'W'},
]
output_variables = []
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
            analysis_configuration[':building_type'] = [building_type]
            analysis_configuration[':epw_file'] = [epw_file[0]]
            analysis_configuration[':output_meters'] = output_meters
            analysis_configuration[':primary_heating_fuel'] = [
                'Electricity',
                'ElectricityHPElecBackup',
                'NaturalGas',
                'NaturalGasHPGasBackup'
            ]
            analysis_configuration[':template'] = [
                'NECB2011',
                'NECB2015',
                'NECB2017',
                'NECB2020']


            analysis_configuration[':analysis_name'] = f"ref_{building_type}_{epw_file[1]}"
            analysis_folder = os.path.join(projects_folder, analysis_configuration[':analysis_name'])
            pathlib.Path(analysis_folder).mkdir(parents=True, exist_ok=True)
            f = open(os.path.join(analysis_folder, "input.yml"), 'w')
            yaml.dump(analysis_configuration, f)
            # Submit analysis
            print(f"Running  {analysis_configuration[':analysis_name']}")
            analysis(project_input_folder=analysis_folder,
                     compute_environment=compute_environment,
                     reference_run=True,
                     output_folder=output_folder)

        if SENSITIVITY_RUNS:
            # Sensitivity Analysis
            for primary_heating_fuel in ['Electricity', 'NaturalGas']:
                analysis_configuration = copy.deepcopy(sensitivity_template)
                analysis_configuration[':building_type'] = [building_type]
                analysis_configuration[':primary_heating_fuel'] = [primary_heating_fuel]
                analysis_configuration[':epw_file'] = [epw_file[0]]
                analysis_configuration[':algorithm_type'] = 'sensitivity'
                analysis_configuration[':output_meters'] = output_meters

                analysis_configuration[':analysis_name'] = f"sens_{building_type}_{primary_heating_fuel}_{epw_file[1]}"
                analysis_folder = os.path.join(projects_folder, analysis_configuration[':analysis_name'])
                pathlib.Path(analysis_folder).mkdir(parents=True, exist_ok=True)
                f = open(os.path.join(analysis_folder, "input.yml"), 'w')
                yaml.dump(analysis_configuration, f)
                # Submit analysis
                print(f"Running {analysis_configuration[':analysis_name']}")
                analysis(project_input_folder=analysis_folder,
                         compute_environment=compute_environment,
                         reference_run=True,
                         output_folder=output_folder)

        if LHS_RUNS:
            # LHS Analysis

            analysis_configuration = copy.deepcopy(optimization_template)

            analysis_configuration[':building_type'] = [building_type]
            analysis_configuration[':epw_file'] = [epw_file[0]]
            analysis_configuration[':output_meters'] = output_meters

            analysis_configuration[':algorithm_type'] = 'sampling-lhs'
            analysis_configuration[':algorithm_lhs_n_samples'] = algorithm_lhs_n_samples
            analysis_configuration[':algorithm_lhs_type'] = 'classic'
            analysis_configuration[':algorithm_lhs_random_seed'] = 1

            analysis_configuration[':primary_heating_fuel'] = [
                'Electricity',
                'ElectricityHPElecBackup',
                'NaturalGas',
                'NaturalGasHPGasBackup']

            analysis_configuration[':analysis_name'] = f"lhs_{building_type}_{epw_file[1]}"
            analysis_folder = os.path.join(projects_folder, analysis_configuration[':analysis_name'])
            pathlib.Path(analysis_folder).mkdir(parents=True, exist_ok=True)
            f = open(os.path.join(analysis_folder, "input.yml"), 'w')
            yaml.dump(analysis_configuration, f)
            # Submit analysis
            print(f"Running {analysis_configuration[':analysis_name']}")
            analysis(project_input_folder=analysis_folder,
                     compute_environment=compute_environment,
                     reference_run=True,
                     output_folder=output_folder)

        # General Optimization
        if OPTIMIZATION_RUNS:
            analysis_configuration = copy.deepcopy(sensitivity_template)
            analysis_configuration[':building_type'] = [building_type]
            analysis_configuration[':epw_file'] = [epw_file[0]]
            analysis_configuration[':primary_heating_fuel'] = [
                'NaturalGas',
                'Electricity',
                'ElectricityHPElecBackup',
                'NaturalGasHPGasBackup'
            ]
            analysis_configuration[':output_meters'] = output_meters
            analysis_configuration[':algorithm_type'] = 'nsga2'
            analysis_configuration[':algorithm_nsga_population'] = algorithm_nsga_population
            analysis_configuration[':algorithm_nsga_n_generations'] = algorithm_nsga_n_generations
            analysis_configuration[':algorithm_nsga_prob'] = 0.85
            analysis_configuration[':algorithm_nsga_eta'] = 3.0
            analysis_configuration[':algorithm_nsga_minimize_objectives'] = [
                'energy_eui_total_gj_per_m_sq',
                'npv_total_per_m_sq'
            ]

            analysis_configuration[
                ':analysis_name'] = f"opt_{building_type}_{epw_file[1]}_{analysis_configuration[':primary_heating_fuel'][0]}"
            analysis_folder = os.path.join(projects_folder, analysis_configuration[':analysis_name'])
            pathlib.Path(analysis_folder).mkdir(parents=True, exist_ok=True)
            f = open(os.path.join(analysis_folder, "input.yml"), 'w')
            yaml.dump(analysis_configuration, f)
            # Submit analysis
            print(f"Running  {analysis_configuration[':analysis_name']}")
            analysis(project_input_folder=analysis_folder,
                     compute_environment=compute_environment,
                     reference_run=True,
                     output_folder=output_folder)



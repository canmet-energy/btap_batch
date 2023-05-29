from pathlib import Path
import os
import sys
import pandas as pd
import copy

PROJECT_ROOT = str(Path(os.path.dirname(os.path.realpath(__file__))).parent.parent)

sys.path.append(PROJECT_ROOT)

from src.btap.cli_helper_methods import analysis
from src.btap.btap_analysis import BTAPAnalysis

def generate_yml(
        building_types_list=None,
        epw_files=None,
        hvac_fuel_types_list=None,
        yaml_project_generation_folder=None,
        pop=None,
        generations=None,
):
    import yaml
    # template .yml file for creating all other .yml files
    analysis_config_file = os.path.join(Path(os.path.dirname(os.path.realpath(__file__))).parent.parent, 'resources', 'solutionsets_optimization_template_input.yml')

    analysis_config, analysis_input_folder, analyses_folder = BTAPAnalysis.load_analysis_input_file(
        analysis_config_file=analysis_config_file)

    for hvac_fuel_type_index in range(0, len(hvac_fuel_types_list)):
        hvac_type = hvac_fuel_types_list[hvac_fuel_type_index][0]
        fuel_type = hvac_fuel_types_list[hvac_fuel_type_index][1]
        print('hvac_type is', hvac_type)
        print('fuel_type is', fuel_type)

        if (hvac_type=='NECB_Default') and (fuel_type=='NaturalGas'):
            # ================================================================================================
            # case 1: (set :ecm_system_name as 'NECB_Default') & (set :primary_heating_fuel as 'NaturalGas')
            for location_name in epw_files:


                for building_type_index in range(0, len(building_types_list)):
                    building_name = building_types_list[building_type_index]
                    print('location_name is', location_name)
                    print('building_name', building_name)

                    if building_name in [
                        'MediumOffice',
                        'LargeOffice'
                    ]:
                        # Make a copy of anaylsis_config and use it as template to create all other .yml files
                        template_yml = copy.deepcopy(analysis_config)
                        # Optimization parameters
                        template_yml[':algorithm_nsga_population'] = pop
                        template_yml[':algorithm_nsga_n_generations'] = generations

                        # :building_type
                        template_yml[':options'][':building_type'] = [building_name]
                        # :epw_file
                        template_yml[':options'][':epw_file'] = [location_name]
                        # :ecm_system_name
                        template_yml[':options'][':ecm_system_name'] = [i for i in template_yml[':options'][':ecm_system_name'] if i in ['NECB_Default']] # this removes all inputs except for 'NECB_Default'
                        # :primary_heating_fuel
                        template_yml[':options'][':primary_heating_fuel'] = [i for i in template_yml[':options'][':primary_heating_fuel'] if i in ['NaturalGas']]
                        # yml file name
                        yml_file_name = template_yml[':analysis_name'].replace('_example', '') + '_' + \
                                        template_yml[':options'][':building_type'][0] + '_' + \
                                        location_name + '_' + \
                                        template_yml[':options'][':primary_heating_fuel'][0] + '_' + \
                                        template_yml[':options'][':ecm_system_name'][0]
                        # :analysis_name
                        template_yml[':analysis_name'] = yml_file_name
                        # yml file path
                        Path(os.path.join(Path(yaml_project_generation_folder), yml_file_name)).mkdir(parents=True, exist_ok=True)
                        yml_file_name = os.path.join(Path(yaml_project_generation_folder), yml_file_name, 'input.yml')
                        # save .yml file
                        file = open(yml_file_name, "w")
                        yaml.dump(template_yml, file)
                        file.close()

                    if building_name in [
                        'SmallOffice',
                        'PrimarySchool',
                        'SecondarySchool',
                        'LowriseApartment',
                        'MidriseApartment',
                        'HighriseApartment'
                    ]:
                        # Make a copy of anaylsis_config and use it as template to create all other .yml files
                        template_yml = copy.deepcopy(analysis_config)
                        # :building_type
                        template_yml[':options'][':building_type'] = [building_name]
                        # :epw_file
                        template_yml[':options'][':epw_file'] = [location_name]
                        # :ecm_system_name
                        template_yml[':options'][':ecm_system_name'] = [i for i in template_yml[':options'][':ecm_system_name'] if i in ['NECB_Default']] # this removes all inputs except for 'NECB_Default'
                        # :primary_heating_fuel
                        template_yml[':options'][':primary_heating_fuel'] = [i for i in template_yml[':options'][':primary_heating_fuel'] if i in ['NaturalGas']]
                        # :chiller_type
                        template_yml[':options'][':chiller_type'] = [i for i in template_yml[':options'][':chiller_type'] if i in ['NECB_Default']]
                        # yml file name
                        yml_file_name = template_yml[':analysis_name'].replace('_example', '') + '_' + \
                                        template_yml[':options'][':building_type'][0] + '_' + \
                                        location_name + '_' + \
                                        template_yml[':options'][':primary_heating_fuel'][0] + '_' + \
                                        template_yml[':options'][':ecm_system_name'][0]
                        # :analysis_name
                        template_yml[':analysis_name'] = yml_file_name
                        # yml file path
                        Path(os.path.join(Path(yaml_project_generation_folder), yml_file_name)).mkdir(parents=True, exist_ok=True)

                        yml_file_name = os.path.join(Path(yaml_project_generation_folder), yml_file_name, 'input.yml')
                        # save .yml file
                        file = open(yml_file_name, "w")
                        yaml.dump(template_yml, file)
                        file.close()

        elif (hvac_type == 'NECB_Default') and (fuel_type == 'Electricity'):
            #================================================================================================
            # case 2: (set :ecm_system_name as 'NECB_Default') & (set :primary_heating_fuel as 'Electricity')
            for location_name in epw_files:
                # print('location_name is', location_name)
                # print(location_name)

                for building_type_index in range(0, len(building_types_list)):
                    building_name = building_types_list[building_type_index]

                    if building_name in [
                        'MediumOffice',
                        'LargeOffice'
                    ]:
                        # Make a copy of anaylsis_config and use it as template to create all other .yml files
                        template_yml = copy.deepcopy(analysis_config)
                        # :building_type
                        template_yml[':options'][':building_type'] = [building_name]
                        # :epw_file
                        template_yml[':options'][':epw_file'] = [location_name]
                        # :ecm_system_name
                        template_yml[':options'][':ecm_system_name'] = [i for i in template_yml[':options'][':ecm_system_name'] if i in ['NECB_Default']] # this removes all inputs except for 'NECB_Default'
                        # :primary_heating_fuel
                        template_yml[':options'][':primary_heating_fuel'] = [i for i in template_yml[':options'][':primary_heating_fuel'] if i in ['Electricity']]
                        # :boiler_eff
                        template_yml[':options'][':boiler_eff'] = [i for i in template_yml[':options'][':boiler_eff'] if i in ['NECB_Default']]
                        # :furnace_eff
                        template_yml[':options'][':furnace_eff'] = [i for i in template_yml[':options'][':furnace_eff'] if i in ['NECB_Default']]
                        # :shw_eff
                        template_yml[':options'][':shw_eff'] = [i for i in template_yml[':options'][':shw_eff'] if i in ['NECB_Default']]
                        # yml file name
                        yml_file_name = template_yml[':analysis_name'].replace('_example', '') + '_' + \
                                        template_yml[':options'][':building_type'][0] + '_' + \
                                        location_name + '_' + \
                                        template_yml[':options'][':primary_heating_fuel'][0] + '_' + \
                                        template_yml[':options'][':ecm_system_name'][0]
                        # :analysis_name
                        template_yml[':analysis_name'] = yml_file_name
                        # yml file path
                        Path(os.path.join(Path(yaml_project_generation_folder), yml_file_name)).mkdir(parents=True, exist_ok=True)
                        yml_file_name = os.path.join(Path(yaml_project_generation_folder), yml_file_name, 'input.yml')
                        # save .yml file
                        file = open(yml_file_name, "w")
                        yaml.dump(template_yml, file)
                        file.close()

                    if building_name in [
                        'SmallOffice',
                        'PrimarySchool',
                        'SecondarySchool',
                        'LowriseApartment',
                        'MidriseApartment',
                        'HighriseApartment'
                    ]:
                        # Make a copy of anaylsis_config and use it as template to create all other .yml files
                        template_yml = copy.deepcopy(analysis_config)
                        # :building_type
                        template_yml[':options'][':building_type'] = [building_name]
                        # :epw_file
                        template_yml[':options'][':epw_file'] = [location_name]
                        # :ecm_system_name
                        template_yml[':options'][':ecm_system_name'] = [i for i in template_yml[':options'][':ecm_system_name'] if i in ['NECB_Default']] # this removes all inputs except for 'NECB_Default'
                        # :primary_heating_fuel
                        template_yml[':options'][':primary_heating_fuel'] = [i for i in template_yml[':options'][':primary_heating_fuel'] if i in ['Electricity']]
                        # :chiller_type
                        template_yml[':options'][':chiller_type'] = [i for i in template_yml[':options'][':chiller_type'] if i in ['NECB_Default']]
                        # :boiler_eff
                        template_yml[':options'][':boiler_eff'] = [i for i in template_yml[':options'][':boiler_eff'] if i in ['NECB_Default']]
                        # :furnace_eff
                        template_yml[':options'][':furnace_eff'] = [i for i in template_yml[':options'][':furnace_eff'] if i in ['NECB_Default']]
                        # :shw_eff
                        template_yml[':options'][':shw_eff'] = [i for i in template_yml[':options'][':shw_eff'] if i in ['NECB_Default']]
                        # yml file name
                        yml_file_name = template_yml[':analysis_name'].replace('_example', '') + '_' + \
                                        template_yml[':options'][':building_type'][0] + '_' + \
                                        location_name + '_' + \
                                        template_yml[':options'][':primary_heating_fuel'][0] + '_' + \
                                        template_yml[':options'][':ecm_system_name'][0]
                        # :analysis_name
                        template_yml[':analysis_name'] = yml_file_name
                        # yml file path
                        Path(os.path.join(Path(yaml_project_generation_folder), yml_file_name)).mkdir(parents=True, exist_ok=True)
                        Path(os.path.join(Path(yaml_project_generation_folder), yml_file_name)).mkdir(parents=True, exist_ok=True)
                        yml_file_name = os.path.join(Path(yaml_project_generation_folder), yml_file_name, 'input.yml')
                        # save .yml file
                        file = open(yml_file_name, "w")
                        yaml.dump(template_yml, file)
                        file.close()

        elif (hvac_type == 'HS09_CCASHP_Baseboard') and (fuel_type == 'NaturalGasHPGasBackup'):
            # ================================================================================================
            # case 3: (:ecm_system_name='HS09_CCASHP_Baseboard') & primary_heating_fuel='NaturalGasHPGasBackup'
            for location_name in epw_files:


                for building_type_index in range(0, len(building_types_list)):
                    building_name = building_types_list[building_type_index]

                    if building_name in [
                        'MediumOffice',
                        'LargeOffice',
                        'SmallOffice',
                        'PrimarySchool',
                        'SecondarySchool',
                        'LowriseApartment',
                        'MidriseApartment',
                        'HighriseApartment'
                    ]:
                        # Make a copy of anaylsis_config and use it as template to create all other .yml files
                        template_yml = copy.deepcopy(analysis_config)
                        # :building_type
                        template_yml[':options'][':building_type'] = [building_name]
                        # :epw_file
                        template_yml[':options'][':epw_file'] = [location_name]
                        # :ecm_system_name
                        template_yml[':options'][':ecm_system_name'] = [i for i in template_yml[':options'][':ecm_system_name'] if i in ['HS09_CCASHP_Baseboard']] # this removes all inputs except for 'HS09_CCASHP_Baseboard'
                        # :primary_heating_fuel
                        template_yml[':options'][':primary_heating_fuel'] = [i for i in template_yml[':options'][':primary_heating_fuel'] if i in ['NaturalGasHPGasBackup']]
                        # :adv_dx_units
                        template_yml[':options'][':adv_dx_units'] = [i for i in template_yml[':options'][':adv_dx_units'] if i in ['NECB_Default']]
                        # :chiller_type
                        template_yml[':options'][':chiller_type'] = [i for i in template_yml[':options'][':chiller_type'] if i in ['NECB_Default']]
                        # yml file name
                        yml_file_name = template_yml[':analysis_name'].replace('_example', '') + '_' + \
                                        template_yml[':options'][':building_type'][0] + '_' + \
                                        location_name + '_' + \
                                        template_yml[':options'][':primary_heating_fuel'][0] + '_' + \
                                        template_yml[':options'][':ecm_system_name'][0]
                        # :analysis_name
                        template_yml[':analysis_name'] = yml_file_name
                        # yml file path
                        Path(os.path.join(Path(yaml_project_generation_folder), yml_file_name)).mkdir(parents=True, exist_ok=True)
                        yml_file_name = os.path.join(Path(yaml_project_generation_folder), yml_file_name, 'input.yml')
                        # save .yml file
                        file = open(yml_file_name, "w")
                        yaml.dump(template_yml, file)
                        file.close()

        elif (hvac_type == 'HS09_CCASHP_Baseboard') and (fuel_type == 'ElectricityHPElecBackup'):
            # ================================================================================================
            # case 4: :ecm_system_name='HS09_CCASHP_Baseboard' & primary_heating_fuel='ElectricityHPElecBackup'
            for location_name in epw_files:

                for building_type_index in range(0, len(building_types_list)):
                    building_name = building_types_list[building_type_index]

                    if building_name in [
                        'MediumOffice',
                        'LargeOffice',
                        'SmallOffice',
                        'PrimarySchool',
                        'SecondarySchool',
                        'LowriseApartment',
                        'MidriseApartment',
                        'HighriseApartment'
                    ]:
                        # Make a copy of anaylsis_config and use it as template to create all other .yml files
                        template_yml = copy.deepcopy(analysis_config)
                        # :building_type
                        template_yml[':options'][':building_type'] = [building_name]
                        # :epw_file
                        template_yml[':options'][':epw_file'] = [location_name]
                        # :ecm_system_name
                        template_yml[':options'][':ecm_system_name'] = [i for i in template_yml[':options'][':ecm_system_name'] if i in ['HS09_CCASHP_Baseboard']] # this removes all inputs except for 'HS09_CCASHP_Baseboard'
                        # :primary_heating_fuel
                        template_yml[':options'][':primary_heating_fuel'] = [i for i in template_yml[':options'][':primary_heating_fuel'] if i in ['ElectricityHPElecBackup']]
                        # :boiler_eff
                        template_yml[':options'][':boiler_eff'] = [i for i in template_yml[':options'][':boiler_eff'] if i in ['NECB_Default']]
                        # :furnace_eff
                        template_yml[':options'][':furnace_eff'] = [i for i in template_yml[':options'][':furnace_eff'] if i in ['NECB_Default']]
                        # :shw_eff
                        template_yml[':options'][':shw_eff'] = [i for i in template_yml[':options'][':shw_eff'] if i in ['NECB_Default']]
                        # :adv_dx_units
                        template_yml[':options'][':adv_dx_units'] = [i for i in template_yml[':options'][':adv_dx_units'] if i in ['NECB_Default']]
                        # :chiller_type
                        template_yml[':options'][':chiller_type'] = [i for i in template_yml[':options'][':chiller_type'] if i in ['NECB_Default']]
                        # yml file name
                        yml_file_name = template_yml[':analysis_name'].replace('_example', '') + '_' + \
                                        template_yml[':options'][':building_type'][0] + '_' + \
                                        location_name + '_' + \
                                        template_yml[':options'][':primary_heating_fuel'][0] + '_' + \
                                        template_yml[':options'][':ecm_system_name'][0]
                        # :analysis_name
                        template_yml[':analysis_name'] = yml_file_name
                        # yml file path
                        Path(os.path.join(Path(yaml_project_generation_folder), yml_file_name)).mkdir(parents=True, exist_ok=True)
                        yml_file_name = os.path.join(Path(yaml_project_generation_folder), yml_file_name, 'input.yml')
                        # save .yml file
                        file = open(yml_file_name, "w")
                        yaml.dump(template_yml, file)
                        file.close()

        elif (hvac_type == 'HS08_CCASHP_VRF') and (fuel_type == 'NaturalGasHPGasBackup'):
            # ================================================================================================
            # case 5: :ecm_system_name='HS08_CCASHP_VRF' & primary_heating_fuel='NaturalGasHPGasBackup'
            for location_name in epw_files:
                # print('location_name is', location_name)
                # print(location_name)

                for building_type_index in range(0, len(building_types_list)):
                    building_name = building_types_list[building_type_index]

                    if building_name in [
                        'MediumOffice',
                        'LargeOffice',
                        'SmallOffice',
                        'PrimarySchool',
                        'SecondarySchool',
                        'LowriseApartment',
                        'MidriseApartment',
                        'HighriseApartment'
                    ]:
                        # Make a copy of anaylsis_config and use it as template to create all other .yml files
                        template_yml = copy.deepcopy(analysis_config)
                        # :building_type
                        template_yml[':options'][':building_type'] = [building_name]
                        # :epw_file
                        template_yml[':options'][':epw_file'] = [location_name]
                        # :ecm_system_name
                        template_yml[':options'][':ecm_system_name'] = [i for i in template_yml[':options'][':ecm_system_name'] if i in ['HS08_CCASHP_VRF']] # this removes all inputs except for 'HS08_CCASHP_VRF'
                        # :primary_heating_fuel
                        template_yml[':options'][':primary_heating_fuel'] = [i for i in template_yml[':options'][':primary_heating_fuel'] if i in ['NaturalGasHPGasBackup']]
                        # :adv_dx_units
                        template_yml[':options'][':adv_dx_units'] = [i for i in template_yml[':options'][':adv_dx_units'] if i in ['NECB_Default']]
                        # :chiller_type
                        template_yml[':options'][':chiller_type'] = [i for i in template_yml[':options'][':chiller_type'] if i in ['NECB_Default']]
                        # :airloop_economizer_type
                        template_yml[':options'][':airloop_economizer_type'] = [i for i in template_yml[':options'][':airloop_economizer_type'] if i in ['NECB_Default']]
                        # yml file name
                        yml_file_name = template_yml[':analysis_name'].replace('_example', '') + '_' + \
                                        template_yml[':options'][':building_type'][0] + '_' + \
                                        location_name + '_' + \
                                        template_yml[':options'][':primary_heating_fuel'][0] + '_' + \
                                        template_yml[':options'][':ecm_system_name'][0]
                        # :analysis_name
                        template_yml[':analysis_name'] = yml_file_name
                        # yml file path
                        Path(os.path.join(Path(yaml_project_generation_folder), yml_file_name)).mkdir(parents=True, exist_ok=True)
                        yml_file_name = os.path.join(Path(yaml_project_generation_folder), yml_file_name, 'input.yml')
                        # save .yml file
                        file = open(yml_file_name, "w")
                        yaml.dump(template_yml, file)
                        file.close()

        elif (hvac_type == 'HS08_CCASHP_VRF') and (fuel_type == 'ElectricityHPElecBackup'):
            # ================================================================================================
            # case 6: :ecm_system_name='HS08_CCASHP_VRF' & primary_heating_fuel='ElectricityHPElecBackup'
            for location_name in epw_files:
                # print('location_name is', location_name)
                # print(location_name)

                for building_type_index in range(0, len(building_types_list)):
                    building_name = building_types_list[building_type_index]

                    if building_name in [
                        'MediumOffice',
                        'LargeOffice',
                        'SmallOffice',
                        'PrimarySchool',
                        'SecondarySchool',
                        'LowriseApartment',
                        'MidriseApartment',
                        'HighriseApartment'
                    ]:
                        # Make a copy of anaylsis_config and use it as template to create all other .yml files
                        template_yml = copy.deepcopy(analysis_config)
                        # :building_type
                        template_yml[':options'][':building_type'] = [building_name]
                        # :epw_file
                        template_yml[':options'][':epw_file'] = [location_name]
                        # :ecm_system_name
                        template_yml[':options'][':ecm_system_name'] = [i for i in template_yml[':options'][':ecm_system_name'] if i in ['HS08_CCASHP_VRF']] # this removes all inputs except for 'HS08_CCASHP_VRF'
                        # :primary_heating_fuel
                        template_yml[':options'][':primary_heating_fuel'] = [i for i in template_yml[':options'][':primary_heating_fuel'] if i in ['ElectricityHPElecBackup']]
                        # :boiler_eff
                        template_yml[':options'][':boiler_eff'] = [i for i in template_yml[':options'][':boiler_eff'] if i in ['NECB_Default']]
                        # :furnace_eff
                        template_yml[':options'][':furnace_eff'] = [i for i in template_yml[':options'][':furnace_eff'] if i in ['NECB_Default']]
                        # :shw_eff
                        template_yml[':options'][':shw_eff'] = [i for i in template_yml[':options'][':shw_eff'] if i in ['NECB_Default']]
                        # :adv_dx_units
                        template_yml[':options'][':adv_dx_units'] = [i for i in template_yml[':options'][':adv_dx_units'] if i in ['NECB_Default']]
                        # :chiller_type
                        template_yml[':options'][':chiller_type'] = [i for i in template_yml[':options'][':chiller_type'] if i in ['NECB_Default']]
                        # :airloop_economizer_type
                        template_yml[':options'][':airloop_economizer_type'] = [i for i in template_yml[':options'][':airloop_economizer_type'] if i in ['NECB_Default']]
                        # yml file name
                        yml_file_name = template_yml[':analysis_name'].replace('_example', '') + '_' + \
                                        template_yml[':options'][':building_type'][0] + '_' + \
                                        location_name + '_' + \
                                        template_yml[':options'][':primary_heating_fuel'][0] + '_' + \
                                        template_yml[':options'][':ecm_system_name'][0]
                        # :analysis_name
                        template_yml[':analysis_name'] = yml_file_name
                        # yml file path
                        Path(os.path.join(Path(yaml_project_generation_folder), yml_file_name)).mkdir(parents=True, exist_ok=True)
                        yml_file_name = os.path.join(Path(yaml_project_generation_folder), yml_file_name, 'input.yml')
                        # save .yml file
                        file = open(yml_file_name, "w")
                        yaml.dump(template_yml, file)
                        file.close()

        elif (hvac_type == 'HS11_ASHP_PTHP') and (fuel_type == 'NaturalGasHPGasBackup'):
            # ================================================================================================
            # case 7: :ecm_system_name='HS11_ASHP_PTHP' & primary_heating_fuel='NaturalGasHPGasBackup'
            for location_name in epw_files:
                # print('location_name is', location_name)
                # print(location_name)

                for building_type_index in range(0, len(building_types_list)):
                    building_name = building_types_list[building_type_index]

                    if building_name in [
                        'MediumOffice',
                        'LargeOffice',
                        'SmallOffice',
                        'PrimarySchool',
                        'SecondarySchool',
                        'LowriseApartment',
                        'MidriseApartment',
                        'HighriseApartment'
                    ]:
                        # Make a copy of anaylsis_config and use it as template to create all other .yml files
                        template_yml = copy.deepcopy(analysis_config)
                        # :building_type
                        template_yml[':options'][':building_type'] = [building_name]
                        # :epw_file
                        template_yml[':options'][':epw_file'] = [location_name]
                        # :ecm_system_name
                        template_yml[':options'][':ecm_system_name'] = [i for i in template_yml[':options'][':ecm_system_name'] if i in ['HS11_ASHP_PTHP']] # this removes all inputs except for 'HS11_ASHP_PTHP'
                        # :primary_heating_fuel
                        template_yml[':options'][':primary_heating_fuel'] = [i for i in template_yml[':options'][':primary_heating_fuel'] if i in ['NaturalGasHPGasBackup']]
                        # :boiler_eff
                        template_yml[':options'][':boiler_eff'] = [i for i in template_yml[':options'][':boiler_eff'] if i in ['NECB_Default']]
                        # :adv_dx_units
                        template_yml[':options'][':adv_dx_units'] = [i for i in template_yml[':options'][':adv_dx_units'] if i in ['NECB_Default']]
                        # :chiller_type
                        template_yml[':options'][':chiller_type'] = [i for i in template_yml[':options'][':chiller_type'] if i in ['NECB_Default']]
                        # :airloop_economizer_type
                        template_yml[':options'][':airloop_economizer_type'] = [i for i in template_yml[':options'][':airloop_economizer_type'] if i in ['NECB_Default']]
                        # yml file name
                        yml_file_name = template_yml[':analysis_name'].replace('_example', '') + '_' + \
                                        template_yml[':options'][':building_type'][0] + '_' + \
                                        location_name + '_' + \
                                        template_yml[':options'][':primary_heating_fuel'][0] + '_' + \
                                        template_yml[':options'][':ecm_system_name'][0]
                        # :analysis_name
                        template_yml[':analysis_name'] = yml_file_name
                        # yml file path
                        Path(os.path.join(Path(yaml_project_generation_folder), yml_file_name)).mkdir(parents=True, exist_ok=True)
                        yml_file_name = os.path.join(Path(yaml_project_generation_folder), yml_file_name, 'input.yml')
                        # save .yml file
                        file = open(yml_file_name, "w")
                        yaml.dump(template_yml, file)
                        file.close()

        elif (hvac_type == 'HS11_ASHP_PTHP') and (fuel_type == 'ElectricityHPElecBackup'):
            # ================================================================================================
            # case 8: :ecm_system_name='HS11_ASHP_PTHP' & primary_heating_fuel='ElectricityHPElecBackup'
            for location_name in epw_files:
                # print('location_name is', location_name)
                # print(location_name)

                for building_type_index in range(0, len(building_types_list)):
                    building_name = building_types_list[building_type_index]

                    if building_name in [
                        'MediumOffice',
                        'LargeOffice',
                        'SmallOffice',
                        'PrimarySchool',
                        'SecondarySchool',
                        'LowriseApartment',
                        'MidriseApartment',
                        'HighriseApartment'
                    ]:
                        # Make a copy of anaylsis_config and use it as template to create all other .yml files
                        template_yml = copy.deepcopy(analysis_config)
                        # :building_type
                        template_yml[':options'][':building_type'] = [building_name]
                        # :epw_file
                        template_yml[':options'][':epw_file'] = [location_name]
                        # :ecm_system_name
                        template_yml[':options'][':ecm_system_name'] = [i for i in template_yml[':options'][':ecm_system_name'] if i in ['HS11_ASHP_PTHP']] # this removes all inputs except for 'HS11_ASHP_PTHP'
                        # :primary_heating_fuel
                        template_yml[':options'][':primary_heating_fuel'] = [i for i in template_yml[':options'][':primary_heating_fuel'] if i in ['ElectricityHPElecBackup']]
                        # :boiler_eff
                        template_yml[':options'][':boiler_eff'] = [i for i in template_yml[':options'][':boiler_eff'] if i in ['NECB_Default']]
                        # :furnace_eff
                        template_yml[':options'][':furnace_eff'] = [i for i in template_yml[':options'][':furnace_eff'] if i in ['NECB_Default']]
                        # :shw_eff
                        template_yml[':options'][':shw_eff'] = [i for i in template_yml[':options'][':shw_eff'] if i in ['NECB_Default']]
                        # :adv_dx_units
                        template_yml[':options'][':adv_dx_units'] = [i for i in template_yml[':options'][':adv_dx_units'] if i in ['NECB_Default']]
                        # :chiller_type
                        template_yml[':options'][':chiller_type'] = [i for i in template_yml[':options'][':chiller_type'] if i in ['NECB_Default']]
                        # :airloop_economizer_type
                        template_yml[':options'][':airloop_economizer_type'] = [i for i in template_yml[':options'][':airloop_economizer_type'] if i in ['NECB_Default']]
                        # yml file name
                        yml_file_name = template_yml[':analysis_name'].replace('_example', '') + '_' + \
                                        template_yml[':options'][':building_type'][0] + '_' + \
                                        location_name + '_' + \
                                        template_yml[':options'][':primary_heating_fuel'][0] + '_' + \
                                        template_yml[':options'][':ecm_system_name'][0]
                        # :analysis_name
                        template_yml[':analysis_name'] = yml_file_name
                        # yml file path
                        Path(os.path.join(Path(yaml_project_generation_folder), yml_file_name)).mkdir(parents=True, exist_ok=True)
                        yml_file_name = os.path.join(Path(yaml_project_generation_folder), yml_file_name, 'input.yml')
                        # save .yml file
                        file = open(yml_file_name, "w")
                        yaml.dump(template_yml, file)
                        file.close()

        elif (hvac_type == 'HS13_ASHP_VRF') and (fuel_type == 'NaturalGasHPGasBackup'):
            # ================================================================================================
            # case 9: :ecm_system_name='HS13_ASHP_VRF' & primary_heating_fuel='NaturalGasHPGasBackup'
            for location_name in epw_files:
                # print('location_name is', location_name)
                # print(location_name)

                for building_type_index in range(0, len(building_types_list)):
                    building_name = building_types_list[building_type_index]

                    if building_name in [
                        'MediumOffice',
                        'LargeOffice',
                        'SmallOffice',
                        'PrimarySchool',
                        'SecondarySchool',
                        'LowriseApartment',
                        'MidriseApartment',
                        'HighriseApartment'
                    ]:
                        # Make a copy of anaylsis_config and use it as template to create all other .yml files
                        template_yml = copy.deepcopy(analysis_config)
                        # :building_type
                        template_yml[':options'][':building_type'] = [building_name]
                        # :epw_file
                        template_yml[':options'][':epw_file'] = [location_name]
                        # :ecm_system_name
                        template_yml[':options'][':ecm_system_name'] = [i for i in template_yml[':options'][':ecm_system_name'] if i in ['HS13_ASHP_VRF']] # this removes all inputs except for 'HS13_ASHP_VRF'
                        # :primary_heating_fuel
                        template_yml[':options'][':primary_heating_fuel'] = [i for i in template_yml[':options'][':primary_heating_fuel'] if i in ['NaturalGasHPGasBackup']]
                        # :adv_dx_units
                        template_yml[':options'][':adv_dx_units'] = [i for i in template_yml[':options'][':adv_dx_units'] if i in ['NECB_Default']]
                        # :chiller_type
                        template_yml[':options'][':chiller_type'] = [i for i in template_yml[':options'][':chiller_type'] if i in ['NECB_Default']]
                        # :airloop_economizer_type
                        template_yml[':options'][':airloop_economizer_type'] = [i for i in template_yml[':options'][':airloop_economizer_type'] if i in ['NECB_Default']]
                        # yml file name
                        yml_file_name = template_yml[':analysis_name'].replace('_example', '') + '_' + \
                                        template_yml[':options'][':building_type'][0] + '_' + \
                                        location_name + '_' + \
                                        template_yml[':options'][':primary_heating_fuel'][0] + '_' + \
                                        template_yml[':options'][':ecm_system_name'][0]
                        # :analysis_name
                        template_yml[':analysis_name'] = yml_file_name
                        # yml file path
                        Path(os.path.join(Path(yaml_project_generation_folder), yml_file_name)).mkdir(parents=True, exist_ok=True)
                        yml_file_name = os.path.join(Path(yaml_project_generation_folder), yml_file_name, 'input.yml')
                        # save .yml file
                        file = open(yml_file_name, "w")
                        yaml.dump(template_yml, file)
                        file.close()

        elif (hvac_type == 'HS13_ASHP_VRF') and (fuel_type == 'ElectricityHPElecBackup'):
            # ================================================================================================
            # case 10: :ecm_system_name='HS13_ASHP_VRF' & primary_heating_fuel='ElectricityHPElecBackup'
            for location_name in epw_files:
                # print('location_name is', location_name)
                # print(location_name)

                for building_type_index in range(0, len(building_types_list)):
                    building_name = building_types_list[building_type_index]

                    if building_name in [
                        'MediumOffice',
                        'LargeOffice',
                        'SmallOffice',
                        'PrimarySchool',
                        'SecondarySchool',
                        'LowriseApartment',
                        'MidriseApartment',
                        'HighriseApartment'
                    ]:
                        # Make a copy of anaylsis_config and use it as template to create all other .yml files
                        template_yml = copy.deepcopy(analysis_config)
                        # :building_type
                        template_yml[':options'][':building_type'] = [building_name]
                        # :epw_file
                        template_yml[':options'][':epw_file'] = [location_name]
                        # :ecm_system_name
                        template_yml[':options'][':ecm_system_name'] = [i for i in template_yml[':options'][':ecm_system_name'] if i in ['HS13_ASHP_VRF']] # this removes all inputs except for 'HS13_ASHP_VRF'
                        # :primary_heating_fuel
                        template_yml[':options'][':primary_heating_fuel'] = [i for i in template_yml[':options'][':primary_heating_fuel'] if i in ['ElectricityHPElecBackup']]
                        # :boiler_eff
                        template_yml[':options'][':boiler_eff'] = [i for i in template_yml[':options'][':boiler_eff'] if i in ['NECB_Default']]
                        # :furnace_eff
                        template_yml[':options'][':furnace_eff'] = [i for i in template_yml[':options'][':furnace_eff'] if i in ['NECB_Default']]
                        # :shw_eff
                        template_yml[':options'][':shw_eff'] = [i for i in template_yml[':options'][':shw_eff'] if i in ['NECB_Default']]
                        # :adv_dx_units
                        template_yml[':options'][':adv_dx_units'] = [i for i in template_yml[':options'][':adv_dx_units'] if i in ['NECB_Default']]
                        # :chiller_type
                        template_yml[':options'][':chiller_type'] = [i for i in template_yml[':options'][':chiller_type'] if i in ['NECB_Default']]
                        # :airloop_economizer_type
                        template_yml[':options'][':airloop_economizer_type'] = [i for i in template_yml[':options'][':airloop_economizer_type'] if i in ['NECB_Default']]
                        # yml file name
                        yml_file_name = template_yml[':analysis_name'].replace('_example', '') + '_' + \
                                        template_yml[':options'][':building_type'][0] + '_' + \
                                        location_name + '_' + \
                                        template_yml[':options'][':primary_heating_fuel'][0] + '_' + \
                                        template_yml[':options'][':ecm_system_name'][0]
                        # :analysis_name
                        template_yml[':analysis_name'] = yml_file_name
                        # yml file path
                        Path(os.path.join(Path(yaml_project_generation_folder), yml_file_name)).mkdir(parents=True, exist_ok=True)
                        yml_file_name = os.path.join(Path(yaml_project_generation_folder), yml_file_name, 'input.yml')
                        # save .yml file
                        file = open(yml_file_name, "w")
                        yaml.dump(template_yml, file)
                        file.close()

    # ================================================================================================



#=======================================================================================================================


##### The below method creates all .yml files and run them
def generate_solution_sets(
    compute_environment='local_docker',
    building_types_list=["SmallOffice"],
    epw_files=['CAN_BC_Vancouver.Intl.AP.718920_CWEC2016.epw'],
    hvac_fuel_types_list=[['NECB_Default','NaturalGas']],
    yaml_project_generation_folder= "C:/test/yaml",
    pop=35,
    generations=2,
    simulation_results_folder="C:/test/runs",
    run_analyses = True
):

    # Call the function that creates all the analyses project folders and input.yml file associated with each folder
    generate_yml(
        building_types_list=building_types_list, # a list of the building_types to look at.
        epw_files=epw_files, # a dictionary of the locations and associated epw files.
        hvac_fuel_types_list=hvac_fuel_types_list,
        yaml_project_generation_folder=yaml_project_generation_folder,
        pop=pop,
        generations=generations,
    )
    print( locals() )

    ##### Do 'analysis' for each input.yml file under the 'solution_set_input_folder' folder
    if run_analyses:
        for filename in os.listdir(Path(yaml_project_generation_folder)):

            project_input_folder = os.path.join(Path(yaml_project_generation_folder), filename)
            output_folder = os.path.join(Path(simulation_results_folder))
            analysis(
                project_input_folder=project_input_folder,
                compute_environment=compute_environment,
                reference_run=True,
                output_folder=output_folder
            )



def post_process_analyses(solution_sets_raw_results_folder = "",
                          post_processed_output_folder = None,
                          aws_database = True):

    # Need error checking on paths.
    if aws_database == False and solution_sets_raw_results_folder == "":
        print("solution sets local folder does not exists")
        exit(1)

    solution_set_output_folder = os.path.join(post_processed_output_folder, 'analyses')
    from src.btap.aws_dynamodb import AWSResultsTable
    ##### Postprocess output files START

    output_folder_names_list = []

    # Get list of :analysis_name performed.
    # If using AWS database
    if aws_database == True:
        from src.btap.aws_dynamodb import AWSResultsTable
        results_df = AWSResultsTable().dump_table(folder_path=post_processed_output_folder, type='csv', analysis_name=None, save_output=True)
        output_folder_names_list = (sorted(results_df[':analysis_name'].unique()))

    # If using local_docker
    else:
        for output_folder_name in os.listdir(Path(solution_sets_raw_results_folder)):
            output_folder_names_list.append(output_folder_name)


    for output_folder_name in output_folder_names_list:
        # print('output_folder_name is', output_folder_name)
        df_prop = []
        file_name_prop = os.path.join(Path(solution_set_output_folder), output_folder_name, 'nsga2', 'results',
                                      'output.xlsx')

        if aws_database == True:
        # ==================================================================================================================
        ### Read output results file of proposed buildings of the folder

            df_prop = results_df.loc[results_df[':analysis_name'] == output_folder_name]

        else:

            # print('file_name_prop is', file_name_prop)
            df_prop = pd.read_excel(file_name_prop)

        # print('df_prop_unmet_hours_cooling is', df_prop['unmet_hours_cooling'])
        # ==================================================================================================================
        ### Find which datapoints meet NECB's requirement for cooling unmet hours
        from decimal import Decimal
        unmet_hours_cooling_threshold = df_prop['baseline_unmet_hours_cooling'] + df_prop[
            'baseline_unmet_hours_cooling'] * Decimal(0.10)
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
        df_prop['baseline_energy_percent_better'] = df_prop.astype({'baseline_energy_percent_better': 'float64'}).dtypes
        print(df_prop.dtypes['baseline_energy_percent_better'])
        # print('bins are', bins)
        df_prop['bin_baseline_energy_percent_better'] = pd.cut(df_prop['baseline_energy_percent_better'], bins)
        # print(df_prop['bin_baseline_energy_percent_better'])
        # print(type(df_prop['bin_baseline_energy_percent_better'][0]))


        # save as .xlsx file
        excel_path = Path(os.path.join(Path(solution_set_output_folder), output_folder_name, 'nsga2', 'results',
                     'output_processed.xlsx'))
        excel_path.parent.absolute().mkdir(parents=True, exist_ok=True)
        df_prop.to_excel(excel_path,index=False)

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
        df_merged = pd.concat(map(pd.read_excel, [file_name_prop.replace('.xlsx', '_processed.xlsx'),
                                                  file_name_prop.replace('.xlsx', '_packages.xlsx')]),
                              ignore_index=True)

        df_merged.to_excel(file_name_prop.replace('.xlsx', '_postprocess.xlsx'), index=False)

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
    output_folder_names_list = []
    for output_folder_name in os.listdir(Path(solution_set_output_folder)):
        output_folder_names_list.append(output_folder_name)
    # print('output_folder_names_list is', output_folder_names_list)
    file_number = 0.0
    for output_folder_name in output_folder_names_list:
        # print('output_folder_name is', output_folder_name)
        ### Read output_processed.xlsx file of proposed buildings of 'output_folder_name' folder
        df = []
        file_name = os.path.join(Path(solution_set_output_folder), output_folder_name, 'nsga2', 'results',
                                 'output_postprocess.xlsx')
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



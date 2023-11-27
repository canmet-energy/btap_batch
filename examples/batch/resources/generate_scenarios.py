import copy
import os
import yaml
import re

pwd = (os.path.dirname(os.path.realpath(__file__)))
# Load yml file into memory

from pathlib import Path
file = os.path.join(pwd, '..', 'resources', 'template.yml')
template = yaml.safe_load(Path(file).read_text())
# Iterage through building_type
for building_type in ['LowriseApartment',
                      'MidriseApartment',
                      'HighriseApartment']:
    for epw_file in [
     'CAN_QC_Montreal-Trudeau.Intl.AP.716270_CWEC2016.epw',
     'CAN_AB_Edmonton.Intl.AP.711230_CWEC2016.epw',
     'CAN_BC_Vancouver.Intl.AP.718920_CWEC2016.epw',
     'CAN_AB_Calgary.Intl.AP.718770_CWEC2016.epw',
     'CAN_ON_Toronto.Pearson.Intl.AP.716240_CWEC2016.epw'
    ]:
        for primary_heating_fuel in [
            'Electricity',
            'NaturalGas',
            'NaturalGasHPGasBackup',
            'ElectricityHPElecBackup'
        ]:
            new_run_options = copy.deepcopy(template)
            new_run_options[':building_type'] = building_type
            new_run_options[':epw_file'] = epw_file
            new_run_options[':primary_heating_fuel'] = primary_heating_fuel
            epw_short = re.search(r"CAN_(\w*_\w*).*", epw_file).group(1)
            new_run_options[':datapoint_name'] = f"{building_type}_{epw_short}_{primary_heating_fuel}"
            f = open(os.path.join(pwd, '..', 'run_options_folder', f"{new_run_options[':datapoint_name']}.yml"), 'w')
            yaml.dump(new_run_options,f)





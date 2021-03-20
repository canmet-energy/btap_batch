import src.btap_batch as btap
import os
import logging
import yaml
from datetime import date
import re


# Displays logging.. Set to INFO or DEBUG for a more verbose output.
logging.basicConfig(level=logging.ERROR)
OPTIONS_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'options.yml')
building_types =  [
      'MidriseApartment',
      'HighriseApartment',
  ]

epw_files = [
      'CAN_QC_Montreal-Trudeau.Intl.AP.716270_CWEC2016.epw',
      'CAN_NS_Halifax.Dockyard.713280_CWEC2016.epw',
      'CAN_AB_Edmonton.Intl.AP.711230_CWEC2016.epw',
      'CAN_BC_Vancouver.Intl.AP.718920_CWEC2016.epw',
      'CAN_AB_Calgary.Intl.AP.718770_CWEC2016.epw',
      'CAN_ON_Toronto.Pearson.Intl.AP.716240_CWEC2016.epw',
      'CAN_YT_Whitehorse.Intl.AP.719640_CWEC2016.epw'
  ]

primary_heating_fuels =  [
    "Electricity",
    "NaturalGas"
]

# Optimization data block.
optimization = {
                ":type": "nsga2",
                ":population": 12,
                ":n_generations": 1,
                ":prob": 0.85,
                ":eta": 3.0,
                ":minimize_objectives": [
                    "cost_utility_neb_total_cost_per_m_sq",
                    "cost_equipment_total_cost_per_m_sq"]
}

for epw_file in epw_files:
    short_city_name = re.compile("(.*?)\.").search(epw_file)[1]
    for building_type in building_types:
        for primary_heating_fuel in primary_heating_fuels:
            # Open the yaml in analysis dict.
            with open(OPTIONS_FILE, 'r') as stream:
                analysis = yaml.safe_load(stream)
            analysis[':analysis_configuration'][':algorithm'] = optimization
            analysis[':analysis_configuration'][':analysis_name'] = f"{short_city_name}_{building_type}_{primary_heating_fuel}"
            analysis[':analysis_configuration'][':kill_database'] = False
            analysis[':building_options'][':epw_file'] = [epw_file]
            analysis[':building_options'][':building_type'] = [building_type]
            analysis[':building_options'][':primary_heating_fuel'] = [primary_heating_fuel]
            print(analysis[':analysis_configuration'][':analysis_name'])
            input_file = os.path.join(os.path.dirname(os.path.realpath(__file__)),f"{analysis[':analysis_configuration'][':analysis_name']}.yml")
            with open(input_file, 'w') as outfile:
                 yaml.dump(analysis, outfile)
            analysis = btap.btap_batch( analysis_config_file=input_file, git_api_token=os.environ['GIT_API_TOKEN'])
            analysis.run()

#output all data from database.
database = btap.BTAPDatabase()
output_folder = os.path.join(os.path.dirname(os.path.realpath(__file__)))
database.generate_output_files( analysis_id = None, output_folder = output_folder)



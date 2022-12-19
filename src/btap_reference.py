import copy
import logging
from .btap_parametric import BTAPParametric

# Class to run reference simulations.. Based on building_type, epw_file, primary_heating_fuel_type


class BTAPReference(BTAPParametric):
    def compute_scenarios(self):
        # Create default options scenario. Uses first value of all arrays.
        # precheck osm files for errors.
        osm_files = {}
        all_osm_files = self.get_local_osm_files()
        for bt in self.building_options[':building_type']:
            for fuel_type in self.building_options[':primary_heating_fuel']:
                for epw in self.building_options[':epw_file']:
                    for template in self.building_options[':template']:
                        run_option = copy.deepcopy(self.building_options)
                        # Set all options to nil/none.
                        for key, value in self.building_options.items():
                            run_option[key] = None
                        run_option[':epw_file'] = epw
                        run_option[':algorithm_type'] = self.analysis_config[':algorithm'][':type']
                        run_option[':template'] = template
                        run_option[':primary_heating_fuel'] = fuel_type
                        # set osm file to pretest..if any.
                        run_option[':building_type'] = bt
                        self.scenarios.append(run_option)
        message = f'Number of Scenarios {len(self.scenarios)}'
        logging.info(message)
        return self.scenarios

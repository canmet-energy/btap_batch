import copy
import logging
from .btap_parametric import BTAPParametric

# Class to run reference simulations.. Based on building_type, epw_file, primary_heating_fuel_type


class BTAPReference(BTAPParametric):
    def compute_scenarios(self):
        # Create default options scenario. Uses first value of all arrays.
        for bt in self.engine.building_options[':building_type']:
            for fuel_type in self.engine.building_options[':primary_heating_fuel']:
                for epw in self.engine.building_options[':epw_file']:
                    for template in self.engine.building_options[':template']:
                        run_option = copy.deepcopy(self.engine.building_options)
                        # Set all options to nil/none.
                        for key, value in self.engine.building_options.items():
                            run_option[key] = None
                        run_option[':epw_file'] = epw
                        run_option[':algorithm_type'] = self.engine.analysis_config[':algorithm'][':type']
                        run_option[':template'] = template
                        run_option[':primary_heating_fuel'] = fuel_type
                        # set osm file to pretest..if any.
                        run_option[':building_type'] = bt
                        self.scenarios.append(run_option)
        message = f'Number of Scenarios {len(self.scenarios)}'
        logging.info(message)
        return self.scenarios

import copy
import logging
from .btap_parametric import BTAPParametric

# Class to manage Sensitivity analysis


class BTAPSensitivity(BTAPParametric):
    def compute_scenarios(self):
        # Create default options scenario. Uses first value of all arrays.
        default_options = copy.deepcopy(self.options)
        for key, value in self.options.items():
            default_options[key] = value[0]
        # Create scenario
        for key, value in self.options.items():
            # If more than one option. Iterate, create run_option for each one.
            if isinstance(value, list) and len(value) > 1:
                for item in value:
                    run_option = copy.deepcopy(default_options)
                    run_option[':algorithm_type'] = self.algorithm_type
                    run_option[key] = item
                    run_option[':scenario'] = key
                    # append scenario to list.
                    self.scenarios.append(run_option)
        message = f'Number of Scenarios {len(self.scenarios)}'
        logging.info(message)
        return self.scenarios

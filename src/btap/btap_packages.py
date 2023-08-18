import copy
import logging
from src.btap.btap_parametric import BTAPParametric
from .btap_parametric import BTAPParametric
class BTAPPackages(BTAPParametric):

    def add_packages(self, packages = None):
        # Create default options scenario. Uses first value of all arrays.
        for run_option in packages:
            run_option[':algorithm_type'] = 'sensitivity_best_packages'
            self.scenarios.append(run_option)

    def compute_scenarios(self):
        message = f'Number of Scenarios {len(self.scenarios)}'
        logging.info(message)
        return self.scenarios
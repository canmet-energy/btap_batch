import copy
import logging
from src.btap.btap_parametric import BTAPParametric


# Class to run reference simulations.. Based on building_type, epw_file, primary_heating_fuel_type


class BTAPReference(BTAPParametric):
    def compute_scenarios(self):
        # Create default options scenario. Uses first value of all arrays.
        for bt in self.options[':building_type']:
            for fuel_type in [
                                'Electricity',
                                'NaturalGas',
                                'NaturalGasHPGasBackup',
                                'NaturalGasHPElecBackupMixed',
                                'ElectricityHPElecBackup',
                                'ElectricityHPGasBackupMixed'
                              ]:
                for epw in self.options[':epw_file']:
                    for template in self.options[':template']:
                        run_option = copy.deepcopy(self.options)
                        # Set all options to nil/none.
                        for key, value in self.options.items():
                            run_option[key] = None
                        run_option[':epw_file'] = epw
                        run_option[':algorithm_type'] = 'reference'
                        run_option[':template'] = template
                        run_option[':primary_heating_fuel'] = fuel_type
                        run_option[':building_type'] = bt
                        self.scenarios.append(run_option)
        message = f'Number of reference scenarios {len(self.scenarios)}'
        logging.info(message)
        return self.scenarios

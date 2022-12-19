import copy
import logging
from .btap_parametric import BTAPParametric

# Class to manage Elimination analysis
class BTAPElimination(BTAPParametric):

    def compute_scenarios(self):
        self.elimination_parameters = [
            [':reference', 'do nothing'],
            [':electrical_loads_scale', '0.0'],
            [':infiltration_scale', '0.0'],
            [':lights_scale', '0.0'],
            [':oa_scale', '0.0'],
            [':occupancy_loads_scale', '0.0'],
            [':shw_scale', '0.0'],
            [':ext_wall_cond', '0.01'],
            [':ext_roof_cond', '0.01'],
            [':ground_floor_cond', '0.01'],
            [':ground_wall_cond', '0.01'],
            [':fixed_window_cond', '0.01'],
            [':fixed_wind_solar_trans', '0.01']
        ]

        building_options = copy.deepcopy(self.building_options)
        for key, value in building_options.items():
            if isinstance(value, list) and len(value) >= 1:
                building_options[key] = value[0]
        # Replace key value with elimination value.
        for elimination_parameter in self.elimination_parameters:
            run_option = copy.deepcopy(building_options)
            run_option[':algorithm_type'] = self.analysis_config[':algorithm'][':type']
            if elimination_parameter[0] != ':reference':
                run_option[elimination_parameter[0]] = elimination_parameter[1]
            run_option[':scenario'] = elimination_parameter[0]
            self.scenarios.append(run_option)
        message = f'Number of Scenarios {len(self.scenarios)}'
        logging.info(message)
        return self.scenarios

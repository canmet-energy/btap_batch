from skopt.space import Space
from skopt.sampler import Lhs
import numpy as np
from .btap_parametric import BTAPParametric


# Class to manage lhs runs. Uses Scipy.. Please see link for options explanation
# https://scikit-optimize.github.io/stable/auto_examples/sampler/initial-sampling-method.html
class BTAPSamplingLHS(BTAPParametric):
    def compute_scenarios(self):
        # This method converts the options for each ecm as an int. This allows for strings and numbers to use the same
        # approach for optimization.
        self.create_options_encoder()
        # lower bound of all options (should be zero)
        xl = [0] * self.number_of_variables()
        # Upper bound.
        xu = self.x_u()
        # create ranges for each ecm and create the Space object.
        space = Space(list(map(lambda x, y: (x, y), xl, xu)))
        # set random seed.

        np.random.seed(self.analysis_config[':algorithm'][':random_seed'])

        # Create the lhs algorithm.
        lhs = Lhs(lhs_type=self.analysis_config[':algorithm'][':lhs_type'], criterion=None)
        # Get samples
        samples = lhs.generate(space.dimensions, n_samples=self.analysis_config[':algorithm'][':n_samples'])
        # create run_option for each scenario.
        for x in samples:
            # Converts discrete integers contains in x argument back into values that btap understands. So for example. if x was a list
            # of zeros, it would convert this to the dict of the first item in each list of the variables in the building_options
            # section of the input yml file.
            run_options = self.generate_run_option_file(x)
            run_options[':scenario'] = 'lhs'
            self.scenarios.append(run_options)
        return self.scenarios


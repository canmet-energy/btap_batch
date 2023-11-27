
import os
import yaml
import logging
from src.btap.btap_parametric import BTAPParametric
from icecream import ic
import glob
import pandas as pd

# Class to manage Sensitivity analysis

class BTAPBatchAnalysis(BTAPParametric):
    def compute_scenarios(self):
        run_options_folder = os.path.join(self.cp.project_input_folder, 'run_options_folder')

        yml_files = glob.glob(os.path.join(run_options_folder, '*.yml'))
        for file in yml_files:
            try:
                ic(file)
                from pathlib import Path
                self.scenarios.append(yaml.safe_load(Path(file).read_text()))
            except yaml.YAMLError as e:
                print(e)
        message = f'Number of Scenarios {len(self.scenarios)}'
        logging.info(message)
        excel_run_options_file = os.path.join(run_options_folder,"run_options.xlsx")
        pd.DataFrame(self.scenarios).to_excel(excel_run_options_file)
        return self.scenarios

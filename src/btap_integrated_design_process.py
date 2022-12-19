import copy
import os
import pandas as pd
from .btap_optimization import BTAPOptimization
from .btap_elimination import BTAPElimination
from .btap_sensitivity import BTAPSensitivity

# Class to manage IDP runs with group elimination,sensitivity and optimization runs.
class BTAPIntegratedDesignProcess:
    def __init__(self,
                 analysis_config=None,
                 building_options=None,
                 project_root=None,
                 git_api_token=None,
                 batch=None,
                 baseline_results=None):
        self.analysis_config = analysis_config
        self.building_options = building_options
        self.project_root = project_root
        self.git_api_token = git_api_token
        self.batch = batch
        self.baseline_results = baseline_results

    # While not a child of BTAPAnalysis, have the same run method for consistency.
    def run(self):
        # excel file container.
        output_excel_files = []

        # Elimination block
        analysis_suffix = '_elim'
        algorithm_type = 'elimination'
        temp_analysis_config = copy.deepcopy(self.analysis_config)
        temp_building_options = copy.deepcopy(self.building_options)
        temp_analysis_config[':algorithm'][':type'] = algorithm_type
        temp_analysis_config[':analysis_name'] = temp_analysis_config[':analysis_name'] + analysis_suffix
        bb = BTAPElimination(analysis_config=temp_analysis_config,
                             building_options=temp_building_options,
                             project_root=self.project_root,
                             git_api_token=self.git_api_token,
                             batch=self.batch,
                             baseline_results=self.baseline_results)
        print(f"running {algorithm_type} stage")
        bb.run()
        output_excel_files.append(os.path.join(bb.results_folder, 'output.xlsx'))

        # Sensitivity block
        analysis_suffix = '_sens'
        algorithm_type = 'sensitivity'
        temp_analysis_config = copy.deepcopy(self.analysis_config)
        temp_building_options = copy.deepcopy(self.building_options)
        temp_analysis_config[':algorithm'][':type'] = algorithm_type
        temp_analysis_config[':analysis_name'] = temp_analysis_config[':analysis_name'] + analysis_suffix
        bb = BTAPSensitivity(analysis_config=temp_analysis_config,
                             building_options=temp_building_options,
                             project_root=self.project_root,
                             git_api_token=self.git_api_token,
                             batch=self.batch,
                             baseline_results=self.baseline_results)
        print(f"running {algorithm_type} stage")
        bb.run()
        output_excel_files.append(os.path.join(bb.results_folder, 'output.xlsx'))

        # Sensitivity block
        analysis_suffix = '_opt'
        algorithm_type = 'nsga2'
        temp_analysis_config = copy.deepcopy(self.analysis_config)
        temp_building_options = copy.deepcopy(self.building_options)
        temp_analysis_config[':algorithm'][':type'] = algorithm_type
        temp_analysis_config[':analysis_name'] = temp_analysis_config[':analysis_name'] + analysis_suffix
        bb = BTAPOptimization(analysis_config=temp_analysis_config,
                              building_options=temp_building_options,
                              project_root=self.project_root,
                              git_api_token=self.git_api_token,
                              batch=self.batch,
                              baseline_results=self.baseline_results)
        print(f"running {algorithm_type} stage")
        bb.run()
        output_excel_files.append(os.path.join(bb.results_folder, 'output.xlsx'))

        # Output results from all analysis into top level output excel.
        df = pd.DataFrame()
        for file in output_excel_files:
            df = df.append(pd.read_excel(file), ignore_index=True)
        df.to_excel(excel_writer=os.path.join(bb.project_root, 'output.xlsx'), sheet_name='btap_data')



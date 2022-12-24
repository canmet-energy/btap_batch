import copy
import os
import pandas as pd
from .btap_optimization import BTAPOptimization
from .btap_elimination import BTAPElimination
from .btap_sensitivity import BTAPSensitivity

# Class to manage IDP runs with group elimination,sensitivity and optimization runs.


class BTAPIntegratedDesignProcess:
    def __init__(self,
                 engine=None,
                 batch=None):
        self.engine = engine
        self.batch = batch

    # While not a child of BTAPAnalysis, have the same run method for consistency.
    def run(self):
        # excel file container.
        output_excel_files = []

        # Elimination block
        analysis_suffix = '_elim'
        algorithm_type = 'elimination'

        temp_engine = copy.deepcopy(self.engine)
        temp_engine.analysis_config[':algorithm'][':type'] = algorithm_type
        temp_engine.analysis_config[':analysis_name'] = temp_engine.analysis_config[':analysis_name'] + analysis_suffix
        bb = BTAPElimination(engine=temp_engine, batch=self.batch)
        print(f"running {algorithm_type} stage")
        bb.run()
        output_excel_files.append(os.path.join(bb.results_folder, 'output.xlsx'))

        # Sensitivity block
        analysis_suffix = '_sens'
        algorithm_type = 'sensitivity'
        temp_engine = copy.deepcopy(self.engine)
        temp_engine.analysis_config[':algorithm'][':type'] = algorithm_type
        temp_engine.analysis_config[':analysis_name'] = temp_engine.analysis_config[':analysis_name'] + analysis_suffix
        bb = BTAPSensitivity(engine=temp_engine, batch=self.batch)
        print(f"running {algorithm_type} stage")
        bb.run()
        output_excel_files.append(os.path.join(bb.results_folder, 'output.xlsx'))

        # Sensitivity block
        analysis_suffix = '_opt'
        algorithm_type = 'nsga2'
        temp_engine = copy.deepcopy(self.engine)
        temp_engine.analysis_config[':algorithm'][':type'] = algorithm_type
        temp_engine.analysis_config[':analysis_name'] = temp_engine.analysis_config[':analysis_name'] + analysis_suffix
        bb = BTAPOptimization(engine=temp_engine, batch=self.batch)
        print(f"running {algorithm_type} stage")
        bb.run()
        output_excel_files.append(os.path.join(bb.results_folder, 'output.xlsx'))

        # Output results from all analysis into top level output excel.
        df = pd.DataFrame()
        for file in output_excel_files:
            df = df.append(pd.read_excel(file), ignore_index=True)
        df.to_excel(excel_writer=os.path.join(bb.engine.project_root, 'output.xlsx'), sheet_name='btap_data')

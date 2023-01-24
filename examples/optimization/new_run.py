from src.compute_resources.btap_optimization import BTAPOptimization
from src.compute_resources.btap_reference import BTAPReference
import copy
from icecream import ic
import os




#Input filename
analysis_config_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'input.yml')



analysis_config, analysis_input_folder, analyses_folder = BTAPOptimization.load_analysis_input_file(
    analysis_config_file=analysis_config_file)

analysis_config[':compute_environment'] = 'local_docker'

# Run reference
ref_analysis_config = copy.deepcopy(analysis_config)
ref_analysis_config[':algorithm_type'] = 'reference'
ref_analysis_config[':analysis_name'] = 'reference_runs'
br = BTAPReference(analysis_config=ref_analysis_config,
                   analysis_input_folder=analysis_input_folder,
                   analyses_folder=analyses_folder)
br.run()

bb = BTAPOptimization(analysis_config=analysis_config,
                      analysis_input_folder=analysis_input_folder,
                      analyses_folder=analyses_folder,
                      reference_run_data_path=br.analysis_excel_results_path())
bb.run()
print(f"Excel results file {bb.analysis_excel_results_path()}")

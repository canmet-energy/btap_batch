from src.compute_resources.docker_image_manager import DockerImageManager
from src.compute_resources.docker_batch import DockerBatch
from src.compute_resources.btap_cli_engine import BTAPEngine
from src.compute_resources.btap_optimization import BTAPOptimization
from src.compute_resources.btap_reference import BTAPReference
import copy
from icecream import ic
import os


#Helper function to run reference
def run_references(analysis_config=None,
                   analyses_folder=None,
                   analysis_input_folder=None,
                   engine=None):
    # Ensure reference run is executed in all other cases unless :run_reference is false.
    if (analysis_config.get(':run_reference') is not False) or (
            analysis_config.get is None):
        # Run reference simulations first.

        ref_analysis_config = copy.deepcopy(analysis_config)
        ref_analysis_config[':algorithm_type'] = 'reference'
        ref_analysis_config[':analysis_name'] = 'reference_runs'
        bb = BTAPReference(
            analysis_config=ref_analysis_config,
            analyses_folder=analyses_folder,
            analysis_input_folder=analysis_input_folder,
            engine=engine)
        print(f"running reference stage")
        bb.run()
        return os.path.join(bb.analysis_results_folder(), 'output.xlsx')


analysis_config_file = os.path.join(os.path.dirname(os.path.realpath(__file__)),'input.yml')

analysis_config, analysis_input_folder, analyses_folder = BTAPOptimization.load_analysis_input_file(analysis_config_file=analysis_config_file)
ref_analysis_config = copy.deepcopy(analysis_config)
ref_analysis_config[':algorithm_type'] = 'reference'
ref_analysis_config[':analysis_name'] = 'reference_runs'
br = BTAPReference(analysis_config=ref_analysis_config,
                   engine=BTAPEngine(),
                   analysis_input_folder=analysis_input_folder,
                   analyses_folder=analyses_folder)
br.run()


bb=BTAPOptimization(analysis_config=analysis_config,
                  engine=BTAPEngine(),
                  analysis_input_folder=analysis_input_folder,
                  analyses_folder=analyses_folder,
                  reference_run_data_path=br.analysis_excel_results_path())
bb.run()
print(f"Excel results file {bb.analysis_excel_results_path()}")



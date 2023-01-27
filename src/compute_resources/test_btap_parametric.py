from src.compute_resources.docker_image_manager import DockerImageManager
from src.compute_resources.docker_batch import DockerBatch

from src.compute_resources.btap_parametric import BTAPParametric
from src.compute_resources.btap_reference import BTAPReference
import copy
from icecream import ic
import yaml
from pathlib import Path
import os


#Helper function to run reference
def run_references(analysis_config=None,
                   analyses_folder=None,
                   analysis_input_folder=None):
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
            analysis_input_folder=analysis_input_folder)
        print(f"running reference stage")
        bb.run()
        return os.path.join(bb.analysis_results_folder(), 'output.xlsx')


image_mgr = DockerImageManager(image_name='btap_cli')
# image_mgr.build_image()


run_options = yaml.safe_load(Path(
    r"C:\Users\plopez\btap_batch\src\test\test_docker_batch\analysis_id\input\datapoint_id\run_options.yml").read_text())

local_project_folder = r"C:\Users\plopez\btap_batch\src\test\test_docker_batch"

batch = DockerBatch(image_manager=image_mgr)

analysis_config_file = r"C:\Users\plopez\btap_batch\examples\custom_osm\input.yml"

analysis_config, analysis_input_folder, analyses_folder = BTAPParametric.load_analysis_input_file(analysis_config_file=analysis_config_file)
ref_analysis_config = copy.deepcopy(analysis_config)
ref_analysis_config[':algorithm_type'] = 'reference'
ref_analysis_config[':analysis_name'] = 'reference_runs'
br = BTAPReference(analysis_config=ref_analysis_config,
                   analysis_input_folder=analysis_input_folder,
                   analyses_folder=analyses_folder)
br.run()
ic(br.analysis_results_folder())


bb=BTAPParametric(analysis_config=analysis_config,
                  analysis_input_folder=analysis_input_folder,
                  analyses_folder=analyses_folder,
                  reference_run_data_path=br.analysis_excel_results_path())
bb.run()



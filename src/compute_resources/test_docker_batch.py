from src.compute_resources.docker_image_manager import DockerImageManager
from src.compute_resources.docker_batch import DockerBatch
from src.compute_resources.docker_job import DockerBTAPJob
import yaml
from pathlib import Path
from icecream import ic

image_mgr = DockerImageManager(image_name='btap_cli')
# image_mgr.build_image()


run_options = yaml.safe_load(Path(
    r"C:\Users\plopez\btap_batch\src\test\test_docker_batch\analysis_id\input\datapoint_id\run_options.yml").read_text())

local_project_folder = r"C:\Users\plopez\btap_batch\src\test\test_docker_batch"

batch = DockerBatch(image_manager=image_mgr)

job = DockerBTAPJob(batch=batch,
                    job_id=run_options[':datapoint_id'],
                    local_project_folder=local_project_folder)

job.submit_job(run_options=run_options)

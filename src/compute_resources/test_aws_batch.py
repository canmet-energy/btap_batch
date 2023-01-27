
from src.compute_resources.aws_image_manager import AWSImageManager
from src.compute_resources.aws_batch import AWSBatch
from src.compute_resources.aws_job import AWSBTAPJob
from icecream import ic
import yaml
from pathlib import Path
import os
import logging

path = os.path.dirname(os.path.realpath(__file__))
logfile = os.path.join(path , "test.log")
# remove old logfile if it is there.
if os.path.exists(logfile):
    os.remove(logfile)

logging.basicConfig(filename=logfile,
                    filemode='a',
                    format='%(asctime)s, %(levelname)-8s [%(filename)s:%(lineno)d:%(funcName)s] %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)
message = f"Log file created: {logfile}"
print(message)
logging.info(message)

run_options = yaml.safe_load(Path(
    r"C:\Users\plopez\btap_batch\src\test\test_docker_batch\analysis_id\input\datapoint_id\run_options.yml").read_text())

local_project_folder = r"C:\Users\plopez\btap_batch\src\test\test_docker_batch"


image = AWSImageManager(image_name='btap_cli')
batch = AWSBatch(image_manager=image)
#batch.tear_down()
#batch.setup()

job = AWSBTAPJob(batch=batch, job_id=run_options[':datapoint_id'])

job.submit_job(run_options=run_options)


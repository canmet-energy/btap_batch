from src.btap.docker_job import DockerBTAPJob
from icecream import ic

# Class to manage local Docker batch run.
class DockerBatch():
    def __init__(self, image_manager=None):
        self.image_manager = image_manager

    def setup(self):
        # Ensure image has been created
        # Set up compute, queue and job descriptions if required.
        print("Nothing to set up for local docker batch")


    def teardown(self):
        # Set up compute, queue and job descriptions if required.
        print("Nothing to tear down for local docker batch")

    def create_job(self,
                   job_id=None
                   ):
        return DockerBTAPJob(batch=self,
                             job_id=job_id,
                             )


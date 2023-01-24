import logging
import time
from pathlib import Path
import yaml
import os
import json
from icecream import ic
from src.compute_resources.docker_job import BTAPDockerJob


# Class to manage local Docker batch run.
class DockerBatch():
    def __init__(self, image_manager=None):
        self.image_manager = image_manager

    def setup(self):
        # Ensure image has been created
        # Set up compute, queue and job descriptions if required.
        print("Nothing to set up for Docker batch")


    def teardown(self):
        # Set up compute, queue and job descriptions if required.
        print("Nothing to tear down")

    def create_job(self,
                   analysis_id=None,
                   analysis_name=None,
                   job_id=None,
                   local_project_folder=None,
                   remote_project_folder=None  # stub for cloud jobs.
                   ):
        return BTAPDockerJob(batch=self,
                             analysis_id=analysis_id,
                             analysis_name=analysis_name,
                             job_id=job_id,
                             local_project_folder=local_project_folder,
                             remote_project_folder=remote_project_folder  # stub for cloud jobs.
                             )


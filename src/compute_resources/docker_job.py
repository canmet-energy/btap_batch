import os
import json
import yaml
import time
import logging
from pathlib import Path
from icecream import ic
from src.compute_resources.common_paths import CommonPaths


class DockerJob:

    def __init__(self,
                 batch=None,
                 engine=None,
                 analysis_id=None,
                 analysis_name=None,
                 job_id=None,
                 local_project_folder=None,
                 remote_project_folder=None  # stub for cloud jobs.
                 ):
        self.analysis_id = analysis_id
        self.analysis_name = analysis_name
        self.job_id = job_id
        self.remote_project_folder = remote_project_folder
        self.local_project_folder = local_project_folder
        self.batch = batch
        self.engine = engine

        #Common object for paths.
        self.cp = CommonPaths()



    def submit_job(self, run_options=None):
        # Timer start.
        start = time.time()

        # job data storage dict.
        job_data = {}
        job_data.update(run_options)

        try:

            self.run_container(run_options)
            job_data = self.engine.post_process_data_result_success(job_data=job_data,
                                                                    local_datapoint_output_folder=self.cp.analysis_output_job_id_folder(job_id=self.job_id)
                                                                    )
            # Flag that is was successful.
            job_data['success'] = True
            job_data['simulation_time'] = time.time() - start
            return job_data
        except Exception as error:
            print(error)
            # post process failed run.
            job_data = self.engine.post_process_data_result_failure(job_data=job_data,
                                                         local_datapoint_output_folder=self.cp.analysis_output_job_id_folder(job_id=self.job_id))
            job_data['success'] = False
            job_data['run_options'] = yaml.dump(run_options)
            job_data['datapoint_output_url'] = 'file:///' + os.path.join(self.cp.analysis_output_job_id_folder(job_id=self.job_id))
            # save btap_data json file.
            local_btap_data_path = os.path.join(self.cp.analysis_output_job_id_folder(job_id=self.job_id), "btap_data.json")
            Path(os.path.dirname(local_btap_data_path)).mkdir(parents=True, exist_ok=True)
            with open(local_btap_data_path, 'w') as outfile:
                json.dump(job_data, outfile, indent=4)
            return job_data

    def run_container(self, run_options):
        # Run the simulation
        result = self.batch.image_manager.run_container(
            volumes={
                self.cp.analysis_output_folder(): {
                    'bind': self.engine.container_output_path(),
                    'mode': 'rw'},
                self.cp.analysis_input_job_id_folder(job_id=self.job_id): {
                    'bind': self.engine.container_input_path(),
                    'mode': 'rw'},
            },
            engine_command=self.engine.engine_command(),
            run_options=run_options)
        # engine post process successful run.

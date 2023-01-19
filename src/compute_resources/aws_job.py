import os
from src.compute_resources.aws_s3 import S3
import json
import yaml
import pathlib
import sys

import boto3
import botocore
import time
import logging
from random import random
from src.compute_resources.docker_job import DockerJob
from src.compute_resources.aws_credentials import AWSCredentials
from src.constants import AWS_MAX_RETRIES
from icecream import ic
from src.compute_resources.common_paths import CommonPaths




class AWSJob(DockerJob):

    def __init__(self,
                 batch=None,
                 engine=None,
                 analysis_id=None,
                 analysis_name=None,
                 job_id=None,
                 local_project_folder=None,
                 remote_project_folder=None,
                 ):
        super().__init__(batch=batch,
                         engine=engine,
                         analysis_id=analysis_id,
                         analysis_name=analysis_name,
                         job_id=job_id,
                         local_project_folder=local_project_folder,
                         remote_project_folder=None,
                         )



        self.cloud_job_id = None  # Set by AWS when job is submitted.
        # update run_options
        self.s3_bucket = self.__aws_credentials().account_id
        self.cp = CommonPaths()



    def __aws_credentials(self):
        return AWSCredentials()

    def job_name(self):
        return f"{self.analysis_id}-{self.job_id}"

    def submit_job(self, run_options=None):
        # Timer start.
        start = time.time()

        #update run options
        run_options[':s3_bucket'] = self.s3_bucket

        # job data storage dict for input and output.
        job_data = {}
        job_data.update(run_options)


        # Container command
        container_command = self.engine.aws_engine_command(input_path=self.cp.s3_container_input_path(self.job_id),
                                                           output_path=self.cp.s3_container_output_path()).replace('\\',
                                                                                                                   '/')
        command = ["/bin/bash", "-c", container_command]
        try:

            logging.info(
                f"Copying from {self.cp.analysis_input_job_id_folder(job_id=self.job_id)} to bucket {self.s3_bucket} folder {self.cp.s3_datapoint_input_folder(job_id=self.job_id)}")
            S3().copy_folder_to_s3(bucket_name=self.s3_bucket,
                                   source_folder=self.cp.analysis_input_job_id_folder(job_id=self.job_id),
                                   target_folder=self.cp.s3_datapoint_input_folder(job_id=self.job_id))
            # Start timer to track simulation time.

            # See https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/batch.html#Batch.Client.submit_job
            self.cloud_job_id = self.__submit_job_wrapper(command=command)['jobId']

            message = f"Submitted job_id {self.job_id} with cloud id {self.cloud_job_id}, job name {self.job_name()} to the job queue {self.batch.job_queue_name}"
            logging.info(message)


            # Set initial state of status variables
            running = False
            result = 'FAILED'
            while True:
                # Don't hammer AWS.. make queries every minute for the run status
                time.sleep(60 + random())
                describeJobsResponse = self.__get_job_status()
                status = describeJobsResponse['jobs'][0]['status']
                if status == 'SUCCEEDED':
                    message = 'SUCCEEDED - Job [%s - %s] %s' % (self.job_name(), self.cloud_job_id, status)
                    logging.info(message)
                    result = 'SUCCEEDED'
                    break
                elif status == 'FAILED':
                    message = 'FAILED - Job [%s - %s] %s' % (self.job_name(), self.cloud_job_id, status)
                    logging.error(message)
                    result = 'FAILED'
                    break
                elif status == 'RUNNING':
                    if not running:
                        running = True
                else:
                    message = 'UNKNOWN - Job [%s - %s] is %-9s' % (self.job_name(), self.cloud_job_id, status)
                    # logging.info(message)
                    sys.stdout.flush()

            self.engine.aws_post_process_data_result_success(job_data=job_data,
                                                             run_options=run_options,
                                                             s3_datapoint_output_folder=self.cp.s3_datapoint_output_folder(job_id=self.job_id))

            # save url to datapoint output for Kamel.
            job_data[
                'datapoint_output_url'] = f"https://s3.console.aws.amazon.com/s3/buckets/{run_options[':s3_bucket']}?region=ca-central-1&prefix={self.cp.s3_datapoint_output_folder(job_id=self.job_id)}/"

            # dump full run_options.yml file into database for convienience.
            job_data['run_options'] = yaml.dump(run_options)

            # Flag that is was successful.
            job_data['success'] = True
            job_data['simulation_time'] = time.time() - start
            return job_data


        except Exception:
            # BTAP Stuff Error.txt
            self.engine.aws_post_process_data_result_failure(job_data=job_data,
                                                             run_options=run_options,
                                                             s3_datapoint_output_folder=self.cp.s3_datapoint_output_folder(job_id=self.job_id))

            job_data['success'] = False

            job_data['run_options'] = yaml.dump(run_options)
            job_data['datapoint_output_url'] = 'file:///' + os.path.join(self.cp.analysis_output_job_id_folder(job_id=self.job_id))

            # Make folder.
            pathlib.Path(self.cp.analysis_output_job_id_folder(job_id=self.job_id)).mkdir(parents=True, exist_ok=True)
            # save btap_data json file to output folder if aws_run.
            with open(self.cp.analysis_output_job_id_btap_json_path(job_id=self.job_id), 'w') as outfile:
                json.dump(job_data, outfile, indent=4)

            return job_data

    def __submit_job_wrapper(self, command=None, n=0):
        try:
            batch_client = boto3.client('batch',
                                        config=botocore.client.Config(
                                            max_pool_connections=self.batch.image_manager.get_threads(),
                                            retries={
                                                'max_attempts': AWS_MAX_RETRIES,
                                                'mode': 'standard'}))
            submitJobResponse = batch_client.submit_job(
                jobName=self.job_name(),
                jobQueue=self.batch.job_queue_name,
                jobDefinition=self.batch.job_def_name,
                containerOverrides={'command': command}
            )
            return submitJobResponse
        except:
            # Implementing exponential backoff
            if n == 8:
                logging.exception(
                    f'Failed to submit job {self.job_name()} in 7 tries while using exponential backoff. Error was {sys.exc_info()[0]} ')
            wait_time = 2 ** n + random()
            logging.warning(f"Implementing exponential backoff for job {self.job_name()} for {wait_time}s")
            time.sleep(wait_time)
            return self.__submit_job_wrapper(command=command, n=n + 1)

    def __get_job_status(self, n=0):
        try:
            batch_client = boto3.client('batch',
                                        config=botocore.client.Config(
                                            max_pool_connections=self.batch.image_manager.get_threads(),
                                            retries={
                                                'max_attempts': AWS_MAX_RETRIES,
                                                'mode': 'standard'}))
            describeJobsResponse = batch_client.describe_jobs(jobs=[self.cloud_job_id])
            return describeJobsResponse
        except:
            if n == 8:
                raise (f'Failed to get job status for {self.cloud_job_id} in 7 tries while using exponential backoff.')
            wait_time = 2 ** n + random()
            logging.warning(f"Implementing exponential backoff for job {self.cloud_job_id} for {wait_time}s")
            time.sleep(wait_time)
            return self.__get_job_status(n=n + 1)




from src.compute_resources.aws_s3 import S3
import sys
import time
import logging
from random import random
from src.compute_resources.aws_credentials import AWSCredentials
from src.compute_resources.common_paths import CommonPaths
from icecream import ic


class AWSAnalysisJob():
    def __init__(self, batch=None, job_id=None):

        self.cloud_job_id = None  # Set by AWS when job is submitted.
        self.job_id = job_id
        # update run_options
        self.s3_bucket = AWSCredentials().account_id
        self.set_paths()
        self.batch = batch

    def set_paths(self):
        # Common object for paths.
        self.cp = CommonPaths()
        # Used for copy_folder_to_s3
        self.source = self.cp.project_input_folder()
        self.target = self.cp.s3_analysis_name_folder()

    def submit_job(self):
        # Timer start.
        start = time.time()

        # Variable to store all input and output information about job.
        job_data = {}
        self.copy_files_to_run_location()
        # See https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/batch.html#Batch.Client.submit_job
        submitJobResponse = self.job_wrapper()
        self.cloud_job_id = submitJobResponse['jobId']
        message = f"Submitted Analysis {self.job_id} , job name {self.aws_job_name()} to the job queue {self.batch.job_queue_name}"
        logging.info(message)




    def job_wrapper(self, n=0):
        # ic(self.aws_job_name())
        # ic(self.batch.job_queue_name)
        # ic(self.batch.job_def_name)
        # ic(self.container_command())
        batch_client = AWSCredentials().batch_client
        try:
            submitJobResponse = batch_client.submit_job(
                jobName=self.aws_job_name(),
                jobQueue=self.batch.job_queue_name,
                jobDefinition=self.batch.job_def_name,
                containerOverrides={'command': self.container_command()}
            )
            message = f"Submitted {self.aws_job_name()} to aws job queue {self.batch.job_queue_name}"
            logging.info(message)
            print(message)
            return submitJobResponse
        except:
            # Implementing exponential backoff
            if n == 8:
                logging.exception(
                    f'Failed to submit job {self.aws_job_name()} in 7 tries while using exponential backoff. Error was {sys.exc_info()[0]} ')
            wait_time = 2 ** n + random()
            logging.warning(f"JobWrapper:Implementing exponential backoff for job {self.aws_job_name()} for {wait_time}s")
            time.sleep(wait_time)
            return self.job_wrapper(n=n + 1)



    def container_command(self):
        command = ["python3",
                   "/btap_batch/bin/btap_batch.py",
                   "run-analysis-project",
                   "--project_folder",
                   self.cp.s3_btap_batch_container_input_path(),
                   "--compute_environment",
                   "aws_batch"
                   ]
        return command

    def copy_files_to_run_location(self):
        message = f"Copying from {self.source} to bucket{self.s3_bucket} target {self.target}"
        logging.info(message)
        S3().delete_s3_folder(bucket=self.s3_bucket, folder=self.target)
        S3().copy_folder_to_s3(bucket_name=self.s3_bucket,
                               source_folder=self.source,
                               target_folder=self.target)



    # Private methods.
    def aws_job_name(self):
        return f"{self.job_id}"

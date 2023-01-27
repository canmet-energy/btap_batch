import os
from src.compute_resources.aws_s3 import S3
import json
import sys
import boto3
import botocore
import time
import logging
from random import random
from src.compute_resources.docker_job import DockerBTAPJob
from src.compute_resources.aws_credentials import AWSCredentials
from src.constants import AWS_MAX_RETRIES
from src.compute_resources.common_paths import CommonPaths
from icecream import ic


class AWSBTAPJob(DockerBTAPJob):
    def __init__(self, batch=None, job_id=None):
        super().__init__(batch=batch,
                         job_id=job_id,
                         )

        self.cloud_job_id = None  # Set by AWS when job is submitted.
        # update run_options
        self.s3_bucket = AWSCredentials().account_id
        self._set_paths()
    #Overridden methods
    def _job_url(self):
        return self.cp.s3_job_url(job_id=self.job_id)

    def _set_paths(self):
        # set for  container command used in btap_cli ruby code.
        # Common object for paths.
        self.cp = CommonPaths()
        self.input_f = self.cp.s3_container_input_path(self.job_id)
        self.output_f = self.cp.s3_container_output_path().replace('\\', '/')
        # Used for copy_folder_to_s3
        self.source = self.cp.analysis_input_job_id_folder(job_id=self.job_id)
        self.target = self.cp.s3_datapoint_input_folder(job_id=self.job_id)
        # Local json file location
        self.local_json_file_path = self.cp.analysis_output_job_id_btap_json_path(job_id=self.job_id)
        self.local_output_job_folder = self.cp.analysis_output_job_id_folder(job_id=self.job_id)
        # Used in postprocessing successful run from S3 and http url path construction.
        self.s3_datapoint_output_folder = self.cp.s3_datapoint_output_folder(job_id=self.job_id)
    def _command_args(self):
        args = [f"--input_path {self.input_f} ",
                f"--output_path {self.output_f} "
                ]
        return args
    def _container_command(self):
        command = ["/bin/bash",
                   "-c",
                   super()._container_command()]
        return command
    def _update_run_options(self, run_options=None):
        super()._update_run_options(run_options=run_options)
        run_options[':s3_bucket'] = self.s3_bucket
        return run_options
    def _copy_files_to_run_location(self):
        logging.info(
            f"Copying from {self.source} to bucket {self.target}")
        S3().copy_folder_to_s3(bucket_name=self.s3_bucket,
                               source_folder=self.source,
                               target_folder=self.target)
    def _get_job_results(self):
        # Gather results from S3
        s3_btap_data_path = os.path.join(self.s3_datapoint_output_folder, 'btap_data.json').replace('\\', '/')
        logging.info(
            f"Getting data from S3 bucket {self.s3_bucket} at path {s3_btap_data_path}")
        content_object = boto3.resource('s3').Object(self.s3_bucket, s3_btap_data_path)
        result_data = json.loads(content_object.get()['Body'].read().decode('utf-8'))
        # Adding simulation high level results from btap_data.json to df.
        result_data = self._enumerate_eplus_warnings(job_data=result_data)
        return result_data
    def _get_container_error(self):
        # Get error message from error file from S3 and store it in the job_data list.
        s3_error_txt_path = os.path.join(self.s3_datapoint_output_folder, 'error.txt').replace('\\', '/')
        content_object = boto3.resource('s3').Object(self.s3_bucket, s3_error_txt_path)
        error_txt = content_object.get()['Body'].read().decode('utf-8')
        return  str(error_txt)
    def _run_container(self):

        # See https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/batch.html#Batch.Client.submit_job
        submitJobResponse = self.__job_wrapper()
        self.cloud_job_id = submitJobResponse['jobId']
        message = f"Submitted job_id {self.job_id} , job name {self.__aws_job_name()} to the job queue {self.batch.job_queue_name}"
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
                message = 'SUCCEEDED - Job [%s - %s] %s' % (self.__aws_job_name(), self.cloud_job_id, status)
                logging.info(message)
                result = 'SUCCEEDED'
                break
            elif status == 'FAILED':
                message = 'FAILED - Job [%s - %s] %s' % (self.__aws_job_name(), self.cloud_job_id, status)
                logging.error(message)
                result = 'FAILED'
                break
            elif status == 'RUNNING':
                if not running:
                    running = True
            else:
                message = 'UNKNOWN - Job [%s - %s] is %-9s' % (self.__aws_job_name(), self.cloud_job_id, status)
                logging.info(message)
                sys.stdout.flush()
    # Private methods.
    def __aws_job_name(self):
        return f"{self.job_id}"

    def __job_wrapper(self, n=0):
        try:
            batch_client = boto3.client('batch',
                                        config=botocore.client.Config(
                                            max_pool_connections=self.batch.image_manager.get_threads(),
                                            retries={
                                                'max_attempts': AWS_MAX_RETRIES,
                                                'mode': 'standard'}))
            submitJobResponse = batch_client.submit_job(
                jobName=self.__aws_job_name(),
                jobQueue=self.batch.job_queue_name,
                jobDefinition=self.batch.job_def_name,
                containerOverrides={'command': self._container_command()}
            )
            ic(self.job_id)

            return submitJobResponse
        except:
            # Implementing exponential backoff
            if n == 8:
                logging.exception(
                    f'Failed to submit job {self.__aws_job_name()} in 7 tries while using exponential backoff. Error was {sys.exc_info()[0]} ')
            wait_time = 2 ** n + random()
            logging.warning(f"JobWrapper:Implementing exponential backoff for job {self.__aws_job_name()} for {wait_time}s")
            time.sleep(wait_time)
            return self.__job_wrapper(n=n + 1)
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
            logging.warning(f"Status:Implementing exponential backoff for job {self.cloud_job_id} for {wait_time}s")
            time.sleep(wait_time)
            return self.__get_job_status(n=n + 1)

class AWSBTAPBatchJob(AWSBTAPJob):
    def __init__(self, batch=None, job_id=None):
        super().__init__(batch=batch,
                         job_id=job_id,
                         )

        self.cloud_job_id = None  # Set by AWS when job is submitted.
        # update run_options
        self.s3_bucket = AWSCredentials().account_id
        self._set_paths()
    #Overridden methods
    def _job_url(self):
        return self.cp.s3_job_url(job_id=self.job_id)

    def _set_paths(self):
        # set for  container command used in btap_cli ruby code.
        # Common object for paths.
        self.cp = CommonPaths()
        # Used for copy_folder_to_s3
        self.source = self.cp.analysis_input_job_id_folder(job_id=self.job_id)
        self.target = self.cp.s3_datapoint_input_folder(job_id=self.job_id)
        # Local json file location
        self.local_json_file_path = self.cp.analysis_output_job_id_btap_json_path(job_id=self.job_id)
        self.local_output_job_folder = self.cp.analysis_output_job_id_folder(job_id=self.job_id)
        # Used in postprocessing successful run from S3 and http url path construction.
        self.s3_datapoint_output_folder = self.cp.s3_datapoint_output_folder(job_id=self.job_id)
    def _command_args(self):
        args = []
        return args
    def _container_command(self):
        command = ["/bin/bash",
                   "-c",
                   super()._container_command()]
        return command
    def _update_run_options(self, run_options=None):
        super()._update_run_options(run_options=run_options)
        run_options[':s3_bucket'] = self.s3_bucket
        return run_options
    def _copy_files_to_run_location(self):
        logging.info(
            f"Copying from {self.source} to bucket {self.target}")
        S3().copy_folder_to_s3(bucket_name=self.s3_bucket,
                               source_folder=self.source,
                               target_folder=self.target)
    def _get_job_results(self):
        # Gather results from S3
        s3_btap_data_path = os.path.join(self.s3_datapoint_output_folder, 'btap_data.json').replace('\\', '/')
        logging.info(
            f"Getting data from S3 bucket {self.s3_bucket} at path {s3_btap_data_path}")
        content_object = boto3.resource('s3').Object(self.s3_bucket, s3_btap_data_path)
        result_data = json.loads(content_object.get()['Body'].read().decode('utf-8'))
        # Adding simulation high level results from btap_data.json to df.
        result_data = self._enumerate_eplus_warnings(job_data=result_data)
        return result_data
    def _get_container_error(self):
        # Get error message from error file from S3 and store it in the job_data list.
        s3_error_txt_path = os.path.join(self.s3_datapoint_output_folder, 'error.txt').replace('\\', '/')
        content_object = boto3.resource('s3').Object(self.s3_bucket, s3_error_txt_path)
        error_txt = content_object.get()['Body'].read().decode('utf-8')
        return  str(error_txt)
    def _run_container(self):

        # See https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/batch.html#Batch.Client.submit_job
        submitJobResponse = self.__job_wrapper()
        self.cloud_job_id = submitJobResponse['jobId']
        message = f"Submitted job_id {self.job_id} , job name {self.__aws_job_name()} to the job queue {self.batch.job_queue_name}"
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
                message = 'SUCCEEDED - Job [%s - %s] %s' % (self.__aws_job_name(), self.cloud_job_id, status)
                logging.info(message)
                result = 'SUCCEEDED'
                break
            elif status == 'FAILED':
                message = 'FAILED - Job [%s - %s] %s' % (self.__aws_job_name(), self.cloud_job_id, status)
                logging.error(message)
                result = 'FAILED'
                break
            elif status == 'RUNNING':
                if not running:
                    running = True
            else:
                message = 'UNKNOWN - Job [%s - %s] is %-9s' % (self.__aws_job_name(), self.cloud_job_id, status)
                logging.info(message)
                sys.stdout.flush()
    # Private methods.
    def __aws_job_name(self):
        return f"{self.job_id}"

    def __job_wrapper(self, n=0):
        try:
            batch_client = boto3.client('batch',
                                        config=botocore.client.Config(
                                            max_pool_connections=self.batch.image_manager.get_threads(),
                                            retries={
                                                'max_attempts': AWS_MAX_RETRIES,
                                                'mode': 'standard'}))
            submitJobResponse = batch_client.submit_job(
                jobName=self.__aws_job_name(),
                jobQueue=self.batch.job_queue_name,
                jobDefinition=self.batch.job_def_name,
                containerOverrides={'command': self._container_command()}
            )
            ic(self.job_id)

            return submitJobResponse
        except:
            # Implementing exponential backoff
            if n == 8:
                logging.exception(
                    f'Failed to submit job {self.__aws_job_name()} in 7 tries while using exponential backoff. Error was {sys.exc_info()[0]} ')
            wait_time = 2 ** n + random()
            logging.warning(f"JobWrapper:Implementing exponential backoff for job {self.__aws_job_name()} for {wait_time}s")
            time.sleep(wait_time)
            return self.__job_wrapper(n=n + 1)
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
            logging.warning(f"Status:Implementing exponential backoff for job {self.cloud_job_id} for {wait_time}s")
            time.sleep(wait_time)
            return self.__get_job_status(n=n + 1)


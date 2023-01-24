from src.constants import MAX_AWS_VCPUS
from src.constants import AWS_MAX_RETRIES
from src.constants import CONTAINER_MEMORY
from src.constants import CONTAINER_VCPU
import boto3
import botocore
import time
import logging
from random import random
from src.compute_resources.aws_credentials import AWSCredentials
from src.compute_resources.aws_iam_roles import IAMBatchJobRole
from src.compute_resources.aws_job import BTAPAWSJob
from src.compute_resources.common_paths import CommonPaths
from icecream import ic

# Role to give permissions to jobs to run.
BATCH_JOB_ROLE = 'arn:aws:iam::834599497928:role/batchJobRole'
# Role to give permissions to batch to run.
BATCH_SERVICE_ROLE = 'arn:aws:iam::834599497928:role/service-role/AWSBatchServiceRole'


class AWSBatch:

    def __init__(self, image_manager=None, compute_environment=None):
        self.image_manager = image_manager
        self.compute_environment_name = compute_environment.get_compute_environment_name()
        self.launch_template_name = f'{self._username()}_storage_template'
        self.job_queue_name = f'{self._username()}_{image_manager.image_name}_job_queue'
        self.job_def_name = f'{self._username()}_{image_manager.image_name}_job_def'


    def setup(self):
        self.__create_job_queue()
        self.__register_job_definition()

    def tear_down(self):
        self.__deregister_job_definition()
        self.__delete_job_queue()


    def __aws_credentials(self):
        return AWSCredentials()

    def _username(self):
        return CommonPaths().get_username().replace('.', '_')


    def __describe_job_queues(self, job_queue_name, n=0):
        batch_client = boto3.client('batch',
                                    config=botocore.client.Config(max_pool_connections=MAX_AWS_VCPUS,
                                                                  retries={
                                                                      'max_attempts': AWS_MAX_RETRIES,
                                                                      'mode': 'standard'}))
        try:
            # See https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/batch.html#Batch.Client.describe_job_queues
            return batch_client.describe_job_queues(jobQueues=[job_queue_name])
        except:
            if n == 8:
                raise (
                    f'Failed to get job Queue status for {job_queue_name} in 7 tries while using exponential backoff.')
            wait_time = 2 ** n + random()
            logging.warning(f"Implementing exponential backoff for job {job_queue_name} for {wait_time}s")
            time.sleep(wait_time)
            return self.__describe_job_queues(job_queue_name, n=n + 1)

    def __create_job_queue(self):

        message = f'Creating Job Queue {self.job_queue_name}'
        logging.info(message)
        print(message)

        batch_client = boto3.client('batch',
                                    config=botocore.client.Config(max_pool_connections=MAX_AWS_VCPUS,
                                                                  retries={
                                                                      'max_attempts': AWS_MAX_RETRIES,
                                                                      'mode': 'standard'}))

        response = batch_client.create_job_queue(jobQueueName=self.job_queue_name,
                                                 priority=100,
                                                 computeEnvironmentOrder=[
                                                     {
                                                         'order': 0,
                                                         'computeEnvironment': self.compute_environment_name
                                                     }
                                                 ])

        while True:
            describe = self.__describe_job_queues(self.job_queue_name)
            jobQueue = describe['jobQueues'][0]
            status = jobQueue['status']
            state = jobQueue['state']
            if status == 'VALID' and state == 'ENABLED':
                message = f'Created Job Queue {self.job_queue_name}, You can monitor your job queue on the AWS Batch management console dashboard.'
                logging.info(message)
                print(message)
                break
            elif status == 'INVALID':
                reason = jobQueue['statusReason']
                message = f'Failed to create job queue: {reason}'
                logging.error(message)
                exit(1)
            time.sleep(5)

        return response

    def __register_job_definition(self,
                                  unitVCpus=CONTAINER_VCPU,
                                  unitMemory=CONTAINER_MEMORY):

        # Store the aws service role arn for AWSBatchServiceRole. This role is created by default when AWSBatch
        # compute environment is created for the first time via the web console automatically.
        message = f'Creating Job Definition {self.job_def_name}'
        logging.info(message)
        print(message)
        batch_client = boto3.client('batch',
                                    config=botocore.client.Config(max_pool_connections=MAX_AWS_VCPUS,
                                                                  retries={
                                                                      'max_attempts': AWS_MAX_RETRIES,
                                                                      'mode': 'standard'}))

        response = batch_client.register_job_definition(jobDefinitionName=self.job_def_name,
                                                        type='container',
                                                        containerProperties={
                                                            'image': self.image_manager.get_image_uri(),
                                                            'vcpus': unitVCpus,
                                                            'memory': unitMemory,
                                                            'privileged': True,
                                                            'jobRoleArn': IAMBatchJobRole().arn()
                                                        })

        return response



    def __deregister_job_definition(self):
        batch_client = boto3.client('batch',
                                    config=botocore.client.Config(max_pool_connections=MAX_AWS_VCPUS,
                                                                  retries={
                                                                      'max_attempts': AWS_MAX_RETRIES,
                                                                      'mode': 'standard'}))

        describe = batch_client.describe_job_definitions(jobDefinitionName=self.job_def_name)
        if len(describe['jobDefinitions']) != 0:

            message = f'Disable Job Definition {self.job_def_name}'
            print(message)
            logging.info(message)
            # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/batch.html#Batch.Client.describe_job_definitions
            describe = batch_client.describe_job_definitions(jobDefinitionName=self.job_def_name)
            # See https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/batch.html#Batch.Client.deregister_job_definition
            response = batch_client.deregister_job_definition(
                jobDefinition=describe['jobDefinitions'][0]['jobDefinitionArn'])
            return response
        return True


    def __delete_job_queue(self):

        describe = self.__describe_job_queues(self.job_queue_name)
        if len(describe['jobQueues']) != 0:

            batch_client = boto3.client('batch',
                                        config=botocore.client.Config(max_pool_connections=MAX_AWS_VCPUS,
                                                                      retries={
                                                                          'max_attempts': AWS_MAX_RETRIES,
                                                                          'mode': 'standard'}))
            # Disable Queue
            # Tell user
            message = f'Disable Job Queue {self.job_queue_name}'
            print(message)
            logging.info(message)
            # See https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/batch.html#Batch.Client.update_job_queue
            batch_client.update_job_queue(jobQueue=self.job_queue_name, state='DISABLED')
            while True:
                # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/batch.html#Batch.Client.describe_job_queues
                describe = self.__describe_job_queues(self.job_queue_name)
                item = describe['jobQueues'][0]
                state = item['state']
                status = item['status']
                if state == 'DISABLED' and status == 'VALID':
                    break
                elif status == 'INVALID':
                    reason = item['statusReason']
                    raise Exception('Failed to job queue is invalid state: %s' % (reason))
                time.sleep(5)
            # Delete Queue

            # Tell user.
            message = f'Delete Job Queue {self.job_queue_name}'
            print(message)
            logging.info(message)

            # See https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/batch.html#Batch.Client.delete_job_queue
            response = batch_client.delete_job_queue(jobQueue=self.job_queue_name)
            # Wait until queue is deleted.
            while True:
                # See https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/batch.html#Batch.Client.describe_job_queues
                describe = self.__describe_job_queues(self.job_queue_name)
                if not describe['jobQueues']:
                    break
                time.sleep(5)
            return response
        else:
            print(f"Job Queue {self.job_queue_name} already deleted.")
            return  True


    def create_job(self,
                   analysis_id=None,
                   analysis_name=None,
                   job_id=None,
                   local_project_folder=None,
                   remote_project_folder=None  # stub for cloud jobs.
                   ):
        return BTAPAWSJob(batch=self,
                          analysis_id=analysis_id,
                          analysis_name=analysis_name,
                          job_id=job_id,
                          local_project_folder=local_project_folder,
                          remote_project_folder=remote_project_folder  # stub for cloud jobs.
                          )

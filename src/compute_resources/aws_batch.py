from src.constants import MAX_AWS_VCPUS
from src.constants import AWS_MAX_RETRIES
from src.constants import AWS_BATCH_ALLOCATION_STRATEGY
from src.constants import AWS_BATCH_COMPUTE_INSTANCE_TYPES
from src.constants import MIN_AWS_VCPUS
from src.constants import AWS_BATCH_DEFAULT_IMAGE
from src.constants import CONTAINER_STORAGE
from src.constants import CONTAINER_MEMORY
from src.constants import CONTAINER_VCPU
import boto3
from botocore.config import Config
import botocore
import time
import logging
from random import random
from src.compute_resources.aws_credentials import AWSCredentials
from src.compute_resources.aws_iam_roles import IAMBatchServiceRole
from src.compute_resources.aws_iam_roles import IAMBatchJobRole
from src.compute_resources.aws_ec2_info import AWS_EC2Info
from src.compute_resources.aws_job import AWSJob

# Role to give permissions to jobs to run.
BATCH_JOB_ROLE = 'arn:aws:iam::834599497928:role/batchJobRole'
# Role to give permissions to batch to run.
BATCH_SERVICE_ROLE = 'arn:aws:iam::834599497928:role/service-role/AWSBatchServiceRole'


class AWSBatch:

    def __init__(self, image_manager=None,engine=None):
        self.compute_environment_name = f"{self.username()}_compute_environment"
        self.launch_template_name = f'{self.username()}_storage_template'
        self.job_queue_name = f'{self.username()}_job_queue'
        self.job_def_name = f'{self.username()}_job_def'
        self.image_manager = image_manager
        self.engine = engine

    def __aws_credentials(self):
        return AWSCredentials()

    def username(self):
        return self.__aws_credentials().user_name.replace('.', '_')

    def setup(self):
        # This method creates batch infrastructure for user.
        launch_template = self.__add_storage_space_launch_template()

        self.__create_compute_environment(launch_template=launch_template)
        self.__create_job_queue()
        self.__register_job_definition()
        print("Completed AWS batch initialization.")

    # Short method that creates a template to increase the disk size of the containers. Default 100GB.
    def __add_storage_space_launch_template(self, sizegb=CONTAINER_STORAGE):
        self.ec2 = boto3.client('ec2', config=Config(retries={'max_attempts': AWS_MAX_RETRIES, 'mode': 'standard'}))

        launch_template = self.ec2.describe_launch_templates()['LaunchTemplates']
        if next((item for item in launch_template if item["LaunchTemplateName"] == self.launch_template_name),
                None) == None:
            message = f'Creating EC2 instance launch template with 100GB of space named {self.launch_template_name}'
            logging.info(message)
            response = self.ec2.create_launch_template(
                DryRun=False,
                LaunchTemplateName=self.launch_template_name,
                LaunchTemplateData={
                    # This setup works for amazon linux 2.
                    # https://aws.amazon.com/premiumsupport/knowledge-center/batch-ebs-volumes-launch-template/
                    'BlockDeviceMappings': [
                        {
                            'DeviceName': '/dev/xvda',
                            'Ebs': {
                                'VolumeSize': sizegb,
                                'VolumeType': 'gp2'
                            }
                        }
                    ]
                }
            )
        else:
            message = f"Launch Template {self.launch_template_name} already exists. Using existing."
            logging.info(message)
        return self.launch_template_name

    def __describe_compute_environments(self, compute_environment_name, n=0):
        batch_client = boto3.client('batch',
                                    config=botocore.client.Config(max_pool_connections=self.image_manager.get_threads(),
                                                                  retries={
                                                                      'max_attempts': AWS_MAX_RETRIES,
                                                                      'mode': 'standard'}))
        try:
            return batch_client.describe_compute_environments(computeEnvironments=[compute_environment_name])
        except:
            if n == 8:
                raise (
                    f'Failed to get job Queue status for {compute_environment_name} in 7 tries while using exponential backoff.')
            wait_time = 2 ** n + random()
            logging.warning(f"Implementing exponential backoff for job {compute_environment_name} for {wait_time}s")
            time.sleep(wait_time)
            return self.__describe_compute_environments(compute_environment_name, n=n + 1)

    def __create_compute_environment(self, launch_template=None, compute_environments=None):

        batch_client = boto3.client('batch',
                                    config=botocore.client.Config(max_pool_connections=self.image_manager.get_threads(),
                                                                  retries={
                                                                      'max_attempts': AWS_MAX_RETRIES,
                                                                      'mode': 'standard'}))
        # Inform user starting to create CE.
        message = f'Creating Compute Environment {self.compute_environment_name}'
        print(message)
        logging.info(message)

        # Call to create Compute environment.
        # See https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/batch.html#Batch.Client.create_compute_environment
        # and https://docs.aws.amazon.com/batch/latest/userguide/compute_environment_parameters.html#compute_environment_type
        response = batch_client.create_compute_environment(
            computeEnvironmentName=self.compute_environment_name,
            type='MANAGED',  # Allow AWS to manage instances.
            serviceRole=IAMBatchServiceRole().arn(),
            computeResources={
                'type': 'EC2',
                'allocationStrategy': AWS_BATCH_ALLOCATION_STRATEGY,
                'minvCpus': MIN_AWS_VCPUS,
                'maxvCpus': MAX_AWS_VCPUS,
                # 'desiredvCpus': DESIRED_AWS_VCPUS,
                'instanceTypes': AWS_BATCH_COMPUTE_INSTANCE_TYPES,
                'imageId': AWS_BATCH_DEFAULT_IMAGE,
                'subnets': AWS_EC2Info().subnet_id_list,
                'securityGroupIds': AWS_EC2Info().securityGroupIds,
                'instanceRole': 'ecsInstanceRole',
                'launchTemplate': {

                    'launchTemplateName': launch_template}
            }
        )
        # Check state of creating CE.
        while True:
            # See https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/batch.html#Batch.Client.describe_compute_environments
            describe = self.__describe_compute_environments(self.compute_environment_name)

            computeEnvironment = describe['computeEnvironments'][0]
            status = computeEnvironment['status']
            # If CE is in valid state, inform user and break from loop.
            if status == 'VALID':
                break
            # If CE is in invalid state, inform user and break from loop.
            elif status == 'INVALID':
                reason = computeEnvironment['statusReason']
                raise Exception('Failed to create compute environment: %s' % (reason))
            time.sleep(1)

        return response

    def __describe_job_queues(self, job_queue_name, n=0):
        batch_client = boto3.client('batch',
                                    config=botocore.client.Config(max_pool_connections=self.image_manager.get_threads(),
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
                                    config=botocore.client.Config(max_pool_connections=self.image_manager.get_threads(),
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
                                    config=botocore.client.Config(max_pool_connections=self.image_manager.get_threads(),
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

    def tear_down(self):
        # This method creates batch infrastructure for user.
        # This method manages the teardown of the batch workflow. See methods for details.
        message = "Shutting down AWSBatch...."
        print(message)
        logging.info(message)
        self.__delete_job_definition()
        self.__delete_job_queue()
        self.__delete_compute_environment()

    def __delete_job_definition(self):
        batch_client = boto3.client('batch',
                                    config=botocore.client.Config(max_pool_connections=self.image_manager.get_threads(),
                                                                  retries={
                                                                      'max_attempts': AWS_MAX_RETRIES,
                                                                      'mode': 'standard'}))
        message = f'Disable Job Definition {self.job_def_name}'
        print(message)
        logging.info(message)
        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/batch.html#Batch.Client.describe_job_definitions
        describe = batch_client.describe_job_definitions(jobDefinitionName=self.job_def_name)
        # See https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/batch.html#Batch.Client.deregister_job_definition
        response = batch_client.deregister_job_definition(
            jobDefinition=describe['jobDefinitions'][0]['jobDefinitionArn'])
        return response

    def __delete_job_queue(self):
        batch_client = boto3.client('batch',
                                    config=botocore.client.Config(max_pool_connections=self.image_manager.get_threads(),
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

    def __delete_compute_environment(self):
        batch_client = boto3.client('batch',
                                    config=botocore.client.Config(max_pool_connections=self.image_manager.get_threads(),
                                                                  retries={
                                                                      'max_attempts': AWS_MAX_RETRIES,
                                                                      'mode': 'standard'}))
        # Inform user starting to create CE.
        message = f'Disable Compute Environment {self.compute_environment_name}'
        print(message)
        logging.info(message)

        # First Disable CE.
        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/batch.html#Batch.Client.update_compute_environment
        batch_client.update_compute_environment(computeEnvironment=self.compute_environment_name, state='DISABLED')

        # Wait until CE is disabled.
        while True:
            # See https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/batch.html#Batch.Client.describe_compute_environments
            describe = self.__describe_compute_environments(self.compute_environment_name)
            computeEnvironment = describe['computeEnvironments'][0]
            state = computeEnvironment['state']
            status = computeEnvironment['status']
            if state == 'DISABLED' and status == 'VALID':
                break
            elif status == 'INVALID':
                reason = computeEnvironment['statusReason']
                raise Exception('Failed to create compute environment is invalid state: %s' % (reason))
            time.sleep(5)
        # Delete CE
        message = f'Deleting Compute Environment {self.compute_environment_name}'
        print(message)
        logging.info(message)
        batch_client.delete_compute_environment(computeEnvironment=self.compute_environment_name)
        # Wait until CE is disabled.
        while True:
            describe = self.__describe_compute_environments(self.compute_environment_name)
            if not describe['computeEnvironments']:
                break
            time.sleep(5)

    def create_job(self,
                   analysis_id=None,
                   analysis_name=None,
                   job_id=None,
                   local_project_folder=None,
                   remote_project_folder=None  # stub for cloud jobs.
                   ):
        return AWSJob(batch=self,
                         engine=self.engine,
                         analysis_id=analysis_id,
                         analysis_name=analysis_name,
                         job_id=job_id,
                         local_project_folder=local_project_folder,
                         remote_project_folder=remote_project_folder  # stub for cloud jobs.
                         )

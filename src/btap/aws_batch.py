from src.btap.constants import WORKER_CONTAINER_MEMORY
from src.btap.constants import WORKER_CONTAINER_VCPU
from src.btap.constants import WORKER_CONTAINER_STORAGE
import time
import logging
from random import random
from src.btap.aws_credentials import AWSCredentials
from src.btap.aws_iam_roles import IAMBatchJobRole
from src.btap.aws_job import AWSBTAPJob
from src.btap.aws_analysis_job import AWSAnalysisJob
from src.btap.common_paths import CommonPaths
from icecream import ic

# Role to give permissions to jobs to run.
BATCH_JOB_ROLE = 'arn:aws:iam::834599497928:role/batchJobRole'
# Role to give permissions to batch to run.
BATCH_SERVICE_ROLE = 'arn:aws:iam::834599497928:role/service-role/AWSBatchServiceRole'


class AWSBatch:

    def __init__(self,
                 image_manager=None,
                 compute_environment=None
                 ):
        self.image_manager = image_manager
        self.compute_environment_name = compute_environment.get_compute_environment_name()
        self.launch_template_name = f'{self._username()}_storage_template'
        self.job_queue_name = f'{self._username()}_{image_manager.image_name}_job_queue'
        self.job_def_name = f'{self._username()}_{image_manager.image_name}_job_def'


    def setup(self, container_vcpu = None, container_memory = None):
        self.__create_job_queue()
        self.__register_job_definition(unitVCpus=container_vcpu,
                                       unitMemory=container_memory)

    def tear_down(self):
        self.__deregister_job_definition()
        self.__delete_job_queue()


    def __aws_credentials(self):
        return AWSCredentials()

    def _username(self):
        return CommonPaths().get_username().replace('.', '_')


    def __describe_job_queues(self, job_queue_name, n=0):
        batch_client = AWSCredentials().batch_client
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

        batch_client = AWSCredentials().batch_client

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
                                  unitVCpus=None,
                                  unitMemory=None):

        # Store the aws service role arn for AWSBatchServiceRole. This role is created by default when AWSBatch
        # compute environment is created for the first time via the web console automatically.
        message = f'Creating Job Definition {self.job_def_name}'
        logging.info(message)
        print(message)
        batch_client = AWSCredentials().batch_client

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
        batch_client = AWSCredentials().batch_client

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

            batch_client = AWSCredentials().batch_client
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
            return True

    def create_job(self, job_id=None, reference_run=False):
        job=None
        if self.image_manager.image_name == 'btap_cli':
            job = AWSBTAPJob(batch=self, job_id=job_id)
        if self.image_manager.image_name == 'btap_batch':
            job = AWSAnalysisJob(batch=self, job_id=job_id, reference_run=reference_run)
        return job



    def get_active_jobs(self):

        # Connect to AWS Batch
        client = AWSCredentials().batch_client

        jobs = []
            # Make into a list
        job_status = ["SUBMITTED", "PENDING", "RUNNABLE",
                      "STARTING", "RUNNING"]
        for js in job_status:
            r = client.list_jobs(
                jobQueue=self.job_queue_name,
                jobStatus=js
            )
            jobs.extend(r["jobSummaryList"])
            while r.get("nextToken") is not None:
                r = client.list_jobs(
                    jobQueue=self.job_queue_name,
                    jobStatus=js,
                    nextToken=r["nextToken"]
                )
                jobs.extend(r["jobSummaryList"])

        # Subset to jobs with a given status
        jobs = [
            j for j in jobs if j["status"] in job_status
        ]

        # print("Number of jobs to clear from {}: {:,}".format(
        #     self.job_queue_name, len(jobs)
        # ))
        if len(jobs) == 0:
            return None
        return jobs


    def clear_queue(self):
        jobs =  self.get_active_jobs()
        for j in jobs:
            if j["status"] not in ["SUCCEEDED", "FAILED", "CANCELED"]:
                print("Cancelling {}".format(j["jobId"]))
                # Get a message to submit as justfication for the failure
                cancel_msg = "Cancelled by user\n"
                # Connect to AWS Batch
                client = AWSCredentials().batch_client
                client.cancel_job(jobId=j["jobId"], reason=cancel_msg)
                client.terminate_job(jobId=j["jobId"], reason=cancel_msg)



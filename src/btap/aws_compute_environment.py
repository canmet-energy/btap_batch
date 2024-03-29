from src.btap.constants import MAX_AWS_VCPUS
from src.btap.constants import AWS_BATCH_ALLOCATION_STRATEGY
from src.btap.constants import AWS_BATCH_COMPUTE_INSTANCE_TYPES
from src.btap.constants import MIN_AWS_VCPUS
from src.btap.constants import AWS_BATCH_DEFAULT_IMAGE
from src.btap.constants import INSTANCE_STORAGE_SIZE_GB
from src.btap.constants import AWS_VOLUME_TYPE
from src.btap.constants import IOPS_VALUE
import time
import logging
from random import random
from src.btap.aws_iam_roles import IAMBatchServiceRole
from src.btap.aws_ec2_info import AWS_EC2Info
from src.btap.common_paths import CommonPaths
from src.btap.aws_credentials import AWSCredentials
from icecream import ic

# Role to give permissions to jobs to run.
BATCH_JOB_ROLE = 'arn:aws:iam::834599497928:role/batchJobRole'
# Role to give permissions to batch to run.
BATCH_SERVICE_ROLE = 'arn:aws:iam::834599497928:role/service-role/AWSBatchServiceRole'


class AWSComputeEnvironment:
    def __init__(self, build_env_name = None, name =''):
        if build_env_name is None:
            build_env_name = CommonPaths().get_build_env_name().replace('.', '_')
        self._compute_environment_name = f"{build_env_name}_{name}_compute_environment"
        self.launch_template_name = f'{build_env_name}_{name}_storage_template'

    def get_compute_environment_name(self):
        return self._compute_environment_name

    def setup(self, maxvCpus=MAX_AWS_VCPUS):
        # This method creates batch infrastructure for user.
        launch_template = self.__add_storage_space_launch_template()
        self.__create_compute_environment(launch_template=launch_template,
                                          maxvCpus=maxvCpus)

    def tear_down(self):
        # This method creates batch infrastructure for user.
        # This method manages the teardown of the batch workflow. See methods for details.
        message = "Tearing down Compute Environment...."
        print(message)
        logging.info(message)
        self.__delete_compute_environment()


    # Short method that creates a template to increase the disk size of the containers. Default 100GB.
    def __add_storage_space_launch_template(self, sizegb=INSTANCE_STORAGE_SIZE_GB):
        self.ec2 = AWSCredentials().ec2_client

        launch_template = self.ec2.describe_launch_templates()['LaunchTemplates']
        if next((item for item in launch_template if item["LaunchTemplateName"] == self.launch_template_name),
                None) == None:
            message = f'Creating EC2 instance launch template using  with {sizegb} of space named {self.launch_template_name}'
            logging.info(message)
            print(message)
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
                                'DeleteOnTermination': True,
                                'Encrypted': False,
                                'VolumeSize': sizegb,
                                'VolumeType': AWS_VOLUME_TYPE,
                                'Iops': IOPS_VALUE
                            }
                        }
                    ]
                }
            )
        else:
            message = f"Launch Template {self.launch_template_name} already exists. Using existing."
            logging.info(message)
            print(message)
        return self.launch_template_name

    def __describe_compute_environments(self, compute_environment_name, n=0):
        batch_client = AWSCredentials().batch_client
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

    def __create_compute_environment(self,
                                     launch_template=None,
                                     allocationStrategy=AWS_BATCH_ALLOCATION_STRATEGY,
                                     minvCpus=MIN_AWS_VCPUS,
                                     maxvCpus=MAX_AWS_VCPUS,
                                     instanceTypes=AWS_BATCH_COMPUTE_INSTANCE_TYPES,
                                     imageId=AWS_BATCH_DEFAULT_IMAGE,
                                     subnets =  None,
                                     securityGroupIds = None,
                                     ):

        if subnets == None:
            subnets = AWS_EC2Info().subnet_id_list

        if securityGroupIds == None:
            securityGroupIds = AWS_EC2Info().securityGroupIds


        batch_client = AWSCredentials().batch_client
        # Inform user starting to create CE.
        message = f'Creating Compute Environment {self._compute_environment_name}'
        print(message)
        logging.info(message)

        # Call to create Compute environment.
        # See https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/batch.html#Batch.Client.create_compute_environment
        # and https://docs.aws.amazon.com/batch/latest/userguide/compute_environment_parameters.html#compute_environment_type
        response = batch_client.create_compute_environment(
            computeEnvironmentName=self._compute_environment_name,
            type='MANAGED',  # Allow AWS to manage instances.
            serviceRole=IAMBatchServiceRole().arn(),
            computeResources={
                'type': 'EC2',
                'allocationStrategy': allocationStrategy,
                'minvCpus': minvCpus,
                'maxvCpus': maxvCpus,
                # 'desiredvCpus': DESIRED_AWS_VCPUS,
                'instanceTypes': instanceTypes,
                'imageId': imageId,
                'subnets': subnets,
                'securityGroupIds': securityGroupIds,
                'instanceRole': 'ecsInstanceRole',
                'launchTemplate': {
                    'launchTemplateName': launch_template}
            }
        )
        # Check state of creating CE.
        while True:
            # See https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/batch.html#Batch.Client.describe_compute_environments
            describe = self.__describe_compute_environments(self._compute_environment_name)

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

    def __delete_compute_environment(self, computeEnvironmentName = None):
        if not computeEnvironmentName is None:
            self._compute_environment_name = computeEnvironmentName
        describe = self.__describe_compute_environments(self._compute_environment_name)
        if len(describe['computeEnvironments']) != 0:
            batch_client = AWSCredentials().batch_client
            # Inform user starting to create CE.
            message = f'Disable Compute Environment {self._compute_environment_name}'
            print(message)
            logging.info(message)

            # First Disable CE.
            # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/batch.html#Batch.Client.update_compute_environment
            batch_client.update_compute_environment(computeEnvironment=self._compute_environment_name, state='DISABLED')

            # Wait until CE is disabled.
            while True:
                # See https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/batch.html#Batch.Client.describe_compute_environments
                describe = self.__describe_compute_environments(self._compute_environment_name)
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
            message = f'Deleting Compute Environment {self._compute_environment_name}'
            print(message)
            logging.info(message)
            batch_client.delete_compute_environment(computeEnvironment=self._compute_environment_name)
            # Wait until CE is disabled.
            while True:
                describe = self.__describe_compute_environments(self._compute_environment_name)
                if not describe['computeEnvironments']:
                    break
                time.sleep(5)
        else:
            print(f"Compute Environment {self._compute_environment_name} already deleted.")
            return True

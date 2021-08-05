# Todo: Build Elimination and Sensitivity Analysis workflows to inform Optimization and Parametric Workflows.
# Todo: Integrate with Pathways viewer.(Done. works with Excel output. Need to add measures)
# Todo: Secure local postgre docker container with a better(random) password
# docker kill btap_postgres

from icecream import ic
import itertools
import copy
import multiprocessing
import concurrent.futures
import shutil
from sklearn import preprocessing
import numpy as np
from pymoo.factory import get_algorithm, get_crossover, get_mutation, get_sampling
from pymoo.optimize import minimize
from pymoo.model.problem import Problem
from multiprocessing.pool import ThreadPool
import docker
from docker.errors import DockerException
import json
import yaml
import errno
import boto3
from botocore.config import Config
import botocore
import os
import time
import uuid
import datetime
import sys
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sqlalchemy.types
import re
import glob
from functools import wraps
import logging
from pymoo.visualization.scatter import Scatter
import socket
import ssl
import requests

# seed the pseudorandom number generator
from random import seed
from random import random
import numpy as np
np.random.seed(123)
import matplotlib.pyplot as plt
from skopt.space import Space
from skopt.sampler import Sobol
from skopt.sampler import Lhs
import traceback
import pickle
import gzip
import pathlib
import csv

seed(1)


BTAP_BATCH_VERSION='1.0.002'

# Maximum AWS CPUS that AWS will allocate for the run.
MAX_AWS_VCPUS = 500
# Number of VCPUs that AWSBatch will initialize with.
# DESIRED_AWS_VCPUS = 50 # Not used currently
# Minimum number of CPU should be set to zero.
MIN_AWS_VCPUS = 0
# Container allocated VCPU
CONTAINER_VCPU = 1
# Container allocated Memory (MB)
CONTAINER_MEMORY = 2000
# Container Storage (GB)
CONTAINER_STORAGE = 100
# AWS Batch Allocation Strategy. https://docs.aws.amazon.com/batch/latest/userguide/allocation-strategies.html
AWS_BATCH_ALLOCATION_STRATEGY = 'BEST_FIT_PROGRESSIVE'
# AWS Compute instances types..setting to optimal to let AWS figure it out for me.
# https://docs.aws.amazon.com/batch/latest/userguide/create-compute-environment.html
AWS_BATCH_COMPUTE_INSTANCE_TYPES =  ['optimal']
# Using the public Amazon Linux 2 AMI to make use of overlay disk storage. Has all aws goodies already installed,
# makeing secure session manager possible, and has docker pre-installed.
AWS_BATCH_DEFAULT_IMAGE = 'ami-0a06b44c462364156'


# Location of Docker folder that contains information to build the btap image locally and on aws.
DOCKERFILES_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'Dockerfiles')
# Location of previously run baseline simulations to compare with design scenarios
BASELINE_RESULTS = os.path.join(os.path.dirname(os.path.realpath(__file__)),'resources', 'baselines.xlsx')
# CER Fuel costs data. Will be used for NPV more extensively.
CER_UTILITY_COSTS = os.path.join(os.path.dirname(os.path.realpath(__file__)),'resources', 'ceb_fuel_end_use_prices.csv')

# These resources were created either by hand or default from the AWS web console. If moving this to another aws account,
# recreate these 3 items in the new account. Also create s3 bucket to use named based account id like we did here.
# That should be all you need.. Ideally these should be created programmatically.
# Role used to build images on AWS Codebuild and ECR.
CLOUD_BUILD_SERVICE_ROLE = 'arn:aws:iam::834599497928:role/service-role/codebuild-test-service-role'
# Role to give permissions to jobs to run.
BATCH_JOB_ROLE = 'arn:aws:iam::834599497928:role/batchJobRole'
BATCH_SERVICE_ROLE = 'arn:aws:iam::834599497928:role/service-role/AWSBatchServiceRole'
# Max Retry attemps for aws clients.
AWS_MAX_RETRIES=12

#Custom exceptions
class FailedSimulationException(Exception):
    pass
#S3 Operations
class S3:
    #Constructor
    def __init__(self):
        # Create the s3 client.
        config = Config(retries={ 'max_attempts': AWS_MAX_RETRIES, 'mode': 'standard'})
        self.s3 = boto3.client('s3',config=config)
    # Method to delete a bucket.
    def delete_bucket(self, bucket_name):
        message = f'Deleting S3 {bucket_name}'
        print(message)
        logging.info(message)
        self.s3.delete_bucket(Bucket=bucket_name)

    # Method to create a bucket.
    def create_bucket(self, bucket_name):
        message =f'Creating S3 {bucket_name}'
        print(message)
        logging.info(message)
        response = self.s3.create_bucket(
            ACL='private',
            Bucket=bucket_name,
            CreateBucketConfiguration={
                'LocationConstraint': 'ca-central-1'
            },
            ObjectLockEnabledForBucket=False
        )
    # Method to download folder.
    def download_s3_folder(self, bucket_name, s3_folder, local_dir=None):
        """
        Download the contents of a folder directory
        Args:
            bucket_name: the name of the s3 bucket
            s3_folder: the folder path in the s3 bucket
            local_dir: a relative or absolute directory path in the local file system
        """
        bucket = self.s3.Bucket(bucket_name)
        for obj in bucket.objects.filter(Prefix=s3_folder):
            target = obj.key if local_dir is None \
                else os.path.join(local_dir, os.path.basename(obj.key))
            if not os.path.exists(os.path.dirname(target)):
                os.makedirs(os.path.dirname(target))
            bucket.download_file(obj.key, target)
    # Delete S3 folder.
    def delete_s3_folder(self, bucket, folder):
        bucket = self.s3.Bucket(bucket)
        bucket.objects.filter(Prefix=folder).delete()
    # Copy folder to S3
    def copy_folder_to_s3(self, bucket_name, source_folder, target_folder):
        # Get files in folder.
        files = glob.glob(source_folder + '/**/*', recursive=True)
        # Go through all files recursively.
        for file in files:
            target_path = file.replace(source_folder, target_folder)
            # s3 likes forward slashes.
            target_path = target_path.replace('\\', '/')
            message = "Uploading %s..." % target_path
            logging.info(message)

            self.s3.upload_file(file, bucket_name, target_path)

    def upload_file(self,file, bucket_name, target_path):
        logging.info(f"uploading {file} to s3 bucket {bucket_name} target {target_path}")
        self.s3.upload_file(file, bucket_name, target_path)

# Class to authenticate to AWS.
class AWSCredentials:
    # Initialize with required clients.
    def __init__(self):
        config = Config(retries={ 'max_attempts': AWS_MAX_RETRIES, 'mode': 'standard'})
        self.sts = boto3.client('sts',config=config)
        self.iam = boto3.client('iam',config=config)
        try:
            self.account_id = self.sts.get_caller_identity()["Account"]
            self.user_id = self.sts.get_caller_identity()["UserId"]
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'ExpiredToken':
                logging.error("Your session has expired while running. Please renew your aws credentials and consider running this in an amazon instance if your run is longer than 2 hours")
                exit(1)
            else:
                print("Unexpected botocore.exceptions.ClientError error: %s" % e)
                exit(1)
        except botocore.exceptions.SSLError as e:
            logging.error("SSL validation failed.. This is usually because you are behind a VPN. Please do not use a VPN.")
            exit(1)



        #get aws username from userid.
        if re.compile(".*:(.*)@.*").search(self.user_id) is None:
            self.user_name = 'osdev'
        else:
            self.user_name = re.compile(".*:(.*)@.*").search(self.user_id)[1]

        self.user_arn = self.sts.get_caller_identity()["Arn"]
        self.region_name = boto3.Session().region_name

        # Store the aws service role arn for AWSBatchServiceRole. This role is created by default when AWSBatch
        # compute environment is created for the first time via the web console automatically.
        # To-do: Create and delete this programmatically.
        service_roles = self.iam.list_roles(PathPrefix='/service-role/')['Roles']
        self.aws_batch_service_role = \
            list(filter(lambda role: role['RoleName'] == 'AWSBatchServiceRole', service_roles))[0]['Arn']

# Class to manage AWS images.
class AWSImage:
    def __init__(self,
                 image_name=None,
                 git_api_token= None,
                 os_version=None,
                 btap_costing_branch=None,
                 os_standards_branch=None,
                 rebuild=False):
        self.credentials = AWSCredentials()
        self.bucket = self.credentials.account_id
        self.git_api_token = git_api_token
        self.os_version = os_version
        self.btap_costing_branch = btap_costing_branch
        self.os_standards_branch = os_standards_branch
        self.image_name = image_name
        self.image_tag = self.credentials.user_name
        self.image_full_name = f'{self.credentials.account_id}.dkr.ecr.{self.credentials.region_name}.amazonaws.com/' + self.image_name + ':' + self.image_tag
        self.ecr_client = boto3.client('ecr')
        # Todo create cloud build service role.
        self.cloudbuild_service_role = CLOUD_BUILD_SERVICE_ROLE
        self.iam = boto3.client('iam')
        self.s3 = boto3.client('s3',)
        self.ecr = boto3.client('ecr')
        self.cloudwatch = boto3.client('logs')
        repositories = self.ecr_client.describe_repositories()['repositories']
        if next((item for item in repositories if item["repositoryName"] == self.image_name), None) == None:
            message = f"Creating repository {self.image_name}"
            logging.info(message)
            self.ecr_client.create_repository(repositoryName=self.image_name)
        else:
            message = f"Repository {self.image_name} already exists. Using existing."
            logging.info(message)

        # Check if image exists.. if not it will create an image from the latest git hub reps.
        # Get list of tags for image name on aws.
        available_tags = sum(
            [d.get('imageTags', [None]) for d in self.ecr.describe_images(repositoryName=image_name)['imageDetails']],
            [])

        if not self.image_tag in available_tags:
            message = f"The tag {self.image_tag} does not exist in the AWS ECR repository for {self.image_name}. Creating from latest sources."
            logging.info(message)
            print(message)

        if rebuild == True:
            message = f"User requested build from sources. image:{self.image_name}:{self.image_tag}  "
            logging.info(message)
            print(message)

        if rebuild == True or not self.image_tag in available_tags:
            message = f"Building image from sources.\n\ttag:{self.image_tag}\n\timage:{self.image_name}\n\tos_version:{self.os_version}\n\tbtap_costing_branch:{self.btap_costing_branch}\n\tos_standards_branch:{self.os_standards_branch}"
            logging.info(message)
            print(message)
            self.build_image()
    def build_image(self):
        # Codebuild image.
        codebuild = boto3.client('codebuild')

        # Upload files to S3 using custom s3 class to a user folder.
        s3 = S3()
        source_folder = os.path.join(DOCKERFILES_FOLDER, self.image_name)
        # Copies Dockerfile from btap_cli repository
        url = 'https://raw.githubusercontent.com/canmet-energy/btap_cli/main/Dockerfile'
        r = requests.get(url, allow_redirects=True)
        open(os.path.join(source_folder,'Dockerfile'), 'wb').write(r.content)

        s3.copy_folder_to_s3(self.bucket, source_folder, self.credentials.user_name + '/' + self.image_name)
        s3_location = 's3://' + self.bucket + '/' + self.credentials.user_name + '/' + self.image_name
        message = f"Copied build configuration files:\n\t from {source_folder}\n to \n\t {s3_location}"
        logging.info(message)
        print(message)

        # create project if it does not exist. This set the environment variables for the build. Note: if you change add
        # ENV to the build process.. you must DELETE the build project first!!!
        if not self.image_name in codebuild.list_projects()['projects']:
            # create build project
            codebuild.create_project(
                name=self.image_name,
                description='string',
                source={
                    'type': 'S3',
                    'location': self.bucket + '/' + self.credentials.user_name + '/' + self.image_name + '/'
                },
                artifacts={
                    'type': 'NO_ARTIFACTS',
                },
                environment={
                    'type': 'LINUX_CONTAINER',
                    'image': 'aws/codebuild/standard:4.0',
                    'computeType': 'BUILD_GENERAL1_2XLARGE',
                    'environmentVariables': [
                        {
                            "name": "AWS_DEFAULT_REGION",
                            "value": self.credentials.region_name
                        },
                        {
                            "name": "AWS_ACCOUNT_ID",
                            "value": self.credentials.account_id
                        },
                        {
                            "name": "IMAGE_REPO_NAME",
                            "value": self.image_name
                        },
                        {
                            "name": "IMAGE_TAG",
                            "value": self.credentials.user_name
                        },
                        {
                            "name": "GIT_API_TOKEN",
                            "value": self.git_api_token
                        },
                        {
                            "name": "OS_STANDARDS_BRANCH",
                            "value": self.os_standards_branch
                        },
                        {
                            "name": "BTAP_COSTING_BRANCH",
                            "value": self.btap_costing_branch
                        },
                        {
                            "name": "OPENSTUDIO_VERSION",
                            "value": self.os_version
                        },
                    ],
                    'privilegedMode': True
                },
                serviceRole=self.cloudbuild_service_role,
            )

        # Start building image.
        start = time.time()
        message = f'Building Image {self.image_name} on Amazon CloudBuild, will take ~10m'
        print(message)
        logging.info(message)
        environmentVariablesOverride = [
            {
                "name": "IMAGE_REPO_NAME",
                "value": self.image_name
            },
            {
                "name": "IMAGE_TAG",
                "value": self.credentials.user_name
            },
            {
                "name": "GIT_API_TOKEN",
                "value": self.git_api_token
            },
            {
                "name": "OS_STANDARDS_BRANCH",
                "value": self.os_standards_branch
            },
            {
                "name": "BTAP_COSTING_BRANCH",
                "value": self.btap_costing_branch
            },
            {
                "name": "OPENSTUDIO_VERSION",
                "value": self.os_version
            }]
        source_location = self.bucket + '/' + self.credentials.user_name + '/' + self.image_name + '/'
        message=f'Code build image env overrides {environmentVariablesOverride}'
        logging.info(message)

        message=f"Building from sources at {source_location}"
        logging.info(message)

        response = codebuild.start_build(projectName=self.image_name,
                                         sourceTypeOverride='S3',
                                         sourceLocationOverride= source_location,
                                         environmentVariablesOverride=environmentVariablesOverride
                                         )
        build_id = response['build']['id']
        # Check state of creating CE.
        while True:
            status = codebuild.batch_get_builds(ids=[build_id])['builds'][0]['buildStatus']
            # If CE is in valid state, inform user and break from loop.
            if status == 'SUCCEEDED':
                message = f'Image {self.image_name} Created on Amazon. \nImage built in {time.time() - start}'
                logging.info(message)
                print(message)
                break
            # If CE is in invalid state... break
            elif status == 'FAILED' or status == 'FAULT' or status == 'TIMED_OUT' or status == 'STOPPED':
                message = f'Build Failed: See amazon web console Codebuild to determine error. buildID:{build_id}'
                print(message)
                logging.error(message)
                exit(1)
            #Check status every 5 secs.
            time.sleep(5)

# Class to run batch simulations on AWS>
class AWSBatch:
    """
    This class  manages creating an aws batch workflow, simplifies creating jobs and manages tear down of the
    aws batch. This is opposed to using the aws web console to configure the batch run. That method can lead to problems in
    management and replication.

    This follows the principal that this class should be all your need to run an aws batch workflow on a
    clean aws system provided by nrcan's CIOSB. This may be used outside of NRCan's network, but has not been tested to
    work outside on vanilla aws accounts.
    """

    def __init__(self,
                 analysis_id=None,
                 btap_image_name='btap_private_cli',
                 rebuild_image=False,
                 git_api_token= None,
                 os_version=None,
                 btap_costing_branch=None,
                 os_standards_branch=None,
                 threads = 24
                 ):
        self.credentials = AWSCredentials()
        bucket = self.credentials.account_id
        # Create the aws clients required.
        config = Config(retries={ 'max_attempts': AWS_MAX_RETRIES, 'mode': 'standard'})
        self.ec2 = boto3.client('ec2', config = config)
        self.batch = boto3.client('batch',config=botocore.client.Config(max_pool_connections=threads,retries={'max_attempts': AWS_MAX_RETRIES, 'mode': 'standard'}))
        self.iam = boto3.client('iam', config = config)
        self.s3 = boto3.client('s3',config=botocore.client.Config(max_pool_connections=threads,retries={'max_attempts': AWS_MAX_RETRIES, 'mode': 'standard'}))
        self.cloudwatch = boto3.client('logs')

        # Create image helper object.
        self.btap_image = AWSImage(image_name=btap_image_name,
                                   rebuild = rebuild_image,
                                   git_api_token=git_api_token,
                                   os_version=os_version,
                                   btap_costing_branch=btap_costing_branch,
                                   os_standards_branch=os_standards_branch,
                                   )
        # This is the role with permissions inside the docker containers. Created by aws web console. (todo: automate creations and destruction)
        self.batch_job_role = BATCH_JOB_ROLE
        # This is the role with the permissions to create batch runs. Created by aws web console. (todo: automate creations and destruction)
        self.aws_batch_service_role = BATCH_SERVICE_ROLE

        # Set Analysis Id.
        if analysis_id == None:
            self.analysis_id = uuid.uuid4()
        else:
            self.analysis_id = analysis_id

        # Compute id is the same as analysis id but stringed.
        self.compute_environment_id = f"{self.analysis_id}"

        # Set up the job def as a suffix of the analysis id"
        self.job_def_id = f"{self.compute_environment_id}_job_def"

        # Set up the job queue id as the suffix of the analysis id.
        self.job_queue_id = f"{self.compute_environment_id}_job_queue"

        # Store the subnets into a list. This was set up by NRCan.
        subnets = self.ec2.describe_subnets()['Subnets']
        self.subnet_id_list = [subnet['SubnetId'] for subnet in subnets]

        # Store the security groups into a list. This was set up by NRCan.
        security_groups = self.ec2.describe_security_groups()["SecurityGroups"]
        self.securityGroupIds = [security_group['GroupId'] for security_group in security_groups]

    # This method is a helper to print/stream logs.
    def printLogs(self, logGroupName, logStreamName, startTime):
        kwargs = {'logGroupName': logGroupName,
                  'logStreamName': logStreamName,
                  'startTime': startTime,
                  'startFromHead': True}

        lastTimestamp = ''
        while True:
            logEvents = self.cloudwatch.get_log_events(**kwargs)

            for event in logEvents['events']:
                lastTimestamp = event['timestamp']
                timestamp = datetime.utcfromtimestamp(lastTimestamp / 1000.0).isoformat()
                print
                '[%s] %s' % ((timestamp + ".000")[:23] + 'Z', event['message'])

            nextToken = logEvents['nextForwardToken']
            if nextToken and kwargs.get('nextToken') != nextToken:
                kwargs['nextToken'] = nextToken
            else:
                break
        return lastTimestamp

    # This method is a helper to print/stream logs.
    def getLogStream(self, logGroupName, jobName, jobId):
        response = self.cloudwatch.describe_log_streams(
            logGroupName=logGroupName,
            logStreamNamePrefix=jobName + '/' + jobId
        )
        logStreams = response['logStreams']
        if not logStreams:
            return ''
        else:
            return logStreams[0]['logStreamName']

    # Short method that creates a template to increase the disk size of the containers. Default 100GB.
    def add_storage_space_launch_template(self, sizegb=CONTAINER_STORAGE):
        template_name = f'{self.credentials.account_id}_storage'
        launch_template = self.ec2.describe_launch_templates()['LaunchTemplates']
        if next((item for item in launch_template if item["LaunchTemplateName"] == template_name), None) == None:
            message = f'Creating EC2 instance launch template with 100GB of space named {template_name}'
            logging.info(message)
            response = self.ec2.create_launch_template(
                DryRun=False,
                LaunchTemplateName=template_name,
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
            message = f"Launch Template {template_name} already exists. Using existing."
            logging.info(message)
        return template_name

    #
    def delete_storage_space_launch_template(self):
        template_name = f'{self.credentials.account_id}_storage'
        response = self.ec2.delete_launch_template(
            LaunchTemplateName=template_name
        )

    def create_compute_environment(self):
        # Inform user starting to create CE.
        message=f'Creating Compute Environment {self.compute_environment_id}'
        print(message)
        logging.info(message)

        # Call to create Compute environment.
        # See https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/batch.html#Batch.Client.create_compute_environment
        response = self.batch.create_compute_environment(
            computeEnvironmentName=self.compute_environment_id,
            type='MANAGED',  # Allow AWS to manage instances.
            serviceRole=self.aws_batch_service_role,
            computeResources={
                'type': 'EC2',
                'allocationStrategy': AWS_BATCH_ALLOCATION_STRATEGY,
                'minvCpus': MIN_AWS_VCPUS,
                'maxvCpus': MAX_AWS_VCPUS,
                #'desiredvCpus': DESIRED_AWS_VCPUS,
                'instanceTypes': AWS_BATCH_COMPUTE_INSTANCE_TYPES,
                'imageId': AWS_BATCH_DEFAULT_IMAGE,
                'subnets': self.subnet_id_list,
                'securityGroupIds': self.securityGroupIds,
                'instanceRole': 'ecsInstanceRole',
                'launchTemplate': {

                    'launchTemplateName': self.add_storage_space_launch_template()}
            }
        )
        # Check state of creating CE.
        while True:
            # See https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/batch.html#Batch.Client.describe_compute_environments
            describe = self.describe_compute_environments(self.compute_environment_id)
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

    def delete_compute_environment(self):
        # Inform user starting to create CE.
        message =f'Disable Compute Environment {self.compute_environment_id}'
        print(message)
        logging.info(message)

        # First Disable CE.
        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/batch.html#Batch.Client.update_compute_environment
        self.batch.update_compute_environment(computeEnvironment=self.compute_environment_id, state='DISABLED')

        # Wait until CE is disabled.
        while True:
            # See https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/batch.html#Batch.Client.describe_compute_environments
            describe = self.describe_compute_environments(self.compute_environment_id)
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
        message=f'Deleting Compute Environment {self.compute_environment_id}'
        print(message)
        logging.info(message)
        self.batch.delete_compute_environment(computeEnvironment=self.compute_environment_id)
        # Wait until CE is disabled.
        while True:
            describe = self.describe_compute_environments(self.compute_environment_id)
            if not describe['computeEnvironments']:
                break
            time.sleep(5)

    def delete_job_queue(self):
        # Disable Queue
        # Tell user
        message = f'Disable Job Queue {self.job_queue_id}'
        print(message)
        logging.info(message)
        # See https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/batch.html#Batch.Client.update_job_queue
        self.batch.update_job_queue(jobQueue=self.job_queue_id, state='DISABLED')
        while True:
            # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/batch.html#Batch.Client.describe_job_queues
            describe = self.describe_job_queues(self.job_queue_id)
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
        message = f'Delete Job Queue {self.job_queue_id}'
        print(message)
        logging.info(message)

        # See https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/batch.html#Batch.Client.delete_job_queue
        response = self.batch.delete_job_queue(jobQueue=self.job_queue_id)
        # Wait until queue is deleted.
        while True:
            # See https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/batch.html#Batch.Client.describe_job_queues
            describe = self.describe_job_queues(self.job_queue_id)
            if not describe['jobQueues']:
                break
            time.sleep(5)
        return response

    def delete_job_definition(self):
        message = f'Disable Job Definition {self.job_def_id}'
        print(message)
        logging.info(message)
        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/batch.html#Batch.Client.describe_job_definitions
        describe = self.batch.describe_job_definitions(jobDefinitionName=self.job_def_id)
        # See https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/batch.html#Batch.Client.deregister_job_definition
        response = self.batch.deregister_job_definition(
            jobDefinition=describe['jobDefinitions'][0]['jobDefinitionArn'])
        return response

    def create_job_queue(self):
        message=f'Creating Job Queue {self.job_queue_id}'
        logging.info(message)
        print(message)

        response = self.batch.create_job_queue(jobQueueName=self.job_queue_id,
                                               priority=100,
                                               computeEnvironmentOrder=[
                                                   {
                                                       'order': 0,
                                                       'computeEnvironment': self.compute_environment_id
                                                   }
                                               ])

        while True:
            describe = self.describe_job_queues(self.job_queue_id)
            jobQueue = describe['jobQueues'][0]
            status = jobQueue['status']
            state = jobQueue['state']
            if status == 'VALID' and state == 'ENABLED':
                message = f'Created Job Queue {self.job_queue_id}, You can monitor your job queue on the AWS Batch management console dashboard.'
                logging.info(message)
                print(message)
                break
            elif status == 'INVALID':
                reason = jobQueue['statusReason']
                message = f'Failed to create job queue: {reason}'
                logging.error( message )
                exit(1)
            time.sleep(5)

        return response

    def register_job_definition(self,
                                unitVCpus=CONTAINER_VCPU,
                                unitMemory=CONTAINER_MEMORY):

        # Store the aws service role arn for AWSBatchServiceRole. This role is created by default when AWSBatch
        # compute environment is created for the first time via the web console automatically.

        message =f'Creating Job Definition {self.job_def_id}'
        logging.info(message)
        print(message)

        response = self.batch.register_job_definition(jobDefinitionName=self.job_def_id,
                                                      type='container',
                                                      containerProperties={
                                                          'image': self.btap_image.image_full_name,
                                                          'vcpus': unitVCpus,
                                                          'memory': unitMemory,
                                                          'privileged': True,
                                                          'jobRoleArn': self.batch_job_role
                                                      })

        return response

    def create_batch_workflow(self):
        # This method creates analysis id for batch run. See methods for details.
        self.create_compute_environment()
        self.create_job_queue()
        self.register_job_definition()

    def shutdown_batch_workflow(self, ):
        # This method manages the teardown of the batch workflow. See methods for details.
        self.delete_job_definition()
        self.delete_job_queue()
        self.delete_compute_environment()

    def submit_job(self, jobName='test', debug=False, command=["/bin/bash", "-c",
                                                               f"bundle exec ruby btap_cli.rb --building_type FullServiceRestaurant --template NECB2017 --enable_costing true "]):
        # Tell user.


        # See https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/batch.html#Batch.Client.submit_job
        submitJobResponse = self.submit_job_wrapper(command, jobName)

        jobId = submitJobResponse['jobId']
        message = f"Submitted job_id {jobId} with job name {jobName} to the job queue {self.job_queue_id}"
        logging.info(message)
        running = False
        startTime = 0
        logGroupName = '/aws/batch/job'
        result = 'FAILED'
        while debug:
            # Don't hammer AWS.. make queries every minute for the run status
            time.sleep(60 + random())
            describeJobsResponse = self.get_job_status(jobId)
            status = describeJobsResponse['jobs'][0]['status']
            if status == 'SUCCEEDED':
                message = 'SUCCEEDED - Job [%s - %s] %s' % (jobName, jobId, status)
                logging.info(message)
                print(message)
                result = 'SUCCEEDED'
                break
            elif status == 'FAILED':
                message = 'FAILED - Job [%s - %s] %s' % (jobName, jobId, status)
                logging.error(message)
                result = 'FAILED'
                break
            elif status == 'RUNNING':
                # Commented out logstream.
                #logStreamName = self.getLogStream(logGroupName, jobName, jobId)
                if not running: #and logStreamName:
                    running = True
                    # print('Output [%s]:\n %s' % (logStreamName, '=' * 80))
                #if logStreamName:
                    #startTime = self.printLogs(logGroupName, logStreamName, startTime) + 1
            else:
                message = 'UNKNOWN - Job [%s - %s] is %-9s' % (jobName, jobId, status)
                #logging.info(message)
                sys.stdout.flush()
        return result

    def submit_job_wrapper(self, command, jobName, n=0):
        try:
            submitJobResponse = self.batch.submit_job(
                jobName=jobName,
                jobQueue=self.job_queue_id,
                jobDefinition=self.job_def_id,
                containerOverrides={'command': command}
            )
            return submitJobResponse
        except:
            #Implementing exponential backoff
            if n==8:
                logging.exception(f'Failed to submit job {jobName} in 7 tries while using exponential backoff. Error was {sys.exc_info()[0]} ')
            wait_time = 2 ** n + random()
            logging.warning(f"Implementing exponential backoff for job {jobName} for {wait_time}s")
            time.sleep(wait_time)
            return self.submit_job_wrapper( command, jobName, n=n+1)

    def get_job_status(self, jobId, n=0):
        try:
            describeJobsResponse = self.batch.describe_jobs(jobs=[jobId])
            return describeJobsResponse
        except:
            if n==8:
                raise(f'Failed to get job status for {jobId} in 7 tries while using exponential backoff.')
            wait_time = 2 ** n + random()
            logging.warning(f"Implementing exponential backoff for job {jobId} for {wait_time}s")
            time.sleep( wait_time )
            return self.get_job_status(jobId, n=n+1)

    def describe_job_queues(self, job_queue_id, n=0):
        try:
            # See https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/batch.html#Batch.Client.describe_job_queues
            return self.batch.describe_job_queues(jobQueues=[job_queue_id])
        except:
            if n == 8:
                raise (
                    f'Failed to get job Queue status for {job_queue_id} in 7 tries while using exponential backoff.')
            wait_time = 2 ** n + random()
            logging.warning(f"Implementing exponential backoff for job {job_queue_id} for {wait_time}s")
            time.sleep(wait_time)
            return self.describe_job_queues(job_queue_id, n=n + 1)

    def describe_compute_environments(self, compute_environment_id, n=0):
        try:
            return self.batch.describe_compute_environments(computeEnvironments=[compute_environment_id])
        except:
            if n == 8:
                raise (
                    f'Failed to get job Queue status for {compute_environment_id} in 7 tries while using exponential backoff.')
            wait_time = 2 ** n + random()
            logging.warning(f"Implementing exponential backoff for job {compute_environment_id} for {wait_time}s")
            time.sleep(wait_time)
            return self.describe_compute_environments(compute_environment_id, n=n + 1)

# Class to manage local docker images.
class Docker:
    def __init__(self,
                 # name of docker image created
                 image_name='btap_private_cli',
                 # If set to true will force a rebuild of the image to the most recent sources.
                 nocache=False,
                 # git token for accessing private repos
                 git_api_token='None',
                 # Standards branch or revision to be used.
                 os_standards_branch='nrcan',
                 # btap_costing branch or revision to be used.
                 btap_costing_branch='master',
                 # openstudio version (used to access old versions if needed)
                 os_version='3.0.1'):
        # Git api token
        self.git_api_token = git_api_token
        # https://github.com/NREL/openstudio-standards/branches should ideally use nrcan
        self.os_standards_branch = os_standards_branch
        # https://github.com/NREL/openstudio-standards/branches should ideally use master
        self.btap_costing_branch = btap_costing_branch
        # OS version.. currently supports 3.0.1
        self.os_version = os_version
        # image name
        self.image_name = image_name
        # if nocache set to True.. will build image from scratch.
        self.nocache = nocache
        # Get the folder of this python file.
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        # determines folder of docker folder relative to this file.
        self.dockerfile = os.path.join(DOCKERFILES_FOLDER, self.image_name)
        # Copies Dockerfile from btap_cli repository
        url = 'https://raw.githubusercontent.com/canmet-energy/btap_cli/main/Dockerfile'
        r = requests.get(url, allow_redirects=True)

        file = open(os.path.join(self.dockerfile,'Dockerfile'), 'wb')
        file.write(r.content)
        file.close()
        # get a docker client object to run docker commands.
        self.docker_client = docker.from_env()
        # initialize image to None.. will assign later.
        self.image = None

    def build_docker_image(self, nocache=False):
        # Set timer to track how long it took to build.
        start = time.time()
        # add info to logger.
        message = f"Building image:{self.image_name}"
        logging.info(message)
        print(message)
        message = f"OS Version:{self.os_version}"
        logging.info(message)
        print(message)
        message = f"BTAP_COSTING Branch:{self.btap_costing_branch}"
        logging.info(message)
        print(message)
        message = f"OS_STANDARDS branch:{self.os_standards_branch}"
        logging.info(message)
        print(message)
        message = f"Dockerfolder being use to build image:{self.dockerfile}"
        logging.info(message)
        print(message)

        buildargs = {
            # Git token to access private repositories.
            'GIT_API_TOKEN': self.git_api_token,
            # Openstudio version.... like '3.0.1'
            'OPENSTUDIO_VERSION': self.os_version,
            # BTAP costing branch. Usually 'master'
            'BTAP_COSTING_BRANCH': self.btap_costing_branch,
            # Openstudio standards branch Usually 'nrcan'
            'OS_STANDARDS_BRANCH': self.os_standards_branch
        }

        # Will build image if does not already exist or if nocache is set true.

        # Get image if it exists.
        image = None
        try:
            image = self.docker_client.images.get(name=self.image_name)
        except docker.errors.ImageNotFound as err:
            image = None

        if image == None or self.nocache == True:
            message = f'Building Image:{self.image_name} will take ~10m... '
            logging.info(message)
            print(message)
            image, json_log = self.docker_client.images.build(
                                                                    # Path to docker file.
                                                                    path=self.dockerfile,
                                                                    # Image name
                                                                    tag=self.image_name,
                                                                    # nocache flag to build use cache or build from scratch.
                                                                    nocache=self.nocache,
                                                                    # ENV variables used in Dockerfile.
                                                                    buildargs=buildargs
                                                                   )
            for chunk in json_log:
                if 'stream' in chunk:
                    for line in chunk['stream'].splitlines():
                        logging.debug(line)
            # let use know that the image built sucessfully.
            message = f'Image built in {(time.time() - start)/60}m'
            logging.info(message)
            print(message)
        else:
            message = "Using existing image."
            logging.info(message)
            print(message)
        self.image = image

        # return image.. also is a part of the object.
        return self.image

    # remove docker image.. this is not use right now.
    def remove_docker_image(self):
        self.docker_client.images.remove(image=self.image_name, force=True)

    # This method will run the simulation with the general command. It passes all the information via the
    # run_options.yml file. This file was created ahead of this in the local_input_folder which is mounted to the
    # container. The output similarly will be placed in the local_output_folder using the datapoint_id as the new
    # folder name.
    def run_container_simulation(self,

                                 # run_options dict is used for finding the folder after the simulation is completed to store in the database.
                                 run_options=None,

                                 # mount point to container of input file(s)
                                 local_input_folder=None,

                                 # mount point for container to copy simulation files.
                                 local_output_folder=None,

                                 # Don't detach.. hold on to current thread.
                                 detach=False):

        # If local i/o folder is not set.. try to use folder where this file is.
        if local_input_folder == None:
            local_input_folder = os.path.join(self.dir_path, 'input')
        if local_output_folder == None:
            local_output_folder = os.path.join(self.dir_path, 'output')




        # Run the simulation
        jobName = f"{run_options[':analysis_id']}-{run_options[':datapoint_id']}"
        message = f"Submitting job {jobName}"
        logging.info(message)
        result = self.docker_client.containers.run(
                                                    # Local image name to use.
                                                    image=run_options[':image_name'],

                                                    # Command issued to container.
                                                    command='bundle exec ruby btap_cli.rb',

                                                    # host volume mount points and setting to read and write.
                                                    volumes={
                                                       local_output_folder: {
                                                           'bind': '/btap_costing/utilities/btap_cli/output',
                                                           'mode': 'rw'},
                                                       local_input_folder: {
                                                           'bind': '/btap_costing/utilities/btap_cli/input',
                                                           'mode': 'rw'},
                                                    },
                                                    # Will detach from current thread.. don't do it if you don't understand this.
                                                    detach=detach,
                                                    # This deletes the container on exit otherwise the container
                                                    # will bloat your system.
                                                    auto_remove=True
           )

        return result

# Parent Analysis class.
class BTAPAnalysis():

    def get_threads(self):
        return multiprocessing.cpu_count() - 2

    def get_local_osm_files(self):
        osm_list = {}
        for file in os.listdir(self.project_root):
            if file.endswith(".osm"):
                osm_list[os.path.splitext(file)[0]] = os.path.join(self.project_root, file)
        return osm_list

    # Constructor will
    def __init__(self, analysis_config_file=None, git_api_token=None):
        self.credentials = None
        self.aws_batch = None
        self.docker = None
        self.database = None
        self.btap_data_df = []
        self.failed_df = []
        # Making sure that used installed docker.
        find_docker = os.system("docker -v")
        if find_docker != 0:
            logging.exception("Docker is not installed on this system")

        # Try to access the docker daemon. If we cannot.. ask user to turn it on and then exit.
        try:
            docker.from_env()
        except DockerException as err:
            logging.error(f"Could not access Docker Daemon. Either it is not running, or you do not have permissions to run docker. {err}")
            exit(1)

        # Load Analysis File into variable
        if not os.path.isfile(analysis_config_file):
            logging.error(f"could not find analysis input file at {analysis_config_file}. Exiting")
            exit(1)
        # Open the yaml in analysis dict.
        with open(analysis_config_file, 'r') as stream:
            analysis = yaml.safe_load(stream)

        # Store analysis config and building_options.
        self.analysis_config = analysis[':analysis_configuration']
        self.building_options = analysis[':building_options']
        
        # Check user selected public version.. if so force costing to be turned off.
        if self.analysis_config[':image_name'] == 'btap_public_cli':
            self.analysis_config[':enable_costing'] = False

        # Set up project root.
        self.project_root = os.path.dirname(analysis_config_file)


        # Create required paths and folders for analysis
        self.create_paths_folders()

        # Initialize database
        self.init_database()

        if self.analysis_config[':compute_environment'] == 'aws_batch':
            # Start batch queue if required.
            self.aws_batch = self.initialize_aws_batch(git_api_token)
        else:
            self.docker = self.build_image(git_api_token=git_api_token)

    def init_database(self):

        self.database = BTAPDatabase()

    # This methods sets the pathnames and creates the input and output folders for the analysis. It also initilizes the
    # sql database.
    def create_paths_folders(self):

        # Create analysis folder
        os.makedirs(self.project_root, exist_ok=True)

        # Create unique id for the analysis
        self.analysis_config[':analysis_id'] = str(uuid.uuid4())

        # Tell user and logger id and names
        print(f'analysis_id is: {self.analysis_config[":analysis_id"]}')
        print(f'analysis_name is: {self.analysis_config[":analysis_name"]}')
        logging.info(f'analysis_id:{self.analysis_config[":analysis_id"]}')
        logging.info(f'analysis_name:{self.analysis_config[":analysis_name"]}')

        # Set analysis name folder.
        self.analysis_name_folder = os.path.join(self.project_root,
                                                 self.analysis_config[':analysis_name'])
        logging.info(f'analysis_folder:{self.analysis_config[":analysis_name"]}')
        self.analysis_id_folder = os.path.join(self.analysis_name_folder,
                                                 self.analysis_config[':analysis_id'])

        # Tell log we are deleting previous runs.
        message = f'Deleting previous runs from: {self.analysis_name_folder}'
        logging.info(message)
        print(message)
        # Check if folder exists
        if os.path.isdir(self.analysis_name_folder):
            # Remove old folder
            try:
                shutil.rmtree(self.analysis_name_folder)
            except PermissionError as err:
                message = f'Could not delete {self.analysis_name_folder}. Do you have a file open in that folder? Exiting'
                print(message)
                logging.error(message)
                exit(1)


        # create local input and output folders
        self.input_folder = os.path.join(self.analysis_id_folder,
                                         'input')
        self.output_folder = os.path.join(self.analysis_id_folder,
                                          'output')


        # Make input / output folder for mounting to container.
        os.makedirs(self.input_folder, exist_ok=True)
        os.makedirs(self.output_folder, exist_ok=True)
        logging.info(f"local mounted input folder:{self.input_folder}")
        logging.info(f"local mounted output folder:{self.output_folder}")

    def run_datapoint(self,run_options):
        # Start timer to track simulation time.
        start = time.time()
        try:
            # Save run options to a unique folder. Run options is modified to contain datapoint id, analysis_id and
            # other run information.
            # Create datapoint id and path to folder where input file should be saved.
            run_options[':btap_batch_version'] = BTAP_BATCH_VERSION
            run_options[':datapoint_id'] = str(uuid.uuid4())
            run_options[':analysis_id'] = self.analysis_config[':analysis_id']
            run_options[':analysis_name'] = self.analysis_config[':analysis_name']
            run_options[':run_annual_simulation'] = self.analysis_config[':run_annual_simulation']
            run_options[':enable_costing'] = self.analysis_config[':enable_costing']
            run_options[':compute_environment'] = self.analysis_config[':compute_environment']
            run_options[':s3_bucket'] = self.analysis_config[':s3_bucket']
            run_options[':image_name'] = self.analysis_config[':image_name']
            run_options[':output_variables'] = self.analysis_config[':output_variables']
            run_options[':output_meters'] = self.analysis_config[':output_meters']

            #S3 paths. Set base to username used in aws.
            if self.analysis_config[':compute_environment'] == 'aws_batch':
                self.credentials = AWSCredentials()
                s3_analysis_folder = os.path.join(self.credentials.user_name, run_options[':analysis_name'], run_options[':analysis_id']).replace('\\', '/')
                s3_datapoint_input_folder = os.path.join(s3_analysis_folder, 'input', run_options[':datapoint_id']).replace('\\', '/')
                s3_output_folder = os.path.join(s3_analysis_folder, 'output').replace('\\', '/')
                s3_datapoint_output_folder = os.path.join( s3_output_folder, run_options[':datapoint_id']).replace('\\', '/')
                s3_btap_data_path = os.path.join( s3_datapoint_output_folder, 'btap_data.json').replace('\\', '/')
                s3_error_txt_path = os.path.join(s3_datapoint_output_folder, 'error.txt').replace('\\', '/')

            # Local Paths
            local_datapoint_input_folder = os.path.join(self.input_folder, run_options[':datapoint_id'])
            local_datapoint_output_folder = os.path.join(self.output_folder, run_options[':datapoint_id'])
            local_run_option_file = os.path.join(local_datapoint_input_folder, 'run_options.yml')
            # Create path to btap_data.json file.
            local_btap_data_path = os.path.join(self.output_folder, run_options[':datapoint_id'],'btap_data.json')
            local_error_txt_path = os.path.join(self.output_folder, run_options[':datapoint_id'], 'error.txt')
            local_eplusout_sql_path = os.path.join(self.output_folder, run_options[':datapoint_id'],'run_dir','run','eplusout.sql')

            # Save run_option file for this simulation.
            os.makedirs(local_datapoint_input_folder, exist_ok=True)
            logging.info(f'saving simulation input file here:{local_run_option_file}')
            with open(local_run_option_file, 'w') as outfile:
                yaml.dump(run_options, outfile, encoding=('utf-8'))

            #Save custom osm file if required.
            local_osm_dict = self.get_local_osm_files()
            if run_options[':building_type'] in local_osm_dict:
                #copy osm file into input folder.
                shutil.copy(local_osm_dict[run_options[':building_type']], local_datapoint_input_folder)
                logging.info(f"Copying osm file from {local_osm_dict[run_options[':building_type']]} to {local_datapoint_input_folder}")

            if run_options[':compute_environment'] == 'aws_batch':

                message = f"Copying from {local_datapoint_input_folder} to bucket {self.analysis_config[':s3_bucket']} folder {s3_datapoint_input_folder}"
                logging.info(message)
                S3().copy_folder_to_s3( bucket_name=self.analysis_config[':s3_bucket'],
                                        source_folder=local_datapoint_input_folder,
                                        target_folder=s3_datapoint_input_folder)
                jobName = f"{run_options[':analysis_id']}-{run_options[':datapoint_id']}"
                bundle_command = f"bundle exec ruby btap_cli.rb --input_path s3://{self.analysis_config[':s3_bucket']}/{s3_datapoint_input_folder} --output_path s3://{self.analysis_config[':s3_bucket']}/{s3_output_folder} "
                # replace \ slashes to / slash for correct s3 convention.
                bundle_command = bundle_command.replace('\\', '/')
                self.aws_batch.submit_job(jobName=jobName, debug=True, command=["/bin/bash", "-c", bundle_command])

                btap_data = {}
                # add run options to dict.
                btap_data.update(run_options)

                # Get btap_data from s3
                message = f"Getting data from S3 bucket {self.analysis_config[':s3_bucket']} at path {s3_btap_data_path}"
                logging.info(message)
                content_object = boto3.resource('s3').Object(self.analysis_config[':s3_bucket'], s3_btap_data_path)
                btap_data.update(json.loads(content_object.get()['Body'].read().decode('utf-8')))
                # save url to datapoint output for Kamel.
                btap_data['datapoint_output_url'] = f"https://s3.console.aws.amazon.com/s3/buckets/{self.analysis_config[':s3_bucket']}?region=ca-central-1&prefix={s3_datapoint_output_folder}/"
            else:

                result = self.docker.run_container_simulation(
                                                            run_options = run_options,
                                                            local_input_folder = local_datapoint_input_folder,
                                                            local_output_folder = self.output_folder,
                                                            detach = False
                )



                # If file was not created...raise an error.
                if not os.path.isfile(local_btap_data_path):
                    raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), local_btap_data_path)

                # Create btap_data dict to store.
                btap_data = {}

                # add run options to dict.
                btap_data.update(run_options)

                # Open the btap Data file in analysis dict.
                file = open(local_btap_data_path, 'r')
                btap_data.update(json.load(file))
                file.close()

                # save output url.
                btap_data['datapoint_output_url'] = 'file:///' + os.path.join(local_datapoint_output_folder)



            # dump full run_options.yml file into database for convienience.
            btap_data['run_options'] = yaml.dump(run_options)

            # Need to zero this in costing btap_data.rb file otherwise may be NA.
            for item in ['energy_eui_heat recovery_gj_per_m_sq', 'energy_eui_heat rejection_gj_per_m_sq']:
                if not btap_data.get(item):
                    btap_data[item] = 0.0




            # Flag that is was successful.
            btap_data['success'] = True
            btap_data['simulation_time'] = time.time() - start

            #return btap_data
            return btap_data

        except Exception as error:
            error_msg = ''
            print(self.analysis_config)
            if self.analysis_config[':compute_environment'] == 'aws_batch':
                content_object = boto3.resource('s3').Object(run_options[':s3_bucket'], s3_error_txt_path)
                print(error_msg)
                error_msg= content_object.get()['Body'].read().decode('utf-8')
            else:
                with open(local_error_txt_path, 'r') as file:
                    error_msg = file.read()
            btap_data = {}
            btap_data.update(run_options)
            btap_data['success'] = False
            btap_data['container_error'] = str(error_msg)
            btap_data['run_options'] = yaml.dump(run_options)
            btap_data['datapoint_output_url'] = 'file:///' + os.path.join(local_datapoint_output_folder)
            #return btap_data
            return btap_data

    def build_image(self, git_api_token=None):

        docker = Docker(image_name=self.analysis_config[':image_name'],
                             git_api_token=git_api_token,
                             os_standards_branch=self.analysis_config[':os_standards_branch'],
                             btap_costing_branch=self.analysis_config[':btap_costing_branch'],
                             os_version=self.analysis_config[':os_version'],
                             nocache=self.analysis_config[':nocache'])
        docker.build_docker_image()
        return docker

    def save_results_to_database(self, results):


        if results['success'] == True:
            # if successful, don't save container_output since it is large.
            results['container_output'] = None
            # This method organizes the data structure of the dataframe to fit into a report table.
            df = self.sort_results(results)

            Session = sessionmaker(bind=self.database.get_engine())
            session = Session()
            df.to_sql('btap_data', con=session.get_bind(), if_exists='append', index=False)
            session.close()
        else:
            # If simulation failed, save failure information for user to debug to database
            # Convert failed results to dataframe and save to sql 'failed_runs' table.
            df = self.sort_results(results)
            Session = sessionmaker(bind=self.database.get_engine())
            session = Session()
            df.to_sql('failed_runs', con=session.get_bind(), if_exists='append', dtype = {':algorithm':sqlalchemy.types.JSON})
            session.close()
            raise FailedSimulationException(f'This scenario failed. dp_values= {results}')
        return results

    def sort_results(self, results):
        # Set up dict for top/high level data from btap_data.json output
        dp_values = {}
        # Set up arrays for tabular information contained in btap_date.json
        dp_tables = []
        # Set up arrays for dicts information contained in btap_data.json
        dp_dicts = []
        # interate through all btap_data top level keys.
        for key in results:
            if isinstance(results[key], list):
                # if the value is a list.. it is probably a table.. so put it in the tables array. Nothing will be done with this
                # at the moment.
                dp_tables.append(results[key])
            elif isinstance(results[key], dict):
                # if the value is a dict.. it is probably a configuration information.. so put it in array. Nothing will be done with this
                dp_tables.append(results[key])
            else:
                # otherwise store the key.
                dp_values[key] = results[key]
        # Convert dp_values to dataframe and add to sql table named 'btap_data'
        logging.info(f'obtained dp_values= {dp_values}')
        df = pd.DataFrame([dp_values])
        return df

    def initialize_aws_batch(self, git_api_token):
        # create aws image, set up aws compute env and create workflow queue.
        aws_batch = AWSBatch(
            analysis_id=self.analysis_config[':analysis_id'],
            btap_image_name=self.analysis_config[':image_name'],
            rebuild_image=self.analysis_config[':nocache'],
            git_api_token=git_api_token,
            os_version=self.analysis_config[':os_version'],
            btap_costing_branch=self.analysis_config[':btap_costing_branch'],
            os_standards_branch=self.analysis_config[':os_standards_branch'],
            threads=self.get_threads()
        )
        aws_batch.create_batch_workflow()
        return aws_batch

    def shutdown_analysis(self):

        # If aws batch was activated..kill the workflow if something went wrong.
        if self.aws_batch != None:
            print("Shutting down AWS Resources")
            self.aws_batch.shutdown_batch_workflow()

        # Generate output files locally if database exists
        if self.database != None:
            print("Generating output files.")
            self.btap_data_df, self.failed_df = self.database.generate_output_files(analysis_id = self.analysis_config[":analysis_id"],
                                                                                    analysis_name = self.analysis_config[":analysis_name"],
                                                                                    output_folder = self.output_folder,
                                                                                    s3_bucket=self.analysis_config[":s3_bucket"],
                                                                                    compute_environment = self.analysis_config[':compute_environment'])
        # Kill database if it exists
        if self.database != None:
            if self.analysis_config[':kill_database'] == True:
                message = "Killing Database Server."
                logging.info(message)
                print(message)
                self.database.kill_database()
            else:
                message = "Leaving database server running."
                logging.info(message)
                print(message)

        # Load baseline run data into dataframe.
        # Add eui_reference to analsys_df





    # This method creates a encoder and decoder of the simulation options to integers.  The ML and AI routines use float,
    # conventionally for optimization problems. Since most of the analysis that we do are discrete options for designers
    # we need to convert all inputs, string, float or int, into  to enumerated integer representations for the optimizer to
    # work.
    def create_options_encoder(self):
        # Determine options the users defined and contants and variable for the analysis. Options / lists that the user
        # provided only one options (a list of size 1) in the analysis input file are to be consider constants in the simulation.
        # this may simplify the calculations that the optimizer has to conduct.

        # Create a dict of the constants.
        self.constants = {}
        # Create a dict of encoders/decoders.
        self.option_encoder = {}

        # Keep track of total possible scenarios to tell user.
        self.number_of_possible_designs = 1
        # Interate through all the building_options contained in the analysis input yml file.
        for key, value in self.building_options.items():
            # If the options for that building charecteristic are > 1 it is a variable to be take part in optimization.
            if isinstance(value, list) and len(value) > 1:
                self.number_of_possible_designs *= len(value)
                # Create the encoder for the building option / key.
                self.option_encoder[key] = {}
                self.option_encoder[key]['encoder'] = preprocessing.LabelEncoder().fit(value)
            elif isinstance(value, list) and len(value) == 1:
                # add the constant to the constant hash.
                self.constants[key] = value[0]
            else:
                # Otherwise warn user that nothing was provided.
                raise (f"building option {key} was set to empty. Pleace enter a value for it.")

        #Return the variables.. but the return value is not really use since these are access via the object variable self anyways.
        return self.constants, self.option_encoder

    # convieniance interface to get number of variables.
    def number_of_variables(self):
        # Returns the number of variables Note this is not a class variable self like the others. That is because this method is used in the
        # problem definition and we need to avoid thread variable issues.
        return len(self.option_encoder)


    # Convience variable to get the upper limit integers of all the variable as an ordered list.
    def x_u(self):
        # Set up return list.
        x_u = []
        # iterage throug each key in the encoder list.
        for key in self.option_encoder:
            # get the max value, which is the length minus 1 since the enumeration starts at 0.
            x_u.append(len(self.option_encoder[key]['encoder'].classes_) - 1)
        # Returns the list of max values.. Note this is not a class variable self like the others. That is because this method is used in the
        # problem definition and we need to avoid thread variable issues.
        return x_u

    # This method takes an ordered list of ints and converts it to a run_options input file.
    def generate_run_option_file(self, x):
        # Create dict that will be the basis of the run_options.yml file.
        run_options = {}
        # Make sure options are the same length as the encoder.
        if len(x) != len(self.option_encoder):
            raise ('input is larger than the encoder was set to.')

        # interate though both the encoder key and x input list at the same time
        for key_name, x_option in zip(self.option_encoder.keys(), x):
            # encoder/decoder for the building option key.
            encoder = self.option_encoder[key_name]['encoder']
            # get the actual value for the run_options
            run_options[key_name] = str(encoder.inverse_transform([x_option])[0])
        # Tell user the options through std out.
        run_options[':scenario'] = 'optimize'
        run_options[':algorithm_type'] = self.analysis_config[':algorithm'][':type']
        run_options[':output_variables'] = self.analysis_config[':output_variables']
        run_options[':output_meters'] = self.analysis_config[':output_meters']
        message = f"Running Option Variables {run_options}"
        logging.info(message)
        # Add the constants to the run options dict.
        run_options.update(self.constants)
        # Add the analysis setting to the run options dict.
        run_options.update(self.analysis_config)


        # Returns the dict.. Note this is not a class variable self like the others. That is because this method is used in the
        # problem definition and we need to avoid thread variable issues.
        return run_options




# Class to Manage parametric runs.
class BTAPParametric(BTAPAnalysis):
    def __init__(self, analysis_config_file=None, git_api_token=None):
        # Run super initializer to set up default variables.
        super().__init__(analysis_config_file, git_api_token)
        self.scenarios = []

    def run(self):
        # Compute all the scenarios for paramteric run.
        self.compute_scenarios()
        try:
            # Run parametric analysis
            self.run_all_scenarios()

        except FailedSimulationException as err:
            message = f"Simulation(s) failed. Analysis cannot continue. Please review failed simulations to determine cause of error in Excel output or if possible the simulation datapoint files. \nLast failure had these inputs:\n\t {err}"
            logging.error(message)
        except botocore.exceptions.SSLError as err:
            message = f"Certificate Failure. This error occurs when AWS does not trust your security certificate. Either because you are using a VPN or your network is otherwise spoofing IPs. Please ensure that you are not on a VPN or contact your network admin. Error: {err}"
            logging.error(message)
        finally:
            self.shutdown_analysis()

    def get_threads(self):
        return_value = None
        if self.analysis_config[':no_of_threads'] == None:
            if self.analysis_config[':compute_environment'] == 'local':
                if self.file_number < multiprocessing.cpu_count() - 2:
                    return_value = self.file_number
                else:
                    return_value =  multiprocessing.cpu_count() - 2
            elif self.analysis_config[':compute_environment'] == 'aws_batch':
                    return_value =  MAX_AWS_VCPUS
        else:
            return_value =  self.analysis_config[':no_of_threads']
        return return_value

    # This method will compute all the possible scenarios from the input file for a parametric run.
    # This will return a list of scenario lists.
    def compute_scenarios(self):

        # Set up storage lists
        l_of_l_of_values = []
        keys = []

        # Iterate through each option set in yml file.
        for key, value in self.building_options.items():

            # Check to see if the value is a list. In other words are there more than one option for that charecteristic.
            if (isinstance(value, list)):

                # Create new array to list
                new_list = []
                for item in value:

                    # Create an indidual item for the option as a keyword/value array.
                    new_list.append([str(key), item])

                # Append list to the lists of options
                l_of_l_of_values.append(new_list)

                # append key to keys
                keys.append(key)

        # to compute all possible permutations done by a python package called itertools.
        scenarios = list(itertools.product(*l_of_l_of_values))
        # go through each option scenario
        for items in scenarios:
            # Create an options hash to store the options
            run_options = {}

            # Go through each item
            for item in items:
                # Save that charecteristic to the options hash
                run_options[item[0]] = item[1]
            run_options[':algorithm_type'] = self.analysis_config[':algorithm'][':type']
            self.scenarios.append(run_options)
            message = f'Number of Scenarios {len(self.scenarios)}'
            logging.info(message)

        return self.scenarios

    def run_all_scenarios(self):
        # Failed runs counter.
        failed_datapoints = 0

        # Total number of runs.
        self.file_number = len(self.scenarios)

        # Keep track of simulation time.
        threaded_start = time.time()
        # Using all your processors minus 1.
        print(f'Using {self.get_threads()} threads.')
        message = f'{self.database.get_num_of_runs_completed(self.analysis_config[":analysis_id"])} of {self.file_number} simulations completed'
        logging.info(message)
        print(message)

        with concurrent.futures.ThreadPoolExecutor(self.get_threads()) as executor:
            futures = []
            # go through each option scenario
            for run_options in self.scenarios:
                # Create an options hash to store the options

                # Executes docker simulation in a thread
                futures.append(executor.submit(self.run_datapoint, run_options=run_options))
            # Bring simulation thread back to main thread
            for future in concurrent.futures.as_completed(futures):
                # Save results to database.
                self.save_results_to_database(future.result())

                # Track failures.
                if not future.result()['success']:
                    failed_datapoints += 1

                # Update user.
                message = f'TotalRuns:{self.file_number}\tCompleted:{self.database.get_num_of_runs_completed(self.analysis_config[":analysis_id"])}\tFailed:{self.database.get_num_of_runs_failed(self.analysis_config[":analysis_id"])}\tElapsed Time: {str(datetime.timedelta(seconds=round(time.time() - threaded_start)))}'
                logging.info(message)
                print(message)
        # At end of runs update for users.
        message = f'{self.file_number} Simulations completed. No. of failures = {self.database.get_num_of_runs_failed(self.analysis_config[":analysis_id"])} Total Time: {str(datetime.timedelta(seconds=round(time.time() - threaded_start)))}'
        logging.info(message)
        print(message)

# Optimization problem definition class.
class BTAPProblem(Problem):
    # Inspiration for this was drawn from examples:
    #   Discrete analysis https://pymoo.org/customization/discrete_problem.html
    #   Stapmap Multithreaded https://pymoo.org/problems/parallelization.html
    def __init__(self,
                 # Required btap object already initialized to help run the optimization.
                 btap_optimization=None,
                 **kwargs):
        # Make analysis object visible throught class.
        self.btap_optimization = btap_optimization

        # Initialize super with information from [':algorithm'] in input file.
        super().__init__(
            # Number of variables that are present in the yml file.
            n_var=self.btap_optimization.number_of_variables(),
            # Number of minimize_objectives in input file.
            n_obj=len(self.btap_optimization.analysis_config[':algorithm'][':minimize_objectives']),
            # We never have contraints.
            n_constr=0,
            # set the lower bound array of variable options.. all start a zero. So an array of zeros.
            xl=[0] * self.btap_optimization.number_of_variables(),
            # the upper bound for each variable option as an integer.. We are dealing only with discrete integers in
            # this optimization.
            xu=self.btap_optimization.x_u(),
            # Tell pymoo to operate on this serially in separate threads since we are using starmap
            elementwise_evaluation=True,
            # Tell pymoo that the variables are discrete integers and not floats as is usually the default.
            type_var=int,
            # options to parent class (not used)
            **kwargs)

    # This is the method that runs each simulation.
    def _evaluate(
            self,
            # x is the list of options represented as integers for this particular run created by pymoo.
            x,
            # out is the placeholder for the fitness / goal functions to be minimized.
            out,
            # options to parent class (not used)
            *args,
            **kwargs):
        # Converts discrete integers contains in x argument back into values that btap understands. So for example. if x was a list
        # of zeros, it would convert this to the dict of the first item in each list of the variables in the building_options
        # section of the input yml file.
        run_options = self.btap_optimization.generate_run_option_file(x.tolist())

        # Run simulation
        results = self.btap_optimization.run_datapoint(run_options)

        # Saves results to database if successful or not.
        self.btap_optimization.save_results_to_database(results)
        analysis_id = self.btap_optimization.analysis_config[':analysis_id']
        message = f'{self.btap_optimization.database.get_num_of_runs_completed(analysis_id)} simulations completed of {self.btap_optimization.max_number_of_simulations}. No. of failures = {self.btap_optimization.database.get_num_of_runs_failed(analysis_id)}'
        logging.info(message)
        print(message)

        # Pass back objective function results.
        objectives = []
        for objective in self.btap_optimization.analysis_config[':algorithm'][':minimize_objectives']:
            objectives.append(results[objective])
        out["F"] = np.column_stack(objectives)

# Class to manage optimization runs.
class BTAPOptimization(BTAPAnalysis):
    def __init__(self, analysis_config_file=None, git_api_token=None):

        # Run super initializer to set up default variables.
        super().__init__(analysis_config_file, git_api_token)

    def run(self):
        message = "success"
        try:
            # Create options encoder. This method creates an object to translate variable options
            # from a list of object to a list of integers. Pymoo and most optimizers operate on floats and strings.
            # We are forcing the use of int for discrete analysis.
            self.create_options_encoder()

            # Run optimization. This will create all the input files, run and gather the results to sql.
            self.run_analysis()

        except FailedSimulationException as err:
            message = f"Simulation(s) failed. Optimization cannot continue. Please review failed simulations to determine cause of error in Excel output or if possible the simulation datapoint files. \nLast failure had these inputs:\n\t {err}"
            logging.error(message)
        except botocore.exceptions.SSLError as err:
            message = f"Certificate Failure. This error occurs when AWS does not trust your security certificate. Either because you are using a VPN or your network is otherwise spoofing IPs. Please ensure that you are not on a VPN or contact your network admin. Error: {err}"
            logging.error(message)
        except Exception as err:
            message = f"Unknown Error.{err} {traceback.format_exc()}"
            logging.error(message)
        finally:
            self.shutdown_analysis()
            return message

    def get_threads(self):
        if self.analysis_config[':no_of_threads'] == None:
            if self.analysis_config[':compute_environment'] == 'local':
                cpus =  multiprocessing.cpu_count() - 2
                population = self.analysis_config[':algorithm'][':population']
                if cpus > population:
                    return population
                else:
                    return cpus

            elif self.analysis_config[':compute_environment'] == 'aws_batch':
                return MAX_AWS_VCPUS

        else:
            return self.analysis_config[':no_of_threads']

    def run_analysis(self):
        print(f"Running Algorithm {self.analysis_config[':algorithm']}")
        print(f"Number of Variables: {self.number_of_variables()}")
        print(f"Number of minima objectives: {self.number_of_minimize_objectives()}")
        print(f"Number of possible designs: {self.number_of_possible_designs}")
        max_number_of_individuals = int(self.analysis_config[':algorithm'][':population']) * int(self.analysis_config[':algorithm'][':n_generations'])
        if self.number_of_possible_designs < max_number_of_individuals:
            self.max_number_of_simulations =  self.number_of_possible_designs
        else:
            self.max_number_of_simulations = max_number_of_individuals
        print("Starting Simulations.")

        # Get algorithm information from yml data entered by user.
        # Type: only nsga2 is supported. See options here.
        # https://pymoo.org/algorithms/nsga2.html
        type = self.analysis_config[':algorithm'][':type']
        pop_size = self.analysis_config[':algorithm'][':population']
        n_gen = self.analysis_config[':algorithm'][':n_generations']
        prob = self.analysis_config[':algorithm'][':prob']
        eta = self.analysis_config[':algorithm'][':eta']
        # initialize the pool
        pool = ThreadPool(self.get_threads())
        message = f'Using {self.get_threads()} threads.'
        logging.info(message)
        print(message)
        # Create pymoo problem. Pass self for helper methods and set up a starmap multithread pool.
        problem = BTAPProblem(btap_optimization=self, parallelization=('starmap', pool.starmap))
        # configure the algorithm.
        method = get_algorithm(type,
                               pop_size=pop_size,
                               sampling=get_sampling("int_random"),
                               crossover=get_crossover("int_sbx", prob=prob, eta=eta),
                               mutation=get_mutation("int_pm", eta=eta),
                               eliminate_duplicates=True,
                               )
        # set to optimize minimize the problem n_gen os the max number of generations before giving up.
        self.res = minimize(problem,
                       method,
                       termination=('n_gen', n_gen),
                       seed=1
                       )
        #Scatter().add(res.F).show()
        # Let the user know the runtime.
        print('Execution Time:', self.res.exec_time)
        # shut down the pool and threads.
        pool.close()





    # convieniance interface to get number of minimized objectives.
    def number_of_minimize_objectives(self):
        # Returns the number of variables Note this is not a class variable self like the others. That is because this method is used in the
        # problem definition and we need to avoid thread variable issues.
        return len(self.analysis_config[':algorithm'][':minimize_objectives'])

# Class to manage lhs runs. Uses Scipy.. Please see link for options explanation
# https://scikit-optimize.github.io/stable/auto_examples/sampler/initial-sampling-method.html
class BTAPSamplingLHS(BTAPParametric):
    def compute_scenarios(self):
        # This method converts the options for each ecm as an int. This allows for strings and numbers to use the same
        # approach for optimization.
        self.create_options_encoder()
        #lower bound of all options (should be zero)
        xl = [0] * self.number_of_variables()
        # Upper bound.
        xu = self.x_u()
        #create ranges for each ecm and create the Space object.
        space = Space(list(map(lambda x, y: (x, y), xl, xu)))
        #set random seed.

        np.random.seed(self.analysis_config[':algorithm'][':random_seed'])

        # Create the lhs algorithm.
        lhs = Lhs(lhs_type=self.analysis_config[':algorithm'][':lhs_type'], criterion=None)
        # Get samples
        samples = lhs.generate(space.dimensions, n_samples=self.analysis_config[':algorithm'][':n_samples'])
        # create run_option for each scenario.
        for x in samples:
            # Converts discrete integers contains in x argument back into values that btap understands. So for example. if x was a list
            # of zeros, it would convert this to the dict of the first item in each list of the variables in the building_options
            # section of the input yml file.
            run_options = self.generate_run_option_file(x)
            run_options[':scenario'] = 'lhs'
            self.scenarios.append(run_options)
        return self.scenarios


class BTAPIntegratedDesignProcess:
    def __init__(self, analysis_config_file=None, git_api_token=None):
        self.analysis_config_file = analysis_config_file
        self.project_root = os.path.dirname(analysis_config_file)
        self.git_api_token = git_api_token

    def run(self):
        # Create Database
        database = BTAPDatabase()

        # Load Analysis File into variable
        if not os.path.isfile(self.analysis_config_file):
            logging.error(f"could not find analysis input file at {self.analysis_config_file}. Exiting")
            exit(1)
        # Open the yaml in analysis dict.
        with open(self.analysis_config_file, 'r') as stream:
            analysis = yaml.safe_load(stream)
        # Run elimination
        # Change analysis type and options
        config = copy.deepcopy(analysis)
        config[':analysis_configuration'][':algorithm'][':type'] = 'elimination'
        config[':analysis_configuration'][':analysis_name'] = config[':analysis_configuration'][
                                                                  ':analysis_name'] + '_elim'
        config[':analysis_configuration'][':kill_database'] = False

        config_file_name = os.path.join(self.project_root, 'elimination.yml')
        with open(config_file_name, 'w') as file:
            yaml.dump(config, file)
        bb = BTAPElimination(analysis_config_file=config_file_name, git_api_token=self.git_api_token)
        print("running elimination stage")
        bb.run()
        # Run sensitivity
        # Change analysis type and options
        config = copy.deepcopy(analysis)
        config[':analysis_configuration'][':algorithm'][':type'] = 'sensitivity'
        config[':analysis_configuration'][':analysis_name'] = config[':analysis_configuration'][
                                                                  ':analysis_name'] + '_sens'
        config[':analysis_configuration'][':kill_database'] = False
        config[':analysis_configuration'][':nocache'] = False
        config_file_name = os.path.join(self.project_root, 'sensitivity.yml')
        with open(config_file_name, 'w') as file:
            yaml.dump(config, file)
        bb = BTAPSensitivity(analysis_config_file=config_file_name, git_api_token=self.git_api_token)
        bb.run()
        # Run optimization
        # Change analysis type and options
        config = copy.deepcopy(analysis)
        config[':analysis_configuration'][':algorithm'][':type'] = 'nsga2'
        config[':analysis_configuration'][':nocache'] = False
        config[':analysis_configuration'][':kill_database'] = False
        config[':analysis_configuration'][':analysis_name'] = config[':analysis_configuration'][
                                                                  ':analysis_name'] + '_opt'
        config_file_name = os.path.join(self.project_root, 'optimization.yml')
        with open(config_file_name, 'w') as file:
            yaml.dump(config, file)
        bb = BTAPOptimization(analysis_config_file=config_file_name, git_api_token=self.git_api_token)
        bb.run()
        # Output results from all analysis into
        database.generate_output_files(analysis_id=None, output_folder=self.project_root)
        message = "Killing Database Server."
        logging.info(message)
        print(message)
        database.kill_database()

# Class to manage local postgres database.
class BTAPDatabase:
    #Contructor sets up paths and database options.
    def __init__(self,
                 username = 'docker',
                 password = 'docker'):
        self.credentials = None
        self.btap_data_df = []
        self.failed_df = []
        # docker run -e POSTGRES_USER=docker -e POSTGRES_PASSWORD=docker -e POSTGRES_DB=btap
        self.docker_client = docker.from_env()
        message = f"Starting postgres database container on localhost."
        logging.info(message)
        print(message)
        # Checking if container already is running.
        containers = self.docker_client.containers.list(filters={'name':'btap_postgres'})
        if containers:
            message = f"Found existing database. Using that."
            logging.info(message)
            print(message)
            self.container = containers[0]
            self.engine = create_engine("postgresql://docker:docker@localhost:5432/btap",
                                        pool_pre_ping=True,
                                        pool_size=MAX_AWS_VCPUS,
                                        max_overflow=50,
                                        pool_timeout=60)
        else:
            try:
                self.container = self.docker_client.containers.run(
                                                            # Local image name to use.
                                                            name='btap_postgres',
                                                            image='postgres',

                                                            # Environment args passed to container.
                                                            environment=[f"POSTGRES_USER={username}",
                                                                         f"POSTGRES_PASSWORD={password}",
                                                                         "POSTGRES_DB=btap"],
                                                            ports={5432:5432},
                                                            # Will detach from current thread.. don't do it if you don't understand this.
                                                            detach=True,
                                                            # This deletes the container on exit otherwise the container
                                                            # will bloat your system.
                                                            auto_remove=True
               )
            except docker.errors.APIError as err:
                    message = f"Error creating database. {err}"
                    logging.error(message)
                    exit(1)

            message = f"Waiting for database to initialize..."
            logging.info(message)
            print(message)
            time.sleep(5)
            self.engine = create_engine("postgresql://docker:docker@localhost:5432/btap",
                                        pool_pre_ping=True,
                                        pool_size=MAX_AWS_VCPUS,
                                        max_overflow=50,
                                        pool_timeout=60)
            self.create_btap_database()
        message = f"DatabaseServer:localhost:5432 DatabaseUserName:{docker} DatabasePassword:{password} DatabaseName:btap"

    def create_btap_database(self):
        # Create btap_data_table
        sql_command = '''CREATE TABLE btap_data (
                    index BIGINT, 
                    ":algorithm_type" TEXT,
                    ":no_of_threads" TEXT,
                    ":dcv_type" TEXT, 
                    ":lights_type" TEXT, 
                    ":ecm_system_name" TEXT, 
                    ":erv_package" TEXT, 
                    ":ext_wall_cond" TEXT, 
                    ":ext_floor_cond" TEXT, 
                    ":ext_roof_cond" TEXT, 
                    ":fixed_window_cond" TEXT, 
                    ":building_type" TEXT, 
                    ":template" TEXT, 
                    ":epw_file" TEXT, 
                    ":primary_heating_fuel" TEXT, 
                    ":lights_scale" TEXT, 
                    ":daylighting_type" TEXT, 
                    ":boiler_eff" TEXT, 
                    ":furnace_eff" TEXT, 
                    ":shw_eff" TEXT, 
                    ":ground_wall_cond" TEXT, 
                    ":ground_floor_cond" TEXT, 
                    ":ground_roof_cond" TEXT, 
                    ":door_construction_cond" TEXT, 
                    ":glass_door_cond" TEXT, 
                    ":overhead_door_cond" TEXT, 
                    ":skylight_cond" TEXT, 
                    ":glass_door_solar_trans" TEXT, 
                    ":fixed_wind_solar_trans" TEXT, 
                    ":skylight_solar_trans" TEXT, 
                    ":fdwr_set" TEXT, 
                    ":srr_set" TEXT, 
                    ":rotation_degrees" TEXT, 
                    ":scale_x" TEXT, 
                    ":scale_y" TEXT, 
                    ":scale_z" TEXT, 
                    ":pv_ground_type" TEXT, 
                    ":pv_ground_total_area_pv_panels_m2" TEXT, 
                    ":pv_ground_tilt_angle" TEXT, 
                    ":pv_ground_azimuth_angle" TEXT, 
                    ":pv_ground_module_description" TEXT,
                    ":adv_dx_units" TEXT,
                    ":nv_type" TEXT,
                    ":nv_opening_fraction" TEXT,
                    ":nv_temp_out_min" TEXT,
                    ":nv_delta_temp_in_out" TEXT,
                    ":chiller_type" TEXT,
                    ":occupancy_loads_scale" TEXT,
                    ":electrical_loads_scale" TEXT,
                    ":oa_scale" TEXT,
                    ":infiltration_scale" TEXT,
                    ":airloop_economizer_type" TEXT,
                    ":compute_environment" TEXT, 
                    ":s3_bucket" TEXT, 
                    ":image_name" TEXT, 
                    ":nocache" BOOLEAN, 
                    ":os_standards_branch" TEXT, 
                    ":btap_costing_branch" TEXT, 
                    ":os_version" TEXT, 
                    ":analysis_name" TEXT, 
                    ":analysis_id" TEXT, 
                    ":run_annual_simulation" BOOLEAN, 
                    ":enable_costing" BOOLEAN, 
                    ":datapoint_id" TEXT, 
                    ":kill_database" BOOLEAN,  
                    ":scenario" TEXT,
                    heating_peak_w_per_m_sq FLOAT(53),
                    cooling_peak_w_per_m_sq FLOAT(53),                  
                    bc_step_code_tedi_kwh_per_m_sq FLOAT(53),
                    bc_step_code_meui_kwh_per_m_sq FLOAT(53),
                    bldg_conditioned_floor_area_m_sq FLOAT(53), 
                    bldg_exterior_area_m_sq FLOAT(53), 
                    bldg_fdwr FLOAT(53), 
                    bldg_name TEXT, 
                    bldg_nominal_floor_to_ceiling_height TEXT, 
                    bldg_nominal_floor_to_floor_height TEXT, 
                    bldg_srr FLOAT(53), 
                    bldg_standards_building_type TEXT, 
                    bldg_standards_number_of_above_ground_stories BIGINT, 
                    bldg_standards_number_of_living_units TEXT, 
                    bldg_standards_number_of_stories BIGINT, 
                    bldg_standards_template TEXT, 
                    bldg_surface_to_volume_ratio FLOAT(53), 
                    bldg_volume_m_cu FLOAT(53), 
                    cost_equipment_envelope_total_cost_per_m_sq FLOAT(53), 
                    cost_equipment_heating_and_cooling_total_cost_per_m_sq FLOAT(53), 
                    cost_equipment_lighting_total_cost_per_m_sq FLOAT(53), 
                    cost_equipment_shw_total_cost_per_m_sq FLOAT(53), 
                    cost_equipment_total_cost_per_m_sq FLOAT(53), 
                    cost_equipment_ventilation_total_cost_per_m_sq FLOAT(53), 
                    cost_rs_means_city TEXT, 
                    cost_rs_means_prov TEXT, 
                    cost_utility_ghg_electricity_kg_per_m_sq FLOAT(53), 
                    "cost_utility_ghg_natural gas_kg_per_m_sq" FLOAT(53), 
                    cost_utility_ghg_oil_kg_per_m_sq FLOAT(53), 
                    cost_utility_ghg_total_kg_per_m_sq FLOAT(53), 
                    cost_utility_neb_electricity_cost_per_m_sq FLOAT(53), 
                    "cost_utility_neb_natural gas_cost_per_m_sq" FLOAT(53), 
                    cost_utility_neb_oil_cost_per_m_sq FLOAT(53), 
                    cost_utility_neb_total_cost_per_m_sq FLOAT(53), 
                    energy_eui_additional_fuel_gj_per_m_sq FLOAT(53), 
                    energy_eui_cooling_gj_per_m_sq FLOAT(53), 
                    energy_eui_district_cooling_gj_per_m_sq FLOAT(53), 
                    energy_eui_district_heating_gj_per_m_sq FLOAT(53), 
                    energy_eui_electricity_gj_per_m_sq FLOAT(53), 
                    energy_eui_fans_gj_per_m_sq FLOAT(53), 
                    "energy_eui_heat recovery_gj_per_m_sq" FLOAT(53), 
                    energy_eui_heating_gj_per_m_sq FLOAT(53), 
                    "energy_eui_interior equipment_gj_per_m_sq" FLOAT(53), 
                    "energy_eui_interior lighting_gj_per_m_sq" FLOAT(53), 
                    energy_eui_natural_gas_gj_per_m_sq FLOAT(53), 
                    energy_eui_pumps_gj_per_m_sq FLOAT(53), 
                    energy_eui_total_gj_per_m_sq FLOAT(53), 
                    "energy_eui_water systems_gj_per_m_sq" FLOAT(53), 
                    energy_peak_electric_w_per_m_sq FLOAT(53), 
                    energy_peak_natural_gas_w_per_m_sq FLOAT(53), 
                    energy_principal_heating_source TEXT, 
                    env_fdwr FLOAT(53), 
                    "env_ground_floors_average_conductance-w_per_m_sq_k" FLOAT(53), 
                    "env_ground_roofs_average_conductance-w_per_m_sq_k" TEXT, 
                    "env_ground_walls_average_conductance-w_per_m_sq_k" TEXT, 
                    "env_outdoor_doors_average_conductance-w_per_m_sq_k" TEXT, 
                    "env_outdoor_floors_average_conductance-w_per_m_sq_k" TEXT, 
                    "env_outdoor_overhead_doors_average_conductance-w_per_m_sq_k" TEXT, 
                    "env_outdoor_roofs_average_conductance-w_per_m_sq_k" FLOAT(53), 
                    "env_outdoor_walls_average_conductance-w_per_m_sq_k" FLOAT(53), 
                    "env_outdoor_windows_average_conductance-w_per_m_sq_k" FLOAT(53), 
                    "env_skylights_average_conductance-w_per_m_sq_k" TEXT, 
                    env_srr FLOAT(53), 
                    location_city TEXT, 
                    location_country TEXT, 
                    location_epw_cdd FLOAT(53), 
                    location_epw_hdd FLOAT(53), 
                    location_latitude FLOAT(53), 
                    location_longitude FLOAT(53), 
                    location_necb_climate_zone TEXT, 
                    location_necb_hdd FLOAT(53), 
                    location_state_province_region TEXT, 
                    location_weather_file TEXT,                     
                    net_site_eui_gj_per_m_sq FLOAT(53),
                    peak_cooling_load_w_per_m_sq_necb FLOAT(53),
                    peak_heating_load_w_per_m_sq_necb FLOAT(53),
                    phius_annual_cooling_demand_kwh_per_m_sq FLOAT(53),
                    phius_annual_heating_demand_kwh_per_m_sq FLOAT(53),
                    phius_necb_meet_cooling_demand BOOLEAN,
                    phius_necb_meet_cooling_peak_load BOOLEAN,
                    phius_necb_meet_heating_demand BOOLEAN,
                    phius_necb_meet_heating_peak_load BOOLEAN,
                    phius_peak_cooling_load_w_per_m_sq FLOAT(53),
                    phius_peak_heating_load_w_per_m_sq FLOAT(53),
                    shw_additional_fuel_per_year FLOAT(53), 
                    shw_electricity_per_day FLOAT(53), 
                    shw_electricity_per_day_per_occupant FLOAT(53), 
                    shw_electricity_per_year FLOAT(53), 
                    shw_natural_gas_per_year FLOAT(53), 
                    shw_total_nominal_occupancy FLOAT(53), 
                    shw_water_m_cu_per_day FLOAT(53), 
                    shw_water_m_cu_per_day_per_occupant FLOAT(53), 
                    shw_water_m_cu_per_year FLOAT(53), 
                    simulation_btap_data_version TEXT, 
                    simulation_date TEXT, 
                    simulation_os_standards_revision TEXT, 
                    simulation_os_standards_version TEXT, 
                    run_options TEXT, 
                    "energy_eui_heat rejection_gj_per_m_sq" FLOAT(53), 
                    success BOOLEAN, 
                    simulation_time FLOAT(53),
                    total_site_eui_gj_per_m_sq FLOAT(53),
                    unmet_hours_cooling FLOAT(53),
                    unmet_hours_cooling_during_occupied FLOAT(53),
                    unmet_hours_heating FLOAT(53),
                    unmet_hours_heating_during_occupied FLOAT(53),
                    container_output TEXT,
                    datapoint_output_url TEXT,
                    ":btap_batch_version" TEXT
                )'''
        with self.engine.connect() as con:
            rs = con.execute(sql_command)

    def get_engine(self):
        return self.engine

    def get_num_of_runs_completed(self,analysis_id = None):
        if not sqlalchemy.inspect(self.engine).has_table('btap_data'):
            return 0
        else:
            if analysis_id == None:
                command = f'SELECT COUNT(*) FROM btap_data'
            else:
                command = f'SELECT COUNT(*) FROM btap_data WHERE ":analysis_id" = \'{analysis_id}\''

            result = self.engine.connect().execute( command )
            return([dict(row) for row in result][0]['count'])

    def get_num_of_runs_failed(self,analysis_id = None):
        #if not self.engine.dialect.has_table(self.engine, 'failed_runs'):
        if not sqlalchemy.inspect(self.engine).has_table('failed_runs'):
            return 0
        else:
            if analysis_id == None:
                command = f'SELECT COUNT(*) FROM failed_runs'
            else:
                command = f'SELECT COUNT(*) FROM failed_runs WHERE ":analysis_id" = \'{analysis_id}\''

            result = self.engine.connect().execute(command)
            return([dict(row) for row in result][0]['count'])

    def generate_output_files(self,
                              analysis_name=None,
                              analysis_id=None,
                              output_folder=None,
                              s3_bucket=None,
                              compute_environment='local'):

        # Create link to database and read all high level simulations into a dataframe.
        sql_engine = self.get_engine()
        sql_connection = sql_engine.connect()
        if self.get_num_of_runs_completed(analysis_id) > 0:
            if analysis_id == None:
                # Get all runs in database.
                self.btap_data_df = pd.read_sql_table('btap_data', sql_connection)
            else:
                command = f'SELECT * FROM btap_data WHERE ":analysis_id" = \'{analysis_id}\''
                self.btap_data_df = pd.read_sql_query(command, sql_engine)

            # PostProcess comparison to baselines.
            self.btap_data_df = PostProcessResults().run(btap_data_df=self.btap_data_df)

        # if there were any failures.. get them too.

        if self.get_num_of_runs_failed(analysis_id) > 0:
            if analysis_id == None:
                self.failed_df = pd.read_sql_table('failed_runs', sql_connection)
            else:
                command = f'SELECT * FROM failed_runs WHERE ":analysis_id" = \'{analysis_id}\''
                self.failed_df = pd.read_sql_query(command, sql_engine)

        sql_connection.close()

        # output to excel
        excel_path = os.path.join(output_folder, 'output.xlsx')
        writer = pd.ExcelWriter(excel_path)

        # btap_data from sql to excel writer
        if isinstance(self.btap_data_df, pd.DataFrame):
            self.btap_data_df.to_excel(writer, sheet_name='btap_data')
        else:
            message = 'No simulations completed.'
            logging.error(message)

        # if there were any failures.. get them too.
        if isinstance(self.failed_df, pd.DataFrame):
            self.failed_df.to_excel(writer, sheet_name='failed_runs')
            message = 'Some simulations failed.'
            logging.error(message)

        if isinstance(self.failed_df, pd.DataFrame) or isinstance(self.btap_data_df, pd.DataFrame):
            writer.save()
            message = f'Excel Output: {excel_path}'
            logging.info(message)
            print(message)

        # If this is an aws_batch run, copy the excel file to s3 for storage.
        if compute_environment == 'aws_batch':
            self.credentials = AWSCredentials()
            target_path = os.path.join(self.credentials.user_name, analysis_name, analysis_id, 'output', 'output.xlsx')
            # s3 likes forward slashes.
            target_path = target_path.replace('\\', '/')
            message = "Uploading %s..." % target_path
            logging.info(message)
            S3().upload_file(excel_path, s3_bucket, target_path)

        writer.close()
        # https://stackoverflow.com/questions/56751070/pandas-xlsxwriter-writer-close-does-not-completely-close-the-excel-file
        writer.handles = None
        return self.btap_data_df, self.failed_df

    def kill_database(self):
        self.container.remove(force=True)


class BTAPElimination(BTAPParametric):

    def compute_scenarios(self):
        self.elimination_parameters = [
            [':reference', 'do nothing'],
            [':electrical_loads_scale', '0.0'],
            [':infiltration_scale', '0.0'],
            [':lights_scale', '0.0'],
            [':oa_scale', '0.0'],
            [':occupancy_loads_scale', '0.0'],
            [':ext_wall_cond', '0.01'],
            [':ext_roof_cond', '0.01'],
            [':ground_floor_cond', '0.01'],
            [':ground_wall_cond', '0.01'],
            [':fixed_window_cond', '0.01'],
            [':fixed_wind_solar_trans', '0.01']
        ]

        building_options = copy.deepcopy(self.building_options)
        for key, value in building_options.items():
            if isinstance(value, list) and len(value) >= 1:
                building_options[key] = value[0]
        #Replace key value with elimination value.
        for elimination_parameter in self.elimination_parameters:
            run_option = copy.deepcopy(building_options)
            run_option[':algorithm_type'] = self.analysis_config[':algorithm'][':type']
            if elimination_parameter[0] != ':reference':
                run_option[elimination_parameter[0]] = elimination_parameter[1]
            run_option[':scenario'] = elimination_parameter[0]
            self.scenarios.append(run_option)
        message = f'Number of Scenarios {len(self.scenarios)}'
        logging.info(message)
        return self.scenarios


class BTAPSensitivity(BTAPParametric):
    def compute_scenarios(self):
        #Create default options scenario. Uses first value of all arrays.
        default_options = copy.deepcopy(self.building_options)
        for key, value in self.building_options.items():
                default_options[key] = value[0]
        #Create scenario
        for key, value in self.building_options.items():
            # If more than one option. Iterate, create run_option for each one.
            if isinstance(value, list) and len(value) > 1:
                for item in value:
                    run_option = copy.deepcopy(default_options)
                    run_option[':algorithm_type'] = self.analysis_config[':algorithm'][':type']
                    run_option[key] = item
                    run_option[':scenario'] = key
                    #append scenario to list.
                    self.scenarios.append(run_option)
        message = f'Number of Scenarios {len(self.scenarios)}'
        logging.info(message)
        return self.scenarios

# This class processed the btap_batch file to add columns as needed. This is a separate class as this can be applied
# independant of simulation runs and optionally at simulation time as well if desired,but may have to make this
# thread-safe if we do.
class PostProcessResults:
    def run(self,
            baseline=BASELINE_RESULTS,
            btap_data_df=r'C:\Users\plopez\test\btap_batch\example\posterity_mid_rise_elec_montreal\7576173d-48f4-47c6-a3aa-81381b9947bb\output\AWS_Opt_Posterity_MidRise_Elec.xlsx',
            output_folder=None):
        if isinstance(btap_data_df, pd.DataFrame):
            analysis_df = btap_data_df
        else:
            analysis_df = pd.read_excel(open(btap_data_df, 'rb'), sheet_name='btap_data')

        self.economics(analysis_df, baseline)

        # Iterate through each datapoint in analysis and collect hourly data.
        hourly_folder = os.path.join(output_folder,'hourly_data')
        os.makedirs(hourly_folder, exist_ok=True)
        ic(hourly_folder)

        for index, row in analysis_df.iterrows():
            if row['datapoint_output_url'].startswith('file:///'):
                #This is a local file. use system copy. First remove prefix
                hourly_data_path = os.path.join(row['datapoint_output_url'][len('file:///'):], 'hourly.csv')
                ic(hourly_data_path)
                shutil.copyfile(hourly_data_path,os.path.join(hourly_folder,row[':datapoint_id']+'.csv') )
            elif row['datapoint_output_url'].startswith('s3://'):
                print("S3 not supported yet to download hourly data.")

        return analysis_df


    def generate_output_files(self,
                              analysis_name = None,
                              analysis_id = None,
                              output_folder = None,
                              s3_bucket = None,
                              compute_environment = 'local'):
        self.report_data_df = None
        self.report_data_dict_df = None
        self.hourly_df =None
        self.failed_df = None
        print("Generating output files.")
        message = 'Gathering data from PostGresql'
        print(message)
        logging.info(message)

        # Create link to database and read all high level simulations into a dataframe.
        sql_engine = self.get_engine()
        sql_connection = sql_engine.connect()
        if self.get_num_of_runs_completed(analysis_id) > 0:
            if analysis_id == None:
                # Get all runs in database.
                self.btap_data_df = pd.read_sql_table('btap_data', sql_connection)
            else:
                command = f'SELECT * FROM btap_data WHERE ":analysis_id" = \'{analysis_id}\''
                self.btap_data_df = pd.read_sql_query(command, sql_engine)

            # PostProcess comparison to baselines.
            self.btap_data_df = PostProcessResults().run(btap_data_df=self.btap_data_df, output_folder= output_folder)

        # if there were any failures.. get them too.

        if self.get_num_of_runs_failed(analysis_id) > 0:
            if analysis_id == None:
                self.failed_df = pd.read_sql_table('failed_runs', sql_connection)
            else:
                command = f'SELECT * FROM failed_runs WHERE ":analysis_id" = \'{analysis_id}\''
                self.failed_df = pd.read_sql_query(command, sql_engine)

        sql_connection.close()

        message = f'Save high level data to excel file to {output_folder}'
        print(message)
        logging.info(message)
        self.save_excel_output(output_folder,
                                self.btap_data_df,
                                self.failed_df)
        return self.btap_data_df,self.failed_df

    def save_excel_output(self,output_folder, btap_data_df, failed_df ):
        # Create excel object
        excel_path = os.path.join(output_folder, 'output.xlsx')
        report_data_path = os.path.join(output_folder, 'report_data.zip')
        with pd.ExcelWriter(excel_path) as writer:
            if isinstance(btap_data_df, pd.DataFrame):
                btap_data_df.to_excel(writer, index=False,sheet_name='btap_data')
            else:
                message = 'No simulations completed.'
                logging.error(message)

            # if there were any failures.. create failure sheet.
            if isinstance(failed_df, pd.DataFrame):
                failed_df.to_excel(writer, sheet_name='failed_runs')
                message = 'Some simulations failed.'
                logging.error(message)
            #Wrtie excel
            if isinstance(failed_df, pd.DataFrame) or isinstance(btap_data_df, pd.DataFrame):
                message = f'Saving Excel Output: {excel_path}'
                logging.info(message)



    def economics(self, analysis_df, baseline):
        file = open(baseline, 'rb')
        baseline_df = pd.read_excel(file, sheet_name='btap_data')
        file.close()
        ceb_fuel_df = pd.read_csv(CER_UTILITY_COSTS)
        merge_columns = [':building_type', ':template', ':primary_heating_fuel', ':epw_file']
        df = pd.merge(analysis_df, baseline_df, how='left', left_on=merge_columns, right_on=merge_columns)
        analysis_df['baseline_savings_energy_cost_per_m_sq'] = round(
            (df['cost_utility_neb_total_cost_per_m_sq_x'] - df[
                'cost_utility_neb_total_cost_per_m_sq_y']), 1)
        analysis_df['baseline_difference_cost_equipment_total_cost_per_m_sq'] = round(
            (df['cost_utility_neb_total_cost_per_m_sq_x'] - df[
                'cost_utility_neb_total_cost_per_m_sq_y']), 1)
        analysis_df['baseline_simple_payback_years'] = round(
            (analysis_df['baseline_difference_cost_equipment_total_cost_per_m_sq'] / analysis_df[
                'baseline_savings_energy_cost_per_m_sq']), 1)
        analysis_df['baseline_peak_electric_percent_better'] = round(((df['energy_peak_electric_w_per_m_sq_y'] - df[
            'energy_peak_electric_w_per_m_sq_x']) * 100.0 / df['energy_peak_electric_w_per_m_sq_y']), 1)
        analysis_df['baseline_energy_percent_better'] = round(((df['energy_eui_total_gj_per_m_sq_y'] - df[
            'energy_eui_total_gj_per_m_sq_x']) * 100 / df['energy_eui_total_gj_per_m_sq_y']), 1)
        analysis_df['baseline_necb_tier'] = pd.cut(analysis_df['baseline_energy_percent_better'],
                                                   bins=[-1000.0, -0.001, 25.00, 50.00, 60.00, 1000.0],
                                                   labels=['non_compliant', 'tier_1', 'tier_2', 'tier_3', 'tier_4'])
        analysis_df['baseline_ghg_percent_better'] = round(((df['cost_utility_ghg_total_kg_per_m_sq_y'] - df[
            'cost_utility_ghg_total_kg_per_m_sq_x']) * 100 / df['cost_utility_ghg_total_kg_per_m_sq_y']), 1)
        # NPV commented out for now.
        # province = 'Quebec'
        # npv_end_year = 2050
        # ngas_rate = ceb_fuel_df.loc[(ceb_fuel_df['province'] == province) & (ceb_fuel_df['fuel_type'] == 'Natural Gas'),str(npv_start_year):str(npv_end_year)].iloc[0].reset_index(drop=True,name='values')
        # elec_rate = ceb_fuel_df.loc[(ceb_fuel_df['province'] == province) & (ceb_fuel_df['fuel_type'] == 'Electricity'),str(npv_start_year):str(npv_end_year)].iloc[0].reset_index(drop=True, name='values')
        # fueloil_rate = ceb_fuel_df.loc[(ceb_fuel_df['province'] == province) & (ceb_fuel_df['fuel_type'] == 'Oil'),str(npv_start_year):str(npv_end_year)].iloc[0].reset_index(drop=True, name='values')
        #
        # df = pd.concat([ngas_rate,elec_rate,fueloil_rate], axis=1,keys=['ngas_cost_per_gj','elec_cost_per_gj','oil_cost_per_gj'])
        # df['saving_ngas_gj_per_m2'] = 50.0
        # df['saving_elec_gj_per_m2'] = 50.0
        # df['saving_oil_gj_per_m2'] = 50.0
        # df['ngas_saving_per_m2'] = df['ngas_cost_per_gj'] * df['saving_ngas_gj_per_m2']
        # df['elec_saving_per_m2'] = df['elec_cost_per_gj'] * df['saving_elec_gj_per_m2']
        # df['oil_saving_per_m2'] =  df['oil_cost_per_gj'] * df['saving_oil_gj_per_m2']
        # df['total_savings_per_m2'] = df['ngas_saving_per_m2'] + df['oil_saving_per_m2'] +df['oil_saving_per_m2']
        # df['total_discounted_savings_per_m2'] = pv(rate=npv_discount_rate, pmt=0, nper=df.index, fv=-df['total_savings_per_m2'])
        # df['total_cumulative_dicounted_savings_per_m2'] = np.cumsum(df['total_discounted_savings_per_m2'])
        # print(df)
        #
        # final_full_year = df[df['total_cumulative_dicounted_savings_per_m2'] < 0].index.values.max()
        # fractional_yr = -df['total_cumulative_dicounted_savings_per_m2'][final_full_year] / df['total_discounted_savings_per_m2'][final_full_year + 1]
        # payback_period = final_full_year + fractional_yr
        # print(payback_period)


# Main method that researchers will interface with. If this gets bigger, consider a factory method pattern.
def btap_batch(analysis_config_file=None, git_api_token=None):
    # Load Analysis File into variable
    if not os.path.isfile(analysis_config_file):
        logging.error(f"could not find analysis input file at {analysis_config_file}. Exiting")
        exit(1)
    # Open the yaml in analysis dict.
    with open(analysis_config_file, 'r') as stream:
        analysis = yaml.safe_load(stream)


    print(f"Compute Environment:{analysis[':analysis_configuration'][':compute_environment']}")
    print(f"Analysis Type:{analysis[':analysis_configuration'][':algorithm'][':type']}")

    # If nsga2 optimization
    if analysis[':analysis_configuration'][':algorithm'][':type'] == 'sampling-lhs':
        opt = BTAPSamplingLHS(
            # Input file.
            analysis_config_file=analysis_config_file ,
            git_api_token=git_api_token
        )
        return opt



    # If nsga2 optimization
    if analysis[':analysis_configuration'][':algorithm'][':type'] == 'nsga2':
        opt = BTAPOptimization(
            # Input file.
            analysis_config_file=analysis_config_file ,
            git_api_token=git_api_token
        )
        return opt
    elif analysis[':analysis_configuration'][':algorithm'][':type'] == 'parametric':
        bb = BTAPParametric(
            # Input file.
            analysis_config_file=analysis_config_file,
            git_api_token=git_api_token
        )
        return bb
    elif analysis[':analysis_configuration'][':algorithm'][':type'] == 'elimination':
        bb = BTAPElimination(
            # Input file.
            analysis_config_file=analysis_config_file,
            git_api_token=git_api_token
        )
        return bb
    elif analysis[':analysis_configuration'][':algorithm'][':type'] == 'sensitivity':
        bb = BTAPSensitivity(
            # Input file.
            analysis_config_file=analysis_config_file,
            git_api_token=git_api_token
        )
        return bb
    elif analysis[':analysis_configuration'][':algorithm'][':type'] == 'idp':
        bb = BTAPIntegratedDesignProcess(
            # Input file.
            analysis_config_file=analysis_config_file,
            git_api_token=git_api_token
        )
        return bb
    else:
        message = f'Unknown algorithm type. Allowed types are nsga2 and parametric. Exiting'
        print(message)
        logging.error(message)
        exit(1)


pp = PostProcessResults().run(
            btap_data_df=r'C:\Users\plopez\PycharmProjects\btap_batch\examples\elimination\elimination_example\62e1ca45-5355-4fa8-9cf5-f433ff9708ac\output\output.xlsx',
            output_folder=r'C:\Users\plopez\PycharmProjects\btap_batch\examples\elimination\elimination_example\62e1ca45-5355-4fa8-9cf5-f433ff9708ac\output')

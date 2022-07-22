# docker image prune -f -a ; docker container prune -f ; docker volume prune -f ; docker builder prune -a -f

# docker kill (docker ps -q -a --filter "ancestor=btap_private_cli")
from icecream import ic
import itertools
import copy
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, as_completed
import shutil
from sklearn import preprocessing
from pymoo.factory import get_algorithm, get_crossover, get_mutation, get_sampling
from pymoo.optimize import minimize
from pymoo.core.problem import ElementwiseProblem
from pymoo.core.problem import starmap_parallelized_eval
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
import re
import glob
import logging
import requests
from random import seed
from random import random
from skopt.space import Space
from skopt.sampler import Lhs
import traceback
import pathlib
import openstudio
import numpy as np
import atexit
from functools import partial
import tqdm
import csv
import numpy_financial as npf

np.random.seed(123)
seed(1)

BTAP_BATCH_VERSION = '1.0.005'

# Maximum AWS CPUS that AWS will allocate for the run.
MAX_AWS_VCPUS = 500
# Number of VCPUs that AWSBatch will initialize with.
# DESIRED_AWS_VCPUS = 50 # Not used currently
# Minimum number of CPU should be set to zero.
MIN_AWS_VCPUS = 0
# Container allocated VCPU for AWS Batch
CONTAINER_VCPU = 1
# Container allocated Memory (MB) for AWS Batch
CONTAINER_MEMORY = 2000
# Container Storage (GB)
CONTAINER_STORAGE = 100
# AWS Batch Allocation Strategy. https://docs.aws.amazon.com/batch/latest/userguide/allocation-strategies.html
AWS_BATCH_ALLOCATION_STRATEGY = 'BEST_FIT_PROGRESSIVE'
# AWS Compute instances types..setting to optimal to let AWS figure it out for me.
# https://docs.aws.amazon.com/batch/latest/userguide/create-compute-environment.html
AWS_BATCH_COMPUTE_INSTANCE_TYPES = ['optimal']
# Using the public Amazon Linux 2 AMI to make use of overlay disk storage. Has all aws goodies already installed,
# makeing secure session manager possible, and has docker pre-installed.
AWS_BATCH_DEFAULT_IMAGE = 'ami-0a06b44c462364156'

# Location of Docker folder that contains information to build the btap image locally and on aws.
DOCKERFILES_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'Dockerfiles')
# Location of previously run baseline simulations to compare with design scenarios
BASELINE_RESULTS = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), '..', 'resources', 'reference', 'output.xlsx')
# Location of space_type library for NECB2011
NECB2011_SPACETYPE_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'resources',
                                       'space_type_library', 'NECB2011_space_types.osm')

# These resources were created either by hand or default from the AWS web console. If moving this to another aws account,
# recreate these 3 items in the new account. Also create s3 bucket to use named based account id like we did here.
# That should be all you need.. Ideally these should be created programmatically.
# Role used to build images on AWS Codebuild and ECR.
CLOUD_BUILD_SERVICE_ROLE = 'arn:aws:iam::834599497928:role/service-role/codebuild-test-service-role'
# Role to give permissions to jobs to run.
BATCH_JOB_ROLE = 'arn:aws:iam::834599497928:role/batchJobRole'
# Role to give permissions to batch to run.
BATCH_SERVICE_ROLE = 'arn:aws:iam::834599497928:role/service-role/AWSBatchServiceRole'
# Max Retry attemps for aws clients.
AWS_MAX_RETRIES = 12
# Dockerfile url location
DOCKERFILE_URL = 'https://raw.githubusercontent.com/canmet-energy/btap_cli/dev/Dockerfile'


# Custom exception for a failed simulation


class FailedSimulationException(Exception):
    pass


# Custom exception for a OSM error.


class OSMErrorException(Exception):
    pass


# Blob Storage operations


class S3:
    # Constructor
    def __init__(self):
        # Create the s3 client.
        config = Config(retries={'max_attempts': AWS_MAX_RETRIES, 'mode': 'standard'})
        self.s3 = boto3.client('s3', config=config)

    # Method to delete a bucket. Not used
    def delete_bucket(self, bucket_name):
        message = f'Deleting S3 {bucket_name}'
        print(message)
        logging.info(message)
        self.s3.delete_bucket(Bucket=bucket_name)

    # Method to check if a bucket exists.
    def check_bucket_exists(self, bucket_name):
        exists = True
        try:
            self.s3.meta.client.head_bucket(Bucket=bucket_name)
        except botocore.exceptions.ClientError as e:
            # If a client error is thrown, then check that it was a 404 error.
            # If it was a 404 error, then the bucket does not exist.
            error_code = e.response['Error']['Code']
            if error_code == '404':
                exists = False
        return exists

    # Method to create a bucket.
    def create_bucket(self, bucket_name):
        message = f'Creating S3 {bucket_name}'
        print(message)
        logging.info(message)
        self.s3.create_bucket(
            ACL='private',
            Bucket=bucket_name,
            CreateBucketConfiguration={
                'LocationConstraint': 'ca-central-1'
            },
            ObjectLockEnabledForBucket=False
        )

    # Method to download folder. Single threaded.
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

    # Copy folder to S3. Single thread.
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

    # Method to upload a file to S3.
    def upload_file(self, file, bucket_name, target_path):
        logging.info(f"uploading {file} to s3 bucket {bucket_name} target {target_path}")
        self.s3.upload_file(file, bucket_name, target_path)


# Class to authenticate to AWS and to get account information
class AWSCredentials:
    # Initialize with required clients.
    def __init__(self):
        config = Config(retries={'max_attempts': AWS_MAX_RETRIES, 'mode': 'standard'})
        self.sts = boto3.client('sts', config=config)
        self.iam = boto3.client('iam', config=config)
        try:
            self.account_id = self.sts.get_caller_identity()["Account"]
            self.user_id = self.sts.get_caller_identity()["UserId"]
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'ExpiredToken':
                logging.error(
                    "Your session has expired while running. Please renew your aws credentials and consider running this in an amazon instance if your run is longer than 2 hours")
                exit(1)
            else:
                print("Unexpected botocore.exceptions.ClientError error: %s" % e)
                exit(1)
        except botocore.exceptions.SSLError:
            logging.error(
                "SSL validation failed.. This is usually because you are behind a VPN. Please do not use a VPN.")
            exit(1)

        # get aws username from userid.
        if re.compile(".*:(.*)@.*").search(self.user_id) is None:
            # This situation occurs when running the host machine on AWS itself.
            self.user_name = 'osdev'
        else:
            # Otherwise it will use your aws user_id
            self.user_name = re.compile(".*:(.*)@.*").search(self.user_id)[1]

        # User ARN (Not used currently)
        self.user_arn = self.sts.get_caller_identity()["Arn"]
        # AWS Region name.
        self.region_name = boto3.Session().region_name


# Class to manage a AWS Batch run
class AWSBatch:
    @classmethod
    def get_threads(cls):
        return MAX_AWS_VCPUS

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
                 git_api_token=None,
                 os_version=None,
                 btap_costing_branch=None,
                 os_standards_branch=None,
                 ):
        self.credentials = AWSCredentials()
        self.bucket = self.credentials.account_id
        self.image_name = btap_image_name
        self.rebuild_image = rebuild_image
        self.git_api_token = git_api_token
        self.os_version = os_version
        self.btap_costing_branch = btap_costing_branch
        self.os_standards_branch = os_standards_branch

        # Create the aws clients required.
        config = Config(retries={'max_attempts': AWS_MAX_RETRIES, 'mode': 'standard'})
        self.ec2 = boto3.client('ec2', config=config)
        self.batch_client = boto3.client('batch', config=botocore.client.Config(max_pool_connections=self.get_threads(),
                                                                                retries={
                                                                                    'max_attempts': AWS_MAX_RETRIES,
                                                                                    'mode': 'standard'}))
        self.iam = boto3.client('iam', config=config)
        self.s3 = boto3.client('s3', config=botocore.client.Config(max_pool_connections=self.get_threads(),
                                                                   retries={'max_attempts': AWS_MAX_RETRIES,
                                                                            'mode': 'standard'}))
        self.cloudwatch = boto3.client('logs')
        self.ecr = boto3.client('ecr')
        self.cloudwatch = boto3.client('logs')
        # Todo create cloud build service role.
        self.cloudbuild_service_role = CLOUD_BUILD_SERVICE_ROLE

        # This is the role with permissions inside the docker containers. Created by aws web console. (todo: automate creations and destruction)
        self.batch_job_role = BATCH_JOB_ROLE
        # This is the role with the permissions to create batch runs. Created by aws web console. (todo: automate creations and destruction)
        self.aws_batch_service_role = BATCH_SERVICE_ROLE

        # Set Analysis Id.
        if analysis_id is None:
            self.analysis_id = uuid.uuid4()
        else:
            self.analysis_id = analysis_id

        # Compute id is the same as analysis id but stringed.
        self.compute_environment_id = f"{self.credentials.user_name.replace('.', '_')}-{self.analysis_id}"

        # Set up the job def as a suffix of the compute_environment_id"
        self.job_def_id = f"{self.compute_environment_id}_job_def"

        # Set up the job queue id as the suffix of the compute_environment_id.
        self.job_queue_id = f"{self.compute_environment_id}_job_queue"

        # Store the subnets into a list. This was set up by NRCan.
        subnets = self.ec2.describe_subnets()['Subnets']
        self.subnet_id_list = [subnet['SubnetId'] for subnet in subnets]

        # Store the security groups into a list. This was set up by NRCan.
        security_groups = self.ec2.describe_security_groups()["SecurityGroups"]
        self.securityGroupIds = [security_group['GroupId'] for security_group in security_groups]

        # On exit deconstructor
        atexit.register(self.tear_down)

    def setup(self):
        # This method creates analysis id for batch run. See methods for details.
        self.build_image()
        self.__create_compute_environment()
        self.__create_job_queue()
        self.__register_job_definition()
        print("Completed AWS batch initialization.")

    def tear_down(self):
        # This method manages the teardown of the batch workflow. See methods for details.
        message = "Shutting down AWSBatch...."
        print(message)
        logging.info(message)
        self.__delete_job_definition()
        self.__delete_job_queue()
        self.__delete_compute_environment()

    def submit_job(self,
                   output_folder,
                   local_btap_data_path,
                   local_datapoint_input_folder,
                   local_datapoint_output_folder,
                   run_options):
        run_options[':s3_bucket'] = self.credentials.account_id
        btap_data = {}
        # add run options to dict.
        btap_data.update(run_options)
        s3_analysis_folder = os.path.join(self.credentials.user_name, run_options[':analysis_name'],
                                          run_options[':analysis_id']).replace('\\', '/')
        s3_datapoint_input_folder = os.path.join(s3_analysis_folder, 'input',
                                                 run_options[':datapoint_id']).replace('\\', '/')
        s3_output_folder = os.path.join(s3_analysis_folder, 'output').replace('\\', '/')
        s3_datapoint_output_folder = os.path.join(s3_output_folder, run_options[':datapoint_id']).replace('\\',
                                                                                                          '/')
        s3_btap_data_path = os.path.join(s3_datapoint_output_folder, 'btap_data.json').replace('\\', '/')
        s3_error_txt_path = os.path.join(s3_datapoint_output_folder, 'error.txt').replace('\\', '/')

        jobName = f"{run_options[':analysis_id']}-{run_options[':datapoint_id']}"

        bundle_command = f"bundle exec ruby btap_cli.rb --input_path s3://{run_options[':s3_bucket']}/{s3_datapoint_input_folder} --output_path s3://{run_options[':s3_bucket']}/{s3_output_folder} "
        # replace \ slashes to / slash for correct s3 convention.
        bundle_command = bundle_command.replace('\\', '/')
        try:

            logging.info(
                f"Copying from {local_datapoint_input_folder} to bucket {run_options[':s3_bucket']} folder {s3_datapoint_input_folder}")
            S3().copy_folder_to_s3(bucket_name=run_options[':s3_bucket'],
                                   source_folder=local_datapoint_input_folder,
                                   target_folder=s3_datapoint_input_folder)
            # Start timer to track simulation time.
            start = time.time()
            self.job(jobName=jobName, debug=True, command=["/bin/bash", "-c", bundle_command])
            # Get btap_data from s3
            logging.info(
                f"Getting data from S3 bucket {run_options[':s3_bucket']} at path {s3_btap_data_path}")
            content_object = boto3.resource('s3').Object(run_options[':s3_bucket'], s3_btap_data_path)
            # Adding simulation high level results to btap_data df.
            btap_data.update(json.loads(content_object.get()['Body'].read().decode('utf-8')))
            # save url to datapoint output for Kamel.
            btap_data[
                'datapoint_output_url'] = f"https://s3.console.aws.amazon.com/s3/buckets/{run_options[':s3_bucket']}?region=ca-central-1&prefix={s3_datapoint_output_folder}/"
            # Store sum of warnings errors and severes.
            btap_data['eplus_warnings'] = sum(
                1 for d in btap_data['eplusout_err_table'] if d.get('error_type') == 'warning')
            btap_data['eplus_severes'] = sum(
                1 for d in btap_data['eplusout_err_table'] if d.get('error_type') == 'severe')
            btap_data['eplus_fatals'] = sum(
                1 for d in btap_data['eplusout_err_table'] if d.get('error_type') == 'fatal')

            # dump full run_options.yml file into database for convienience.
            btap_data['run_options'] = yaml.dump(run_options)

            # Need to zero this in costing btap_data.rb file otherwise may be NA.
            for item in ['energy_eui_heat recovery_gj_per_m_sq', 'energy_eui_heat rejection_gj_per_m_sq']:
                if not btap_data.get(item):
                    btap_data[item] = 0.0

            # Flag that is was successful.
            btap_data['success'] = True
            btap_data['simulation_time'] = time.time() - start
            return btap_data


        except Exception:
            error_msg = ''
            content_object = boto3.resource('s3').Object(run_options[':s3_bucket'], s3_error_txt_path)
            print(error_msg)
            error_msg = content_object.get()['Body'].read().decode('utf-8')
            btap_data = {}
            btap_data.update(run_options)
            btap_data['success'] = False
            btap_data['container_error'] = str(error_msg)
            btap_data['run_options'] = yaml.dump(run_options)
            btap_data['datapoint_output_url'] = 'file:///' + os.path.join(local_datapoint_output_folder)
            # save btap_data json file to output folder if aws_run.
            pathlib.Path(os.path.dirname(local_btap_data_path)).mkdir(parents=True, exist_ok=True)
            with open(local_btap_data_path, 'w') as outfile:
                json.dump(btap_data, outfile, indent=4)
            return btap_data

    def job(self, jobName='test', debug=False, command=None):
        # Tell user.

        # See https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/batch.html#Batch.Client.submit_job
        submitJobResponse = self.__submit_job_wrapper(command, jobName)

        jobId = submitJobResponse['jobId']
        message = f"Submitted job_id {jobId} with job name {jobName} to the job queue {self.job_queue_id}"
        logging.info(message)
        running = False
        # logGroupName = '/aws/batch/job'
        result = 'FAILED'
        while debug:
            # Don't hammer AWS.. make queries every minute for the run status
            time.sleep(60 + random())
            describeJobsResponse = self.__get_job_status(jobId)
            status = describeJobsResponse['jobs'][0]['status']
            if status == 'SUCCEEDED':
                message = 'SUCCEEDED - Job [%s - %s] %s' % (jobName, jobId, status)
                logging.info(message)
                result = 'SUCCEEDED'
                break
            elif status == 'FAILED':
                message = 'FAILED - Job [%s - %s] %s' % (jobName, jobId, status)
                logging.error(message)
                result = 'FAILED'
                break
            elif status == 'RUNNING':
                # Commented out logstream.
                # logStreamName = self.getLogStream(logGroupName, jobName, jobId)
                if not running:  # and logStreamName:
                    running = True
                    # print('Output [%s]:\n %s' % (logStreamName, '=' * 80))
                # if logStreamName:
                # startTime = self.printLogs(logGroupName, logStreamName, startTime) + 1
            else:
                message = 'UNKNOWN - Job [%s - %s] is %-9s' % (jobName, jobId, status)
                # logging.info(message)
                sys.stdout.flush()
        return result

    def build_image(self, rebuild=False):
        
        # Ensure image is rebuilt if requested
        rebuild=self.rebuild_image

        self.image_tag = self.credentials.user_name
        self.image_full_name = f'{self.credentials.account_id}.dkr.ecr.{self.credentials.region_name}.amazonaws.com/' + self.image_name + ':' + self.image_tag

        # Todo create cloud build service role.

        repositories = self.ecr.describe_repositories()['repositories']
        if next((item for item in repositories if item["repositoryName"] == self.image_name), None) == None:
            message = f"Creating repository {self.image_name}"
            logging.info(message)
            self.ecr.create_repository(repositoryName=self.image_name)
        else:
            message = f"Repository {self.image_name} already exists. Using existing."
            logging.info(message)

        # Check if image exists.. if not it will create an image from the latest git hub reps.
        # Get list of tags for image name on aws.
        available_tags = sum(
            [d.get('imageTags', [None]) for d in
             self.ecr.describe_images(repositoryName=self.image_name)['imageDetails']],
            [])

        if not self.image_tag in available_tags:
            message = f"The tag {self.image_tag} does not exist in the AWS ECR repository for {self.image_name}. Creating from latest sources."
            logging.info(message)
            print(message)

        if rebuild:
            message = f"User requested build from sources. image:{self.image_name}:{self.image_tag}  "
            logging.info(message)
            print(message)

        if rebuild == True or not self.image_tag in available_tags:
            message = f"Building image from sources.\n\ttag:{self.image_tag}\n\timage:{self.image_name}\n\tos_version:{self.os_version}\n\tbtap_costing_branch:{self.btap_costing_branch}\n\tos_standards_branch:{self.os_standards_branch}"
            logging.info(message)
            print(message)
            # Codebuild image.
            codebuild = boto3.client('codebuild')

            # Upload files to S3 using custom s3 class to a user folder.
            s3 = S3()
            source_folder = os.path.join(DOCKERFILES_FOLDER, self.image_name)
            # Copies Dockerfile from btap_cli repository
            url = DOCKERFILE_URL
            r = requests.get(url, allow_redirects=True)
            with open(os.path.join(source_folder, 'Dockerfile'), 'wb') as file:
                file.write(r.content)

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
            message = f'Code build image env overrides {environmentVariablesOverride}'
            logging.info(message)

            message = f"Building from sources at {source_location}"
            logging.info(message)

            response = codebuild.start_build(projectName=self.image_name,
                                             sourceTypeOverride='S3',
                                             sourceLocationOverride=source_location,
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
                # Check status every 5 secs.
                time.sleep(5)

    # This method is a helper to print/stream logs.
    def __printLogs(self, logGroupName, logStreamName, startTime):
        kwargs = {'logGroupName': logGroupName,
                  'logStreamName': logStreamName,
                  'startTime': startTime,
                  'startFromHead': True}

        lastTimestamp = ''
        while True:
            # Note if using a linter and get warning "Expected Dictionary and got Dict" This is a false positive.
            logEvents = self.cloudwatch.get_log_events(**kwargs)

            for event in logEvents['events']:
                lastTimestamp = event['timestamp']
                timestamp = datetime.utcfromtimestamp(lastTimestamp / 1000.0).isoformat()

            nextToken = logEvents['nextForwardToken']
            if nextToken and kwargs.get('nextToken') != nextToken:
                kwargs['nextToken'] = nextToken
            else:
                break
        return lastTimestamp

    # This method is a helper to print/stream logs.
    def __getLogStream(self, logGroupName, jobName, jobId):
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
    def __add_storage_space_launch_template(self, sizegb=CONTAINER_STORAGE):
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

    def __delete_storage_space_launch_template(self):
        template_name = f'{self.credentials.account_id}_storage'
        response = self.ec2.delete_launch_template(
            LaunchTemplateName=template_name
        )

    def __create_compute_environment(self):
        # Inform user starting to create CE.
        message = f'Creating Compute Environment {self.compute_environment_id}'
        print(message)
        logging.info(message)

        # Call to create Compute environment.
        # See https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/batch.html#Batch.Client.create_compute_environment
        # and https://docs.aws.amazon.com/batch/latest/userguide/compute_environment_parameters.html#compute_environment_type
        response = self.batch_client.create_compute_environment(
            computeEnvironmentName=self.compute_environment_id,
            type='MANAGED',  # Allow AWS to manage instances.
            serviceRole=self.aws_batch_service_role,
            computeResources={
                'type': 'EC2',
                'allocationStrategy': AWS_BATCH_ALLOCATION_STRATEGY,
                'minvCpus': MIN_AWS_VCPUS,
                'maxvCpus': MAX_AWS_VCPUS,
                # 'desiredvCpus': DESIRED_AWS_VCPUS,
                'instanceTypes': AWS_BATCH_COMPUTE_INSTANCE_TYPES,
                'imageId': AWS_BATCH_DEFAULT_IMAGE,
                'subnets': self.subnet_id_list,
                'securityGroupIds': self.securityGroupIds,
                'instanceRole': 'ecsInstanceRole',
                'launchTemplate': {

                    'launchTemplateName': self.__add_storage_space_launch_template()}
            }
        )
        # Check state of creating CE.
        while True:
            # See https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/batch.html#Batch.Client.describe_compute_environments
            describe = self.__describe_compute_environments(self.compute_environment_id)
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

    def __delete_compute_environment(self):
        # Inform user starting to create CE.
        message = f'Disable Compute Environment {self.compute_environment_id}'
        print(message)
        logging.info(message)

        # First Disable CE.
        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/batch.html#Batch.Client.update_compute_environment
        self.batch_client.update_compute_environment(computeEnvironment=self.compute_environment_id, state='DISABLED')

        # Wait until CE is disabled.
        while True:
            # See https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/batch.html#Batch.Client.describe_compute_environments
            describe = self.__describe_compute_environments(self.compute_environment_id)
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
        message = f'Deleting Compute Environment {self.compute_environment_id}'
        print(message)
        logging.info(message)
        self.batch_client.delete_compute_environment(computeEnvironment=self.compute_environment_id)
        # Wait until CE is disabled.
        while True:
            describe = self.__describe_compute_environments(self.compute_environment_id)
            if not describe['computeEnvironments']:
                break
            time.sleep(5)

    def __delete_job_queue(self):
        # Disable Queue
        # Tell user
        message = f'Disable Job Queue {self.job_queue_id}'
        print(message)
        logging.info(message)
        # See https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/batch.html#Batch.Client.update_job_queue
        self.batch_client.update_job_queue(jobQueue=self.job_queue_id, state='DISABLED')
        while True:
            # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/batch.html#Batch.Client.describe_job_queues
            describe = self.__describe_job_queues(self.job_queue_id)
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
        response = self.batch_client.delete_job_queue(jobQueue=self.job_queue_id)
        # Wait until queue is deleted.
        while True:
            # See https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/batch.html#Batch.Client.describe_job_queues
            describe = self.__describe_job_queues(self.job_queue_id)
            if not describe['jobQueues']:
                break
            time.sleep(5)
        return response

    def __delete_job_definition(self):
        message = f'Disable Job Definition {self.job_def_id}'
        print(message)
        logging.info(message)
        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/batch.html#Batch.Client.describe_job_definitions
        describe = self.batch_client.describe_job_definitions(jobDefinitionName=self.job_def_id)
        # See https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/batch.html#Batch.Client.deregister_job_definition
        response = self.batch_client.deregister_job_definition(
            jobDefinition=describe['jobDefinitions'][0]['jobDefinitionArn'])
        return response

    def __create_job_queue(self):
        message = f'Creating Job Queue {self.job_queue_id}'
        logging.info(message)
        print(message)

        response = self.batch_client.create_job_queue(jobQueueName=self.job_queue_id,
                                                      priority=100,
                                                      computeEnvironmentOrder=[
                                                          {
                                                              'order': 0,
                                                              'computeEnvironment': self.compute_environment_id
                                                          }
                                                      ])

        while True:
            describe = self.__describe_job_queues(self.job_queue_id)
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
                logging.error(message)
                exit(1)
            time.sleep(5)

        return response

    def __register_job_definition(self,
                                  unitVCpus=CONTAINER_VCPU,
                                  unitMemory=CONTAINER_MEMORY):

        # Store the aws service role arn for AWSBatchServiceRole. This role is created by default when AWSBatch
        # compute environment is created for the first time via the web console automatically.

        message = f'Creating Job Definition {self.job_def_id}'
        logging.info(message)
        print(message)

        response = self.batch_client.register_job_definition(jobDefinitionName=self.job_def_id,
                                                             type='container',
                                                             containerProperties={
                                                                 'image': self.image_full_name,
                                                                 'vcpus': unitVCpus,
                                                                 'memory': unitMemory,
                                                                 'privileged': True,
                                                                 'jobRoleArn': self.batch_job_role
                                                             })

        return response

    def __submit_job_wrapper(self, command, jobName, n=0):
        try:
            submitJobResponse = self.batch_client.submit_job(
                jobName=jobName,
                jobQueue=self.job_queue_id,
                jobDefinition=self.job_def_id,
                containerOverrides={'command': command}
            )
            return submitJobResponse
        except:
            # Implementing exponential backoff
            if n == 8:
                logging.exception(
                    f'Failed to submit job {jobName} in 7 tries while using exponential backoff. Error was {sys.exc_info()[0]} ')
            wait_time = 2 ** n + random()
            logging.warning(f"Implementing exponential backoff for job {jobName} for {wait_time}s")
            time.sleep(wait_time)
            return self.__submit_job_wrapper(command, jobName, n=n + 1)

    def __get_job_status(self, jobId, n=0):
        try:
            describeJobsResponse = self.batch_client.describe_jobs(jobs=[jobId])
            return describeJobsResponse
        except:
            if n == 8:
                raise (f'Failed to get job status for {jobId} in 7 tries while using exponential backoff.')
            wait_time = 2 ** n + random()
            logging.warning(f"Implementing exponential backoff for job {jobId} for {wait_time}s")
            time.sleep(wait_time)
            return self.__get_job_status(jobId, n=n + 1)

    def __describe_job_queues(self, job_queue_id, n=0):
        try:
            # See https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/batch.html#Batch.Client.describe_job_queues
            return self.batch_client.describe_job_queues(jobQueues=[job_queue_id])
        except:
            if n == 8:
                raise (
                    f'Failed to get job Queue status for {job_queue_id} in 7 tries while using exponential backoff.')
            wait_time = 2 ** n + random()
            logging.warning(f"Implementing exponential backoff for job {job_queue_id} for {wait_time}s")
            time.sleep(wait_time)
            return self.__describe_job_queues(job_queue_id, n=n + 1)

    def __describe_compute_environments(self, compute_environment_id, n=0):
        try:
            return self.batch_client.describe_compute_environments(computeEnvironments=[compute_environment_id])
        except:
            if n == 8:
                raise (
                    f'Failed to get job Queue status for {compute_environment_id} in 7 tries while using exponential backoff.')
            wait_time = 2 ** n + random()
            logging.warning(f"Implementing exponential backoff for job {compute_environment_id} for {wait_time}s")
            time.sleep(wait_time)
            return self.__describe_compute_environments(compute_environment_id, n=n + 1)


# Class to manage local Docker batch run.
class DockerBatch:

    @classmethod
    def get_threads(cls):
        # Try to access the docker daemon. If we cannot.. ask user to turn it on and then exit.
        try:
            docker.from_env()
        except DockerException as err:
            logging.error(
                f"Could not access Docker Daemon. Either it is not running, or you do not have permissions to run docker. {err}. Could not get number of cpus used in Docker.")
            exit(1)
        # Return number of cpus minus 2 to give a bit of slack.
        return int(docker.from_env().containers.run(image='alpine', command='nproc --all', remove=True)) - 2

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
        url = DOCKERFILE_URL
        r = None
        try:
            r = requests.get(url, allow_redirects=True)
        except requests.exceptions.SSLError as err:
            logging.error(
                "Could not set up SSL certificate. Are you behind a VPN? This will interfere with SSL certificates.")
            exit(1)

        file = open(os.path.join(self.dockerfile, 'Dockerfile'), 'wb')
        file.write(r.content)
        file.close()
        # get a docker client object to run docker commands.
        self.docker_client = docker.from_env()
        # initialize image to None.. will assign later.
        self.image = None

    def setup(self):
        self.build_image()

    def build_image(self):
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
        message = f"OS_STANDARDS Branch:{self.os_standards_branch}"
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
                buildargs=buildargs,
                # remove temp containers.
                forcerm=True
            )
            for chunk in json_log:
                if 'stream' in chunk:
                    for line in chunk['stream'].splitlines():
                        logging.debug(line)
            # let use know that the image built sucessfully.
            message = f'Image built in {(time.time() - start) / 60}m'
            logging.info(message)
            print(message)
        else:
            message = "Using existing image."
            logging.info(message)
            print(message)
        self.image = image

        # return image.. also is a part of the object.
        return self.image

    # This method will run the simulation with the general command. It passes all the information via the
    # run_options.yml file. This file was created ahead of this in the local_input_folder which is mounted to the
    # container. The output similarly will be placed in the local_output_folder using the datapoint_id as the new
    # folder name.

    def submit_job(self,
                   output_folder,
                   local_btap_data_path,
                   local_datapoint_input_folder,
                   local_datapoint_output_folder,
                   run_options):
        local_error_txt_path = os.path.join(output_folder, run_options[':datapoint_id'], 'error.txt')
        btap_data = {}
        # add run options to dict.
        btap_data.update(run_options)
        # Start timer to track simulation time.
        start = time.time()
        try:

            result = self.job(
                run_options=run_options,
                local_input_folder=local_datapoint_input_folder,
                local_output_folder=output_folder,
                detach=False
            )
            # If file was not created...raise an error.
            if not os.path.isfile(local_btap_data_path):
                raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), local_btap_data_path)
            # Open the btap Data file in analysis dict.
            file = open(local_btap_data_path, 'r')
            btap_data.update(json.load(file))
            file.close()
            # save output url.
            btap_data['datapoint_output_url'] = 'file:///' + os.path.join(local_datapoint_output_folder)
            # Store sum of warnings errors and severes.
            btap_data['eplus_warnings'] = sum(
                1 for d in btap_data['eplusout_err_table'] if d.get('error_type') == 'warning')
            btap_data['eplus_severes'] = sum(
                1 for d in btap_data['eplusout_err_table'] if d.get('error_type') == 'severe')
            btap_data['eplus_fatals'] = sum(
                1 for d in btap_data['eplusout_err_table'] if d.get('error_type') == 'fatal')
            # dump full run_options.yml file into database for convienience.
            btap_data['run_options'] = yaml.dump(run_options)
            # Need to zero this in costing btap_data.rb file otherwise may be NA.
            for item in ['energy_eui_heat recovery_gj_per_m_sq', 'energy_eui_heat rejection_gj_per_m_sq']:
                if not btap_data.get(item):
                    btap_data[item] = 0.0
            # Flag that is was successful.
            btap_data['success'] = True
            btap_data['simulation_time'] = time.time() - start
            return btap_data
        except Exception as error:
            error_msg = ''
            if os.path.exists(local_error_txt_path):
                with open(local_error_txt_path, 'r') as file:
                    error_msg = file.read()
            btap_data = {}
            btap_data.update(run_options)
            btap_data['success'] = False
            btap_data['container_error'] = str(error_msg)
            btap_data['run_options'] = yaml.dump(run_options)
            btap_data['datapoint_output_url'] = 'file:///' + os.path.join(local_datapoint_output_folder)
            return btap_data

    def job(self,

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
        volumes = {
            local_output_folder: {
                'bind': '/btap_costing/utilities/btap_cli/output',
                'mode': 'rw'},
            local_input_folder: {
                'bind': '/btap_costing/utilities/btap_cli/input',
                'mode': 'rw'},
        }
        # Runnning docker command
        run_options[
            'docker_command'] = f"docker run --rm -v {local_output_folder}:/btap_costing/utilities/btap_cli/output -v {local_input_folder}:/btap_costing/utilities/btap_cli/input {run_options[':image_name']} bundle exec ruby btap_cli.rb"
        result = self.docker_client.containers.run(
            # Local image name to use.
            image=run_options[':image_name'],

            # Command issued to container.
            command='bundle exec ruby btap_cli.rb',

            # host volume mount points and setting to read and write.
            volumes=volumes,
            # Will detach from current thread.. don't do it if you don't understand this.
            detach=detach,
            # This deletes the container on exit otherwise the container
            # will bloat your system.
            auto_remove=True
        )

        return result


# Parent Analysis class from with all analysis inherit
class BTAPAnalysis():
    # This does some simple check on the osm file to ensure that it has the required inputs for btap.
    def check_list(self, osm_file):
        print("Preflight check of local osm file.")
        # filepath = r"C:\Users\plopez\PycharmProjects\btap_batch\examples\idp\idp_example_elim\b6056cd4-e4f5-44eb-ae57-73b624faa5ce\output\0fba95bd-455a-44f4-8532-2e167a95cffa\sizing_folder\autozone_systems\run\in.osm"
        version_translator = openstudio.osversion.VersionTranslator()
        model = version_translator.loadModel(openstudio.path(osm_file)).get()
        necb_lib = openstudio.osversion.VersionTranslator().loadModel(openstudio.path(NECB2011_SPACETYPE_PATH)).get()

        messages = ''
        if not model.getBuilding().standardsBuildingType().is_initialized():
            messages += f"OS:Building, you have not defined the standardsBuildingType\n"

        if not model.getBuilding().standardsNumberOfAboveGroundStories().is_initialized():
            messages += f"OS:Building, you have not defined the standardsNumberOfAboveGroundStories\n"

        if not model.getBuilding().standardsNumberOfStories().is_initialized():
            messages += f"OS:Building, you have not defined the standardsNumberOfStories\n"

        for space in model.getSpaces():
            if not space.spaceType().is_initialized():
                messages += f"OS:Space {space.name().get()} does not have a spacetype defined.\n"

            if not space.thermalZone().is_initialized():
                messages += f"OS:Space {space.name().get()} is not associated with a zone.\n"
        model_spacetypes = []
        for spacetype in model.getSpaceTypes():
            if not spacetype.standardsBuildingType().is_initialized():
                messages += f"OS:SpaceType {spacetype.name().get()} does not have a standardBuildingType defined.\n"
            if not spacetype.standardsSpaceType().is_initialized():
                messages += f"OS:SpaceType {spacetype.name().get()} does not have a standardsSpaceType defined.\n"

            if spacetype.standardsSpaceType().is_initialized() and spacetype.standardsBuildingType().is_initialized():
                model_spacetypes.append(spacetype.standardsBuildingType().get() + spacetype.standardsSpaceType().get())

        # Check if we are using NECB2011 spacetypes
        necb_spacetypes = list(
            map(lambda spacetype: spacetype.standardsBuildingType().get() + spacetype.standardsSpaceType().get(),
                necb_lib.getSpaceTypes()))
        for st in model_spacetypes:
            if not st in necb_spacetypes:
                messages += f"OS:SpaceType {st} is not associated a valid NECB2011 spacetype.\n"

        if len(messages) > 0:
            logging.error(f"The errors below need to be fixed in your osm file.\n{messages}\n")
            raise OSMErrorException(f"The osm file {osm_file} is misconfigured.. Analysis aborted.\n")

    def get_local_osm_files(self):
        osm_list = {}
        osm_folder = os.path.join(self.project_root, 'osm_folder')
        if pathlib.Path(osm_folder).is_dir():
            for file in os.listdir(osm_folder):
                if file.endswith(".osm"):
                    osm_list[os.path.splitext(file)[0]] = os.path.join(osm_folder, file)
        return osm_list

    # Constructor will
    def __init__(self,
                 analysis_config=None,
                 building_options=None,
                 project_root=None,
                 git_api_token=None,
                 batch=None,
                 baseline_results=None):
        self.credentials = None
        self.batch = batch
        self.btap_data_df = []
        self.failed_df = []
        self.analysis_config = analysis_config
        self.building_options = building_options
        self.project_root = project_root  # os.path.dirname(analysis_config_file)
        self.baseline_results = baseline_results

        # Making sure that used installed docker.
        find_docker = os.system("docker -v")
        if find_docker != 0:
            logging.exception("Docker is not installed on this system")

        # Try to access the docker daemon. If we cannot.. ask user to turn it on and then exit.
        try:
            docker.from_env()
        except DockerException as err:
            logging.error(
                f"Could not access Docker Daemon. Either it is not running, or you do not have permissions to run docker. {err}")
            exit(1)

        # Check user selected public version.. if so force costing to be turned off.
        if self.analysis_config[':image_name'] == 'btap_public_cli':
            self.analysis_config[':enable_costing'] = False

        # Set up project root.

        # Create required paths and folders for analysis
        self.create_paths_folders()

        # If batch object has not been pass/created.. make one.
        # This really should be replaced with a https://en.wikipedia.org/wiki/Factory_method_pattern.
        if self.batch == None:
            if self.analysis_config[':compute_environment'] == 'aws_batch':
                # If aws batch object was not passed.. create it.

                # Start batch queue if required.
                # create aws image, set up aws compute env and create workflow queue.
                self.batch = AWSBatch(
                    analysis_id=self.analysis_config[':analysis_id'],
                    btap_image_name=self.analysis_config[':image_name'],
                    rebuild_image=self.analysis_config[':nocache'],
                    git_api_token=git_api_token,
                    os_version=self.analysis_config[':os_version'],
                    btap_costing_branch=self.analysis_config[':btap_costing_branch'],
                    os_standards_branch=self.analysis_config[':os_standards_branch'],
                )
                self.batch.setup()
            else:
                self.batch = DockerBatch(image_name=self.analysis_config[':image_name'],
                                         git_api_token=git_api_token,
                                         os_standards_branch=self.analysis_config[':os_standards_branch'],
                                         btap_costing_branch=self.analysis_config[':btap_costing_branch'],
                                         os_version=self.analysis_config[':os_version'],
                                         nocache=self.analysis_config[':nocache'])
                self.batch.setup()

    def get_num_of_runs_failed(self):
        if os.path.isdir(self.failures_folder):
            return len([name for name in os.listdir(self.failures_folder) if
                        os.path.isfile(os.path.join(self.failures_folder, name))])
        else:
            return 0

    def get_num_of_runs_completed(self):

        if os.path.isdir(self.database_folder):
            return len([name for name in os.listdir(self.database_folder) if
                        os.path.isfile(os.path.join(self.database_folder, name))])
        else:
            return 0

    # This methods sets the pathnames and creates the input and output folders for the analysis. It also initilizes the
    # sql database.
    def create_paths_folders(self):

        # Create analysis folder
        os.makedirs(self.project_root, exist_ok=True)

        # Create unique id for the analysis if not given.
        if not ':analysis_id' in self.analysis_config or self.analysis_config[':analysis_id'] == None:
            self.analysis_config[':analysis_id'] = str(uuid.uuid4())

        # Tell user and logger id and names
        print(f'analysis_id is: {self.analysis_config[":analysis_id"]}')
        print(f'analysis_name is: {self.analysis_config[":analysis_name"]}')
        print(f'analysis type is: {self.analysis_config[":algorithm"][":type"]}')
        logging.info(f'analysis_id:{self.analysis_config[":analysis_id"]}')
        logging.info(f'analysis_name:{self.analysis_config[":analysis_name"]}')
        logging.info(f'analysis type is: {self.analysis_config[":algorithm"][":type"]}')

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

        message = f'Creating new folders for analysis'
        logging.info(message)
        print(message)
        # create local input and output folders
        self.input_folder = os.path.join(self.analysis_id_folder,
                                         'input')
        self.output_folder = os.path.join(self.analysis_id_folder,
                                          'output')
        self.results_folder = os.path.join(self.analysis_id_folder,
                                           'results')
        self.database_folder = os.path.join(self.results_folder,
                                            'database')
        self.failures_folder = os.path.join(self.results_folder,
                                            'failures')

        # Make input / output folder for mounting to container.
        os.makedirs(self.input_folder, exist_ok=True)
        os.makedirs(self.output_folder, exist_ok=True)
        os.makedirs(self.results_folder, exist_ok=True)
        os.makedirs(self.database_folder, exist_ok=True)
        os.makedirs(self.failures_folder, exist_ok=True)
        logging.info(f"local mounted input folder:{self.input_folder}")
        logging.info(f"local mounted output folder:{self.output_folder}")
        logging.info(f"local mounted results_folder folder:{self.results_folder}")
        logging.info(f"local mounted database_folder folder:{self.database_folder}")
        logging.info(f"local mounted failures_folder folder:{self.failures_folder}")

    def run_datapoint(self, run_options):
        # Start timer to track simulation time.
        start = time.time()

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
        run_options[':image_name'] = self.analysis_config[':image_name']
        run_options[':output_variables'] = self.analysis_config[':output_variables']
        run_options[':output_meters'] = self.analysis_config[':output_meters']
        run_options[':algorithm_type'] = self.analysis_config[':algorithm'][':type']

        # Local Paths
        local_datapoint_input_folder = os.path.join(self.input_folder, run_options[':datapoint_id'])
        local_datapoint_output_folder = os.path.join(self.output_folder, run_options[':datapoint_id'])
        local_run_option_file = os.path.join(local_datapoint_input_folder, 'run_options.yml')
        # Create path to btap_data.json file.
        local_btap_data_path = os.path.join(self.output_folder, run_options[':datapoint_id'], 'btap_data.json')

        # Save run_option file for this simulation.
        os.makedirs(local_datapoint_input_folder, exist_ok=True)
        logging.info(f'saving simulation input file here:{local_run_option_file}')
        with open(local_run_option_file, 'w') as outfile:
            yaml.dump(run_options, outfile, encoding=('utf-8'))

        # Save custom osm file if required.
        local_osm_dict = self.get_local_osm_files()
        if run_options[':building_type'] in local_osm_dict:
            shutil.copy(local_osm_dict[run_options[':building_type']], local_datapoint_input_folder)
            logging.info(
                f"Copying osm file from {local_osm_dict[run_options[':building_type']]} to {local_datapoint_input_folder}")

        # Submit Job to batch
        return self.batch.submit_job(self.output_folder,
                                     local_btap_data_path,
                                     local_datapoint_input_folder,
                                     local_datapoint_output_folder,
                                     run_options)

    def save_results_to_database(self, results):
        if results['success'] == True:
            # If container completed with success don't save container output.
            results['container_output'] = None
            if results['eplus_fatals'] > 0:
                # If we had fatal errors..the run was not successful after all.
                results['success'] = False
        # This method organizes the data structure of the dataframe to fit into a report table.
        df = self.sort_results(results)

        # Save datapoint row information to disc in case of catastrophic failure or when C.K. likes to hit Ctrl-C

        pathlib.Path(self.database_folder).mkdir(parents=True, exist_ok=True)
        df.to_csv(os.path.join(self.database_folder, f"{results[':datapoint_id']}.csv"))

        # Save failures to a folder as well.

        if results['success'] == False:
            df.to_csv(os.path.join(self.failures_folder, f"{results[':datapoint_id']}.csv"))
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

    def shutdown_analysis(self):
        self.generate_output_file(baseline_results=self.baseline_results)

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

        # Return the variables.. but the return value is not really use since these are access via the object variable self anyways.
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

    def generate_output_file(self, baseline_results=None):

        # Process csv file to create single dataframe with all simulation results
        PostProcessResults(baseline_results=baseline_results,
                           database_folder=self.database_folder,
                           results_folder=self.results_folder).run()
        excel_path = os.path.join(self.results_folder, 'output.xlsx')

        # If this is an aws_batch run, copy the excel file to s3 for storage.
        if self.analysis_config[':compute_environment'] == 'aws_batch':
            self.credentials = AWSCredentials()
            target_path = os.path.join(self.credentials.user_name, self.analysis_config[':analysis_name'],
                                       self.analysis_config[':analysis_id'], 'results', 'output.xlsx')
            # s3 likes forward slashes.
            target_path = target_path.replace('\\', '/')
            message = "Uploading %s..." % target_path
            logging.info(message)
            S3().upload_file(excel_path, self.credentials.account_id, target_path)
        return


# Class to Manage parametric runs.
class BTAPParametric(BTAPAnalysis):
    def __init__(self,
                 analysis_config=None,
                 building_options=None,
                 project_root=None,
                 git_api_token=None,
                 batch=None,
                 baseline_results=None
                 ):
        # Run super initializer to set up default variables.
        super().__init__(analysis_config=analysis_config,
                         building_options=building_options,
                         project_root=project_root,
                         git_api_token=git_api_token,
                         batch=batch,
                         baseline_results=baseline_results)
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
            print("Shutdown..")
            self.shutdown_analysis()

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
        print(f'Using {self.batch.get_threads()} threads.')
        time.sleep(0.01)
        with tqdm.tqdm(desc=f"Failed:{self.get_num_of_runs_failed()}: Progress Bar", total=len(self.scenarios),
                       colour='green') as pbar:
            with concurrent.futures.ThreadPoolExecutor(self.batch.get_threads()) as executor:
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
                    message = f'TotalRuns:{self.file_number}\tCompleted:{self.get_num_of_runs_completed()}\tFailed:{self.get_num_of_runs_failed()}\tElapsed Time: {str(datetime.timedelta(seconds=round(time.time() - threaded_start)))}'
                    logging.info(message)
                    pbar.update(1)

        # At end of runs update for users.
        message = f'{self.file_number} Simulations completed. No. of failures = {self.get_num_of_runs_failed()} Total Time: {str(datetime.timedelta(seconds=round(time.time() - threaded_start)))}'
        logging.info(message)
        print(message)


# Optimization problem definition class using Pymoo
class BTAPProblem(ElementwiseProblem):
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
            # Tell pymoo that the variables are discrete integers and not floats as is usually the default.
            type_var=int,
            # options to parent class (not used)
            **kwargs)  # Note if using a linter and get warning "Expected Dictionary and got Dict" This is a false positive.

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
        message = f'{self.btap_optimization.get_num_of_runs_completed()} simulations completed of {self.btap_optimization.max_number_of_simulations}. No. of failures = {self.btap_optimization.get_num_of_runs_failed()}'
        logging.info(message)
        self.btap_optimization.pbar.update(1)
        # Pass back objective function results.
        objectives = []
        for objective in self.btap_optimization.analysis_config[':algorithm'][':minimize_objectives']:
            if not (objective in results):
                raise FailedSimulationException(
                    f"Objective value {objective} not found in results of simulation. Most likely due to failure of simulation runs. Stopping optimization")
            objectives.append(results[objective])

        out["F"] = np.column_stack(objectives)


# Class to manage optimization analysis
class BTAPOptimization(BTAPAnalysis):
    def __init__(self,
                 analysis_config=None,
                 building_options=None,
                 project_root=None,
                 git_api_token=None,
                 batch=None,
                 baseline_results=None
                 ):
        # Run super initializer to set up default variables.
        super().__init__(analysis_config=analysis_config,
                         building_options=building_options,
                         project_root=project_root,
                         git_api_token=git_api_token,
                         batch=batch,
                         baseline_results=baseline_results)

    def run(self):

        message = "success"
        try:
            # Create options encoder. This method creates an object to translate variable options
            # from a list of object to a list of integers. Pymoo and most optimizers operate on floats and strings.
            # We are forcing the use of int for discrete analysis.
            self.create_options_encoder()

            # Run optimization. This will create all the input files, run and gather the results.
            self.run_analysis()

        except FailedSimulationException as err:
            message = f"Simulation(s) failed. Optimization cannot continue. Please review failed simulations to determine cause of error in Excel output or if possible the simulation datapoint files. \nLast failure:\n\t {err}"
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

    def run_analysis(self):
        print(f"Running Algorithm {self.analysis_config[':algorithm']}")
        print(f"Number of Variables: {self.number_of_variables()}")
        print(f"Number of minima objectives: {self.number_of_minimize_objectives()}")
        print(f"Number of possible designs: {self.number_of_possible_designs}")
        max_number_of_individuals = int(self.analysis_config[':algorithm'][':population']) * int(
            self.analysis_config[':algorithm'][':n_generations'])
        if self.number_of_possible_designs < max_number_of_individuals:
            self.max_number_of_simulations = self.number_of_possible_designs
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

            message = f'Using {self.batch.get_threads()} threads.'
            logging.info(message)
            print(message)
            # Sometime the progress bar appears before the print statement above. This paused the execution slightly.
            time.sleep(0.01)

            # Set up progress bar tracker.
            with tqdm.tqdm(desc=f"Optimization Progress", total=self.max_number_of_simulations, colour='green') as pbar:
                # Need to make pbar available to the __evaluate method.
                self.pbar = pbar
                # Create thread pool object.
                with ThreadPool(self.batch.get_threads()) as pool:
                    # Create pymoo problem. Pass self for helper methods and set up a starmap multithread pool.
                    problem = BTAPProblem(btap_optimization=self, runner=pool.starmap,
                                          func_eval=starmap_parallelized_eval)
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
                    # Scatter().add(res.F).show()
                    # Let the user know the runtime.
                    print('Execution Time:', self.res.exec_time)

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
        # lower bound of all options (should be zero)
        xl = [0] * self.number_of_variables()
        # Upper bound.
        xu = self.x_u()
        # create ranges for each ecm and create the Space object.
        space = Space(list(map(lambda x, y: (x, y), xl, xu)))
        # set random seed.

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


# Class to manage IDP runs with group elimination,sensitivity and optimization runs.
class BTAPIntegratedDesignProcess:
    def __init__(self,
                 analysis_config=None,
                 building_options=None,
                 project_root=None,
                 git_api_token=None,
                 batch=None,
                 baseline_results=None):
        self.analysis_config = analysis_config
        self.building_options = building_options
        self.project_root = project_root
        self.git_api_token = git_api_token
        self.batch = batch
        self.baseline_results = baseline_results

    # While not a child of BTAPAnalysis, have the same run method for consistency.
    def run(self):
        # excel file container.
        output_excel_files = []

        # Elimination block
        analysis_suffix = '_elim'
        algorithm_type = 'elimination'
        temp_analysis_config = copy.deepcopy(self.analysis_config)
        temp_building_options = copy.deepcopy(self.building_options)
        temp_analysis_config[':algorithm'][':type'] = algorithm_type
        temp_analysis_config[':analysis_name'] = temp_analysis_config[':analysis_name'] + analysis_suffix
        bb = BTAPElimination(analysis_config=temp_analysis_config,
                             building_options=temp_building_options,
                             project_root=self.project_root,
                             git_api_token=self.git_api_token,
                             batch=self.batch,
                             baseline_results=self.baseline_results)
        print(f"running {algorithm_type} stage")
        bb.run()
        output_excel_files.append(os.path.join(bb.results_folder, 'output.xlsx'))

        # Sensitivity block
        analysis_suffix = '_sens'
        algorithm_type = 'sensitivity'
        temp_analysis_config = copy.deepcopy(self.analysis_config)
        temp_building_options = copy.deepcopy(self.building_options)
        temp_analysis_config[':algorithm'][':type'] = algorithm_type
        temp_analysis_config[':analysis_name'] = temp_analysis_config[':analysis_name'] + analysis_suffix
        bb = BTAPSensitivity(analysis_config=temp_analysis_config,
                             building_options=temp_building_options,
                             project_root=self.project_root,
                             git_api_token=self.git_api_token,
                             batch=self.batch,
                             baseline_results=self.baseline_results)
        print(f"running {algorithm_type} stage")
        bb.run()
        output_excel_files.append(os.path.join(bb.results_folder, 'output.xlsx'))

        # Sensitivity block
        analysis_suffix = '_opt'
        algorithm_type = 'nsga2'
        temp_analysis_config = copy.deepcopy(self.analysis_config)
        temp_building_options = copy.deepcopy(self.building_options)
        temp_analysis_config[':algorithm'][':type'] = algorithm_type
        temp_analysis_config[':analysis_name'] = temp_analysis_config[':analysis_name'] + analysis_suffix
        bb = BTAPOptimization(analysis_config=temp_analysis_config,
                              building_options=temp_building_options,
                              project_root=self.project_root,
                              git_api_token=self.git_api_token,
                              batch=self.batch,
                              baseline_results=self.baseline_results)
        print(f"running {algorithm_type} stage")
        bb.run()
        output_excel_files.append(os.path.join(bb.results_folder, 'output.xlsx'))

        # Output results from all analysis into top level output excel.
        df = pd.DataFrame()
        for file in output_excel_files:
            df = df.append(pd.read_excel(file), ignore_index=True)
        df.to_excel(excel_writer=os.path.join(bb.project_root, 'output.xlsx'), sheet_name='btap_data')


# Class to manage Elimination analysis
class BTAPElimination(BTAPParametric):

    def compute_scenarios(self):
        self.elimination_parameters = [
            [':reference', 'do nothing'],
            [':electrical_loads_scale', '0.0'],
            [':infiltration_scale', '0.0'],
            [':lights_scale', '0.0'],
            [':oa_scale', '0.0'],
            [':occupancy_loads_scale', '0.0'],
            [':shw_scale', '0.0'],
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
        # Replace key value with elimination value.
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


# Class to manage Sensitivity analysis
class BTAPSensitivity(BTAPParametric):
    def compute_scenarios(self):
        # Create default options scenario. Uses first value of all arrays.
        default_options = copy.deepcopy(self.building_options)
        for key, value in self.building_options.items():
            default_options[key] = value[0]
        # Create scenario
        for key, value in self.building_options.items():
            # If more than one option. Iterate, create run_option for each one.
            if isinstance(value, list) and len(value) > 1:
                for item in value:
                    run_option = copy.deepcopy(default_options)
                    run_option[':algorithm_type'] = self.analysis_config[':algorithm'][':type']
                    run_option[key] = item
                    run_option[':scenario'] = key
                    # append scenario to list.
                    self.scenarios.append(run_option)
        message = f'Number of Scenarios {len(self.scenarios)}'
        logging.info(message)
        return self.scenarios


# Class to manage preflight run with is to simply check if any custom OSM files can run.
class BTAPPreflight(BTAPParametric):
    def compute_scenarios(self):
        # Create default options scenario. Uses first value of all arrays.
        # precheck osm files for errors.
        osm_files = {}
        all_osm_files = self.get_local_osm_files()
        for filepath in all_osm_files:
            if filepath in self.building_options[':building_type']:
                osm_files[filepath] = all_osm_files[filepath]
        # iterate through files.
        for osm_file in osm_files:
            run_option = copy.deepcopy(self.building_options)
            # Set all options to nil/none.
            for key, value in self.building_options.items():
                run_option[key] = None
            # lock weather location and other items.. this is simply to check if the osm files will run.
            run_option[':epw_file'] = 'CAN_QC_Montreal-Trudeau.Intl.AP.716270_CWEC2016.epw'
            run_option[':algorithm_type'] = self.analysis_config[':algorithm'][':type']
            run_option[':template'] = 'NECB2011'
            run_option[':primary_heating_fuel'] = 'Electricity'
            # set osm file to pretest..if any.
            run_option[':building_type'] = osm_file
            # check basic items are in file.
            self.check_list(osm_files[osm_file])
            self.scenarios.append(run_option)

        message = f'Number of Scenarios {len(self.scenarios)}'
        logging.info(message)
        return self.scenarios


# Class to run reference simulations.. Based on building_type, epw_file, primary_heating_fuel_type
class BTAPReference(BTAPParametric):
    def compute_scenarios(self):
        # Create default options scenario. Uses first value of all arrays.
        # precheck osm files for errors.
        osm_files = {}
        all_osm_files = self.get_local_osm_files()
        for bt in self.building_options[':building_type']:
            for fuel_type in self.building_options[':primary_heating_fuel']:
                for epw in self.building_options[':epw_file']:
                    for template in self.building_options[':template']:
                        run_option = copy.deepcopy(self.building_options)
                        # Set all options to nil/none.
                        for key, value in self.building_options.items():
                            run_option[key] = None
                        run_option[':epw_file'] = epw
                        run_option[':algorithm_type'] = self.analysis_config[':algorithm'][':type']
                        run_option[':template'] = template
                        run_option[':primary_heating_fuel'] = fuel_type
                        # set osm file to pretest..if any.
                        run_option[':building_type'] = bt
                        self.scenarios.append(run_option)
        message = f'Number of Scenarios {len(self.scenarios)}'
        logging.info(message)
        return self.scenarios


# This class processes the btap_batch file to add columns as needed. This is a separate class as this can be applied
# independant of simulation runs.
class PostProcessResults():
    def __init__(self,
                 baseline_results=BASELINE_RESULTS,
                 database_folder=None,
                 results_folder=None,
                 npv_start_year=2020,
                 npv_end_year=2050,
                 discount_rate=0.03
                 ):

        self.npv_start_year = npv_start_year
        self.npv_end_year = npv_end_year
        self.discount_rate = discount_rate

        filepaths = [os.path.join(database_folder, f) for f in os.listdir(database_folder) if f.endswith('.csv')]
        btap_data_df = pd.concat(map(pd.read_csv, filepaths))
        btap_data_df.reset_index()

        if isinstance(btap_data_df, pd.DataFrame):
            self.btap_data_df = btap_data_df
        else:
            self.btap_data_df = pd.read_excel(open(btap_data_df, 'rb'), sheet_name='btap_data')
        self.baseline_results = baseline_results
        self.results_folder = results_folder

    def run(self):
        self.reference_comparisons()
        self.get_files(file_paths=['run_dir/run/in.osm', 'run_dir/run/eplustbl.htm', 'hourly.csv'])
        self.save_excel_output()
        self.operation_on_hourly_output()
        return self.btap_data_df

    # This method gets files from the run folders into the results folders.  This is both for S3 and local analyses.
    # This is all done serially...if this is too slow, we should implement a parallel method using threads.. While probably
    # Not an issue for local analyses, it may be needed for large run. Here is an example of somebody with an example of parallel
    # downloads from S3 using threads.  https://emasquil.github.io/posts/multithreading-boto3/
    def get_files(self, file_paths=None):
        for file_path in file_paths:
            pathlib.Path(os.path.dirname(self.results_folder)).mkdir(parents=True, exist_ok=True)
            filename = os.path.basename(file_path)
            extension = pathlib.Path(filename).suffix
            message = f"Getting {filename} files"
            logging.info(message)
            bin_folder = os.path.join(self.results_folder, filename)
            os.makedirs(bin_folder, exist_ok=True)
            s3 = boto3.resource('s3')
            func = partial(self.download_file, bin_folder, extension, file_path, s3)
            files = self.btap_data_df['datapoint_output_url'].tolist()
            failed_downloads = []

            with tqdm.tqdm(desc=f"Downloading {filename} files", total=len(self.btap_data_df.index),
                           colour='green') as pbar:
                with ThreadPoolExecutor(max_workers=32) as executor:
                    # Using a dict for preserving the downloaded file for each future, to store it as a failure if we need that
                    futures = {
                        executor.submit(func, row): row for index, row in self.btap_data_df.iterrows()
                    }
                    for future in as_completed(futures):
                        if future.exception():
                            failed_downloads.append(futures[future])
                        pbar.update(1)
            if len(failed_downloads) > 0:
                failed_csv_list = os.path.join(self.results_folder, "failed_downloads.csv")
                message = f"Some downloads have failed. Saving ids to csv here: {failed_csv_list}"
                logging.error(message)
                print(message)
                with open(
                        os.path.join(self.results_folder, "failed_downloads.csv"), "w", newline=""
                ) as csvfile:
                    wr = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
                    wr.writerow(failed_downloads)

    def download_file(self, bin_folder, extension, file_path, s3, row):
        # If files are local
        if row['datapoint_output_url'].startswith('file:///'):
            # This is a local file. use system copy. First remove prefix
            local_file_path = os.path.join(row['datapoint_output_url'][len('file:///'):], file_path)
            if os.path.isfile(local_file_path):
                shutil.copyfile(local_file_path, os.path.join(bin_folder, row[':datapoint_id'] + extension))

        # If files are on S3
        elif row['datapoint_output_url'].startswith('https://s3'):
            p = re.compile(
                "https://s3\.console\.aws\.amazon\.com/s3/buckets/(\d*)\?region=(.*)&prefix=(.*)")
            m = p.match(row['datapoint_output_url'])
            bucket = m.group(1)
            region = m.group(2)
            prefix = m.group(3)
            s3_file_path = prefix + file_path
            target_on_local = os.path.join(bin_folder, row[':datapoint_id'] + extension)
            message = f"Getting file from S3 bucket {bucket} at path {s3_file_path} to {target_on_local}"
            logging.info(message)
            try:
                s3.Bucket(bucket).download_file(s3_file_path, target_on_local)
            except botocore.exceptions.ClientError as e:
                if e.response['Error']['Code'] == "404":
                    print("The object does not exist.")
                else:
                    raise
            # Copy output files ('run_dir/run/in.osm', 'run_dir/run/eplustbl.htm', 'hourly.csv') to s3 for storage.
            self.credentials = AWSCredentials()
            target_path_on_aws = os.path.join("/".join(s3_file_path.split("/")[:3]),'results', file_path, row[':datapoint_id'] + extension)
            target_path_on_aws = target_path_on_aws.replace('\\', '/') # s3 likes forward slashes.
            message = "Uploading %s..." % target_path_on_aws
            logging.info(message)
            S3().upload_file(target_on_local, self.credentials.account_id, target_path_on_aws)


    def save_excel_output(self):
        # Create excel object
        excel_path = os.path.join(self.results_folder, 'output.xlsx')
        with pd.ExcelWriter(excel_path) as writer:
            if isinstance(self.btap_data_df, pd.DataFrame):
                self.btap_data_df.to_excel(writer, index=False, sheet_name='btap_data')
                message = f'Saved Excel Output: {excel_path}'
                logging.info(message)
                print(message)
            else:
                message = 'No simulations completed.'
                logging.error(message)

    # The below operation_on_hourly_output method is for performing operations on hourly output; for instance, sum of hourly data
    def operation_on_hourly_output(self):
        # Find the directory of results
        dir_results = self.results_folder

        # Go through each folder in the results folder.
        for folder_in_results_name in os.listdir(dir_results):
            # Find path of the results folder
            folder_in_results_path = os.path.join(self.results_folder, folder_in_results_name)
            if folder_in_results_name == 'hourly.csv':
                # Find path of the folder where the .yml file is
                yml_file_folder_path = "\\".join(folder_in_results_path.split("\\")[:-4])
                # Find path of the .yml file
                yml_file_path = os.path.join(yml_file_folder_path, 'input.yml')
                # Get inputs in the .yml file
                analysis_config, building_options = load_btap_yml_file(yml_file_path)
                # Get variables specified in the :output_variables variable
                output_var = analysis_config[':output_variables']
                # Get number of variables specified in the :output_variables variable
                output_var_length = len(output_var)

                datapoint_number = 0.0
                df_output = []
                for file_object in os.listdir(folder_in_results_path):
                    # Set path of the output file that will be generated by the operation_on_hourly_output method
                    output_file = os.path.join(folder_in_results_path, "sum_hourly_res.csv")

                    if file_object != 'sum_hourly_res.csv':
                        # Find path of the datapoint in the hourly.csv folder of the results folder
                        datapoint_path = os.path.join(folder_in_results_path, file_object)

                        # Check if the datapoint is empty or not
                        if os.stat(datapoint_path).st_size == 0:
                            datapoint_empty = True
                        else:
                            datapoint_empty = False

                        # Go through datapoint if it is not empty
                        if datapoint_empty == False:

                            # Read the datapoint csv file
                            df = pd.read_csv(datapoint_path)

                            # Get column headers of the df
                            df_columns = df.columns

                            # Create an empty dataframe with the 'df_columns' column headers
                            if datapoint_number == 0.0:
                                df_output = []
                                df_output = pd.DataFrame(columns=df_columns)

                            # Go through each variable of output_var; Do below items for only the ones that their value for 'operation' in the .yml file is not '*'
                            for count_operation_var in range(0,output_var_length):
                                operation_var = output_var[count_operation_var]['variable']
                                operation_case = output_var[count_operation_var]['operation']
                                operation_unit = output_var[count_operation_var]['unit']
                                if operation_var not in df_output['Name']:
                                    df_operation_var = df.loc[df['Name'] == operation_var]
                                    if operation_case == 'sum':
                                        if operation_unit == 'GJ':
                                            value_sum = df_operation_var.iloc[:,4:].sum(axis=0) / 10**9
                                            value_sum['Units'] = 'GJ'
                                        elif operation_unit == 'kWh':
                                            value_sum = 277.778 * df_operation_var.iloc[:,4:].sum(axis=0) / 10**9
                                            value_sum['Units'] = 'kWh'
                                        elif operation_unit != '*':
                                            message = f"Unknown unit for the sum operation on hourly outputs. Allowed units are GJ and kWh."
                                            logging.error(message)
                                        value_sum['datapoint_id'] = df_operation_var['datapoint_id'].iloc[0]
                                        value_sum['Name'] = df_operation_var['Name'].iloc[0]
                                        value_sum['KeyValue'] = ""
                                        df_output = df_output.append(value_sum, True)
                                    elif operation_case != '*':
                                        message = f"Unknown operation type on hourly outputs. Allowed operation type is sum."
                                        logging.error(message)
                            # Go to the next datapoint
                            datapoint_number += 1.0

                if len(df_output) > 0.0:

                    # Save the df_output as the output_file
                    df_output.to_csv(output_file, index=False)

                    # Copy sum_hourly_res.csv to s3 for storage if run on AWS.
                    try:
                        sum_hourly_res_path = os.path.join(self.results_folder, 'hourly.csv', 'sum_hourly_res.csv')
                        self.credentials = AWSCredentials()
                        target_path_on_aws = os.path.join(self.credentials.user_name, "\\".join(sum_hourly_res_path.split("\\")[-5:]))
                        target_path_on_aws = target_path_on_aws.replace('\\', '/')  # s3 likes forward slashes.
                        message = "Uploading %s..." % target_path_on_aws
                        logging.info(message)
                        S3().upload_file(sum_hourly_res_path, self.credentials.account_id, target_path_on_aws)
                    except:
                        print('Run locally. No need to copy sum_hourly_res.csv to s3')

    def reference_comparisons(self):
        if self.baseline_results != None:
            file = open(self.baseline_results, 'rb')
            self.baseline_df = pd.read_excel(file, sheet_name='btap_data')
            file.close()
            merge_columns = [':building_type', ':template', ':primary_heating_fuel', ':epw_file']
            df = pd.merge(self.btap_data_df, self.baseline_df, how='left', left_on=merge_columns,
                          right_on=merge_columns).reset_index()  # Note: in this case, the 'x' suffix stands for the proposed building; and 'y' stands for the baseline (reference) building

            if (('cost_utility_neb_total_cost_per_m_sq_y' in df.columns) and ('cost_utility_neb_total_cost_per_m_sq_x' in df.columns)):
                self.btap_data_df['baseline_savings_energy_cost_per_m_sq'] = round(
                    (df['cost_utility_neb_total_cost_per_m_sq_y'] - df[
                        'cost_utility_neb_total_cost_per_m_sq_x']), 1).values

            self.btap_data_df['baseline_difference_energy_eui_electricity_gj_per_m_sq'] = round(
                (df['energy_eui_electricity_gj_per_m_sq_y'] - df[
                    'energy_eui_electricity_gj_per_m_sq_x']), 1).values

            self.btap_data_df['baseline_difference_energy_eui_natural_gas_gj_per_m_sq'] = round(
                (df['energy_eui_natural_gas_gj_per_m_sq_y'] - df[
                    'energy_eui_natural_gas_gj_per_m_sq_x']), 1).values

            self.btap_data_df['baseline_difference_energy_eui_additional_fuel_gj_per_m_sq'] = round(
                (df['energy_eui_additional_fuel_gj_per_m_sq_y'] - df[
                    'energy_eui_additional_fuel_gj_per_m_sq_x']), 1).values

            if (('cost_equipment_total_cost_per_m_sq_y' in df.columns) and ('cost_equipment_total_cost_per_m_sq_x' in df.columns)):
                self.btap_data_df['baseline_difference_cost_equipment_total_cost_per_m_sq'] = round(
                    (df['cost_equipment_total_cost_per_m_sq_y'] - df[
                        'cost_equipment_total_cost_per_m_sq_x']), 1).values

            if (('baseline_difference_cost_equipment_total_cost_per_m_sq' in df.columns) and ('baseline_savings_energy_cost_per_m_sq' in df.columns)):
                self.btap_data_df['baseline_simple_payback_years'] = round(
                    (self.btap_data_df['baseline_difference_cost_equipment_total_cost_per_m_sq'] / self.btap_data_df[
                        'baseline_savings_energy_cost_per_m_sq']), 1).values

            self.btap_data_df['baseline_peak_electric_percent_better'] = round(
                ((df['energy_peak_electric_w_per_m_sq_y'] - df[
                    'energy_peak_electric_w_per_m_sq_x']) * 100.0 / df['energy_peak_electric_w_per_m_sq_y']), 1).values

            self.btap_data_df['baseline_energy_percent_better'] = round(((df['energy_eui_total_gj_per_m_sq_y'] - df[
                'energy_eui_total_gj_per_m_sq_x']) * 100 / df['energy_eui_total_gj_per_m_sq_y']), 1).values

            self.btap_data_df['baseline_necb_tier'] = pd.cut(self.btap_data_df['baseline_energy_percent_better'],
                                                             bins=[-1000.0, -0.001, 25.00, 50.00, 60.00, 1000.0],
                                                             labels=['non_compliant', 'tier_1', 'tier_2', 'tier_3',
                                                                     'tier_4']).values

            self.btap_data_df['baseline_ghg_percent_better'] = round(((df['cost_utility_ghg_total_kg_per_m_sq_y'] - df[
                'cost_utility_ghg_total_kg_per_m_sq_x']) * 100 / df['cost_utility_ghg_total_kg_per_m_sq_y']), 1).values

            self.economics()

    def economics(self):

        # Get energy end-use prices (CER data from https://apps.cer-rec.gc.ca/ftrppndc/dflt.aspx?GoCTemplateCulture=en-CA)
        ceb_fuel_df = pd.read_csv(os.path.join(os.path.realpath(__file__), '..', 'resources','ceb_fuel_end_use_prices.csv'))

        # Find which province the proposed building is located in
        provinces_names_map = {'QC': 'Quebec',
                               'NL': 'Newfoundland and Labrador',
                               'NS': 'Nova Scotia',
                               'PE': 'Prince Edward Island',
                               'ON': 'Ontario',
                               'MB': 'Manitoba',
                               'SK': 'Saskatchewan',
                               'AB': 'Alberta',
                               'BC': 'British Columbia',
                               'YT': 'Yukon',
                               'NT': 'Northwest Territories',
                               'NB': 'New Brunswick',
                               'NU': 'Nunavut'}
        province = provinces_names_map[self.btap_data_df['location_state_province_region'].values[0]]

        # Get energy end-use prices (CER data from https://apps.cer-rec.gc.ca/ftrppndc/dflt.aspx?GoCTemplateCulture=en-CA)
        energy_price_elec = ceb_fuel_df.loc[(ceb_fuel_df['province'] == province) & (ceb_fuel_df['fuel_type'] == 'Electricity'),str(self.npv_start_year):str(self.npv_end_year)].iloc[0].reset_index(drop=True, name='values')
        energy_price_ngas = ceb_fuel_df.loc[(ceb_fuel_df['province'] == province) & (ceb_fuel_df['fuel_type'] == 'Natural Gas'),str(self.npv_start_year):str(self.npv_end_year)].iloc[0].reset_index(drop=True,name='values')
        energy_price_fueloil = ceb_fuel_df.loc[(ceb_fuel_df['province'] == province) & (ceb_fuel_df['fuel_type'] == 'Oil'),str(self.npv_start_year):str(self.npv_end_year)].iloc[0].reset_index(drop=True, name='values')

        #-------------------------------------------------------------------------------------------------------------------------------------------------------------
        ##### Part I: Calculate difference in NPV of proposed and reference buildings (including equipment and energy cost)
        # Note: If there is on-site energy generation (e.g. PV), it should be considered in the calculation of EUI for the calculation of energy use cost and NPV.
        # To do so, it has been assumed that on-site energy generation is only for electricity.
        # The difference in electricity EUI of proposed and reference building is re-calculated for NPV. It will be: ['baseline_difference_energy_eui_electricity_gj_per_m_sq' + ('total_site_eui_gj_per_m_sq' - 'net_site_eui_gj_per_m_sq')]
        # Note that if there is no on-site energy generation, 'total_site_eui_gj_per_m_sq' and 'net_site_eui_gj_per_m_sq' will be equal.
        # Note: 'total_site_eui_gj_per_m_sq' is the gross energy consumed by the building (REF: https://unmethours.com/question/25416/what-is-the-difference-between-site-energy-and-source-energy/)
        # Note: 'net_site_eui_gj_per_m_sq' is the final energy consumed by the building after accounting for on-site energy generations (e.g. PV) (REF: https://unmethours.com/question/25416/what-is-the-difference-between-site-energy-and-source-energy/)
        # Part I has two steps:
        # Step I: Calculate the difference in energy use cost of the reference and proposed building for the period of npv_start_year to npv_end_year.
        # Step II: Calculate NPV difference between the reference and proposed building for the period of npv_start_year to npv_end_year.
        if ('baseline_difference_cost_equipment_total_cost_per_m_sq' in self.btap_data_df.columns):
            self.btap_data_df['baseline_difference_npv_elec'] = self.btap_data_df.apply(lambda x: x['baseline_difference_cost_equipment_total_cost_per_m_sq'] + npf.npv(self.discount_rate, energy_price_elec * (x['baseline_difference_energy_eui_electricity_gj_per_m_sq'] + x['total_site_eui_gj_per_m_sq'] - x['net_site_eui_gj_per_m_sq'])) if npf.npv(self.discount_rate, energy_price_elec * (x['baseline_difference_energy_eui_electricity_gj_per_m_sq'] + x['total_site_eui_gj_per_m_sq'] - x['net_site_eui_gj_per_m_sq']))>0.0 else 0.0, axis=1)
            self.btap_data_df['baseline_difference_npv_ngas'] = self.btap_data_df.apply(lambda x: x['baseline_difference_cost_equipment_total_cost_per_m_sq'] + npf.npv(self.discount_rate, energy_price_ngas * x['baseline_difference_energy_eui_natural_gas_gj_per_m_sq']) if npf.npv(self.discount_rate, energy_price_ngas * x['baseline_difference_energy_eui_natural_gas_gj_per_m_sq'])>0.0 else 0.0, axis=1)
            self.btap_data_df['baseline_difference_npv_fueloil'] = self.btap_data_df.apply(lambda x: x['baseline_difference_cost_equipment_total_cost_per_m_sq'] + npf.npv(self.discount_rate, energy_price_fueloil * x['baseline_difference_energy_eui_additional_fuel_gj_per_m_sq']) if npf.npv(self.discount_rate, energy_price_fueloil * x['baseline_difference_energy_eui_additional_fuel_gj_per_m_sq'])>0.0 else 0.0, axis=1)

        #-------------------------------------------------------------------------------------------------------------------------------------------------------------
        ##### Part II: Calculate NPV of proposed buildings (including equipment and energy cost)
        # Note: If there is on-site energy generation (e.g. PV), it should be considered in the calculation of EUI for the calculation of energy use cost and NPV.
        # To do so, it has been assumed that on-site energy generation is only for electricity.
        # Electricity EUI of proposed building is re-calculated for NPV. It will be: ['energy_eui_electricity_gj_per_m_sq' - ('total_site_eui_gj_per_m_sq' - 'net_site_eui_gj_per_m_sq')]
        # Note that if there is no on-site energy generation, 'total_site_eui_gj_per_m_sq' and 'net_site_eui_gj_per_m_sq' will be equal.
        # Note: 'total_site_eui_gj_per_m_sq' is the gross energy consumed by the building (REF: https://unmethours.com/question/25416/what-is-the-difference-between-site-energy-and-source-energy/)
        # Note: 'net_site_eui_gj_per_m_sq' is the final energy consumed by the building after accounting for on-site energy generations (e.g. PV) (REF: https://unmethours.com/question/25416/what-is-the-difference-between-site-energy-and-source-energy/)
        # Part II has two steps:
        # Step I: Calculate energy cost of the proposed building for the period of npv_start_year to npv_end_year:
        # Step II: Calculate NPV of the proposed building for the period of npv_start_year to npv_end_year:
        if ('cost_equipment_total_cost_per_m_sq' in self.btap_data_df.columns):
            self.btap_data_df['proposed_building_npv_elec'] = self.btap_data_df.apply(lambda x: x['cost_equipment_total_cost_per_m_sq'] + npf.npv(self.discount_rate, energy_price_elec * (x['energy_eui_electricity_gj_per_m_sq'] - (x['total_site_eui_gj_per_m_sq'] - x['net_site_eui_gj_per_m_sq']))) if npf.npv(self.discount_rate, energy_price_elec * (x['energy_eui_electricity_gj_per_m_sq'] - (x['total_site_eui_gj_per_m_sq'] - x['net_site_eui_gj_per_m_sq'])))>0.0 else 0.0, axis=1)
            self.btap_data_df['proposed_building_npv_ngas'] = self.btap_data_df.apply(lambda x: x['cost_equipment_total_cost_per_m_sq'] + npf.npv(self.discount_rate, energy_price_ngas * x['energy_eui_natural_gas_gj_per_m_sq']) if npf.npv(self.discount_rate, energy_price_ngas * x['energy_eui_natural_gas_gj_per_m_sq'])>0.0 else 0.0, axis=1)
            self.btap_data_df['proposed_building_npv_fueloil'] = self.btap_data_df.apply(lambda x: x['cost_equipment_total_cost_per_m_sq'] + npf.npv(self.discount_rate, energy_price_fueloil * x['energy_eui_additional_fuel_gj_per_m_sq']) if npf.npv(self.discount_rate, energy_price_fueloil * x['energy_eui_additional_fuel_gj_per_m_sq'])>0.0 else 0.0, axis=1)


# Helper method to load input.yml file into data structures required by btap_batch
def load_btap_yml_file(analysis_config_file):
    # Load Analysis File into variable
    if not os.path.isfile(analysis_config_file):
        logging.error(f"could not find analysis input file at {analysis_config_file}. Exiting")
        exit(1)
    # Open the yaml in analysis dict.
    with open(analysis_config_file, 'r') as stream:
        analysis = yaml.safe_load(stream)
    # Store analysis config and building_options.
    analysis_config = analysis[':analysis_configuration']
    building_options = analysis[':building_options']
    return analysis_config, building_options


# Main method that re will interface with. If this gets bigger, consider a factory method pattern.
def btap_batch(analysis_config_file=None, git_api_token=None, batch=None):
    # Load Analysis File into variable
    if not os.path.isfile(analysis_config_file):
        print(f"could not find analysis input file at {analysis_config_file}. Exiting")
        exit(1)
    # Open the yaml in analysis dict
    analysis_config, building_options = load_btap_yml_file(analysis_config_file)
    project_root = os.path.dirname(analysis_config_file)

    # Set Analysis Id if not set
    if (not ':analysis_id' in analysis_config) or analysis_config[':analysis_id'] is None:
        analysis_config[':analysis_id'] = str(uuid.uuid4())

    logfile = os.path.join(project_root, f"{analysis_config[':analysis_id']}.log")
    # remove old logfile if it is there.
    if os.path.exists(logfile):
        os.remove(logfile)

    logging.basicConfig(filename=logfile,
                        filemode='a',
                        format='%(asctime)s, %(levelname)-8s [%(filename)s:%(lineno)d:%(funcName)s] %(message)s',
                        datefmt='%H:%M:%S',
                        level=logging.DEBUG)
    message = f"Log file created: {logfile}"
    print(message)
    logging.info(message)

    print(f"Compute Environment:{analysis_config[':compute_environment']}")
    print(f"Analysis Type:{analysis_config[':algorithm'][':type']}")



    if analysis_config[':compute_environment'] == 'aws_batch' and batch is None:
        # create aws image, set up aws compute env and create workflow queue.

        batch = AWSBatch(
            analysis_id=analysis_config[':analysis_id'],
            btap_image_name=analysis_config[':image_name'],
            rebuild_image=analysis_config[':nocache'],
            git_api_token=git_api_token,
            os_version=analysis_config[':os_version'],
            btap_costing_branch=analysis_config[':btap_costing_branch'],
            os_standards_branch=analysis_config[':os_standards_branch']
        )
        # Create batch queue on aws.
        batch.setup()
    elif analysis_config[':compute_environment'] == 'local' and batch is None:
        batch = DockerBatch(image_name=analysis_config[':image_name'],
                            git_api_token=git_api_token,
                            os_standards_branch=analysis_config[':os_standards_branch'],
                            btap_costing_branch=analysis_config[':btap_costing_branch'],
                            os_version=analysis_config[':os_version'],
                            nocache=analysis_config[':nocache'])
        # Create batch queue on docker desktop.
        batch.setup()

    baseline_results = None
    # Ensure reference run is executed in all other cases unless :run_reference is false.
    if (not ':run_reference' in analysis_config) or (analysis_config[':run_reference'] != False) or (
            analysis_config[':run_reference'] is None):
        # Run reference simulations first.

        analysis_suffix = '_ref'
        algorithm_type = 'reference'
        temp_analysis_config = copy.deepcopy(analysis_config)
        temp_building_options = copy.deepcopy(building_options)
        temp_analysis_config[':algorithm'][':type'] = algorithm_type
        temp_analysis_config[':analysis_name'] = temp_analysis_config[':analysis_name'] + analysis_suffix
        bb = BTAPReference(analysis_config=temp_analysis_config,
                           building_options=temp_building_options,
                           project_root=project_root,
                           git_api_token=git_api_token,
                           batch=batch)
        print(f"running {algorithm_type} stage")
        bb.run()
        baseline_results = os.path.join(bb.results_folder, 'output.xlsx')

    # pre-flight
    if analysis_config[':algorithm'][':type'] == 'pre-flight':
        opt = BTAPPreflight(
            # Input file.
            analysis_config=analysis_config,
            building_options=building_options,
            project_root=project_root,
            git_api_token=git_api_token,
            batch=batch
        )
        return opt
    elif analysis_config[':algorithm'][':type'] == 'reference':
        # Run reference simulations first.
        analysis_suffix = '_ref'
        algorithm_type = 'reference'
        temp_analysis_config = copy.deepcopy(analysis_config)
        temp_building_options = copy.deepcopy(building_options)
        temp_analysis_config[':algorithm'][':type'] = algorithm_type
        temp_analysis_config[':analysis_name'] = temp_analysis_config[':analysis_name'] + analysis_suffix
        bb = BTAPReference(analysis_config=temp_analysis_config,
                           building_options=temp_building_options,
                           project_root=project_root,
                           git_api_token=git_api_token,
                           batch=batch)
        print(f"running {algorithm_type} stage")
        bb.run()
    # LHS
    elif analysis_config[':algorithm'][':type'] == 'sampling-lhs':
        return BTAPSamplingLHS(analysis_config=analysis_config,
                               building_options=building_options,
                               project_root=project_root,
                               git_api_token=git_api_token,
                               batch=batch,
                               baseline_results=baseline_results)
    # nsga2
    elif analysis_config[':algorithm'][':type'] == 'nsga2':
        return BTAPOptimization(analysis_config=analysis_config,
                                building_options=building_options,
                                project_root=project_root,
                                git_api_token=git_api_token,
                                batch=batch,
                                baseline_results=baseline_results)
    # parametric
    elif analysis_config[':algorithm'][':type'] == 'parametric':
        return BTAPParametric(analysis_config=analysis_config,
                              building_options=building_options,
                              project_root=project_root,
                              git_api_token=git_api_token,
                              batch=batch,
                              baseline_results=baseline_results)
    # elimination
    elif analysis_config[':algorithm'][':type'] == 'elimination':
        return BTAPElimination(analysis_config=analysis_config,
                               building_options=building_options,
                               project_root=project_root,
                               git_api_token=git_api_token,
                               batch=batch,
                               baseline_results=baseline_results)
    # Sensitivity
    elif analysis_config[':algorithm'][':type'] == 'sensitivity':
        return BTAPSensitivity(analysis_config=analysis_config,
                               building_options=building_options,
                               project_root=project_root,
                               git_api_token=git_api_token,
                               batch=batch,
                               baseline_results=baseline_results)
    # IDP
    elif analysis_config[':algorithm'][':type'] == 'idp':
        return BTAPIntegratedDesignProcess(analysis_config=analysis_config,
                                           building_options=building_options,
                                           project_root=project_root,
                                           git_api_token=git_api_token,
                                           batch=batch,
                                           baseline_results=baseline_results)
    # osm_batch
    elif analysis_config[':algorithm'][':type'] == 'osm_batch':
        # Need to force this to use the NECB2011 standards class for now.
        return BTAPParametric(analysis_config=analysis_config,
                              building_options=building_options,
                              project_root=project_root,
                              git_api_token=git_api_token,
                              batch=batch)
    else:
        message = f'Unknown algorithm type. Allowed types are nsga2 and parametric. Exiting'
        print(message)
        logging.error(message)
        exit(1)
    if not batch is None:
        batch.tear_down()

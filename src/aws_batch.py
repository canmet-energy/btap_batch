import botocore, boto3
from botocore.config import Config
import logging
import re
import os
import atexit
import uuid
import json,yaml
import time
import datetime
import pathlib
from random import random
import sys
# Do not delete this import...This will set up certificates based on the host system. This
# also must be right ahead of the requests import.
import pip_system_certs.wrapt_requests
import requests
import glob
from .constants import AWS_MAX_RETRIES, MAX_AWS_VCPUS, MIN_AWS_VCPUS, CLOUD_BUILD_SERVICE_ROLE, BATCH_JOB_ROLE
from .constants import BATCH_SERVICE_ROLE, CONTAINER_VCPU, CONTAINER_MEMORY,CONTAINER_STORAGE
from .constants import AWS_BATCH_ALLOCATION_STRATEGY,AWS_BATCH_COMPUTE_INSTANCE_TYPES, AWS_BATCH_DEFAULT_IMAGE
from .constants import DOCKERFILE_URL, DOCKERFILES_FOLDER

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
                    "Your session has expired while running. Please renew your aws credentials and consider running "
                    "this in an amazon instance if your run is longer than 2 hours")
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

    def get_threads(self):
        return MAX_AWS_VCPUS

    """
    This class  manages creating an aws batch workflow, simplifies creating jobs and manages tear down of the
    aws batch. This is opposed to using the aws web console to configure the batch run. 
    That method can lead to problems in management and replication.

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

        # This is the role with permissions inside the docker containers.
        # Created by aws web console. (todo: automate creations and destruction)
        self.batch_job_role = BATCH_JOB_ROLE
        # This is the role with the permissions to create batch runs.
        # Created by aws web console. (todo: automate creations and destruction)
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
        # This method creates batch infrastructure for user.
        self.build_image()
        self.__create_compute_environment()
        self.__create_job_queue()
        self.__register_job_definition()
        print("Completed AWS batch initialization.")

    def tear_down(self):
        # This method creates batch infrastructure for user.
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
            # Store sum of warning, error and severe messages.
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
        rebuild = self.rebuild_image

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




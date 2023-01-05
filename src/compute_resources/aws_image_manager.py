
from src.compute_resources.aws_credentials import AWSCredentials
from src.constants import MAX_AWS_VCPUS,DOCKERFILE_URL,DOCKERFILES_FOLDER
from src.compute_resources.docker_image_manager import DockerImageManager
from src.compute_resources.s3 import S3
from src.compute_resources.iam_roles import IAMCloudBuildRole
import boto3
import os
import time
import requests
import logging


class AWSImageManager(DockerImageManager):

    def __get_credentials(self):
        credentials = AWSCredentials()
        return credentials

    def __init__(self):
        self.credentials = self.__get_credentials()
        self.bucket = self.credentials.account_id

    def image_tag(self):
        return self.credentials.user_name

    def get_threads(self):
        return MAX_AWS_VCPUS

    def build_image(self,
                    dockerfile=None,
                    build_args=None,
                    force_rm=True,
                    verbose=False):
        ecr = boto3.client('ecr')

        image_build_args = build_args
        image_name = image_build_args['IMAGE_REPO_NAME']
        image_build_args['IMAGE_TAG']=self.credentials.user_name
        image_build_args['GIT_API_TOKEN'] = os.environ['GIT_API_TOKEN']

        self.__create_image_repository(repository_name=image_name)

        message = f"Building image with build args {image_build_args}"
        logging.info(message)
        print(message)
        # Codebuild image.
        codebuild = boto3.client('codebuild')

        # Upload files to S3 using custom s3 class to a user folder.
        s3 = S3()
        source_folder = os.path.join(DOCKERFILES_FOLDER, image_name)
        # Copies Dockerfile from btap_cli repository
        url = DOCKERFILE_URL
        r = requests.get(url, allow_redirects=True)
        with open(os.path.join(source_folder, 'Dockerfile'), 'wb') as file:
            file.write(r.content)

        s3.copy_folder_to_s3(self.bucket, source_folder, self.credentials.user_name + '/' + image_name)
        s3_location = 's3://' + self.bucket + '/' + self.credentials.user_name + '/' + image_name
        message = f"Copied build configuration files:\n\t from {source_folder}\n to \n\t {s3_location}"
        logging.info(message)
        print(message)

        # create project if it does not exist. This set the environment variables for the build. Note: if you change an
        # ENV to the build process.. you must DELETE the build project first!!!
        # create build project
        environment_vars = [
                               {
                                   "name": "AWS_DEFAULT_REGION",
                                   "value": self.credentials.region_name
                               },
                               {
                                   "name": "AWS_ACCOUNT_ID",
                                   "value": self.credentials.account_id
                               }
                           ] + [{"name": k, "value": v} for k, v in image_build_args.items()]

        codebuild_project_name = f"{image_name}-{self.credentials.user_name}".replace('.','-')
        # Delete codebuild project if it already exists.
        if codebuild_project_name in codebuild.list_projects()['projects']:
            response = codebuild.delete_project(name=codebuild_project_name)

        # Create IAM role permission dynamically.
        cloud_build_role = IAMCloudBuildRole()
        cloud_build_role.create_role()

        codebuild.create_project(
            name=codebuild_project_name,
            description='string',
            source={
                'type': 'S3',
                'location': self.bucket + '/' + self.credentials.user_name + '/' + image_name + '/'
            },
            artifacts={
                'type': 'NO_ARTIFACTS',
            },
            environment={
                'type': 'LINUX_CONTAINER',
                'image': 'aws/codebuild/standard:4.0',
                'computeType': 'BUILD_GENERAL1_2XLARGE',
                'environmentVariables': environment_vars,
                'privilegedMode': True
            },
            serviceRole=cloud_build_role.arn(),
        )

        # Start building image.
        start = time.time()
        message = f'Building Image {image_name} on Amazon CloudBuild, will take ~10m'
        print(message)
        logging.info(message)
        environmentVariablesOverride = environment_vars
        source_location = self.bucket + '/' + self.credentials.user_name + '/' + image_name + '/'
        message = f'Code build image env overrides {environmentVariablesOverride}'
        logging.info(message)

        message = f"Building from sources at {source_location}"
        logging.info(message)
        print(environmentVariablesOverride)
        response = codebuild.start_build(projectName=image_name,
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
                message = f'Image {image_name} Created on Amazon. \nImage built in {time.time() - start}. Deleting artifacts.'
                response = codebuild.delete_project(name=codebuild_project_name)
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
        #Delete cloud build role.
        cloud_build_role.delete()

    def __create_image_repository(self, repository_name=None):
        ecr = boto3.client('ecr')
        repositories = ecr.describe_repositories()['repositories']
        if next((item for item in repositories if item["repositoryName"] == repository_name), None) == None:
            message = f"Creating repository {repository_name}"
            logging.info(message)
            ecr.create_repository(repositoryName=repository_name)
        else:
            message = f"Repository {repository_name} already exists. Using existing."
            logging.info(message)

    def get_image(self, image_name=None, image_tag=None):
        image = None
        ecr = boto3.client('ecr')
        # Check if image exists.. if not it will create an image from the latest git hub reps.
        # Get list of tags for image name on aws.
        available_tags = sum(
            [d.get('imageTags', [None]) for d in
             ecr.describe_images(repositoryName=image_name)['imageDetails']],
            [])
        if image_tag in available_tags:
            image = f'{self.credentials.account_id}.dkr.ecr.{self.credentials.region_name}.amazonaws.com/' + image_name + ':' + image_tag
        else:
            image = None
        return image




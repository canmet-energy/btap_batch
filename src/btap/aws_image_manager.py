from src.btap.aws_credentials import AWSCredentials
from src.btap.constants import MAX_AWS_VCPUS, MAX_SIMULATIONS_PER_ANALYSIS
from src.btap.docker_image_manager import DockerImageManager
from src.btap.aws_s3 import S3
from src.btap.aws_iam_roles import IAMCodeBuildRole
from src.btap.aws_batch import AWSBatch
from src.btap.common_paths import CommonPaths
import time
import logging
from icecream import ic


class AWSImageManager(DockerImageManager):

    def __aws_credentials(self):
        return AWSCredentials()

    def __init__(self,
                 build_env_name=None,
                 image_name=None,
                 compute_environment=None
                 ):
        super().__init__(image_name=image_name)
        self.build_env_name = build_env_name
        self.credentials = self.__aws_credentials()
        self.bucket = self.credentials.account_id
        self.region = self.credentials.region_name
        self.compute_environment = compute_environment
        self.image_tag = 'latest'

    def get_image_uri(self):
        return f"{self.credentials.account_id}.dkr.ecr.{self.credentials.region_name}.amazonaws.com/{self.get_full_image_name()}:{self.image_tag}"

    def get_threads(self):
        if MAX_AWS_VCPUS > MAX_SIMULATIONS_PER_ANALYSIS:
            return MAX_SIMULATIONS_PER_ANALYSIS
        else:
            return MAX_AWS_VCPUS

    def _image_repo_name(self):
        return self.get_full_image_name()

    def _get_image_build_args(self):
        build_args = super()._get_image_build_args()
        build_args['IMAGE_REPO_NAME'] = self._image_repo_name()
        build_args['IMAGE_TAG'] = 'latest'
        return build_args

    def build_image(self, build_args=None):
        self.build_args = build_args
        self._create_image_repository(repository_name=self._image_repo_name())

        message = f"Building image."
        logging.info(message)
        print(message)
        # Codebuild image.
        codebuild = AWSCredentials().codebuild_client

        # Upload files to S3 using custom s3 class to a user folder.
        s3 = S3()

        source_folder = CommonPaths().get_dockerfile_folder_path(image_name=self.image_name)

        s3.copy_folder_to_s3(self.bucket, source_folder, self.get_build_env_name() + '/' + self.image_name)
        s3_location = 's3://' + self.bucket + '/' + self.get_build_env_name() + '/' + self.image_name
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
                           ] + [{"name": k, "value": v} for k, v in self._get_image_build_args().items()]

        codebuild_project_name = self.get_full_image_name().replace('.', '-')
        # Delete codebuild project if it already exists.
        if codebuild_project_name in codebuild.list_projects()['projects']:
            codebuild.delete_project(name=codebuild_project_name)

        codebuild.create_project(
            name=codebuild_project_name,
            description='string',
            source={
                'type': 'S3',
                'location': self.bucket + '/' + self.get_build_env_name() + '/' + self.image_name + '/'
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
            serviceRole=IAMCodeBuildRole().arn(),
        )

        # Start building image.
        start = time.time()
        url = f"https://{self.credentials.region_name}.console.aws.amazon.com/codesuite/codebuild"
        message = f'Building Image {self.get_full_image_name()} on {url}, will take ~10m'
        print(message)
        logging.info(message)
        source_location = self.bucket + '/' + self.get_build_env_name() + '/' + self.image_name + '/'
        message = f'Code build image env overrides {environment_vars}'
        logging.info(message)

        message = f"Building from sources at {source_location}"
        logging.info(message)
        response = codebuild.start_build(projectName=self.get_full_image_name(),
                                         sourceTypeOverride='S3',
                                         sourceLocationOverride=source_location,
                                         environmentVariablesOverride=environment_vars
                                         )
        build_id = response['build']['id']
        # Check state of creating CE.
        while True:
            status = codebuild.batch_get_builds(ids=[build_id])['builds'][0]['buildStatus']
            # If CE is in valid state, inform user and break from loop.
            if status == 'SUCCEEDED':
                message = f'Image {self.image_name} Created on Amazon. \nImage built in {time.time() - start}. Deleting artifacts.'
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


    def delete_image(self):
        self._delete_image_repository(repository_name=self._image_repo_name())





    def _create_image_repository(self, repository_name=None):
        ecr = AWSCredentials().ecr_client
        repositories = ecr.describe_repositories()['repositories']
        if next((item for item in repositories if item["repositoryName"] == repository_name), None) == None:
            message = f"Creating repository {repository_name}"
            logging.info(message)
            ecr.create_repository(repositoryName=repository_name)
        else:
            message = f"Repository {repository_name} already exists. Using existing."
            logging.info(message)

    @staticmethod
    def list_repositories():
        import boto3
        import botocore
        import src.btap.constants
        aws_config = botocore.client.Config(
            region_name='ca-central-1',
            max_pool_connections=MAX_AWS_VCPUS,
            retries={'max_attempts': 60,
                     'mode': 'standard'})
        ecr = boto3.client('ecr', config=aws_config)
        # Initialize the object count
        object_count = 0
        ecr = AWSCredentials().ecr_client

        repositories = []
        describe_repo_paginator = ecr.get_paginator('describe_repositories')
        for response_listrepopaginator in describe_repo_paginator.paginate():
            for repo in response_listrepopaginator['repositories']:
                    repositories.append(repo['repositoryName'])

        return repositories
    @staticmethod
    def get_existing_build_env_names():
        build_env_names = [k for k in AWSImageManager().list_repositories() if 'btap_cli' in k]
        build_env_names = [x.removesuffix('_btap_cli') for x in build_env_names]
        return build_env_names

    def _delete_image_repository(self, repository_name=None):
        ecr = AWSCredentials().ecr_client
        repositories = ecr.describe_repositories()['repositories']
        if not next((item for item in repositories if item["repositoryName"] == repository_name), None) == None:
            message = f"Deleting repository {repository_name}"
            logging.info(message)
            print(message)
            ecr.delete_repository(repositoryName=repository_name, force=True)
        else:
            message = f"Repository {repository_name} does not exists. Not Deleting it."
            logging.info(message)
            print(message)

    def get_image(self, image_name=None, image_tag='latest'):
        image = None
        ecr = AWSCredentials().ecr_client
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

    def get_batch(self):
        return AWSBatch(image_manager=self,
                        compute_environment=self.compute_environment
                        )


from src.btap.aws_credentials import AWSCredentials
from src.btap.constants import MAX_AWS_VCPUS
from src.btap.docker_image_manager import DockerImageManager
from src.btap.aws_s3 import S3
from src.btap.aws_iam_roles import IAMCodeBuildRole
from src.btap.aws_batch import AWSBatch
from src.btap.common_paths import CommonPaths
import time
import logging

class AWSWeatherLibrary:

    def __aws_credentials(self):
        return AWSCredentials()

    def __init__(self):
        self.credentials = self.__aws_credentials()
        self.bucket = self.credentials.account_id
        self.region = self.credentials.region_name

    def load_weather_library(self, cust_weather_dir):
        s3 = S3
        s3.copy_folder_to_s3(bucket_name=self.bucket, source_folder=cust_weather_dir, target_folder=s3.get_username() + '/' + 'btap_weather_library')
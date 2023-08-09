from src.btap.aws_credentials import AWSCredentials
from src.btap.aws_s3 import S3
import os
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
        aws_username = os.environ.get('AWS_USERNAME')
        if aws_username is None:
            print('Please set AWS_USERNAME environment variable to your aws username. See https://github.com/canmet-energy/btap_batch/blob/main/README.md#requirements to ensure all requirements are met before running. ')
            exit(1)
        s3 = S3()
        bucket_name = self.bucket
        target_folder = str(aws_username) + '/' + 'btap_weather_library'
        s3.copy_folder_to_s3(bucket_name=bucket_name, source_folder=cust_weather_dir, target_folder=target_folder)
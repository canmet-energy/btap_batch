import botocore
import boto3
import logging
import re
from src.compute_resources.constants import AWS_MAX_RETRIES,MAX_AWS_VCPUS
from pathlib import Path
import traceback


class AWSCredentials:
    # Initialize with required clients.

    def __init__(self):
        # standard common aws configuration.
        self._aws_config = botocore.client.Config(
            region_name='ca-central-1',
            max_pool_connections=MAX_AWS_VCPUS,
            retries={'max_attempts': AWS_MAX_RETRIES,
                     'mode': 'standard'})
        # all client created in this class.
        self.batch_client = boto3.client('batch', config=self._aws_config)
        self.sts_client = boto3.client('sts', config=self._aws_config)
        self.iam_client = boto3.client('iam', config=self._aws_config)
        self.iam_resource = boto3.resource('iam')
        self.s3_client = boto3.client('s3', config=self._aws_config)
        self.s3_resource = boto3.resource('s3')
        self.ec2_client = boto3.client('ec2', config=self._aws_config)
        self.codebuild_client = boto3.client('codebuild', config=self._aws_config)
        self.ecr_client = boto3.client('ecr', config=self._aws_config)
        try:
            self.account_id = self.sts_client.get_caller_identity()["Account"]
            self.user_id = self.sts_client.get_caller_identity()["UserId"]
        except botocore.exceptions.ClientError as e:
            traceback.print_exc()
            if e.response['Error']['Code'] == 'ExpiredToken':
                logging.error(
                    f"Your Credentials are invalid. PLease update your aws credentials. If running remotely, the max session in two hours. "
                    f"\nYour AWS credentials should be place in the file {str(Path.home())}\\.credentials")
                exit(1)
            else:
                print("Unexpected botocore.exceptions.ClientError error: %s" % e)
                exit(1)
        except botocore.exceptions.SSLError:
            logging.error(
                "SSL validation failed.. This is usually because you are behind a VPN. Please do not use a VPN while using Amazon Web Services..")
            exit(1)

        # get aws username from userid.
        if re.compile(".*:(.*)@.*").search(self.user_id) is None:
            # This situation occurs when running the host machine on AWS itself.
            self.user_name = 'unknown'
        else:
            # Otherwise it will use your aws user_id
            self.user_name = re.compile(".*:(.*)@.*").search(self.user_id)[1]

        # User ARN (Not used currently)
        self.user_arn = self.sts_client.get_caller_identity()["Arn"]
        # AWS Region name.
        self.region_name = boto3.Session().region_name


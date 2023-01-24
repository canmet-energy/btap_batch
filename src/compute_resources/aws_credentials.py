import botocore
import boto3
from botocore.config import Config
import logging
import re
from src.constants import AWS_MAX_RETRIES
from pathlib import Path
import getpass
import traceback
import sys
import traceback

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
            self.user_name = 'unkown'
        else:
            # Otherwise it will use your aws user_id
            self.user_name = re.compile(".*:(.*)@.*").search(self.user_id)[1]

        # User ARN (Not used currently)
        self.user_arn = self.sts.get_caller_identity()["Arn"]
        # AWS Region name.
        self.region_name = boto3.Session().region_name


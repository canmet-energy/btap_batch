import logging
import json
from icecream import ic
from src.btap.aws_credentials import AWSCredentials
from src.btap.common_paths import CommonPaths

class IAMRoles():
    def __init__(self):
        self.credentials = self.get_credentials()
        self.path = '/service-role/'
        self.role_name = ""
        self.max_duration = 43200
        self.assume_role_policy = {}
        self.managed_policies = []
        self.description = ''

    def arn(self):
        iam_res = AWSCredentials().iam_resource
        role = iam_res.Role(self.full_role_name())
        role.load()
        return role.arn

    def full_role_name(self):
        return f"{CommonPaths().get_username().replace('.', '-')}-{self.role_name}"

    def create_role(self):
        # delete if it already exists.
        self.delete()
        iam_client = AWSCredentials().iam_client
        iam_res = AWSCredentials().iam_resource
        iam_client.create_role(
            Path=self.path,
            RoleName=self.full_role_name(),
            AssumeRolePolicyDocument=(json.dumps(self.assume_role_policy)),
            Description=self.description,
            MaxSessionDuration=self.max_duration
        )
        role = iam_res.Role(self.full_role_name())
        role.load()
        for managed_policy in self.managed_policies:
            role.attach_policy(
                PolicyArn=managed_policy.get('PolicyArn')
            )
        logging.info(f'{self.full_role_name()} iam role has been created')

    def delete(self):
        iam = AWSCredentials().iam_client
        try:
            for mp in self.managed_policies:
                iam.detach_role_policy(
                    RoleName=self.full_role_name(),
                    PolicyArn=mp.get('PolicyArn')
                )
            response = iam.delete_role(
                RoleName=self.full_role_name()
            )
        except iam.exceptions.NoSuchEntityException:
            logging.info(f'iam_role {self.full_role_name()} did not exist. So not deleting.')
            print(f'iam_role {self.full_role_name()} did not exist. So not deleting.')
        logging.info(f'iam_role {self.full_role_name()} deleted.')

    def get_credentials(self):
        credentials = AWSCredentials()
        return credentials

class IAMCodeBuildRole(IAMRoles):
    def __init__(self):
        self.credentials = self.get_credentials()
        self.path = '/service-role/'
        self.role_name = "code_build"
        self.max_duration = 43200
        self.description = ''
        self.assume_role_policy = {'Version': '2012-10-17',
                                   'Statement': [
                                       {
                                           'Action': 'sts:AssumeRole',
                                           'Effect': 'Allow',
                                           'Principal': {
                                               'Service': 'codebuild.amazonaws.com'
                                           }
                                       }
                                   ]
                                   }

        self.managed_policies = [{'PolicyArn': 'arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryFullAccess',
                                  'PolicyName': 'AmazonEC2ContainerRegistryFullAccess'},
                                 {'PolicyArn': 'arn:aws:iam::aws:policy/CloudWatchFullAccess',
                                  'PolicyName': 'CloudWatchFullAccess'},
                                 {'PolicyArn': 'arn:aws:iam::aws:policy/AmazonS3FullAccess',
                                  'PolicyName': 'AmazonS3FullAccess'}]

class IAMBatchJobRole(IAMRoles):
    def __init__(self):
        self.credentials = self.get_credentials()
        self.path = '/service-role/'
        self.role_name = "batch_job_role"
        self.max_duration = 43200
        self.description = ''
        self.assume_role_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "",
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "ecs-tasks.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }

        self.managed_policies = [
            {
                'PolicyArn': 'arn:aws:iam::aws:policy/AmazonS3FullAccess',
                'PolicyName': 'AmazonS3FullAccess'},
            {
                'PolicyArn': 'arn:aws:iam::aws:policy/AWSBatchFullAccess',
                'PolicyName': 'AWSBatchFullAccess'},
            {
                'PolicyArn': 'arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess',
                'PolicyName': 'AmazonDynamoDBFullAccess'},


        ]


class IAMBatchServiceRole(IAMRoles):
    def __init__(self):
        self.credentials = self.get_credentials()
        self.path = '/service-role/'
        self.role_name = "batch_service_role"
        self.max_duration = 43200
        self.description = ''
        self.assume_role_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "batch.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }

        self.managed_policies = [{'PolicyArn': 'arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryFullAccess',
                                  'PolicyName': 'AmazonEC2ContainerRegistryFullAccess'},
                                 {'PolicyArn': 'arn:aws:iam::aws:policy/AmazonRDSFullAccess',
                                  'PolicyName': 'AmazonRDSFullAccess'},
                                 {'PolicyArn': 'arn:aws:iam::aws:policy/service-role/AWSBatchServiceRole',
                                  'PolicyName': 'AWSBatchServiceRole'},
                                 {'PolicyArn': 'arn:aws:iam::aws:policy/AmazonS3FullAccess',
                                  'PolicyName': 'AmazonS3FullAccess'}]

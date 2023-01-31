import logging
import json
from icecream import ic
from src.compute_resources.aws_credentials import AWSCredentials
from src.compute_resources.common_paths import CommonPaths


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
        logging.info(f'iam_role {self.full_role_name()} deleted.')

    def get_credentials(self):
        credentials = AWSCredentials()
        return credentials

    def copy_iam_role(self, old_role_name='AWSBatchServiceRole', new_role_name='new_role'):
        iam = AWSCredentials().iam_client
        sourceRole = iam.get_role(RoleName=old_role_name).get('Role')
        list_role_policies = iam.list_role_policies(RoleName=old_role_name)['PolicyNames']
        inline_policies = []

        for list_role_policy in list_role_policies:
            inline_policies.append(iam.get_role_policy(RoleName=old_role_name, PolicyName=list_role_policy))

        managed_policies = iam.list_attached_role_policies(RoleName=old_role_name)['AttachedPolicies']
        ic(sourceRole)
        ic(managed_policies)
        ic(inline_policies)

        exit(1)

        if sourceRole.get('PermissionsBoundary') is None:
            iam.create_role(
                Path=sourceRole.get('Path'),
                RoleName=new_role_name,
                AssumeRolePolicyDocument=(json.dumps(sourceRole['AssumeRolePolicyDocument'])),
                Description=sourceRole.get('Description', ''),
                MaxSessionDuration=sourceRole.get('MaxSessionDuration'),
                Tags=sourceRole.get('Tags', [])
            )
        else:
            iam.create_role(
                Path=sourceRole.get('Path'),
                RoleName=new_role_name,
                AssumeRolePolicyDocument=(json.dumps(sourceRole['AssumeRolePolicyDocument'])),
                Description=sourceRole.get('Description', ''),
                MaxSessionDuration=sourceRole.get('MaxSessionDuration'),
                PermissionsBoundary=sourceRole.get('PermissionsBoundary').get('PermissionsBoundaryArn'),
                Tags=sourceRole.get('Tags', [])
            )

        for inline_policy in inline_policies:
            ic(inline_policy)
            response = iam.put_role_policy(
                RoleName=new_role_name,
                PolicyName=inline_policy.get('PolicyName'),
                PolicyDocument=(json.dumps(inline_policy['PolicyDocument']))
            )

        for managed_policy in managed_policies:
            ic(managed_policy)
            iam.attach_role_policy(
                RoleName=new_role_name,
                PolicyArn=managed_policy.get('PolicyArn')
            )


class IAMCloudBuildRole(IAMRoles):
    def __init__(self):
        self.credentials = self.get_credentials()
        self.path = '/service-role/'
        self.role_name = "cloud_build"
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
                'PolicyName': 'AWSBatchFullAccess'}

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

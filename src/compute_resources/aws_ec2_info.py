import boto3
from src.constants import AWS_MAX_RETRIES

from botocore.config import Config
class AWS_EC2Info():
    def __init__(self):
        self.ec2 = boto3.client('ec2', config=Config(retries={'max_attempts': AWS_MAX_RETRIES, 'mode': 'standard'}))
        # Store the subnets into a list. This was set up by NRCan.
        subnets = self.ec2.describe_subnets()['Subnets']
        self.subnet_id_list = [subnet['SubnetId'] for subnet in subnets]

        # Store the security groups into a list. This was set up by NRCan.
        security_groups = self.ec2.describe_security_groups()["SecurityGroups"]
        self.securityGroupIds = [security_group['GroupId'] for security_group in security_groups]

    def get_security_group_ids(self):
        return self.securityGroupIds

    def get_subnet_id_list(self):
        return self.subnet_id_list
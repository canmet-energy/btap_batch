from src.btap.aws_credentials import AWSCredentials
class AWS_EC2Info():
    def __init__(self):
        self.ec2 = AWSCredentials().ec2_client
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
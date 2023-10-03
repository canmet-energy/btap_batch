from src.btap.aws_credentials import AWSCredentials
class AWS_EC2Info():
    def __init__(self):
        self.ec2 = AWSCredentials().ec2_client
        # Store the subnets into a list. This was set up by NRCan.
        subnets = self.ec2.describe_subnets()['Subnets']
        self.subnet_id_list = [subnet['SubnetId'] for subnet in subnets]

        # Store the security groups into a list. This was set up by NRCan.
        security_groups = self.ec2.describe_security_groups()["SecurityGroups"]

        #self.securityGroupIds = [security_group['GroupId'] for security_group in security_groups]
        self.securityGroupIds = [
            "sg-0b758a14c1c07dccb",
            "sg-03aca9d7141369a80",
            "sg-0aa84223197378680",
            "sg-042c335305537a4a6",
            "sg-071c6df0b561e70d7"
        ]

    def get_security_group_ids(self):
        return self.securityGroupIds

    def get_subnet_id_list(self):
        return self.subnet_id_list

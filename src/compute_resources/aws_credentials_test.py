from src.compute_resources.aws_credentials import AWSCredentials
from icecream import ic
awscred = AWSCredentials()
ic(awscred.user_arn)
ic(awscred.region_name)
ic(awscred.user_name)
ic(awscred.user_id)
ic(awscred.iam)
ic(awscred.account_id)

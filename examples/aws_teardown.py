from src.compute_resources.aws_batch import AWSBatch
from src.compute_resources.aws_compute_environment import AWSComputeEnvironment
from src.compute_resources.aws_image_manager import AWSImageManager
from src.compute_resources.aws_iam_roles import IAMBatchJobRole,IAMBatchServiceRole,IAMCloudBuildRole

ace = AWSComputeEnvironment()
aim_cli = AWSImageManager(image_name='btap_cli')
ab = AWSBatch(image_manager=aim_cli, compute_environment=ace)
ab.tear_down()
ace.tear_down()
IAMBatchJobRole().delete()
IAMCloudBuildRole().delete()
IAMBatchServiceRole().delete()

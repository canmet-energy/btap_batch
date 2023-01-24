from src.compute_resources.test_aws_batch import AWSBatch,AWSImageManager,BTAPEngine
from src.compute_resources.aws_iam_roles import IAMBatchJobRole,IAMBatchServiceRole,IAMCloudBuildRole
aim_cli = AWSImageManager(image_name='btap_cli')
ab = AWSBatch(image_manager=aim_cli,engine=BTAPEngine())
ab.tear_down()
IAMBatchJobRole().delete()
IAMCloudBuildRole.delete()
IAMBatchServiceRole.delete()

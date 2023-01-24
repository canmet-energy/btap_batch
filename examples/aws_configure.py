from src.compute_resources.test_aws_batch import AWSBatch,AWSImageManager,BTAPEngine
from src.compute_resources.aws_iam_roles import IAMBatchJobRole,IAMBatchServiceRole,IAMCloudBuildRole
IAMBatchJobRole().delete()
IAMCloudBuildRole.delete()
IAMBatchServiceRole.delete()

aim_cli = AWSImageManager(image_name='btap_cli')
aim_cli.build_image()
aim_bb = AWSImageManager(image_name='btap_batch')
aim_bb.build_image()
ab = AWSBatch(image_manager=aim_cli,engine=BTAPEngine())
ab.tear_down()

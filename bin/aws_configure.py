from src.compute_resources.aws_batch import AWSBatch
from src.compute_resources.aws_compute_environment import AWSComputeEnvironment
from src.compute_resources.aws_image_manager import AWSImageManager
from src.compute_resources.aws_iam_roles import IAMBatchJobRole, IAMBatchServiceRole, IAMCloudBuildRole
import time
from icecream import ic

build_args_btap_cli = {'OPENSTUDIO_VERSION': '3.2.1',
                       'BTAP_COSTING_BRANCH': 'master',
                       'OS_STANDARDS_BRANCH': 'nrcan'}

build_args_btap_batch = {'BTAP_BATCH_BRANCH': 'remove_anaconda'}

# Tear down
ace = AWSComputeEnvironment()
# aim_cli = AWSImageManager(image_name='btap_cli')
# ab = AWSBatch(image_manager=aim_cli, compute_environment=ace)
# ab.tear_down()
# ace.tear_down()
# IAMBatchJobRole().delete()
# IAMCloudBuildRole().delete()
# IAMBatchServiceRole().delete()
# time.sleep(5)
#
# # Create new
# IAMBatchJobRole().create_role()
# IAMCloudBuildRole().create_role()
# IAMBatchServiceRole().create_role()
# time.sleep(5)  # Give a few seconds for role to apply.
# ace = AWSComputeEnvironment()
# ace.setup()
# aim_cli = AWSImageManager(image_name='btap_cli')
# aim_cli.build_image(build_args=build_args_btap_cli)
# aim_batch = AWSImageManager(image_name='btap_batch')
# aim_batch.build_image(build_args=build_args_btap_batch)
#
# ab_cli = AWSBatch(image_manager=aim_cli,
#                   compute_environment=ace)
# ab_cli.setup()

aim_btap_batch = AWSImageManager(image_name='btap_batch', compute_environment=ace)
aim_btap_batch.build_image(build_args=build_args_btap_batch)
bb_btap_batch = aim_btap_batch.get_batch()
bb_btap_batch.tear_down()
bb_btap_batch.setup()
bb_btap_batch.create_job()






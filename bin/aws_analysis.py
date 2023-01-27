from src.compute_resources.aws_image_manager import AWSImageManager
from src.compute_resources.aws_compute_environment import AWSComputeEnvironment


image_manager = AWSImageManager(image_name='btap_batch', compute_environment=AWSComputeEnvironment())
batch = image_manager.get_batch()












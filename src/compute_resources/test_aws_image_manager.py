from src.compute_resources.aws_image_manager import AWSImageManager
import yaml
from icecream import ic

aim = AWSImageManager(image_name='btap_cli')
ic(aim.get_image_uri())
#aim.build_image()





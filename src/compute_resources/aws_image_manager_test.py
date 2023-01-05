from src.compute_resources.aws_image_manager import AWSImageManager
import yaml
from icecream import ic

aim = AWSImageManager()
build_args = yaml.safe_load("""
IMAGE_REPO_NAME: btap_cli
OPENSTUDIO_VERSION: 3.2.1
BTAP_COSTING_BRANCH: master
OS_STANDARDS_BRANCH: nrcan
""")
dockerfile = r"C:\Users\plopez\btap_batch\src\Dockerfiles\btap_cli"
aim.build_image(dockerfile=dockerfile,build_args=build_args,verbose=True)





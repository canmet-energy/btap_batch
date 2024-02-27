from src.btap.aws_image_manager import AWSImageManager
from src.btap.cli_helper_methods import delete_aws_build_env
build_env_names = AWSImageManager.get_existing_build_env_names()
build_env_names.sort()
for name in build_env_names:
    delete_aws_build_env(build_env_name=name)
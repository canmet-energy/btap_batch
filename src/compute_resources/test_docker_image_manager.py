from src.compute_resources.docker_image_manager import DockerImageManager
from icecream import ic
dim = DockerImageManager(image_name='btap_cli')
ic(dim.get_image_build_cli())
ic(dim.build_image())
ic(dim.get_image())
ic(dim.get_threads())
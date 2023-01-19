from src.compute_resources.docker_image_manager import DockerImageManager
import yaml
from icecream import ic
dim = DockerImageManager(image_name='btap_cli')
#ic(dim.build_image())
ic(dim.get_image())
ic(dim.get_threads())
ic(DockerImageManager(image_name='phylroy').get_image())
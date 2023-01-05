from src.compute_resources.docker_image_manager import DockerImageManager
import yaml
import icecream as ic
dim = DockerImageManager()

build_args = yaml.safe_load("""
IMAGE_REPO_NAME: btap_cli
OPENSTUDIO_VERSION: 3.2.1
BTAP_COSTING_BRANCH: master
OS_STANDARDS_BRANCH: nrcan
""")
dockerfile = r"C:\Users\plopez\btap_batch\src\Dockerfiles\btap_cli"
dim.build_image( dockerfile=dockerfile,
                    build_args=build_args,
                    force_rm=True,
                    verbose=True)
ic(dim.get_image(image_name='btap_cli'))

ic(dim.get_threads())
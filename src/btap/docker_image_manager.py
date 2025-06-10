import docker
from docker.errors import DockerException, BuildError
import os
import logging
from src.btap.docker_batch import DockerBatch
from src.btap.common_paths import CommonPaths
import time
import subprocess
from icecream import ic


class DockerImageManager:

    def get_build_env_name(self):
        return CommonPaths().get_build_env_name()

    def __init__(self,
                 build_env_name = None,
                 image_name=None,
                 compute_environement=None):
        self.build_env_name = build_env_name
        self.cli_run_command = "docker run --rm"
        self.cli_build_command = "docker build"
        self.image_name = image_name
        self.build_args = None

    def check_docker(self):
        # Making sure that used installed docker.
        if subprocess.run(["docker", "-v"], capture_output=True, shell=True).returncode != 0:

            logging.exception("Docker is not installed on this system")

        # Try to access the docker daemon. If we cannot.. ask user to turn it on and then exit.
        try:
            docker.from_env()
        except DockerException as err:
            logging.error(
                f"Could not access Docker Daemon. Either it is not running, or you do not have permissions to run docker. {err}")
            exit(1)

    # Common
    def _get_image_build_args(self):
        build_args = self.build_args
        build_args['GIT_API_TOKEN'] = os.environ['GIT_API_TOKEN']
        build_args['BUILD_ENV_NAME'] = CommonPaths().get_build_env_name()
        return build_args

    def get_image(self):
        self.check_docker()
        try:
            image = docker.from_env().images.get(name=self.get_full_image_name())
        except docker.errors.ImageNotFound as err:
            image = None
        return image

    # Common
    def get_full_image_name(self):
        if self.build_env_name is None:
            return f"{self.get_build_env_name()}_{self.image_name}"
        else:
            return f"{self.get_build_env_name()}_{self.image_name}"


    # Common
    def get_image_build_cli(self):
        temp_string = ''
        for key, value in self._get_image_build_args().items():
            temp_string += f"--build-arg {key}={value} "
        docker_build_command = f"{self.cli_build_command} -t {self.get_full_image_name()} {temp_string} {CommonPaths().get_dockerfile_folder_path(image_name=self.image_name)}"
        return docker_build_command

    # Common
    def build_image(self, build_args=None):
        self.check_docker()
        self.build_args = build_args
        container_client = docker.from_env()
        start = time.time()
        try:
            image, json_log = container_client.images.build(
                # Path to docker file.
                path=CommonPaths().get_dockerfile_folder_path(image_name=self.image_name),
                # Image name
                tag=self.get_full_image_name(),
                # nocache flag to build use cache or build from scratch.
                nocache=True,
                # ENV variables used in Dockerfile.
                buildargs=self._get_image_build_args(),
                # remove temp containers.
                forcerm=True
            )
        except BuildError as e:
            print(f"Something went wrong with image build {self.get_full_image_name()}! The logs are: ")
            for line in e.build_log:
                if 'stream' in line:
                    print(line['stream'].strip())
                    logging.error(line['stream'].strip())
            print(f"The error description is: {e}")
            print(f"Building ENV used were {self._get_image_build_args()}")
            print(f"You can debug the build with the following docker command:")
            print(self.get_image_build_cli())
            print("Cannot continue. Exiting")
            exit(1)

        print(time.time() - start)
        return image

    # Common
    def get_threads(self):
        # Try to access the docker daemon. If we cannot.. ask user to turn it on and then exit.
        self.check_docker()
        try:
            docker.from_env()
        except DockerException as err:
            logging.error(
                f"Could not access Docker Daemon. Either it is not running, or you do not have permissions to run docker. {err}. Could not get number of cpus used in Docker.")
            exit(1)
        # Return number of cpus minus 2 to give a bit of slack.
        return int(docker.from_env().containers.run(image='alpine', command='nproc --all', remove=True)) - 2

    # Common
    # gets docker run command with proper volume mounts as a string.
    def run_command_cli_string(self,
                               volumes=None,
                               ):
        volume_map = ''
        for key, value in volumes.items():
            volume_map = volume_map + f" -v {key}:{value.get('bind')}"
        return f"{self.cli_run_command} {volume_map} {self.get_full_image_name()} "

    # ?
    def run_container(self,
                      volumes=None,
                      engine_command=None,
                      run_options=None):

        self.check_docker()
        run_options['docker_command'] = f"{self.run_command_cli_string(volumes=volumes)} {engine_command}"
        logging.info(f"Running: {run_options['docker_command']}")

        # Set volumes for docker client command.
        result = docker.from_env().containers.run(
            # Local image name to use.
            image=self.get_full_image_name(),

            # Command issued to container.
            command=engine_command,

            # host volume mount points and setting to read and write.
            volumes=volumes,
            # Will detach from current thread.. don't do it if you don't understand this.
            detach=False,
            # This deletes the container on exit otherwise the container
            # will bloat your system.
            auto_remove=True
        )
        return result

    def get_batch(self):
        return DockerBatch(image_manager=self)

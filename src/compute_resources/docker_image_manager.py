import docker
from docker.errors import DockerException
import os
import logging
import yaml
from pathlib import Path
from src.compute_resources.aws_credentials import LocalCredentials
from src.compute_resources.docker_batch import DockerBatch
DOCKERFILES_FOLDER = os.path.join(Path(os.path.dirname(os.path.realpath(__file__))).parent.absolute(), 'Dockerfiles')



class DockerImageManager:
    def __local_credentials(self):
        return LocalCredentials()

    def get_username(self):
        return self.__local_credentials().get_username().replace('.', '_')

    def __init__(self, image_name=None):
        self.check_docker()
        self.cli_run_command = "docker run --rm"
        self.cli_build_command = "docker build -t"
        self.image_name = image_name
        self.image_configuration = None
        if not os.path.isfile(self._get_image_config_file_path()):
            logging.error(f"could not find image_config input file for {self.image_name} image name at {self._get_image_config_file_path()}. Exiting")
            exit(1)

        # Open the yaml in analysis dict.
        with open(self._get_image_config_file_path(), 'r') as stream:
            config = yaml.safe_load(stream)
        # Store analysis config and building_options.
        self.image_configuration = config.get(':image_configuration')




    def check_docker(self):
        # Making sure that used installed docker.
        if os.system("docker -v") != 0:
            logging.exception("Docker is not installed on this system")

        # Try to access the docker daemon. If we cannot.. ask user to turn it on and then exit.
        try:
            docker.from_env()
        except DockerException as err:
            logging.error(
                f"Could not access Docker Daemon. Either it is not running, or you do not have permissions to run docker. {err}")
            exit(1)


    #Common
    def _get_dockerfile_folder_path(self):
        return os.path.join(DOCKERFILES_FOLDER, self.image_name)

    #Common
    def _get_image_config_file_path(self):
        return os.path.join(self._get_dockerfile_folder_path(), 'image_config.yml')

    #Common
    def _get_image_build_args(self):
        build_args = self.image_configuration.get(':build_args')
        build_args['GIT_API_TOKEN'] = os.environ['GIT_API_TOKEN']
        return build_args


    def get_image(self):
        try:
            image = docker.from_env().images.get(name=self.get_full_image_name())
        except docker.errors.ImageNotFound as err:
            image = None
        return image

    #Common
    def get_full_image_name(self):
        return f"{self.get_username()}_{self.image_name}"

    #Common
    def get_image_build_cli(self):
        temp_string = ''
        for key, value in self._get_image_build_args().items():
            temp_string += f"--build-arg {key}={value} "
        docker_build_command = f"{self.cli_build_command} -t {self.get_full_image_name()} {temp_string} {self._get_dockerfile_folder_path()}"
        return docker_build_command

    #Common
    def build_image(self):
        container_client = docker.from_env()
        image, json_log = container_client.images.build(
            # Path to docker file.
            path=self._get_dockerfile_folder_path(),
            # Image name
            tag=self.get_full_image_name(),
            # nocache flag to build use cache or build from scratch.
            nocache=True,
            # ENV variables used in Dockerfile.
            buildargs=self._get_image_build_args(),
            # remove temp containers.
            forcerm=True
        )
        for chunk in json_log:
            if 'stream' in chunk:
                for line in chunk['stream'].splitlines():
                    logging.debug(line)
        return image

    #Common
    def get_threads(self):
        # Try to access the docker daemon. If we cannot.. ask user to turn it on and then exit.
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

    #?
    def run_container(self,
                      volumes=None,
                      engine_command=None,
                      run_options=None):


        run_options[
            'docker_command'] = f"{self.run_command_cli_string(volumes=volumes)} {engine_command}"
        print(run_options['docker_command'])

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

    def get_batch(self,engine=None):
        return DockerBatch(engine=engine,image_manager=self)




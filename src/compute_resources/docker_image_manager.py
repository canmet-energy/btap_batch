import docker
from docker.errors import DockerException
import os
import logging
import requests
from src.constants import DOCKERFILE_URL

class DockerImageManager:
    def get_image(self,
                  image_name=None,
                  image_tag='latest'):
        try:
            image = docker.from_env().images.get(name=image_name)
        except docker.errors.ImageNotFound as err:
            image = None
        return image

    def build_image(self,
                    dockerfile=None,
                    build_args=None,
                    force_rm=True,
                    verbose=True):
        container_client = docker.from_env()

        image_name = build_args['IMAGE_REPO_NAME']
        build_args['GIT_API_TOKEN'] = os.environ['GIT_API_TOKEN']

        temp_string = ''
        for key, value in build_args.items():
            temp_string += f"--build-arg {key}={value} "
        docker_build_command = f"docker build -t {image_name} {temp_string} {dockerfile}"

        print(dockerfile)

        image, json_log = container_client.images.build(
            # Path to docker file.
            path=dockerfile,
            # Image name
            tag=image_name,
            # nocache flag to build use cache or build from scratch.
            nocache=True,
            # ENV variables used in Dockerfile.
            buildargs=build_args,
            # remove temp containers.
            forcerm=force_rm
        )
        for chunk in json_log:
            if 'stream' in chunk:
                for line in chunk['stream'].splitlines():
                    logging.debug(line)
                    if verbose is True:
                        print(line)
        return image

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

    def get_dockerfile_from_git(self, dockerfile_local_path=None, dockerfile_url=None):
        # Copies Dockerfile from btap_cli repository
        url = DOCKERFILE_URL
        r = None
        try:
            r = requests.get(url, allow_redirects=True)
        except requests.exceptions.SSLError as err:
            logging.error(
                "Could not set up SSL certificate. Are you behind a VPN? This will interfere with SSL certificates.")
            exit(1)
        file = open(os.path.join(dockerfile_local_path, 'Dockerfile'), 'wb')
        file.write(r.content)
        file.close()



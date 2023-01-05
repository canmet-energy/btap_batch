import docker
import logging
# Do not delete this import...This will set up certificates based on the host system.
import pip_system_certs.wrapt_requests
import requests
import time
import json
import errno
from src.constants import *
from docker.errors import DockerException
from icecream import ic
from pathlib import Path


# Class to manage local Docker batch run.


class DockerBatch:

    def __native_get_container_client(self):
        return docker.from_env()

    def __init__(self):
        # get a docker client object to run docker commands.
        self.container_client = self.__native_get_container_client()
        # initialize image to None.. will assign later.
        self.image = None

    def set_engine(self, engine=None):
        self.engine = engine


    def native_build_image(self, dockerfile=None, nocache=None, buildargs=None, force_rm=True, verbose=True):
        container_client = self.__native_get_container_client()

        image_name = buildargs['IMAGE_REPO_NAME']
        buildargs['GIT_API_TOKEN'] = os.environ['GIT_API_TOKEN']

        temp_string = ''
        for key, value in buildargs.items():
            temp_string += f"--build-arg {key}={value} "
        docker_build_command = f"docker build -t {image_name} {temp_string} {dockerfile}"

        print(dockerfile)

        image, json_log = container_client.images.build(
            # Path to docker file.
            path=dockerfile,
            # Image name
            tag=image_name,
            # nocache flag to build use cache or build from scratch.
            nocache=nocache,
            # ENV variables used in Dockerfile.
            buildargs=buildargs,
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

    def native_get_image_by_name(self, image_name=None):
        try:
            image = self.container_client.images.get(name=image_name)
        except docker.errors.ImageNotFound as err:
            image = None
        return image

    def native_run_cli_container(self,
                                 detach=None,
                                 local_input_folder=None,
                                 local_output_folder=None,
                                 container_input_folder=None,
                                 container_output_folder=None,
                                 container_command=None,
                                 run_options=None,
                                 image_name=None):

        # Save command string so user can run this command later if they choose to.
        run_options[
            'docker_command'] = f"docker run --rm -v {local_output_folder}:{container_output_folder} -v {local_input_folder}:{container_input_folder} {image_name} {container_command}"

        # Set volumes for docker client command.
        volumes = {
            local_output_folder: {
                'bind': container_output_folder,
                'mode': 'rw'},
            local_input_folder: {
                'bind': container_input_folder,
                'mode': 'rw'},
        }


        result = self.container_client.containers.run(
            # Local image name to use.
            image=image_name,

            # Command issued to container.
            command=container_command,

            # host volume mount points and setting to read and write.
            volumes=volumes,
            # Will detach from current thread.. don't do it if you don't understand this.
            detach=detach,
            # This deletes the container on exit otherwise the container
            # will bloat your system.
            auto_remove=True
        )
        return result


    def get_threads(self):
        # Try to access the docker daemon. If we cannot.. ask user to turn it on and then exit.
        try:
            self.__native_get_container_client()
        except DockerException as err:
            logging.error(
                f"Could not access Docker Daemon. Either it is not running, or you do not have permissions to run docker. {err}. Could not get number of cpus used in Docker.")
            exit(1)
        # Return number of cpus minus 2 to give a bit of slack.
        return int(docker.from_env().containers.run(image='alpine', command='nproc --all', remove=True)) - 2

    def get_dockerfile_from_git(self, dockerfile_path=None):
        # Copies Dockerfile from btap_cli repository
        url = DOCKERFILE_URL
        r = None
        try:
            r = requests.get(url, allow_redirects=True)
        except requests.exceptions.SSLError as err:
            logging.error(
                "Could not set up SSL certificate. Are you behind a VPN? This will interfere with SSL certificates.")
            exit(1)
        file = open(os.path.join(dockerfile_path, 'Dockerfile'), 'wb')
        file.write(r.content)
        file.close()

    def setup(self):
        self.build_image()

    def build_image(self):
        image_build_args = self.engine.datapoint_image_configuration[':image_build_args']
        image_build_args['GIT_API_TOKEN'] = os.environ['GIT_API_TOKEN']
        image_name = image_build_args['IMAGE_REPO_NAME']
        # Set timer to track how long it took to build.
        start = time.time()
        # add info to logger.
        message = f"Building image:{image_name}"
        logging.info(message)
        print(message)
        message = f"With arguments:{image_build_args}"
        logging.info(message)
        print(message)

        # determines folder of docker folder relative to this file.
        self.dockerfile = os.path.join(DOCKERFILES_FOLDER, image_name)
        self.get_dockerfile_from_git(dockerfile_path=self.dockerfile)
        message = f"Dockerfolder being use to build image:{self.dockerfile}"
        logging.info(message)
        print(message)

        # Will build image if does not already exist or if nocache is set true.

        # Get image if it exists.
        self.image = self.native_get_image_by_name(image_name=image_name)


        if self.image == None or self.engine.analysis_config[':nocache'] == True:
            message = f'Building Image:{image_name} will take ~10m... '
            logging.info(message)
            print(message)
            self.image = self.native_build_image(dockerfile=self.dockerfile,
                                                 nocache=True,
                                                 buildargs=image_build_args,
                                                 force_rm=True)

            # let use know that the image built successfully.
            message = f'Image built in {(time.time() - start) / 60}m'
            logging.info(message)
            print(message)
        else:
            message = "Using existing image."
            logging.info(message)
            print(message)

        # return image.. also is a part of the object.
        return self.image


    # This method will run the simulation with the general command. It passes all the information via the
    # run_options.yml file. This file was created ahead of this in the local_input_folder which is mounted to the
    # container. The output similarly will be placed in the local_output_folder using the datapoint_id as the new
    # folder name.

    def submit_job(self,
                   local_btap_data_path=None,
                   local_datapoint_input_folder=None,
                   local_datapoint_output_folder=None,
                   run_options=None):
        local_parent_output_folder = Path(local_datapoint_output_folder).parent.absolute()
        job_config = self.engine.datapoint_image_configuration.get(':job_configuration')
        container_input_path = job_config.get(':container_input_path')
        container_output_path = job_config.get(':container_output_path')
        container_command = job_config.get(':container_command')
        image_name = self.engine.datapoint_image_configuration.get(':image_build_args').get('IMAGE_REPO_NAME')


        local_error_txt_path = os.path.join(local_parent_output_folder, run_options[':datapoint_id'], 'error.txt')
        btap_data = {}
        # add run options to dict.
        btap_data.update(run_options)
        # Start timer to track simulation time.
        start = time.time()
        try:

            result = self.job(
                run_options=run_options,
                local_input_folder=local_datapoint_input_folder,
                local_output_folder=local_parent_output_folder,
                detach=False,
                container_input_path=container_input_path,
                container_output_path = container_output_path,
                container_command = container_command,
                image_name = image_name
            )
            # If file was not created...raise an error.
            if not os.path.isfile(local_btap_data_path):
                raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), local_btap_data_path)
            self.btap_post_process_data_result_success(btap_data, local_btap_data_path, local_datapoint_output_folder, run_options)
            # Flag that is was successful.
            btap_data['success'] = True
            btap_data['simulation_time'] = time.time() - start
            return btap_data
        except Exception as error:
            self.btap_post_process_data_result_failure(btap_data, local_error_txt_path)

            btap_data.update(run_options)
            btap_data['success'] = False
            btap_data['run_options'] = yaml.dump(run_options)
            btap_data['datapoint_output_url'] = 'file:///' + os.path.join(local_datapoint_output_folder)
            return btap_data

    def btap_post_process_data_result_failure(self, btap_data, local_error_txt_path):
        if os.path.exists(local_error_txt_path):
            with open(local_error_txt_path, 'r') as file:
                btap_data['container_error'] = str(file.read())

    def btap_post_process_data_result_success(self, btap_data, local_btap_data_path, local_datapoint_output_folder, run_options):
        # Open the btap Data file in analysis dict.
        file = open(local_btap_data_path, 'r')
        btap_data.update(json.load(file))
        file.close()
        # save output url.
        btap_data['datapoint_output_url'] = 'file:///' + os.path.join(local_datapoint_output_folder)
        # Store sum of warnings errors and severes.
        btap_data['eplus_warnings'] = sum(
            1 for d in btap_data['eplusout_err_table'] if d.get('error_type') == 'warning')
        btap_data['eplus_severes'] = sum(
            1 for d in btap_data['eplusout_err_table'] if d.get('error_type') == 'severe')
        btap_data['eplus_fatals'] = sum(
            1 for d in btap_data['eplusout_err_table'] if d.get('error_type') == 'fatal')
        # dump full run_options.yml file into database for convienience.
        btap_data['run_options'] = yaml.dump(run_options)
        # Need to zero this in costing btap_data.rb file otherwise may be NA.
        for item in ['energy_eui_heat recovery_gj_per_m_sq', 'energy_eui_heat rejection_gj_per_m_sq']:
            if not btap_data.get(item):
                btap_data[item] = 0.0

    def job(self,

            # run_options dict is used for finding the folder after the simulation is completed to store in the database.
            run_options=None,

            # mount point to container of input file(s)
            local_input_folder=None,

            # mount point for container to copy simulation files.
            local_output_folder=None,

            # Don't detach.. hold on to current thread.
            detach=False,

            container_input_path=None,
            container_output_path = None,
            container_command = None,
            image_name = None
            ):




        # Run the simulation
        jobName = f"{run_options[':analysis_id']}-{run_options[':datapoint_id']}"
        message = f"Submitting job {jobName}"
        logging.info(message)
        result = self.native_run_cli_container(detach=detach,
                                               local_input_folder=local_input_folder,
                                               local_output_folder=local_output_folder,
                                               container_input_folder=container_input_path,
                                               container_output_folder=container_output_path,
                                               container_command=container_command,
                                               run_options=run_options,
                                               image_name=image_name)


        return result


import yaml

dct = yaml.safe_load('''
:datapoint_image_configuration:
  :nocache: false
  :dockerfile_folder: btap_cli
  :image_build_args:
    IMAGE_REPO_NAME: btap_cli
    OPENSTUDIO_VERSION: 3.2.1
    BTAP_COSTING_BRANCH: master
    OS_STANDARDS_BRANCH: nrcan
    GIT_API_TOKEN: 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
''')

# db = DockerBatch()
# db.native_build_image(dockerfile=r'C:\Users\plopez\btap_batch\src\Dockerfiles\btap_private_cli',
#                       buildargs=dct[':datapoint_image_configuration'][':image_build_args'],
#                       nocache=True)


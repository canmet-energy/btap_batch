import docker
import logging
# Do not delete this import...This will set up certificates based on the host system.
import pip_system_certs.wrapt_requests
import requests
import time
import json,yaml
import errno
from .constants import *
from docker.errors import DockerException
from icecream import ic


# Class to manage local Docker batch run.
class DockerBatch:

    def native_get_container_client(self):
        return docker.from_env()

    def native_build_image(self, dockerfile=None, image_name = None, nocache=None, buildargs=None, force_rm=True):

        buildargs_string = ''
        for key, value in buildargs.items():
            buildargs_string += f"--build-arg {key}={value} "
        docker_build_command = f"docker build -t {image_name} {buildargs_string} {dockerfile}"
        print(docker_build_command)

        image, json_log = self.container_client.images.build(
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
        return image

    def native_get_image_by_name(self, image_name=None):
        try:
            image = self.container_client.images.get(name=image_name)
        except docker.errors.ImageNotFound as err:
            image = None
        return image

    def native_run_btap_cli_container(self, detach=None,
                                      local_input_folder=None,
                                      local_output_folder=None,
                                      run_options=None,
                                      volumes=None):
        # Running docker command
        run_options[
            'docker_command'] = f"docker run --rm -v {local_output_folder}:/btap_costing/utilities/btap_cli/output -v {local_input_folder}:/btap_costing/utilities/btap_cli/input {run_options[':image_name']} bundle exec ruby btap_cli.rb"
        result = self.container_client.containers.run(
            # Local image name to use.
            image=run_options[':image_name'],

            # Command issued to container.
            command='bundle exec ruby btap_cli.rb',

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
            self.native_get_container_client()
        except DockerException as err:
            logging.error(
                f"Could not access Docker Daemon. Either it is not running, or you do not have permissions to run docker. {err}. Could not get number of cpus used in Docker.")
            exit(1)
        # Return number of cpus minus 2 to give a bit of slack.
        return int(docker.from_env().containers.run(image='alpine', command='nproc --all', remove=True)) - 2



    def __init__(self,
                 engine=None):
        self.engine = engine

        # Get the folder of this python file.
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        # determines folder of docker folder relative to this file.
        self.dockerfile = os.path.join(DOCKERFILES_FOLDER, self.engine.analysis_config[':image_name'])
        self.get_dockerfile_from_git(dockerfile_path=self.dockerfile)
        # get a docker client object to run docker commands.
        self.container_client = self.native_get_container_client()
        # initialize image to None.. will assign later.
        self.image = None

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
        # Set timer to track how long it took to build.
        start = time.time()
        # add info to logger.
        message = f"Building image:{self.engine.analysis_config[':image_name']}"
        logging.info(message)
        print(message)
        message = f"OS Version:{self.engine.analysis_config[':os_version']}"
        logging.info(message)
        print(message)
        message = f"BTAP_COSTING Branch:{self.engine.analysis_config[':btap_costing_branch']}"
        logging.info(message)
        print(message)
        message = f"OS_STANDARDS Branch:{self.engine.analysis_config[':os_standards_branch']}"
        logging.info(message)
        print(message)
        message = f"Dockerfolder being use to build image:{self.dockerfile}"
        logging.info(message)
        print(message)

        buildargs = {
            # Git token to access private repositories.
            'GIT_API_TOKEN': self.engine.git_api_token,
            # Openstudio version.... like '3.0.1'
            'OPENSTUDIO_VERSION': self.engine.analysis_config[':os_version'],
            # BTAP costing branch. Usually 'master'
            'BTAP_COSTING_BRANCH': self.engine.analysis_config[':btap_costing_branch'],
            # Openstudio standards branch Usually 'nrcan'
            'OS_STANDARDS_BRANCH': self.engine.analysis_config[':os_standards_branch']
        }

        # Will build image if does not already exist or if nocache is set true.

        # Get image if it exists.
        self.image = self.native_get_image_by_name(image_name=self.engine.analysis_config[':image_name'])


        if self.image == None or self.engine.analysis_config[':nocache'] == True:
            message = f'Building Image:{self.engine.analysis_config[":image_name"]} will take ~10m... '
            logging.info(message)
            print(message)
            self.image = self.native_build_image(dockerfile=self.dockerfile,
                                                 image_name=self.engine.analysis_config[':image_name'],
                                                 nocache=self.engine.analysis_config[':nocache'],
                                                 buildargs=self.engine.docker_build_args,
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
                   output_folder,
                   local_btap_data_path,
                   local_datapoint_input_folder,
                   local_datapoint_output_folder,
                   run_options):
        local_error_txt_path = os.path.join(output_folder, run_options[':datapoint_id'], 'error.txt')
        btap_data = {}
        # add run options to dict.
        btap_data.update(run_options)
        # Start timer to track simulation time.
        start = time.time()
        try:

            result = self.job(
                run_options=run_options,
                local_input_folder=local_datapoint_input_folder,
                local_output_folder=output_folder,
                detach=False
            )
            # If file was not created...raise an error.
            if not os.path.isfile(local_btap_data_path):
                raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), local_btap_data_path)
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
            # Flag that is was successful.
            btap_data['success'] = True
            btap_data['simulation_time'] = time.time() - start
            return btap_data
        except Exception as error:
            error_msg = ''
            if os.path.exists(local_error_txt_path):
                with open(local_error_txt_path, 'r') as file:
                    error_msg = file.read()
            btap_data = {}
            btap_data.update(run_options)
            btap_data['success'] = False
            btap_data['container_error'] = str(error_msg)
            btap_data['run_options'] = yaml.dump(run_options)
            btap_data['datapoint_output_url'] = 'file:///' + os.path.join(local_datapoint_output_folder)
            return btap_data

    def job(self,

            # run_options dict is used for finding the folder after the simulation is completed to store in the database.
            run_options=None,

            # mount point to container of input file(s)
            local_input_folder=None,

            # mount point for container to copy simulation files.
            local_output_folder=None,

            # Don't detach.. hold on to current thread.
            detach=False):

        # If local i/o folder is not set.. try to use folder where this file is.
        if local_input_folder == None:
            local_input_folder = os.path.join(self.dir_path, 'input')
        if local_output_folder == None:
            local_output_folder = os.path.join(self.dir_path, 'output')

        # Run the simulation
        jobName = f"{run_options[':analysis_id']}-{run_options[':datapoint_id']}"
        message = f"Submitting job {jobName}"
        logging.info(message)
        volumes = {
            local_output_folder: {
                'bind': '/btap_costing/utilities/btap_cli/output',
                'mode': 'rw'},
            local_input_folder: {
                'bind': '/btap_costing/utilities/btap_cli/input',
                'mode': 'rw'},
        }
        result = self.native_run_btap_cli_container(detach, local_input_folder, local_output_folder, run_options,
                                                    volumes)

        return result

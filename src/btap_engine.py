import os
import logging
import yaml
class BTAPEngine:
    # Helper method to load input.yml file into data structures required by btap_batch

    def container_command(self,input_path=None, output_path=None):
        return f"bundle exec ruby btap_cli.rb --input_path {input_path} --output_path {output_path} "




    def __init__(self, analysis_config_file=None):
        # Load Analysis File into variable
        if not os.path.isfile(analysis_config_file):
            logging.error(f"could not find analysis input file at {analysis_config_file}. Exiting")
        # Open the yaml in analysis dict.
        with open(analysis_config_file, 'r') as stream:
            analysis = yaml.safe_load(stream)
        # Store analysis config and building_options.
        self.compute_environment = analysis.get(':compute_environment')
        self.datapoint_image_configuration = analysis.get(':datapoint_image_configuration')
        self.analysis_config = analysis.get(':analysis_configuration')
        self.building_options = analysis.get(':building_options')
        self.git_api_token = os.environ['GIT_API_TOKEN']
        self.project_root = os.path.dirname(analysis_config_file)

        #BTAP Specific
        self.baseline_results = None
        return

    def load_configuration_file(self,analysis_config_file=None):
        self.load_container_image_build_args()


    def load_model_options(self,analysis_config_file=None):
        # Load Analysis File into variable
        if not os.path.isfile(analysis_config_file):
            logging.error(f"could not find analysis input file at {analysis_config_file}. Exiting")
        # Open the yaml in analysis dict.
        with open(analysis_config_file, 'r') as stream:
            analysis = yaml.safe_load(stream)
        self.building_options = analysis.get(':building_options')
        return self.building_options

    def load_analysis_config(self,analysis_config_file=None):
        # Load Analysis File into variable
        if not os.path.isfile(analysis_config_file):
            logging.error(f"could not find analysis input file at {analysis_config_file}. Exiting")
        # Open the yaml in analysis dict.
        with open(analysis_config_file, 'r') as stream:
            analysis = yaml.safe_load(stream)
        self.building_options = analysis.get(':building_options')
        return self.building_options

    def docker_build_args(self):
        buildargs_string = ''
        dockerfile = ''
        image_name = self.datapoint_image_configuration[':image_build_args']['IMAGE_REPO_NAME']
        image_build_args = self.datapoint_image_configuration[':image_build_args']
        image_build_args['GIT_API_TOKEN'] = os.environ['GIT_API_TOKEN']

        for key, value in image_build_args.items():
            buildargs_string += f"--build-arg {key}={value} "
        docker_build_command = f"docker build -t {image_name} {buildargs_string} {dockerfile}"
        print(docker_build_command)


# bte = BTAPEngine(r"C:\Users\plopez\btap_batch\examples\custom_osm\input.yml")
# print(bte.docker_build_args())

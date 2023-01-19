import os
import logging
import yaml
import json
import errno
import pathlib
import boto3
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

    def post_process_data_result_failure(self,
                                         job_data,
                                         local_error_txt_path):
        if os.path.exists(local_error_txt_path):
            with open(local_error_txt_path, 'r') as file:
                job_data['container_error'] = str(file.read())


    def aws_post_process_data_result_failure(self,
                                         job_data=None,
                                         bucket_name=None,
                                         s3_datapoint_output_folder=None,
                                         local_datapoint_output_folder=None):
        s3_error_txt_path = os.path.join(s3_datapoint_output_folder, 'error.txt').replace('\\', '/')
        content_object = boto3.resource('s3').Object(bucket_name, s3_error_txt_path)
        error_msg = content_object.get()['Body'].read().decode('utf-8')
        job_data['container_error'] = str(error_msg)
        print(error_msg)
        # save btap_data json file to output folder if aws_run.
        local_btap_data_path = os.path.join(local_datapoint_output_folder, "btap_data.json")
        pathlib.Path(os.path.dirname(local_btap_data_path)).mkdir(parents=True, exist_ok=True)
        with open(local_btap_data_path, 'w') as outfile:
            json.dump(job_data, outfile, indent=4)

    def post_process_data_result_success(self, job_data, local_datapoint_output_folder, run_options):
        local_btap_data_path = os.path.join(local_datapoint_output_folder, "btap_data.json")
        # If file was not created...raise an error.
        if not os.path.isfile(local_btap_data_path):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), local_btap_data_path)
        # Open the btap Data file in analysis dict.
        file = open(local_btap_data_path, 'r')
        job_data.update(json.load(file))
        file.close()
        # save output url.
        job_data['datapoint_output_url'] = 'file:///' + os.path.join(local_datapoint_output_folder)
        self.common_code(job_data=job_data)


    def aws_post_process_data_result_success(self,
                                         job_data=None,
                                         run_options=None,
                                         s3_datapoint_output_folder=None):
        # BTAP data gathering
        s3_btap_data_path = os.path.join(s3_datapoint_output_folder, 'btap_data.json').replace('\\', '/')
        logging.info(
            f"Getting data from S3 bucket {run_options[':s3_bucket']} at path {s3_btap_data_path}")
        content_object = boto3.resource('s3').Object(run_options[':s3_bucket'], s3_btap_data_path)
        # Adding simulation high level results from btap_data.json to df.
        job_data.update(json.loads(content_object.get()['Body'].read().decode('utf-8')))
        self.common_code(job_data)

    def common_code(self, job_data):
        job_data['eplus_warnings'] = sum(
            1 for d in job_data['eplusout_err_table'] if d.get('error_type') == 'warning')
        job_data['eplus_severes'] = sum(
            1 for d in job_data['eplusout_err_table'] if d.get('error_type') == 'severe')
        job_data['eplus_fatals'] = sum(
            1 for d in job_data['eplusout_err_table'] if d.get('error_type') == 'fatal')
        # Need to zero this in costing btap_data.rb file otherwise may be NA.
        for item in ['energy_eui_heat recovery_gj_per_m_sq', 'energy_eui_heat rejection_gj_per_m_sq']:
            if not job_data.get(item):
                job_data[item] = 0.0

# bte = BTAPEngine(r"C:\Users\plopez\btap_batch\examples\custom_osm\input.yml")
# print(bte.docker_build_args())

import os
import logging
import json
import errno
import pathlib
import boto3



# Location of Docker folder that contains information to build the btap image locally and on aws.
class BTAPCLI:

    def __init__(self):
        self._engine_command = 'bundle exec ruby btap_cli.rb'
        self._container_input_path = '/openstudio-standards/utilities/btap_cli/input'
        self._container_output_path = '/openstudio-standards/utilities/btap_cli/output'

    def docker_container_command(self, engine_args=[]):
        arg_string = ''
        for arg in engine_args:
            arg_string = arg_string + f" {arg}"
        return self._engine_command + arg_string

    @staticmethod
    def aws_container_command(input_path=None, output_path=None):
        return f"bundle exec ruby btap_cli.rb --input_path {input_path} --output_path {output_path} "


    def container_input_path(self):
        return self._container_input_path

    def container_output_path(self):
        return self._container_output_path

    @staticmethod
    def get_file_from_output_folder_as_string(local_datapoint_output_folder=None,
                                              bucket_name=None,
                                              s3_datapoint_output_folder=None,
                                              relative_file_path=None):
        if bucket_name is None:  # Docker
            file_path = os.path.join(local_datapoint_output_folder, relative_file_path)
            if os.path.exists(file_path):
                with open(file_path, 'r') as file:
                    return str(file.read())
        else:  # AWS
            file_path = os.path.join(s3_datapoint_output_folder, relative_file_path).replace('\\', '/')
            content_object = boto3.resource('s3').Object(bucket_name, file_path)
            return str(content_object.get()['Body'].read().decode('utf-8'))

    def post_process_data_result_failure(self,
                                         job_data=None,
                                         local_datapoint_output_folder=None):
        # Get error message from error file and store it in the job_data list.
        job_data['container_error'] = self.get_file_from_output_folder_as_string(
            local_datapoint_output_folder=local_datapoint_output_folder,
            relative_file_path='error.txt')
        return job_data

    @staticmethod
    def aws_post_process_data_result_failure(
                                             job_data=None,
                                             run_options=None,
                                             s3_datapoint_output_folder=None,
                                             local_datapoint_output_folder=None):
        s3_error_txt_path = os.path.join(s3_datapoint_output_folder, 'error.txt').replace('\\', '/')
        content_object = boto3.resource('s3').Object(run_options[':s3_bucket'], s3_error_txt_path)
        error_msg = content_object.get()['Body'].read().decode('utf-8')
        job_data['container_error'] = str(error_msg)
        print(error_msg)
        # save btap_data json file to output folder if aws_run.
        local_btap_data_path = os.path.join(local_datapoint_output_folder, "btap_data.json")
        pathlib.Path(os.path.dirname(local_btap_data_path)).mkdir(parents=True, exist_ok=True)
        with open(local_btap_data_path, 'w') as outfile:
            json.dump(job_data, outfile, indent=4)
        return job_data

    @staticmethod
    def aws_post_process_data_result_success(job_data=None,
                                             run_options=None,
                                             s3_datapoint_output_folder=None):
        # BTAP data gathering
        s3_btap_data_path = os.path.join(s3_datapoint_output_folder, 'btap_data.json').replace('\\', '/')
        logging.info(
            f"Getting data from S3 bucket {run_options[':s3_bucket']} at path {s3_btap_data_path}")
        content_object = boto3.resource('s3').Object(run_options[':s3_bucket'], s3_btap_data_path)
        # Adding simulation high level results from btap_data.json to df.
        job_data.update(json.loads(content_object.get()['Body'].read().decode('utf-8')))
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
        return job_data


    def post_process_data_result_success(self,
                                         job_data=None,
                                         local_datapoint_output_folder=None
                                         ):
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
        return job_data




    @staticmethod
    def common_code(job_data):
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
        return job_data


class BTAPBATCH(BTAPCLI):
    def __init__(self):
        self._engine_command = 'bundle exec ruby btap_cli.rb'
        self._container_input_path = '/openstudio-standards/utilities/btap_cli/input'
        self._container_output_path = '/openstudio-standards/utilities/btap_cli/output'




# bte = BTAPEngine(r"C:\Users\plopez\btap_batch\examples\custom_osm\input.yml")
# print(bte.docker_build_args())

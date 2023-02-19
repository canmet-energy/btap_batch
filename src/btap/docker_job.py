import os
import json
import yaml
import time
from pathlib import Path
import errno
from src.btap.common_paths import CommonPaths
from icecream import ic

class DockerBTAPJob:
    def __init__(self, batch=None, job_id=None,):
        self.batch = batch
        self.job_id = job_id
        self.engine_command = 'bundle exec ruby btap_cli.rb'
        self._set_paths()
    #public
    def submit_job(self, run_options=None):
        # Timer start.
        start = time.time()

        self.run_options = self._update_run_options(run_options)

        # Variable to store all input and output information about job.
        job_data = {}
        job_data.update(self.run_options)
        # Save pristine run_options.
        job_data['run_options'] = yaml.dump(self.run_options)
        job_data['datapoint_output_url'] = self._job_url()
        self._copy_files_to_run_location()
        try:
            self._run_container()
            # Update job_data with possible modifications to run_options.
            job_data.update(self.run_options)
            # Flag that is was successful.
            job_data['status'] = "SUCCEEDED"
            job_data['simulation_time'] = time.time() - start
            job_data.update(self._get_job_results())
            return job_data
        except Exception as error:
            print(error)
            # Update job_data with possible modifications to run_options.
            job_data.update(self.run_options)
            # Flag that is was failure and save container error.
            job_data['container_error'] = self._get_container_error()
            job_data['status'] = 'FAILED'
            self._save_output_file(job_data)
            return job_data
    #protected
    def _job_url(self):
        return self.cp.local_job_url(job_id=self.job_id)
    def _set_paths(self):
        # Common object for paths.
        self.cp = CommonPaths()
        self.analysis_output_folder = self.cp.algorithm_run_folder()
        self.analysis_output_job_id_folder = self.cp.analysis_output_job_id_folder(job_id=self.job_id)
        self.analysis_input_job_id_folder = self.cp.analysis_input_job_id_folder(job_id=self.job_id)
        self.local_json_file_path = self.cp.analysis_output_job_id_btap_json_path(job_id=self.job_id)

    def _command_args(self):
        args = []
        return args
    def _container_command(self):
        arg_string = ''
        for arg in self._command_args():
            arg_string = arg_string + f" {arg}"
        return self.engine_command + arg_string
    def _update_run_options(self, run_options=None):
        run_options[':job_id'] = self.job_id
        return run_options
    def _copy_files_to_run_location(self):
        # No files to copy for local run.
        return True
    def _get_job_results(self):
        # If file was not created...raise an error.
        if not os.path.isfile(self.local_json_file_path):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), self.local_json_file_path)
        # Open the btap Data file in analysis dict.
        file = open(self.local_json_file_path, 'r')
        result_data = json.load(file)
        file.close()
        result_data = self._enumerate_eplus_warnings(job_data=result_data)
        return result_data
    def _get_container_error(self):
        # Get error message from error file lcoally and store it in the job_data list.
        file_path = os.path.join(self.analysis_output_job_id_folder, 'error.txt')
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                return str(file.read())
    def _run_container(self):
        # Run the simulation
        result = self.batch.image_manager.run_container(
            volumes=self.__volume_mounts(),
            engine_command=self._container_command(),
            run_options=self.run_options)
        # engine post process successful run.
    def _enumerate_eplus_warnings(self, job_data=None):
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
    def _save_output_file(self, job_data):
        # save btap_data json file.
        Path(os.path.dirname(self.local_json_file_path)).mkdir(parents=True, exist_ok=True)
        with open(self.local_json_file_path, 'w') as outfile:
            json.dump(job_data, outfile, indent=4)
    #private methods
    def __volume_mounts(self):
        volumes = {
            self.analysis_output_folder: {
                'bind': '/btap_costing/utilities/btap_cli/output',
                'mode': 'rw'},
            self.analysis_input_job_id_folder: {
                'bind': '/btap_costing/utilities/btap_cli/input',
                'mode': 'rw'},
        }
        return volumes




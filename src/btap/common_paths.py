import os
from pathlib import Path

PROJECT_ROOT = str(Path(os.path.dirname(os.path.realpath(__file__))).parent.absolute())
DOCKERFILES_FOLDER = os.path.join(Path(os.path.dirname(os.path.realpath(__file__))).parent.absolute(), 'Dockerfiles')
PROJECT_FOLDER = os.path.join(Path(os.path.dirname(os.path.realpath(__file__))).parent.parent.absolute())
EXAMPLE_FOLDER = os.path.join(PROJECT_FOLDER, 'examples')
OUTPUT_FOLDER = os.path.join(PROJECT_FOLDER, "output")
SCHEMA_FOLDER = os.path.join(PROJECT_FOLDER, "schemas")
if os.name == 'nt':
    HOME = os.path.join(os.environ['USERPROFILE'])
    USER = os.environ['USERNAME']
else:
    HOME = os.path.join(os.environ['HOME'])
    USER = os.getenv('USER', 'no_user')

CONFIG_FOLDER = os.path.join(HOME, '.btap', 'config')
HISTORIC_WEATHER_LIST = "https://github.com/canmet-energy/btap_weather/raw/main/historic_weather_filenames.json"
FUTURE_WEATHER_LIST = "https://github.com/canmet-energy/btap_weather/raw/main/future_weather_filenames.json"
HISTORIC_WEATHER_REPO = "https://github.com/canmet-energy/btap_weather/raw/main/historic/"
FUTURE_WEATHER_REPO = "https://github.com/canmet-energy/btap_weather/raw/main/future/"
AWS_BUCKET = '834599497928'


class CommonPaths(object):
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CommonPaths, cls).__new__(cls)
            # Put any initialization here.
        return cls._instance

    def set_analysis_info(self,
                          analysis_name=None,
                          analysis_id=None,
                          local_output_folder=None,
                          project_input_folder=None,
                          algorithm_type=None,
                          aws_bucket='834599497928'):
        self.local_output_folder = local_output_folder
        self._analysis_name = analysis_name
        self._analysis_id = analysis_id
        self.project_input_folder = project_input_folder
        self.algorithm_type = algorithm_type
        # Make output folder if it does not exist
        #Path(local_output_folder).mkdir(parents=True, exist_ok=True)

    def get_project_name(self):
        return self._analysis_name

    def schema_folder(self):
        return

    def get_analysis_id(self):
        return self._analysis_id

    def get_build_env_name(self):
        if os.environ.get('BUILD_ENV_NAME') is None:
            print('Please set BUILD_ENV_NAME environment variable to your aws username.')
            exit(1)
        return os.environ.get('BUILD_ENV_NAME').replace('.', '_')

    # Common
    def get_dockerfile_folder_path(self, image_name=None):
        return os.path.join(DOCKERFILES_FOLDER, image_name)

    # Common
    def get_image_config_file_path(self, image_name=None):
        return os.path.join(self.get_dockerfile_folder_path(image_name=image_name), 'image_config.yml')



    # /input
    def get_project_input_folder(self):
        return self.project_input_folder

# Output

    # /output
    def output_folder(self):
        return self.local_output_folder

    # /output/analysis_name
    def project_output_folder(self):
        return os.path.join(self.output_folder(), self.get_project_name())

    # /output/analysis_name/algorithm_type
    def algorithm_folder(self):
        return os.path.join(self.project_output_folder(), self.algorithm_type)


    # /output/analysis_name/analysis_type/runs
    def algorithm_run_folder(self):
        return os.path.join(self.algorithm_folder(), 'run')



    # /output/analysis_name/algorithm_type/job_id
    def analysis_job_id_folder(self, job_id=None):
        return os.path.join(self.algorithm_folder(),'run', job_id)

    # /output/analysis_name/results
    def analysis_results_folder(self):
        return os.path.join(self.project_output_folder(), 'results')

    #  /output/analysis_name/algorithm_type/results/output.xlsx
    def analysis_excel_results_path(self):
        return os.path.join(self.analysis_results_folder(), 'output.xlsx')

    # /output/analysis_name/algorithm_type/results/failures
    def analysis_failures_folder(self):
        return os.path.join(self.analysis_results_folder(), 'failures')


    # /output/analysis_name/algorithm_type/results/database
    def analysis_database_folder(self):
        return os.path.join(self.analysis_results_folder(), 'database')

    # /output/analysis_name/analysis_type/runs/job_id/btap_data.json
    def analysis_output_job_id_btap_json_path(self, job_id=None):
        return os.path.join(self.analysis_job_id_folder(job_id=job_id), "btap_data.json")

    # file:///output/analysis_name/analysis_type/runs/job_id
    def local_job_url(self, job_id=None):
        return 'file:///' + os.path.join(self.analysis_job_id_folder(job_id=job_id))

    # S3 paths

    def s3_url_prefix(self,path):
        bucket = AWS_BUCKET
        return f"s3://{bucket}/{path}"


    # /BUILD_ENV_NAME/analysis_name
    def s3_analysis_name_folder(self,url=False):
        return os.path.join(self.get_build_env_name(), self.get_project_name()).replace('\\', '/')


    # /BUILD_ENV_NAME/analysis_name/algorithm_type
    def s3_algorithm_folder(self):
        return os.path.join(self.s3_analysis_name_folder(), self.algorithm_type).replace('\\', '/')


    # /BUILD_ENV_NAME/analysis_name/algorithm_type
    def s3_output_folder(self):
        return os.path.join(self.s3_algorithm_folder()).replace('\\', '/')

    # /BUILD_ENV_NAME/analysis_name/algorithm_type/results
    def s3_analysis_results_folder(self):
        return os.path.join(self.s3_analysis_name_folder(), 'results').replace('\\', '/')

    # /BUILD_ENV_NAME/analysis_name/analysis_type/job_id
    def s3_datapoint_input_folder(self, job_id=None):
        s3_input_folder = os.path.join(self.s3_algorithm_folder()).replace('\\', '/')
        return os.path.join(s3_input_folder, 'run', job_id).replace('\\', '/')

    # /BUILD_ENV_NAME/analysis_name/algorithm_type/run/job_id
    def s3_datapoint_output_folder(self, job_id=None):
        return os.path.join(self.s3_output_folder(),'run', job_id).replace('\\', '/')

    # /BUILD_ENV_NAME/analysis_name/results/output.xlsx
    def s3_analysis_excel_output_path(self):
        return os.path.join(self.s3_analysis_results_folder(), 'output.xlsx').replace('\\', '/')

    # s3://bucket/BUILD_ENV_NAME/analysis_name
    def s3_btap_batch_container_input_path(self):
        bucket = AWS_BUCKET
        return f"s3://{bucket}/{self.s3_analysis_name_folder()}".replace('\\', '/')


    # s3://bucket//BUILD_ENV_NAME/analysis_name/algorithm_type/job_id
    def s3_btap_cli_container_input_path(self, job_id=None):
        bucket = AWS_BUCKET
        return f"s3://{bucket}/{self.s3_datapoint_input_folder(job_id=job_id)}".replace('\\', '/')

    #s3://bucket//BUILD_ENV_NAME/analysis_name/algorithm_type/run
    def s3_btap_cli_container_output_path(self):
        bucket = AWS_BUCKET
        return f"s3://{bucket}/{self.s3_output_folder()}/run".replace('\\', '/')

    def s3_job_url(self, job_id=None):
        bucket = AWS_BUCKET
        return f"https://s3.console.aws.amazon.com/s3/buckets/{bucket}?region=ca-central-1&prefix={self.s3_datapoint_output_folder(job_id=job_id)}/"




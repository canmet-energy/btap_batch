import os
from pathlib import Path
from src.compute_resources.aws_credentials import AWSCredentials

DOCKERFILES_FOLDER = os.path.join(Path(os.path.dirname(os.path.realpath(__file__))).parent.absolute(), 'Dockerfiles')


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
                          project_input_folder=None):
        self.local_output_folder = local_output_folder
        self._analysis_name = analysis_name
        self._analysis_id = analysis_id
        self.project_input_folder = project_input_folder

    def get_analysis_name(self):
        return self._analysis_name

    def get_analysis_id(self):
        return self._analysis_id

    def get_username(self):
        if os.environ.get('AWS_USERNAME') is None:
            print('Please set AWS_USERNAME environment variable to your aws username.')
            exit(1)
        return os.environ.get('AWS_USERNAME').replace('.', '_')

    # Common
    def get_dockerfile_folder_path(self, image_name=None):
        return os.path.join(DOCKERFILES_FOLDER, image_name)

    # Common
    def get_image_config_file_path(self, image_name=None):
        return os.path.join(self.get_dockerfile_folder_path(image_name=image_name), 'image_config.yml')

    # /output
    def output_folder(self):
        return self.local_output_folder

    # /input
    def project_input_folder(self):
        return self.project_input_folder

    # /output/analysis_name
    def analysis_name_folder(self):
        return os.path.join(self.output_folder(), self.get_analysis_name())

    # /output/analysis_name/analysis_id
    def analysis_id_folder(self):
        return os.path.join(self.analysis_name_folder(), self.get_analysis_id())

    # /output/analysis_name/analysis_id
    def analysis_output_folder(self):
        return os.path.join(self.analysis_id_folder())

    # /output/analysis_name/analysis_id/job_id
    def analysis_output_job_id_folder(self, job_id=None):
        return os.path.join(self.analysis_output_folder(), job_id)

    # /output/analysis_name/analysis_id
    def analysis_input_folder(self):
        return os.path.join(self.analysis_id_folder())

    # /output/analysis_name/analysis_id/job_id
    def analysis_input_job_id_folder(self, job_id=None):
        return os.path.join(self.analysis_input_folder(), job_id)

    # /output/analysis_name/analysis_id/results
    def analysis_results_folder(self):
        return os.path.join(self.analysis_id_folder(), 'results')

    # /output/analysis_name/analysis_id/results/output.xlsx
    def analysis_excel_results_path(self):
        return os.path.join(self.analysis_results_folder(), 'output.xlsx')
    def analysis_excel_output_path(self):
        return os.path.join(self.analysis_results_folder(), 'output.xlsx')


    # /output/analysis_name/analysis_id/results/failures
    def analysis_failures_folder(self):
        return os.path.join(self.analysis_results_folder(), 'failures')


    # /output/analysis_name/analysis_id/results/database
    def analysis_database_folder(self):
        return os.path.join(self.analysis_results_folder(), 'database')

    # /output/analysis_name/analysis_id/job_id/btap_data.json
    def analysis_output_job_id_btap_json_path(self, job_id=None):
        return os.path.join(self.analysis_output_job_id_folder(job_id=job_id), "btap_data.json")

    # file:///output/analysis_name/analysis_id/job_id
    def local_job_url(self, job_id=None):
        return 'file:///' + os.path.join(self.analysis_output_job_id_folder(job_id=job_id))

    # S3 paths

    def s3_url_prefix(self,path):
        bucket = AWSCredentials().account_id
        return f"s3://{bucket}/{path}"


    # /phylroy_lopez/analysis_name
    def s3_analysis_name_folder(self,url=False):
        return os.path.join(self.get_username(), self.get_analysis_name()).replace('\\', '/')


    # /phylroy_lopez/analysis_name/analysis_id
    def s3_analysis_id_folder(self):
        return os.path.join(self.s3_analysis_name_folder(), self.get_analysis_id()).replace('\\', '/')

    # /phylroy_lopez/analysis_name/analysis_id
    def s3_input_folder(self):
        return os.path.join(self.s3_analysis_id_folder()).replace('\\', '/')
    def s3_output_folder(self):
        return os.path.join(self.s3_analysis_id_folder()).replace('\\', '/')

    # /phylroy_lopez/analysis_name/analysis_id/results
    def s3_analysis_results_folder(self):
        return os.path.join(self.s3_analysis_id_folder(), 'results').replace('\\', '/')

    # /phylroy_lopez/analysis_name/analysis_id/job_id
    def s3_datapoint_input_folder(self, job_id=None):
        return os.path.join(self.s3_input_folder(), job_id).replace('\\', '/')
    def s3_datapoint_output_folder(self, job_id=None):
        return os.path.join(self.s3_output_folder(), job_id).replace('\\', '/')

    # /phylroy_lopez/analysis_name/analysis_id/results/output.xlsx
    def s3_analysis_excel_output_path(self):
        return os.path.join(self.s3_analysis_results_folder(), 'output.xlsx').replace('\\', '/')

    # s3://bucket/phylroy_lopez/analysis_name
    def s3_btap_batch_container_input_path(self):
        bucket = AWSCredentials().account_id
        return f"s3://{bucket}/{self.s3_analysis_name_folder()}".replace('\\', '/')


    # s3://bucket/phylroy_lopez/analysis_name/analysis_id/job_id
    def s3_btap_cli_container_input_path(self, job_id=None):
        bucket = AWSCredentials().account_id
        return f"s3://{bucket}/{self.s3_datapoint_input_folder(job_id=job_id)}".replace('\\', '/')

    #s3://bucket//phylroy_lopez/analysis_name/analysis_id (container will add job_id folder)
    def s3_btap_cli_container_output_path(self):
        bucket = AWSCredentials().account_id
        return f"s3://{bucket}/{self.s3_output_folder()}".replace('\\', '/')

    def s3_job_url(self, job_id=None):
        bucket = AWSCredentials().account_id
        return f"https://s3.console.aws.amazon.com/s3/buckets/{bucket}?region=ca-central-1&prefix={self.s3_datapoint_output_folder(job_id=job_id)}/"


# cp = CommonPaths()
# cp.set_analysis_info(analysis_name='analysis_name',
#                      analysis_id='analysis_id',
#                      analyses_folder='analysis_folder',
#                      analysis_project_folder='analysis_project_folder')
# print(cp.s3_job_url(job_id="asdfasdf"))

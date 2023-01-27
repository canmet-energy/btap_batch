# 1 Copy analysis folder to s3
# 2 start btap_batch container on AWS
# 2.1 btap_batch script downloads analysis folder with argument of s3 location
# 2.2 run analysis ensure output is set to analysis folder location. Error trap.

from src.compute_resources.aws_s3 import S3

def submit_analysis(bucket_name, project_folder, target_folder):
    # Copy analysis project folder to S3
    bucketname = 'test'
    project_folder = r'C:\Users\plopez\btap_batch\examples\optimization'
    target_folder = r''
    S3.copy_folder_to_s3(bucket_name=bucketname, source_folder=project_folder, target_folder='')


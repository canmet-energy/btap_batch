
import botocore
import logging
import glob
from src.btap.aws_credentials import AWSCredentials
from cloudpathlib import CloudPath
import pathlib

# Blob Storage operations
class S3:
    # Constructor
    def __init__(self):
        # Create the s3 client.
        self.s3client = AWSCredentials().s3_client


    # Method to delete a bucket. Not used
    def delete_bucket(self, bucket_name):
        message = f'Deleting S3 {bucket_name}'
        print(message)
        logging.info(message)
        self.s3client.delete_bucket(Bucket=bucket_name)

    # Method to check if a bucket exists.
    def check_bucket_exists(self, bucket_name):
        exists = True
        try:
            self.s3client.meta.client.head_bucket(Bucket=bucket_name)
        except botocore.exceptions.ClientError as e:
            # If a client error is thrown, then check that it was a 404 error.
            # If it was a 404 error, then the bucket does not exist.
            error_code = e.response['Error']['Code']
            if error_code == '404':
                exists = False
        return exists

    # Method to create a bucket.
    def create_bucket(self, bucket_name):
        message = f'Creating S3 {bucket_name}'
        print(message)
        logging.info(message)
        self.s3client.create_bucket(
            ACL='private',
            Bucket=bucket_name,
            CreateBucketConfiguration={
                'LocationConstraint': 'ca-central-1'
            },
            ObjectLockEnabledForBucket=False
        )

    # Method to download folder. Single threaded.
    def download_s3_folder(self, s3_folder, local_dir=None):
        if CloudPath(s3_folder).exists():
            try:
                CloudPath(s3_folder).download_to(local_dir)
            except botocore.exceptions.ClientError as e:
                error_code = e.response['Error']['Code']
                print(f"Error occured when trying to download folder {s3_folder} to {local_dir} with {error_code}")
        else:
            print(f"Folder {s3_folder} does not exist. Cannot continue.")
            exit(1)

    # Delete S3 folder.
    def delete_s3_folder(self, bucket, folder):
        bucket = AWSCredentials().s3_resource.Bucket(bucket)
        bucket.objects.filter(Prefix=folder).delete()

    # Copy folder to S3. Single thread.
    def copy_folder_to_s3(self, bucket_name, source_folder, target_folder):
        # Get files in folder.
        files = glob.glob(source_folder + '/**/*', recursive=True)

        # Go through all files recursively.
        for file in files:
            if not pathlib.Path(file).is_dir():
                target_path = file.replace(source_folder, target_folder)
                # s3 likes forward slashes.
                target_path = target_path.replace('\\', '/')
                message = "Uploading %s..." % target_path
                logging.info(message)
                self.s3client.upload_file(file, bucket_name, target_path)

    # Method to upload a file to S3.
    def upload_file(self, file=None, bucket_name=None, target_path=None):
        logging.info(f"uploading {file} to s3 bucket {bucket_name} target {target_path}")
        self.s3client.upload_file(file, bucket_name, target_path)


# def find_files(self, bucket_name=None,  pattern=None):
#     import boto3
#     client = boto3.client('s3')
#     paginator = client.get_paginator('list_objects_v2')
#     page_iterator = paginator.paginate(Bucket=bucket_name)
#     objects = page_iterator.search(f"Contents[?contains(Key, `{pattern}`)][]")
#
#
#     find_files(bucket_name='834599497928',
#                pattern='output.xlsx')
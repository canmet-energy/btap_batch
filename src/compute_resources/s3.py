
import botocore
import boto3
from botocore.config import Config
import logging
from src.constants import AWS_MAX_RETRIES
import os
import glob

# Blob Storage operations
class S3:
    # Constructor
    def __init__(self):
        # Create the s3 client.
        config = Config(retries={'max_attempts': AWS_MAX_RETRIES, 'mode': 'standard'})
        self.s3 = boto3.client('s3', config=config)

    # Method to delete a bucket. Not used
    def delete_bucket(self, bucket_name):
        message = f'Deleting S3 {bucket_name}'
        print(message)
        logging.info(message)
        self.s3.delete_bucket(Bucket=bucket_name)

    # Method to check if a bucket exists.
    def check_bucket_exists(self, bucket_name):
        exists = True
        try:
            self.s3.meta.client.head_bucket(Bucket=bucket_name)
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
        self.s3.create_bucket(
            ACL='private',
            Bucket=bucket_name,
            CreateBucketConfiguration={
                'LocationConstraint': 'ca-central-1'
            },
            ObjectLockEnabledForBucket=False
        )

    # Method to download folder. Single threaded.
    def download_s3_folder(self, bucket_name, s3_folder, local_dir=None):
        """
        Download the contents of a folder directory
        Args:
            bucket_name: the name of the s3 bucket
            s3_folder: the folder path in the s3 bucket
            local_dir: a relative or absolute directory path in the local file system
        """
        bucket = self.s3.Bucket(bucket_name)
        for obj in bucket.objects.filter(Prefix=s3_folder):
            target = obj.key if local_dir is None \
                else os.path.join(local_dir, os.path.basename(obj.key))
            if not os.path.exists(os.path.dirname(target)):
                os.makedirs(os.path.dirname(target))
            bucket.download_file(obj.key, target)

    # Delete S3 folder.
    def delete_s3_folder(self, bucket, folder):
        bucket = self.s3.Bucket(bucket)
        bucket.objects.filter(Prefix=folder).delete()

    # Copy folder to S3. Single thread.
    def copy_folder_to_s3(self, bucket_name, source_folder, target_folder):
        # Get files in folder.
        files = glob.glob(source_folder + '/**/*', recursive=True)
        # Go through all files recursively.
        for file in files:
            target_path = file.replace(source_folder, target_folder)
            # s3 likes forward slashes.
            target_path = target_path.replace('\\', '/')
            message = "Uploading %s..." % target_path
            logging.info(message)

            self.s3.upload_file(file, bucket_name, target_path)

    # Method to upload a file to S3.
    def upload_file(self, file, bucket_name, target_path):
        logging.info(f"uploading {file} to s3 bucket {bucket_name} target {target_path}")
        self.s3.upload_file(file, bucket_name, target_path)


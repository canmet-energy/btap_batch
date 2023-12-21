import botocore
import logging
import glob
from src.btap.aws_credentials import AWSCredentials
from cloudpathlib import CloudPath
import pathlib
from concurrent.futures import FIRST_EXCEPTION, ThreadPoolExecutor, wait
from dataclasses import dataclass, field
from functools import partial
from typing import Callable, Optional, Tuple
from queue import PriorityQueue
import boto3
from tqdm import tqdm


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
        # print(f"Uploading {source_folder} to S3 {target_folder}")
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


    def download_file(self, s3_file=None, bucket_name=None, target_path=None):
        pathlib.Path(target_path).parent.mkdir(parents=True, exist_ok=True)


        try:
            meta_data = self.s3client.head_object(Bucket=bucket_name, Key=s3_file)
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == "404":
                print(f"ERROR: The file {s3_file} was not found on S3. Skipping")
                return False
            else:
                print(f"ERROR: An error occurred tranferring {s3_file}. Skipping file.")
                return False
        else:
            total_length = int(meta_data.get('ContentLength', 0))
            with tqdm(total=total_length, desc=f'source: s3://{bucket_name}/{s3_file} to {target_path}',
                      bar_format="{percentage:.1f}%|{bar:25} | {rate_fmt} | {desc}", unit='B', unit_scale=True,
                      unit_divisor=1024,
                      colour='green') as pbar:
                self.s3client.download_file(bucket_name, s3_file, target_path, Callback=pbar.update)
            return True




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

    def s3_get_list_of_folders_in_folder(self, bucket=None, prefix=None, delimiter='/'):
        from icecream import ic
        folders = []
        import boto3
        client = boto3.client('s3')
        result = client.list_objects(Bucket=bucket, Prefix=prefix, Delimiter=delimiter)
        for o in result.get('CommonPrefixes'):
            folders.append(o.get('Prefix'))
        return folders

    def count_objects_in_s3_folder(self, bucket_name, prefix):
        import boto3
        # Create an S3 client
        s3 = boto3.client('s3')

        # Initialize the object count
        object_count = 0

        # Use the list_objects_v2 API to retrieve the objects in the folder
        paginator = s3.get_paginator('list_objects_v2')
        response_iterator = paginator.paginate(Bucket=bucket_name, Prefix=prefix)

        # Iterate through the paginated responses
        for response in response_iterator:
            if 'Contents' in response:
                object_count += len(response['Contents'])
        return object_count


    def bulk_del_with_pbar(self, bucket, prefix):
        from tqdm import tqdm
        print(f'Deleting...{prefix} from bucket {bucket} on S3')
        with tqdm(unit=' objects', total=S3().count_objects_in_s3_folder(bucket_name=bucket,prefix=prefix)) as pbar:
            S3().bulk_delete(
                bucket=bucket, prefix=prefix,
                on_delete=lambda num: pbar.update(num),
            )
        print('Done')




    def bulk_delete(self,
                    bucket, prefix,
                    workers=8, page_size=1000, delimiter='/',
                    get_s3_client=lambda: boto3.client('s3'), on_delete=lambda num: None,
                    ):
        s3 = get_s3_client()
        queue = PriorityQueue()

        @dataclass(order=True)
        class Work:
            # A tuple that determines the priority of the bit of work in "func". This is a sort of
            # "coordinate" in the paginated node tree that prioritises a depth-first search.
            priority: Tuple[Tuple[int, int], ...]
            # The work function itself that fetches a page of Key/CommonPrefixes, or deletes
            func: Optional[Callable[[], None]] = field(compare=False)

        # A sentinal "stop" Work instance with priority chosen to be before all work. So when it's
        # queued the workers will stop at the very next opportunity
        stop = Work(((-1, -1),), None)

        def do_work():
            while (work := queue.get()) is not stop:
                work.func()
                queue.task_done()
                with queue.mutex:
                    unfinished_tasks = queue.unfinished_tasks
                if unfinished_tasks == 0:
                    for _ in range(0, workers):
                        queue.put(stop)

        def list_iter(prefix):
            return iter(s3.get_paginator('list_objects_v2').paginate(
                Bucket=bucket, Prefix=prefix,
                Delimiter=delimiter, MaxKeys=page_size, PaginationConfig={'PageSize': page_size},
            ))

        def delete_page(page):
            s3.delete_objects(Bucket=bucket, Delete={'Objects': page})
            on_delete(len(page))

        def process_page(page_iter, priority):
            try:
                page = next(page_iter)
            except StopIteration:
                return

            # Deleting a page is done at the same priority as this function. It will often be done
            # straight after this call because this call must have been the highest priority for it to
            # have run, but there could be unfinished nodes earlier in the depth-first search that have
            # since submitted work, and so would be prioritised over the deletion
            if contents := page.get('Contents'):
                delete_priority = priority
                queue.put(Work(
                    priority=delete_priority,
                    func=partial(delete_page, [{'Key': obj['Key']} for obj in contents]),
                ))

            # Processing child prefixes are done after deletion and in order. Importantly anything each
            # child prefix itself enqueues should be done before the work of any later child prefixes
            # to make it a depth-first search. Appending the index of the child prefix to the priority
            # tuple of this function does this, because the work inside each child prefix will only
            # ever enqueue work at its priority or greater, but always less than the priority of
            # subsequent child prefixes or the next page.
            for prefix_index, obj in enumerate(page.get('CommonPrefixes', [])):
                prefix_priority = priority + ((prefix_index, 0),)
                queue.put(Work(
                    priority=prefix_priority,
                    func=partial(process_page,
                                 page_iter=list_iter(obj['Prefix']), priority=prefix_priority)
                ))

            # The next page in pagination for this prefix is processed after delete for this page,
            # after all the child prefixes are processed, and after anything the child prefixes
            # themselves enqueue.
            next_page_priority = priority[:-1] + ((priority[-1][0], priority[-1][1] + 1),)
            queue.put(Work(
                priority=next_page_priority,
                func=partial(process_page, page_iter=page_iter, priority=next_page_priority),
            ))

        with ThreadPoolExecutor(max_workers=workers) as worker_pool:
            # Bootstrap with the first page
            priority = ((0, 0),)
            queue.put(Work(
                priority=priority,
                func=partial(process_page, page_iter=list_iter(prefix), priority=priority),
            ))

            # Run workers, waiting for the first exception, if any, raised by them
            done, _ = wait(
                tuple(worker_pool.submit(do_work) for _ in range(0, workers)),
                return_when=FIRST_EXCEPTION,
            )

            # If an exception raised, stop all the other workers because otherwise exiting the
            # ThreadPoolExecutor context will block, and re-raise the exception
            if e := next(iter(done)).exception():
                for _ in range(0, workers - 1):
                    queue.put(stop)
                raise e from None


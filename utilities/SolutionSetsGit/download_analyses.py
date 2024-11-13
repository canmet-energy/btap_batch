import os
import pandas as pd
from src.btap.aws_s3 import S3
import zipfile
import pathlib
import re
from icecream import ic


# This method will a single analysis present in a given S3 path. It will only download the zips and output
# excel files.  It will rename the files with the analysis_name/parent folder name.
# bucket is the s3 bucket.
# prefix is the s3 analysis folder to parse. Note the trailing / is important. It denoted that it is a folder to S3.
# target path is the path on this machine where the files will be stored.
# hourly_csv, eplusout_sql, in_osm, eplustbl_htm are bools that indicate to download those zipfiles. It will always download
# the output.xlsx file.
def download_analysis(key='phylroy_lopez_1/parametric_example/',
                      bucket='834599497928',
                      target_path='/home/plopez/btap_batch/downloads',
                      hourly_csv=False,
                      in_osm=False,
                      eplusout_sql=False,
                      eplustbl_htm=False,
                      unzip_and_delete=True,
                      ):
    filetype = 'output.xlsx'
    source_zip_file = os.path.join(key, 'results', filetype).replace('\\', '/')
    target_zip_basename = os.path.join(target_path, os.path.basename(os.path.dirname(key)) + "_" + filetype)
    S3().download_file(s3_file=source_zip_file, bucket_name=bucket, target_path=target_zip_basename)

    if hourly_csv:
        filetype = 'hourly.csv.zip'
        source_zip_file = os.path.join(key, 'results', 'zips', filetype).replace('\\', '/')
        target_zip_basename = os.path.join(target_path, os.path.basename(os.path.dirname(key)) + "_" + filetype)
        is_downloaded = S3().download_file(s3_file=source_zip_file, bucket_name=bucket, target_path=target_zip_basename)
        if unzip_and_delete and is_downloaded:
            extraction_folder_suffix = 'hourly.csv'
            extraction_folder = os.path.join(target_path, extraction_folder_suffix)
            pathlib.Path(extraction_folder).mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(target_zip_basename, 'r') as zip_ref:
                zip_ref.extractall(extraction_folder)
            pathlib.Path(target_zip_basename).unlink(missing_ok=True)

    if in_osm:
        filetype = 'in.osm.zip'
        source_zip_file = os.path.join(key, 'results', 'zips', filetype).replace('\\', '/')
        target_zip_basename = os.path.join(target_path, os.path.basename(os.path.dirname(key)) + "_" + filetype)
        is_downloaded = S3().download_file(s3_file=source_zip_file, bucket_name=bucket, target_path=target_zip_basename)
        if unzip_and_delete and is_downloaded:
            extraction_folder_suffix = 'in.osm'
            extraction_folder = os.path.join(target_path, extraction_folder_suffix)
            pathlib.Path(extraction_folder).mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(target_zip_basename, 'r') as zip_ref:
                zip_ref.extractall(extraction_folder)
            pathlib.Path(target_zip_basename).unlink(missing_ok=True)

    if eplusout_sql:
        filetype = 'eplusout.sql.zip'
        source_zip_file = os.path.join(key, 'results', 'zips', filetype).replace('\\', '/')
        target_zip_basename = os.path.join(target_path, os.path.basename(os.path.dirname(key)) + "_" + filetype)
        is_downloaded = S3().download_file(s3_file=source_zip_file, bucket_name=bucket, target_path=target_zip_basename)
        if unzip_and_delete and is_downloaded:
            extraction_folder_suffix = 'eplusout.sql'
            extraction_folder = os.path.join(target_path, extraction_folder_suffix)
            pathlib.Path(extraction_folder).mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(target_zip_basename, 'r') as zip_ref:
                zip_ref.extractall(extraction_folder)
            pathlib.Path(target_zip_basename).unlink(missing_ok=True)

    if eplustbl_htm:
        filetype = 'eplustbl.htm.zip'
        source_zip_file = os.path.join(key, 'results', 'zips', filetype).replace('\\', '/')
        target_zip_basename = os.path.join(target_path, os.path.basename(os.path.dirname(key)) + "_" + filetype)
        is_downloaded = S3().download_file(s3_file=source_zip_file, bucket_name=bucket, target_path=target_zip_basename)
        if unzip_and_delete and is_downloaded:
            extraction_folder_suffix = 'eplustbl.htm'
            extraction_folder = os.path.join(target_path, extraction_folder_suffix)
            pathlib.Path(extraction_folder).mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(target_zip_basename, 'r') as zip_ref:
                zip_ref.extractall(extraction_folder)
            pathlib.Path(target_zip_basename).unlink(missing_ok=True)


# This method will download all the analysis present in a given S3 path. It will only download the zips and output
# excel files.  It will rename the files with the analysis_name/parent folder name.
# bucket is the s3 bucket.
# prefix is the s3 folder to parse. Note the trailing / is important. It denoted that it is a folder to S3.
# target path is the path on this machine where the files will be stored.

def download_analyses(bucket='834599497928',
                      prefix='solution_sets/',
                      target_path='/home/plopez/btap_batch/downloads',
                      hourly_csv=True,
                      in_osm=True,
                      eplusout_sql=True,
                      eplustbl_htm=True,
                      concat_excel_files=True,
                      regex_filter='vin.*YUL.*',
                      unzip_and_delete=True,
                      dry_run=True
                      ):
    folders = S3().s3_get_list_of_folders_in_folder(bucket=bucket, prefix=prefix)
    if prefix + 'btap_cli/' in folders:
        folders.remove(prefix + 'btap_cli/')

    if prefix + 'btap_batch/' in folders:
        folders.remove(prefix + 'btap_batch/')

    for folder in folders:

        if re.search(regex_filter, folder) != None:
            print(f"Processing {folder}")
        if re.search(regex_filter, folder) and not dry_run:
            download_analysis(key=folder,
                              bucket=bucket,
                              target_path=target_path,
                              hourly_csv=hourly_csv,
                              in_osm=in_osm,
                              eplusout_sql=eplusout_sql,
                              eplustbl_htm=eplustbl_htm,
                              unzip_and_delete=unzip_and_delete
                              )
    if concat_excel_files and not dry_run:
        print(f"Creating master csv and parquet results file.")
        all_files = os.listdir(target_path)
        xlsx_files = [f for f in all_files if f.endswith('.xlsx')]
        df_list = []
        for xlsx in xlsx_files:
            try:
                df = pd.read_excel(os.path.join(target_path, xlsx))
                print(f"Appending {xlsx} to master csv file.")
                df_list.append(df)
            except Exception as e:
                print(f"Could not read file {xlsx} because of error: {e}")
        # Concatenate all data into one DataFrame
        big_df = pd.concat(df_list, ignore_index=True)

        # Save the final result to a new CSV file
        master_csv_path = os.path.join(target_path, 'master.csv')
        big_df.to_csv(master_csv_path, index=False)

        # Create parquet file.
        master_parquet_file = os.path.join(target_path, 'master.parquet')
        # Horrible workaround to deal with non-uniform datatypes in columns.
        big_df = pd.read_csv(master_csv_path, dtype='unicode')
        big_df.to_parquet(master_parquet_file)






download_analyses(bucket='834599497928',
                  prefix='sgilani/',  # S3 prefix MUST have a trailing /
                  target_path=r'D:/BTAP/OEE_Electrification/PrimarySchool',  # Your local download folder.
                  hourly_csv=False,  # download hourly.csv zip
                  in_osm=True,  # download osm zip
                  eplusout_sql=False,  # download sqlite files zip
                  eplustbl_htm=False,  # download e+ htm report zip
                  concat_excel_files=True,  # concat all output.xlsx files to a master.csv and parquet file
                  regex_filter='OEEelec_PrimarySchool_NaturalGas_YY.*$',  # an example that gets MidriseApartment from Toronto except the vintage analyses
                  unzip_and_delete=False,  # This will unzip the zip files of all the above into a folder and delete the original zip file.
                  dry_run=False  # If set to true.. will do a dry run and not download anything. This is used to make sure your regex is working as intended.
                  )

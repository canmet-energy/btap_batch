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






# download_analyses(bucket='834599497928',
#                   prefix='sgilani/',  # S3 prefix MUST have a trailing /
#                   target_path=r'C:/Users/sgilani/OneDrive - NRCan RNCan/Documents/BTAP/OEE-2024/Simulation/AWS-runs/Scenarios',  # Your local download folder.
#                   hourly_csv=False,  # download hourly.csv zip
#                   in_osm=False,  # download osm zip
#                   eplusout_sql=False,  # download sqlite files zip
#                   eplustbl_htm=False,  # download e+ htm report zip
#                   concat_excel_files=False,  # concat all output.xlsx files to a master.csv and parquet file
#                   regex_filter='OEEelec_SC_SchoolElec_ElecResWH_Primary_\S\S\S_env_*',#'OEEelec_SC_MURBElec_ElecResWH_Lowrise_\S\S\S_env_*',  # an example that gets MidriseApartment from Toronto except the vintage analyses
#                   unzip_and_delete=False,  # This will unzip the zip files of all the above into a folder and delete the original zip file.
#                   dry_run=True  # If set to true.. will do a dry run and not download anything. This is used to make sure your regex is working as intended.
#                   )




#=======================================================================================================================
#### Download OEE outputs one by one, as the 'download_analyses' did not download all cases
# First, create a list of all scenarios
list_analysis_name = []
ENVELOPE = [
        'env_necb',
        'env_necb_15',
        'env_necb_30'
    ]
ELECsystems_OEE = [
        # 'MURBElec_ElecResWH',
        # 'MURBMixed_ElecResWH',
        # 'MURBASHPElec_ElecResWH',
        # 'MURBASHPMixed_ElecResWH',
        # 'SchoolElec_ElecResWH',
        # 'SchoolMixed_ElecResWH',
        # 'SchoolASHPElec_ElecResWH',
        # 'SchoolASHPMixed_ElecResWH',
        # ### 'CASHPElec_ElecResWH',
        # ### 'CASHPMixed_ElecResWH',
        # 'CGSHPElec_ElecResWH',
        # 'CGSHPMixed_ElecResWH',
        # 'VRFElecBoiler_ElecResWH',
        # 'VRFMixedBoiler_ElecResWH',
        # 'VRFElecResBackup_ElecResWH',

        ### 'MURBElec_HPWH',
        ### 'MURBMixed_HPWH',
        ### 'MURBASHPElec_HPWH',
        ### 'MURBASHPMixed_HPWH',
        ### 'SchoolElec_HPWH',
        ### 'SchoolMixed_HPWH',
        ### 'SchoolASHPElec_HPWH',
        ### 'SchoolASHPMixed_HPWH',
        ### 'CASHPElec_HPWH',
        ### 'CASHPMixed_HPWH',
        ### 'CGSHPElec_HPWH',
        ### 'CGSHPMixed_HPWH',
        ### 'VRFElecBoiler_HPWH',
        ### 'VRFMixedBoiler_HPWH',
        ### 'VRFElecResBackup_HPWH',

        'MURBMixed_ElecResWH_0199',
        'MURBASHPMixed_ElecResWH_0199',
        'SchoolMixed_ElecResWH_0199',
        'SchoolASHPMixed_ElecResWH_0199',
        'CGSHPMixed_ElecResWH_0199',
        'VRFMixedBoiler_ElecResWH_0199'
    ]
epw_files = [
    ['CAN_BC_Vancouver.Intl.AP.718920_NRCv12022_TMY_GW1.5.epw', 'YVR'],  # CZ 4

    ['CAN_BC_Kelowna.Intl.AP.712030_NRCv12022_TMY_GW1.5.epw', 'YLW'],  # CZ 5
    ['CAN_ON_Toronto-Pearson.Intl.AP.716240_NRCv12022_TMY_GW1.5.epw', 'YYZ'],  # CZ 5

    ['CAN_ON_Ottawa-Macdonald-Cartier.Intl.AP.716280_NRCv12022_TMY_GW1.5.epw', 'YOW'],  # CZ 6
    ['CAN_QC_Montreal-Trudeau.Intl.AP.716270_NRCv12022_TMY_GW1.5.epw', 'YUL'],  # CZ 6
    ['CAN_NS_Halifax-Stanfield.Intl.AP.713950_NRCv12022_TMY_GW1.5.epw', 'YHZ'],  # CZ 6
    ['CAN_NL_St.Johns.Intl.AP.718010_NRCv12022_TMY_GW1.5.epw', 'YYT'],  # CZ 6
    ['CAN_PE_Charlottetown.AP.717060_NRCv12022_TMY_GW1.5.epw', 'YYG'],  # CZ 6
    ['CAN_NB_Fredericton.Intl.AP.717000_NRCv12022_TMY_GW1.5.epw', 'YFC'],  # CZ 6

    ['CAN_AB_Calgary.Intl.AP.718770_NRCv12022_TMY_GW1.5.epw', 'YYC'],  # CZ 7A
    ['CAN_AB_Edmonton.Intl.CS.711550_NRCv12022_TMY_GW1.5.epw', 'YEG'],  # CZ 7A
    ['CAN_SK_Saskatoon-Diefenbaker.Intl.AP.718660_NRCv12022_TMY_GW1.5.epw', 'YXE'],  # CZ 7A
    ['CAN_MB_Winnipeg-Richardson.Intl.AP.718520_NRCv12022_TMY_GW1.5.epw', 'YWG'],  # CZ 7A
]
for scenario in ELECsystems_OEE:
    for epw_file in epw_files:
        if scenario.startswith("School"):
            list_building_type = [
                'PrimarySchool',
                'SecondarySchool'
            ]
        elif scenario.startswith("MURB"):
            list_building_type = [
                'LowriseApartment',
                'MidriseApartment',
                'HighriseApartment'
            ]
        else:
            list_building_type = [
                'LowriseApartment',
                'MidriseApartment',
                'HighriseApartment',
                'PrimarySchool',
                'SecondarySchool'
            ]

        for building_type in list_building_type:
            if building_type.endswith("School"):
                building_name = building_type.replace('School', '')
            elif building_type.endswith("Apartment"):
                building_name = building_type.replace('Apartment', '')

            for envelope in ENVELOPE:
                if scenario.endswith("_0199"):
                    if building_type.endswith("School"):
                        if building_name == "Primary":
                            building_name = building_name.replace('Primary', 'Pri')
                        elif building_name == "Secondary":
                            building_name = building_name.replace('Secondary', 'Sec')
                    elif building_type.endswith("Apartment"):
                        building_name = building_name.replace('rise', '')
                    analysis_name = f"OEEelec_SC_{scenario}_{building_name}_{epw_file[1]}_{envelope}"
                else:
                    analysis_name = f"OEEelec_SC_{scenario}_{building_name}_{epw_file[1]}_{envelope}"
                list_analysis_name.append(analysis_name)
print(list_analysis_name)
print(len(list_analysis_name))

### 'OEEelec_SC_MURBASHPMixed_ElecResWH_Highrise_YEG_env_necb/'
datapoint_number = 0.0
for analysis_name in list_analysis_name:
    print('analysis_name', analysis_name)
    print(datapoint_number, analysis_name)
    # download_analyses(bucket='834599497928',
    #                   prefix='sgilani/',
    #                   target_path=r'C:/Users/sgilani/OneDrive - NRCan RNCan/Documents/BTAP/OEE-2024/Simulation/AWS-runs/Scenarios',
    #                   hourly_csv=False,
    #                   in_osm=False,
    #                   eplusout_sql=False,
    #                   eplustbl_htm=False,
    #                   concat_excel_files=False,
    #                   regex_filter=analysis_name,
    #                   unzip_and_delete=False,
    #                   dry_run=False
    #                   )
    datapoint_number += 1.0

    key='sgilani/'
    bucket='834599497928'
    target_path=r'C:/Users/sgilani/OneDrive - NRCan RNCan/Documents/BTAP/OEE-2024/Simulation/AWS-runs/Scenarios'

    filetype = 'output.xlsx'
    source_zip_file = os.path.join(key, analysis_name, 'results', filetype).replace('\\', '/')
    print('source_zip_file', source_zip_file)
    target_zip_basename = os.path.join(target_path, analysis_name+'.xlsx')
    print('target_zip_basename', target_zip_basename)
    S3().download_file(s3_file=source_zip_file, bucket_name=bucket, target_path=target_zip_basename)

#=======================================================================================================================

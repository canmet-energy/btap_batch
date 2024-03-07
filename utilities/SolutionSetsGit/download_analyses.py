






download_analyses(bucket='834599497928',
                  build_env_name='solution_sets/',  # S3 prefix MUST have a trailing /
                  target_path=r'/home/plopez/btap_batch/downloads/Solution/LowriseApartment',  # Your local download folder.
                  hourly_csv=True,  # download hourly.csv zip
                  in_osm=True,  # download osm zip
                  eplusout_sql=False,  # download sqlite files zip
                  eplustbl_htm=False,  # download e+ htm report zip
                  concat_excel_files=True,  # concat all output.xlsx files to a master.csv and parquet file
                  analysis_name_filter='LowriseApartment.*$',  # an example that gets MidriseApartment from Toronto except the vintage analyses
                  unzip_and_delete=False,  # This will unzip the zip files of all the above into a folder and delete the original zip file.
                  dry_run=True  # If set to true.. will do a dry run and not download anything. This is used to make sure your regex is working as intended.
                  )

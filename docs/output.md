# Outputs

## Local Run 
BTAP batch will save the results from the analysis to your selected output folder if you ran with compute_environment set to **local**.

The format is mostly the same for all analysis types. 
```
->output
    ->analysis_name
        ->algorithm_type
            ->runs
        ->reference
            ->runs
        ->results
            ->database
            ->eplusout.sql
            ->eplus.html
            ->failures
            ->hourly.csv
            ->in.osm
            ->output.xlsx
```
The algorithm_type would actually be the name of the algorithm used ( parametric, nsga2, sample_lhs, sensitivity, etc). 
* **algorithm_type->runs** contains the raw Energyplus simulation input and outputs
* **reference->runs** contains the ray Energyplus runs of the reference building models used to compare against the proposed runs. 
* **results->database** contains the high level annual results for each simulation. 
* **results->eplusout.sql** contains the EnergyPlus simulation results sql database for each run. This is great for 
programmatically obtaining more detailed information about the run. 
* **result->eplus.html** contains the standard EnergyPlus HTML summary output. 
* **results->failures** contains information on the failed/crashed simulation runs. 
* **results->hourly.csv** This folder contains the hourly data requested in the [optional hourly output](hourly_outputs.md)
* **results->in.osm** contained the OpenStudio models for all the simulation runs. 
* **results->output.xlsx** contains all the inputs used for each simulation and the high level annual simulation 
information results.  The column ***'datapoint_id'*** contains a unique identifier that can be used to look up information in 
all the other folder.  A convention was used that all columns with a ":" prefix indicated an input.  All the others are 
outputs from the simulation

## AWS Runs
The output of AWS  runs is not stored all locally, but on the S3 Bucket. 

The s3_bucket_name used by NRCan staff is   the ':analysis_name' you chose and the analysis_id 
generated by the script. For example, if you ran the analysis with the analysis_name: set to 'example_analysis', the default 
:s3_bucket is '834599497928' for the nrcan account, and your aws username is 'phylroy.lopez'. The runs would be kept on S3 in a path like
```
s3://<:s3_bucket_name>/<build_env_name>/<:analysis_name>/
```
Where 
* s3_bucket_name: '834599497928'
* build_env_name: is the name you set in the build_conf.yml file in [this step](configure.md)
* analysis_name: is the name you set in the input.yml file. 

You can see the contents on your AWS S3 console. 

### Download Results
There are at least three ways you can download the results files from S3. You can use the 
[aws cli](https://docs.aws.amazon.com/cli/latest/reference/s3/cp.html). You can use the AWS web console to download 
individual files, or you can use btap_batch's  aws-download command. Below is a the cli help message descibing the usage.
```
(venv) PS C:\Users\plopez\PycharmProjects\btap_batch> python ./bin/btap_batch.py aws-download -h
Usage: btap_batch.py aws-download [OPTIONS]

  Download results from 1 or more analyses performed on Amazon's S3 bucket.

Options:
  --s3_bucket TEXT       Bucket where build environment exists and analyses
                         were run.   [default: 834599497928 for NRCan CE-O]
  --build_env_name TEXT  name of aws build_environment simulation was run
                         with.  [default: solution_sets]
  --analysis_name TEXT   name of analysis or you can use regex to get single or
                         mulitple analyses performed under a build environment name
                         [default: LowriseApartment.*$]
  --output_path TEXT     Path to save downloaded data to.  [default:
                         C:\Users\plopez/btap_batch/downloads]
  --download             By default, will not download and just show the
                         folders it finds on S3. This is used to make sure
                         your regex is working as intended before you add this
                         flag to set to true.
  --osm                  Download OSM files
  --hourly               Download Hourly data
  --eplussql             Download EnergyPlus SQLite output data
  --eplushtm             Download EnergyPlus HTM output data
  -h, --help             Show this message and exit.

```

Note: This has the potential to download a lot of data! For that reason, if you run the command without the --download 
switch, it will simply output the folder names on S3 that it will download. If you invoke the command with the --download switch
it will really download what you are asking for. This has an added feature that it will also create a master.csv and 
master.parquet file. These files contained all the output.xlsx files contcatenates. This is useful keep all analysis results 
for example multiple optimization runs for different building types, in a single file. 
# Run Analysis

Once you have created your project folder that contains the input.yml file and optionally the custom_osm folder 
containing custom osm files you created. You are ready to run an analysis. 
 
Ensure that you have selected the correct **compute_environment** (local or aws) in your build_conf.yml file, and have built
the environment before we attempt to run the analysis. If not refer to [this](configure.md). 

Once that is confirmed you can run the analysis with the 'run' command. The run command has a few switches. You can see 
them with the help '-h' switch. 

To run a project 'example/optimization' analysis for example, on the compute environment indicated in your build_config.yml 
file, and have the results go to the default output folder. Execute this command. 
```
python ./bin/btap_batch.py run -p ./example/optimization 
```
To specify an output folder, you can optionally use the '-o' switch with the full path where you wish to save the output. 
```
python ./bin/btap_batch.py run -p ./example/optimization -o C:\MyOutputFolder
```

If running **local**. You should see output like this.
```
(venv) PS C:\Users\plopez\PycharmProjects\btap_batch> python ./bin/btap_batch.py run -p C:\Users\plopez\PycharmProjects\btap_batch\examples\optimization
Using build_env_name from build_config.yml: plopez
running on local
analyses_folder is:C:\Users\plopez\PycharmProjects\btap_batch\output
analysis_id is: 37e11ef3-86d5-4d58-b76f-af5ca5ec93d6
analysis_name is: optimization_example
Deleting previous runs from: C:\Users\plopez\PycharmProjects\btap_batch\output\optimization_example\reference
Creating new folders for analysis
Using 46 threads.
Failed:0: Progress Bar:   0%|                                                                                                                                    | 0/4 [00:00<?, ?it/s]
```

if compute_environment is set to **aws** you should see a job submission to aws. You can observe the progress using the
AWS Batch web console. This will delete any data on the S3 folder if you ran this previously with the same 
:analysis_name and build_env_name. See the AWS section in [output](output.md) for more details.

```bash
(venv) PS C:\Users\plopez\PycharmProjects\btap_batch> python.exe ./bin./btap_batch.py run -p .\examples\optimization 
Using build_env_name from build_config.yml: plopez
Deleting old files in S3 folder plopez\optimization_example/
Deleting...plopez\optimization_example/ from bucket 834599497928 on S3
Submitted optimization_example to aws job queue plopez_btap_batch_job_queue

```

# Kill Analysis
We are all human and make mistakes. Sometimes we need to kill the analysis to prevent from wasting time and money. 

## Kill Local
To cancel an analysis, use the **CTRL-C** keystroke to stop the processes. This make take a few 
hits to cancel the local run. You will need to delete any partially completed output files from your computer.
## Kill AWS
To cancel a set of jobs sent to AWS issue the command
```
 python ./bin/btap_batch.py aws-kill
```
This will use the aws build_env name defined in your build_config.yml to kill all jobs issued to aws under your build_env_name. You must ensure 
that you use the same build_env_name that you used when you started the analysis.   




# Run Analysis

Once you have developed you have created your project folder that contains the input.yml file and optionally the custom_osm folder containing custome osm files you created. You are ready to run a simulation. 
 
Ensure that you have selected the correct compute_environment (local or aws) in your build_conf.yml file, and have built the environment before we attempt to run the analysis. If not refer to [this](configure.md). Once that is confirmed you can run the analysis with the 'run' command. The run command has a few switches. You can see them with the help '-h' switch. 

```angular2html
(venv) PS C:\Users\plopez\PycharmProjects\btap_batch> python ./bin/btap_batch.py run -h  
Usage: btap_batch.py run [OPTIONS]

  This will run an analysis project. You must specify a project folder.

Options:
  -p, --project_folder TEXT     location of folder containing input.yml file
                                and optionally support folders such as
                                osm_folder folder for custom models. Default
                                is the optimization example folder.
  --output_folder TEXT          Path to output results. Defaulted to this
                                projects output folder ./btap_batch/output
  -c, --build_config_path TEXT  location of Location of build_config.yml file.
                                Default location is
                                C:\Users\plopez\.btap\config
  --compute_environment TEXT    Forces Computer environment to use over-riding 
                                what is in build_config.yml. 
  -h, --help                    Show this message and exit.

```

So to run the project 'example/optimization' analysis on the default compute environment in your build_config.yml file,  and have the results go to the default output folder. Execute this command. 
```angular2html
python ./bin/btap_batch.py run -p ./example/optimization. 
```
Note: You can use full absolute paths in the -p switch. 




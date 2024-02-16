# Configuration of Build Environment

You need to configure your computer by first creating a **build_config.yml** file. This file will tell btap:
* how to build the simulation environment  
* where to build and do the simulation analysis (**Local** or for really large analysis on the cloud at **Amazon**)
* what weather files to include in the build environment for your analyses.

The build command is one of several commands you have at your disposal in btap_batch.  You can use the -h switch to reveal all the commands. Here is an example of the help output.
```angular2html
(venv) PS C:\Users\plopez\PycharmProjects\btap_batch> python ./bin/btap_batch.py -h    
Usage: btap_batch.py [OPTIONS] COMMAND [ARGS]...

Options:
  --version   Show the version and exit.
  -h, --help  Show this message and exit.

Commands:
  aws-download  Download results from 1 or more analyses performed on...
  aws-kill      This will terminate all aws analyses.
  aws-rm-build  This delete all resources on aws for the given...
  batch         This will run all the analysis projects in a given folder...
  build         This will build the environment required to run an analysis.
  credits
  run           This will run an analysis project.
  run-examples  This will run all the analysis projects in the examples...
```
For now we will focus on the **build** command. Here are is the help for that specific command

```angular2html
(venv) PS C:\Users\plopez\PycharmProjects\btap_batch> python ./bin/btap_batch.py build -h
Usage: btap_batch.py build [OPTIONS]

  This will build the environment required to run an analysis. If running for
  the first time. A template configuration will be placed in your home folder
  here:C:\Users\plopez\.btap\config

Options:
  -p, --build_config_path TEXT  location of Location of build_config.yml file.
                                Default location is
                                C:\Users\plopez\.btap\config
  -h, --help                    Show this message and exit.

```

You can generate a template of the build_config.yml file by trying to build and environment for the first time.
```
python ./bin/btap_batch build
```
It will create a file under your home folder. For example if your computer username was plopez. It should create a file at the location below. 

```
c:/Users/plopez/.btap/build_config.yml
```

Use this to ensure that the weather files, branches and compute environment selected is what you wish to use for your subsequent analyses.

## Building the analysis environment
Once you have select how you wish to run btap_batch from your build_config.yml file. You may build the compute environment. This will be used to run your simulations. Depending on what you have chosen and your compute environment. It will download and build all the resources you need for analysis. 

To build, or rebuild the build environment simply type.

```
python ./bin/btap_batch build
```
Please note that if you wish to update your environment to the latest version of btap, change compute environments or, you will have to run these commands again. This will rebuild your environment.

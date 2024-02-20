# Configuration of Build Environment

You need to configure your computer by first creating a **build_config.yml** file. This file will tell btap:
* how to build the simulation environment  
* where to build and do the simulation analysis (**Local** or for really large analysis on the cloud at **Amazon**)
* what weather files to include in the build environment for your analyses.


You can create an sandbox build environment that will have all dependancies automatically install with specific versions
of OpenStudio and EnergyPlus.  You can accomplish this by editing your build_conf.yml file and running the **build** command. 

```bash
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
Once you have selected how you wish to run btap_batch from your build_config.yml file. You may build the compute environment. This will be used to run your simulations. Depending on what you have chosen and your compute environment. It will download and build all the resources you need for analysis. 

To build, or rebuild the build environment simply type. It should take about 10m to build the environment either locally
or on AWS.  

```
python ./bin/btap_batch build
```

:warning: **Do not cancel this process. Let it run to completion**





Please note that if you wish to update your environment to the latest version of btap, change compute environments or, you will have to run these commands again. This will rebuild your environment.

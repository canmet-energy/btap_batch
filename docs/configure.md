You need to configure your computer by first creating a build_config.yml file. This file will tell btap how to:
* build the simulation environment  
* where to build and do the analysis (**Local** or for really large analysis  **Amazon**)


 You can generate a template by trying to build and environment for the first time.
```
python ./bin/btap_batch build
```
It will create a file under your home folder. For example if your computer username was plopez. It should create a file at the location below. 

```
c:/Users/plopez/.btap/build_config.yml
```

## Building the analysis environment
Once you have select how you wish to run btap_batch from your build_config.yml file. You may build the compute environment. This will be used to run your simulations. You depending on what you have chosen and your compute environment. It will download and build all the resources you need for analysis. 

To build, or rebuild the build environment simply type.

```
python ./bin/btap_batch build
```
Please note that if you wish to update your environment to the latest version of btap, you will have to run these commands again. This will rebuild your environment.
```
python ./bin/btap_batch.py build-environment --compute_environment local --disable_costing --weather_list C:\Users\ckirney\btap_batch\chris-weather-list.yml
```
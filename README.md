# BTAP

BTAP also can also perform optimization analysis for any given minimization criterion based on simulation output. 

## Background
BTAP allows you to quickly generate archetypical buildings based on Canadian codes and data and apply common energy conservation measures to explore possible technology packages. BTAP calulates energy, NECB Tier performance,  operational carbon and relative capital costs for all scenarios where possible. 

The most common used cases for BTAP is to:
* examine the cost effective performance of codes and standards across Canada.
* examine design pathways to Net-Zero Buildings.
* development of surrogate models to quickly examine the entire solution space without requiring simulations (StatsCan Support 2024)

For machine learning, BTAP can also generate large samples using the Latin Hypercube Sampling analysis. A machine learning surrogate model pipeline will be added to the project in 2023-24.
BTAP almost exclusively runs on the cloud. There are options ways to run it locally on Linux and Windows systems and via command line. If you are interested in this approach please contact phylroy.lopez@nrcan-rncan.gc.ca .  

### Vintage Supported
The project currently supports the following vintages for both code rulesets and incremental costing of utility costs and incremental capital costs.  
* NECB2011
* NECB2015
* NECB2017
* NECB2020

There is also experimental vintage archetypes that can be used. Please contact Chris.Kirney@nrcan-rncan.gc.ca for more details on this project. 
*1980-2010
*Pre1980

### Commercial Building Geometries
BTAP comes with the standard geometries built-in commercial building spacetype geometric models. The are based on the U.S. DOE reference building archetypes, but gutted of everything except the geometry and space type information. You can find a list of the buildings [here](./docs/BtapBuildingGeometryLibrary.md)
You can also create your own buildings using the OpenStudio SketchUp Plug-in included in the OpenStudio Installation. Other tools support conversion to an openstudio model including Revit, and eQuest. More information on creating your model is kept [here](todo)
 
### Utility Cost Support
BTAP supports the National Energy Board Utility rates. These are averaged costs per GJ and do not have block or tiered surcharges. BTAP does support block rate structure, however this is advanced and we recommend using NREL's tariff measure that can be found [here](https://bcl.nrel.gov/node/82923] 

### Capital Cost Support
Please note: Costing support requires a licence for RSMeans. Please contact RSMeans for a licence if you wish to use their data. 

We use a third party resource to cost aspects of the models that BTAP generates. The cities that are supported are listed [here](./docs/CostingSupportedCities.md).
If another weather file is selected that is not on this list, BTAP will try to select a city closest to the list below to use for costing. The latitude and longitudes included in the table are used to calculate this. This may produce unexpected results if not aware. 

BTAP will automatically cost materials, equipment and labour. BTAP Costing will only cost items that have energy impact. It will for example cost the wall construction layers, but not the structural components. 
Some items that BTAP costs are:
* Labour, Overhead
* Layer Materials in Constructions and fenestration.
* Piping, Ductworks, Headers based on actual geometry of the building. This is required when evaluating forces air vs hydronic solutions. 
* Standard HVAC Equipment, Boilers, Chillers, HeatPumps, Service Hot Water. 

Some examples of items it will not cost are:
* Internal walls, doors, toilets, structural beams, furniture, etc.   

It will also only cost what is contained with the btap standard measures. For example if you add a measure to add overhangs into the BTAP workflow. It will not cost it. BTAP uses internal naming conventions to cost items and make decisions on how components are costed. This does not mean you cannot use other measures created by other authors on [NREL's Building Component Library](https://bcl.nrel.gov/). It just means it will not be costed. 
 

## Why This Python Project?
This project simplifies the process to run parametric and optimization runs. It uses code directly from 
openstudio-standards and requires no PAT measures. It takes advantage of all the costing and energy conservation development work
that CanmetEnergy-Ottawa has developed to date. 

Using AWS batch also reduces the cost of simulations and enables researchers to use AWS dashboards to monitor the simulation runs. BTAP_BATCH
takes advantage of Amazons cost-effective batch queue system to complete simulations. 

## Requirements
* Windows 10 Professional version 1909 or greater 
* [Docker](https://docs.docker.com/desktop/install/windows-install/) running on your computer. Ensure that you complete creating the docker-users group on your system.
* [Python 3.9](https://www.python.org/ftp/python/3.9.13/python-3.9.13-amd64.exe) and Pip installed. 
* [Git client](https://git-scm.com/downloads)
* A high speed internet connection.
* A github account and [git-token](https://docs.github.com/en/github/authenticating-to-github/creating-a-personal-access-token)
* Add the github token as a user windows/linux environment variable as GIT_API_TOKEN. Search for'Edit Environment Variables for your Account' in Window control panel to add your token name and value.
* A computer with at least 8GB+ ram and 4 or more cores (8+ threads). Preferably a powerful multi-core computer to run simulations fast locally. (24 core/48 thread with 32GB+) 
* [OpenStudio 3.6.1](https://github.com/NREL/OpenStudio/releases/tag/v3.6.1) (optional) Required to use the OpenStudio App to edit osm files.
* [OpenStudio Application 1.6.0](https://github.com/openstudiocoalition/OpenStudioApplication/releases) (optional) Required to use the OpenStudio App to edit osm files.
* If you would like to use costing and have an RSMeans account contact chris.kirney@nrcan-rncan.gc.ca for permissions to access canmet-energy repositories (For use of the btap_private_cli costing image.)

### Amazon HPC only:
* [AWS CLI version 2 on Windows](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2-windows.html).
* [Set Up AWS credentials file](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html) . 
* Add your AWS username added to your computer environment variable as AWS_USERNAME. Should be something like firstname.lastname. Do this as you did the GIT_API_TOKEN above.
* Add an AWS S3 bucket with a name same as your aws account id. This should be a 12 digit integer created in the ca-central region.


## Download Code and Python packages using Pip.

For the following I will be assuming that you are installing this on your C: drive root. 

```
cd C:/
git clone https://github.com/canmet-energy/btap_batch
cd btap_batch
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
```

## Build Environment

You need to configure the docker images locally and on AWS to run any analysis. These depend on the branches that you use to create your environment. 

The btap_batch cli command for this is called 'build-environment'. You can invoke the help for this command using the -h switch. This lets to you know the option switches to change which branches you wish to use for your analyses. 
```
python ./bin/btap_batch.py build-environment -h

```

However to use the most recent stable versions openstudio-standards, btap_costing, and btap_batch, simply run this command to configure your system to run locally. Note: if you do not have an RSMeans licence you MUST disable costing.
```
python ./bin/btap_batch.py build-environment --compute_environment local_docker --disable_costing
```
and/or to configure Amazon Web Services..
```
python ./bin/btap_batch.py build-environment --compute_environment aws_batch --disable_costing
```
Please note that if you wish to update your environment to the latest branches of development, you will have to run these commands again. This will rebuild your environment.


### Parametric Analysis Local Machine
1. To run a parametric analysis, go to the example.yml analysis file in the 'examples/parametric' folder. Each 
parameter is explained in that file. Ensure that parametric analysis is a reasonable size for your system (i.e. Do not 
run millions of simulations on your 2 core laptop). Ensure that the ':compute_environment' variable is set to local.  
2. Please ensure that the btap_batch python venv environment is active. If it is not, run the following from the project folder. 
```
venv\Scripts\activate.bat
```

You can run the analysis using the run-analysis-project. You can inspect the switches available for this comm
```
python ./bin/btap_batch.py run-analysis-project --compute_environment local_docker --project_folder C:\Users\plopez\btap_batch\examples\parametric --reference_run
```
3. Simulation should start to run. A folder will be created in output folder with the variable name you set 
':analysis_name' in the yml file. In that folder you will see two folders, 'parametric' and 'reference'. 'reference' 
contains the reference run analysis. This is the information use to compare the 'parametric' runs against. both of these folders
contain a 'runs' folder and 'results' folder.  


### Output
* The runs folder contains folders with uuids for all the simulations that you are running. It contains the 
run_options.yml file. This contains the selections created for that particular run. This contains all the input and 
output files from OS/Energyplus.

* The results folder contains the summary results of all the simulations. 
    * The database folder contains all the csv outputs from each run.
    * The eplustbl.htm folder contains the energyplus html output for each run. 
    * The failures folder contain the input files that did not simulation correctly. 
    * The hourly.csv folder contains the hourly data requested for each simulation. 
    * The in.osm contains the OpenStudio osm file used for each simulation. 
    * The output.xlsx is an excel file that contains the results from all the simulations.  

## Using Amazon AWS for analysis
1. Ensure you are not connected to a VPN and do not connect while running simulations.
2. Change '-compute_environment' to aws_batch (note that ':compute_environment' is in example.yml analysis file in the 'example' folder).
3. Update your AWS credentials to ensure it is up to date through your AWS Account -> btap-dev -> Command line and programmatic Access. Copy the Text in 'Option 2'.
4. Use your updated AWS credentials in '.aws/credentials' file in your user folder.
*Note*:  Navigate to '.aws' folder in your user folder using windows powershell. Run the command: ```$ aws configure```. Set the default region name to ca-central-1, and output format to json. Then, open the generated credentials file in '.aws' folder in your user folder. Use your updated AWS credentials in the credentials file. Replace the first line that looks something like this [834599497928_PowerUser] to [default] and save the file.

```
python ./bin/btap_batch.py run-analysis-project --compute_environment aws_batch --project_folder C:\Users\plopez\btap_batch\examples\parametric --run_reference
```

The output of the runs is not stored all locally, but on the S3 Bucket,  the ':analysis_name' you chose and the analysis_id 
generated by the script. For example, if you ran the analysis with the analysis_name: set to 'example_analysis', the default 
:s3_bucket is '834599497928' for the nrcan account, and your aws username is 'phylroy.lopez'. The runs would be kept on S3 in a path like
```
s3://<:s3_bucket_name>/<your_user_name>/<:analysis_name>/
```
*Note*: This script will not delete anything from S3. So you must delete your S3 folders yourself.


## Optimization 
To perform an optimization run you can review the example contained in examples/optimiztion. The .yml file contains all the 
options for the analysis. 

* The :analysis_configuration->:algorithm->:type should be set to nsga2.
* The :analysis_configuration->:algorithm->:population should be set to the number of threads that you have available on your system. 
* The :analysis_configuration->:algorithm->:n_generations determine how many generations to run. This defines how long your simulation will take n* time to run a single simulaiton. 
* The :analysis_configuration->:algorithm->:prob is set to 0.85. Please see pymoo docs if you wish to change this. 
* The :analysis_configuration->:algorithm->:eta is set to 3.0. Please see pymoo docs if you wish to change this.  
* The :analysis_configuration->:algorithm->:minimize_objectives: is set to  [ "energy_eui_total_gj_per_m_sq","cost_equipment_total_cost_per_m_sq"] for most optimization problems. The :minimized_objectives can be anything in the btap_data.json file. You can view the output of a btap_data.json file 
from a local parametric run. However most of the time the above variables would be sufficient to optimize building designs.

To run the example simple point the --project_folder switch to the analysis input folder.

```
python ./bin/btap_batch.py run-analysis-project --compute_environment <choose local_docker or aws_batch> --project_folder .\examples\optimization --reference_run
```

## Elimination Analysis
BTAP allows you to quickly perform an elimination analysis. This will set various aspects of the building to effectively
 'zero' to examine the maximum saving theoretically possible. For example one simulation will set the roof insulation to a very large number
 to while keeping the rest of the building the same. This will show the maximum possible savings from roof insulation. We currents examine these
 measures as part of elimination. 
 ```json
[
    [':electrical_loads_scale', '0.0'],
    [':infiltration_scale', '0.0'],
    [':lights_scale', '0.0'],
    [':oa_scale', '0.0'],
    [':occupancy_loads_scale', '0.0'],
    [':ext_wall_cond', '0.01'],
    [':ext_roof_cond', '0.01'],
    [':ground_floor_cond', '0.01'],
    [':ground_wall_cond', '0.01'],
    [':fixed_window_cond', '0.01'],
    [':fixed_wind_solar_trans', '0.01']
]
```
To run an elimination analysis, you can review the examples/elimination folder and yml file as a starting point. You run the analysis in the same manner 
as the parametric analysis. The key difference is the :analysis_configuration->:algorithm->:type is set to 
'elimination'. Note: It will use the first value in each measure in the YML file as the basecase..so you can customized the 
basecase to something other than 'NECB_Default' if you wish. 

## Sensitivity Analysis
BTAP allows you to quickly perform an sensitivity analysis on all the measures available. It will go through each measure value
and change only those values, this effectively creates a sensitivity run for each measure. 

To run an elimination analysis, you can review the examples/elimination folder. You run the analysis in the same manner 
as the parametric analysis. The key difference is the :analysis_configuration->:algorithm->:type is set to 'sensitivity'.

## Latin Hypercube Sampling (LHS)
There are times that a sampling of the solution space is required to inform machine learning algorithms. BTAPBatch 
supports the [Scipy implementation](https://scikit-optimize.github.io/stable/auto_examples/sampler/initial-sampling-method.html).

Examine the example folder to see the input.yml configuration format. 

## Custom OSM file. 
There are some instances where we would like to perform an analysis on an osm file not in the default btap library. In 
these situations you can load a local file to the analysis. You simple add the osm file(s) that you wish to examine in 
the same folder as the py and yml file. Then you can use the custom osm file by identifying it in the
 :building_options->:building_type field in the yml file. Note to not add the .osm to the building type name. See the 
example in examples/custom_osm where we have added test1 and test2 osm file. 

## Creating your Own Model
You can create a custom osm file by using SketchUp 2021 with the OpenStudio Plugin. 
### Geometry
You can view the intructional videos on how to create geometric models using SketchUp and the OpenStudio plug-in. 
Here is a video to perform takeoffs from a DWG file. You can also import PDF files and do the same procedure. 
[NREL Take-Off Video Part 1](https://www.youtube.com/watch?v=T41MXqlvp0E)

Do not bother to add windows or doors. BTAP will automatically add these to the model based on the vintage template or the inputs in
the BTAPBatch input yml file. 

### Zone Multipliers
BTAP supports use of multipliers vertically (i.e by floor). This will help reduce the runtime of the simulation. Please 
do not use horizontal zone multipliers as this will not work with btap's costing algorithms.  

### Space Types
Space types must be defined as NECB 2011 spacetypes. BTAP will map these to the template you select in the btap_batch 
analysis file. You can find the osm library file of the NECB spacetypes in the resources/space_type_library folder that
 you can import and use in defining the spacetypes in your model. 

### Number of Floors
BTAP needs to know the number of above and below ground floors. This cannot be interpreted accurately from the geometry
 for all building types, for example split level models. To identify this, open the 
 OSM file and find the 'OS:Building' object and add the correct values to  'Standards Number of Stories' and 
 'Standards Number of Above Ground Stories'. To be clear, 'Standards Number of Stories' is the total number of 
 stories in the model including basement levels. 
 
 ### Building Type
 Please add a standards building type name to the osm file's OS:Building object.  You can choose one of the name of the 16 building types.
 
## Output
When the analysis is finished, you can review the output.xlxs file that is created in the output folder in 
the analysis directory. It will contain all the high level information for each simulation as well as a link to the 
simulation folder where energyplus ran if you want the raw results. The IDP workflow creates a special summary output.xlsx 
for all the elimination, sensitivity and optimization runs in the same folder and the yml input file. 

## Monitoring the Analysis
While the program will output items to the console, there are a few other ways to monitor the results if you wish. The high level output is contained in the results/database folder. Failures are collected in the results/failures folder.  


### Amazon Web Services
If you are running on aws-batch. You can monitor the simulation in the AWS Batch Dashboard and the compute resources 
being used in the EC2 dashboard. 

## Developers
Note that all of these cli commands are available in ./src/btap/cli_helper_methods.py. You can use these to chain programmatically run analyses from Python itself.


## Troubleshooting
**Problem**: Analysis seem to fail with errors creating the database server or out of space / cannot write errors.

**Solution**: Sometimes docker fills either it hard disk or your system hard disk. You can check how much docker is using with this command. 
```
docker system df
```

This will produce an output that will show how full your system is. 

```
TYPE            TOTAL     ACTIVE    SIZE      RECLAIMABLE
Images          3         0         13.51GB   13.51GB (100%)
Containers      0         0         0B        0B
Local Volumes   4         0         624MB     624MB (100%)
Build Cache     0         0         0B        0B
```

You can remove the images, containers and volumes all at once with the following command. Warning! This will delete all your containers from your system. Make sure you have backed up any work to a safe location.  See [docker documentation on this](https://docs.docker.com/engine/reference/commandline/system_prune/) for more information. 
```
docker system prune -a -f --volumes
```


## Troubleshooting
**Problem**: Analysis seem to be very slow locally. Takes literally hours to run simple simulations

**Solution**: If you are using WSL in your docker setttings. You may get a performance boost by not using WSL. Go into your Docker
settings and under "General" tab, deselect the "Use the WSL2 based engine" This will force Docker to use the Hyper-V engine.  Then go to the "Resources" tab and allocate
 80% of your computers total processor capacity. The processor capacity if the number of cpu cores you have x2. 
 Similarly devote 50-80% of your Memory, keep 2GB of swap and whatever disk image size you can spare from your disk storage.. I would recommend at least 200GB. 
 Apply and restart. You may have to reboot your computer and launch Docker Desktop as soon as you log in to windows. 

**Problem**: Certificate issues

**Solution**: To fix certificate issues when using AWS from a computer at work do the following: 
* Put an proper certificate somewhere on your system. 
* Look for your AWS 'config' file (the path should be something 'C:\Users\ckirney\.aws\c') 
* Edit the 'config' file with a text editor. 
* Add "ca_bundle = <path to your certificate>" to the end of the 'config' file (e.g. on my computer I added "ca_bundle = C:\Users\ckirney\py_cert\nrcan+azure+amazon.cer") and save the changes.
* if you are on the NRCan network you can point to this file in your config folder.
```
 \\s0-ott-nas1\CETC-CTEC\BET\windows_certs\nrcan_azure_amazon.cer . 
```



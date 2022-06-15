# eSim 2022
For those attending the eSim 2022 workshop on BTAP I have a few additional instructions in addition to those below for hardware, software and getting started. These are not mandatory but will let you take part in some of the exercises. Although OpenStudio-3.2.1 and the OpenStudioApp-1.2.1 are listed as optional in the requirements section below, they will be used for the exercises. In addition, attached are some files that we will be using.

# BTAP Batch
BTAP Batch allows you to run paramteric and optimization analysis on your local machine and on the Amazon Cloud. You can
select the parameters you wish to analyse by modifying an input .yml file, and run the simulation.  BTAP_BATCH will produce the 
simulation outputs files for each simulation as well as a high level data summary excel file of all the design options.  

## Background
BTAP is the Building Technology Assesement Platform developed by Natural Resources Canada's research arm CanmetENERGY. It is developed upon the OpenStudio/EnergyPlus open-source framework created by the US DOE and the US National Renewable Energy Laboratory. 
BTAP can create standard reference building energy models of various vintages quickly for any location in Canada and perform energy efficiency scenario analysis for many building improvement measures such and insulation, windows, and mechanical systems. With its built in costing algorithm, it can perform limited cost-comparison of design scenarios. 
BTAP leverages data-driven methodology expert system rulesets that adhear to the National Energy Code for buildings as it basis. If it is in the code, it is implmented as accurately as possible. 
The most common used cases for BTAP is to:
* examine the cost effective performance of codes and standards across Canada.
* examine design pathways to Net-Zero Buildings.

BTAP almost exclusively runs on the cloud. There are options ways to run it locally on Linux and Windows systems and via command line. If you are interested in this approach please contact phylroy.lopez@nrcan-rncan.gc.ca .  

### Vintage Supported
The project currently supports the following vintages for both code rulesets and incremental costing of utility costs and incremental capital costs.  
* NECB2011
* NECB2015
* NECB2017

Note: Work is underway under the General Infrastructure PERD project to add older vintages to the ruleset library. Please contact chris.kirney@nrcan-rncan.gc.ca for more details on this initiative. 

### Commercial Building Geometries
BTAP comes with the standard geometries built-in commercial building spacetype geometric models. The are based on the U.S. DOE reference building archetypes, but gutted of everything except the geometry and space type information. You can find a list of the buildings [here](./docs/BtapBuildingGeometryLibrary.md)
You can also create your own buildings using the OpenStudio SketchUp Plug-in included in the OpenStudio Installation. Other tools support conversion to an openstudio model including Revit, and eQuest. More information on creating your model is kept [here](todo)
 
### Costed Cities Supported. 
We use a third party resource to cost aspects of the models that BTAP generates. The cities that are supported are listed [here](./docs/CostingSupportedCities.md).
If another weather file is selected that is not on this list, BTAP will try to select a city closest to the list below to use for costing. The latitude and longitudes included in the table are used to calculate this. This may produce unexpected results if not aware. 

### Utility Cost Support
BTAP supports the National Energy Board Utility rates. These are averaged costs per GJ and do not have block or tiered surcharges. BTAP does support block rate structure, however this is advanced and we recommend using NREL's tariff measure that can be found [here](https://bcl.nrel.gov/node/82923] 

### Capital Cost Support
BTAP will automatically cost materials, equipment and labour. BTAP Costing will only cost items that have energy impact. It will for example cost the wall construction layers, but not the structural components. 
Some items that BTAP costs are:
* Labour, Overhead
* Layer Materials in Constructions and fenestration.
* Piping, Ductworks, Headers based on actual geometry of the building. This is required when evaluating forces air vs hydronic solutions. 
* Standard HVAC Equipment, Boilers, Chillers, HeatPumps, Service Hot Water. 

Some examples of items it will not cost are:
* Internal walls, doors, toilets, structural beams, furniture, etc.   

It will also only cost what is contained with the btap standard measures. For example if you add a measure to add overhangs into the BTAP workflow. It will not cost it. BTAP uses internal naming conventions to cost items and make decisions on how components are costed. This does not mean you cannot use other measures created by other authors on [NREL's Building Component Library](https://bcl.nrel.gov/). It just means it will not be costed. 
 

## Why BTAP Batch?
BTAP Batch simplifies the process to run parametric and optimization runs. It uses code directly from 
openstudio-standards and requires no PAT measures. It takes advantage of all the costing and energy conservation development work
that CanmetEnergy-Ottawa has developed to date. 

BTAP_Batch also supports doing analysis from different branches of the btap_costing and NREL's OpenStudio Standards projects. This 
was very difficult to do with NREL's PAT interface.

Using AWS batch also reduces the cost of simulations and enables researchers to use AWS dashboards to monitor the simulation runs. BTAP_BATCH
takes advantage of Amazons cost-effective batch queue system to complete simulations. 
 
# Costing: btap_private_cli vs btap_public_cli engines
BTAP provide costing for baseline and ecm design scenarios. The cost is unlike most tools where a simple cost-per-area is 
applied. BTAP take into account the geometry of the buiding, and the occupancy type, and sized to adjust cost for piping, 
size of ductwork, wiring and other impacts that are critical to costing estimates. Cost is done with help of commercial third
party data, as such is only contained in the 'btap_private_cli' image_name. To utilize this feature you must have a licence 
from NRCan's IP office. We will then grant access to you via your github account. 

The non-cost version that is freely available called 'btap_public_cli' is available by changing the :image_name field in the input yml
file. You will still need a github token set up on your system to run the analysis. This accesses NREL's Openstudio 
Standards repository that contains the code for most North American building standards including Canada's NECB, as well 
as an array of energy conservation measures. 
 
## Requirements
* Windows 10 Professional version 1909 or greater (As a  workaround. if you are using 1709, make sure your git repository is cloned into C:/users/your-user-name/btap_batch) Performance however will not be optimal and will not use all available ram. 
* [Docker](https://docs.docker.com/docker-for-windows/install/) running on your computer.
* A python **miniconda** environment [3.8](https://docs.conda.io/en/latest/miniconda.html). use Windows installers.
* A git [client](https://git-scm.com/downloads)
* A high speed internet connection.
* A github account and [git-token](https://docs.github.com/en/github/authenticating-to-github/creating-a-personal-access-token)
* Add the github token as a user windows/linux environment variable as GIT_API_TOKEN
* If you would like to use costing and have an RSMeans account contact chris.kirney@nrcan-rncan.gc.ca for permissions to access canmet-energy repositories (For use of the btap_private_cli costing image.)
* For AWS runs: [AWS CLI on Windows, install the AWS CLI version 2 on Windows](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2-windows.html).
* If you are an NRCan employee: [NRCan btap_dev AWS account credentials set up on your computer](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html) for Amazon HPC runs(Optional). 
* At least 8GB+ ram with 4 or more cores (8+ threads). Preferably a powerful multi-core computer to run simulations fast locally. (24 core/48 thread with 32GB+)
* [OpenStudio 3.2.1](https://github.com/NREL/OpenStudio/releases/tag/v3.2.1) (optional) Required to use the OpenStudio App and the SketchUp plugin.
* [OpenStudio App 1.2.1](https://github.com/openstudiocoalition/OpenStudioApplication/releases/tag/v1.2.1) (optional) To view BTAP models and to create custom geometry models (must have OpenStudio v3.2.1 installed first).
* [SketchUp 2021](https://help.sketchup.com/en/downloading-older-versions) (optional) To view BTAP models and create custom geometry models in SketchUp.
* [OpenStudio SketchUp Plugin 1.2.1](https://github.com/openstudiocoalition/openstudio-sketchup-plugin/releases/tag/v1.2.1) (optional) To modify OpenStudio models in SketchUp.

## Test Requirements are Met
### Miniconda
Open Windows Start->Anaconda3-Anaconda Prompt(Miniconda)
### Git
Execute the following command. This should produce a version number for git if it is installed correctly.
```
git --version
```
### Docker
Ensure Docker for Windows Desktop is running (Windows Start->Docker Desktop) You should have a docker icon then running in your system tray. You will need to ensure that this is running for any btap analysis. This command will test if it is working properly.
```
docker run hello-world
```
If you get a permission denied error to you will need to [add your windows user account to the docker-group](https://docs.microsoft.com/en-us/visualstudio/containers/troubleshooting-docker-errors?view=vs-2019#docker-users-group). You will require admin priviliges to do this. 

## Configuration
1. Open a miniconda prompt (Start->Anaconda3(64-bit)->Anaconda Prompt) Not Powershell!

2. Clone this repository to your computer and change into the project folder using windows powershell.
```
git clone https://github.com/canmet-energy/btap_batch
cd btap_batch
```
3. Set up your conda/python environment 'btap_batch'. This will download all required packages to your system.  
For those familiar with Ruby, this is similar to a Gemfile vendor/bundle environment. You can do this by running 
the .bat file below
```
conda env create --prefix ./env --file environment.yml
```
4. Activate your conda environment. It should give you the command after step 3.. Should look like this.  
```
conda activate <path_to_your_environment>
```



## QuickStart Command Line 
### Parametric Analysis Local Machine
1. To run a parametric analysis, go to the example.yml analysis file in the 'examples/parametric' folder. Each 
parameter is explained in that file. Ensure that parametric analysis is a reasonable size for your system (i.e. Do not 
run millions of simulations on your 2 core laptop). Ensure that the ':compute_environment' variable is set to local.  
2. Run the example.py file from the root of the btap_batch project folder. On Windows you will need to set the 
PYTHONPATH to that folder. Please ensure that the btap_batch environment is active. 
```
set PYTHONPATH=%cd% && python examples\parametric\run.py
```
3. Simulation should start to run. A folder will be created in parametric folder with the variable name you set 
':analysis_name' in the yml file. It will create a unique folder under this based on a random UUID for this analysis. In 
that folder you will see two folders, 'input' and 'output'. 

### Output
* The input folder contains folders with uuids for all the simulations that you are running. It contains the 
run_options.yml file. This contains the selections created for that particular run. 

* The output folder contains full output runs for all the local simulation. This also contains the output.xlsx file 
with high level information from all the simulations. 

## Using Amazon AWS for analysis
1. Ensure you are not connected to a VPN and do not connect while running simulations.
2. Change ':compute_environment' to aws_batch (note that ':compute_environment' is in example.yml analysis file in the 'example' folder).
3. Update your AWS credentials to ensure it is up to date through your AWS Account -> btap-dev -> Command line and programmatic Access. Copy the Text in 'Option 2'.
4. Use your updated AWS credentials in '.aws/credentials' file in your user folder.
*Note*:  Navigate to '.aws' folder in your user folder using windows powershell. Run the command: ```$ aws configure```. Set the default region name to ca-central-1, and output format to json. Then, open the generated credentials file in '.aws' folder in your user folder. Use your updated AWS credentials in the credentials file. Replace the first line that looks something like this [834599497928_PowerUser] to [default] and save the file.
5. Run the example.py file from the root of the btap_batch project folder. On Windows you will need to set the 
PYTHONPATH to that folder. Please ensure that the btap_batch environment is active. 
```
set PYTHONPATH=%cd% && python examples\parametric\parametric.py
```

The output of the runs is not stored all locally, but on the S3 Bucket,  the ':analysis_name' you chose and the analysis_id 
generated by the script. For example, if you ran the analysis with the analysis_name: set to 'example_analysis', the default 
:s3_bucket is '834599497928' for the 'btap_dev' account, and your aws username is 'phylroy.lopez'. The runs would be kept on S3 in a path like
```
s3://<:s3_bucket_name>/<your_user_name>/<:analysis_name>/<:analysis_id>/
```
*Note*: This script will not delete anything from S3. So you must delete your S3 folders yourself.

The excel output will be saved on your local machine in the output folder for the run. 

6. Run the command 'docker kill btap_postgres' when you are done with your analysis. If btap_batch crashed or 
:kill_database was set to false. The database may still be running on your local system. Just in case, execute this command. 


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

For more details on the nsga algorithm please visit the pymoo website. 

To run the optimization, follow the steps explained above under 'Parametric Analysis Local Machine'or 'Parametric AWS' depending on whether you run locally or on cloud, except for Step 5 for which, run the below file:
```
set PYTHONPATH=%cd% && python examples\optimization\run.py
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
supports the 
[Scipy implementation](https://scikit-optimize.github.io/stable/auto_examples/sampler/initial-sampling-method.html) the
 parameters required for LHS are: 
 * :analysis_configuration->:algorithm->:type is 'sampling-lhs'
 * :analysis_configuration->:algorithm->:n_samples: is the total number of samples. 
 * :analysis_configuration->:algorithm->:lhs_type is can be 'classic', 'centered','maximin', 'correlation','ratio'.
 * :analysis_configuration->:algorithm->:random_seed can in any integer. Used to have consistent random numbers. 
 
 The analysis will use all local cpu cores or any AWS batch resources available to run. 

## Custom OSM file. 
There are some instances where we would like to perform an analysis on an osm file not in the default btap library. In 
these situations you can load a local file to the analysis. You simple add the osm file(s) that you wish to examine in 
the same folder as the py and yml file. Then you can use the custom osm file by identifying it in the
 :building_options->:building_type field in the yml file. Note to not add the .osm to the building type name. See the 
example in examples/custom_osm where we have added test1 and test2 osm file. 


## IDP Workflow
NREL's [A Handbook for Planning and Conducting Charrettes](https://www.nrel.gov/docs/fy09osti/44051.pdf) details an 
approach to model buildings to support design charettes and integrated design process. Appendix G of the document details 
the need for elimination, and sensitivity analysis as part of the modelling process. BTAP batch IDP wrokflow automates a 
portion of that analysis for early design support by automating the runs for these analysis and provide results. These outputs
may help validate the initial baseline model and help determine which energy conservation measures to consider.

## Create Custom OSM File
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


# Development Notes

## How to update outputs from btap_data.json to btap_batch. 
BTAPBatch will complain if it see data in btap_data.json it does not recognize. Please follow the below steps when adding 
information to btap_data.json top level. Tables in btap_data.json are ignored by BTAPBatch at the moment. 
1.	Add columns to the sql database schema with the input argument name for each argument in 'src/btap_batch.py'. Note the convention to have a ':' for input variables. They should be all "TEXT" type.
2.	Update the example input files of 'examples/multi_analyses/options.yml' and 'examples/parametric/example.yml' to include the new input arguments. 
3.	Run the btap_batch tests. This will run both locally and on AWS. To run only locally or on AWS, comment the appropriate line under the 'compute_environment' loop in the test file of 'src/test/test_btap_batch.py'.

## Testing
Please run the test in btap_batch\src\test\test_btap_batch.py to ensure the code functions as expected after any development.
You can adjust the parameters in the test if you wish to examine other scenarios. 

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
**Problem**: Analysis seem to be very slow locally. Takes literaly hours to run simple simulations

**Solution**: If you are using WSL in your docker setttings. You may get a performance boost by not using WSL. Go into your Docker
settings and under "General" tab, deselect the "Use the WSL2 based engine" This will force Dockder to use the Hyper-V engine.  Then go to the "Resources" tab and allocate
 80% of your computers total processor capacity. The processor capacity if the number of cpu cores you have x2. 
 Similarly devote 50-80% of your Memory, keep 2GB of swap and whatever disk image size you can spare from your disk storage.. I would recommend at least 200GB. 
 Apply and restart. You may have to reboot your computer and lauch Docker Desktop as soon as you log in to windows. 
```

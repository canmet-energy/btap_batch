# BTAP Batch
BTAP Batch allows you to run paramteric and optimization analysis on your local machine and on the Amazon Cloud. You can
select the parameters you wish to analyse by modifying an input .yml file, and run the simulation.  BTAP_BATCH will produce the 
simulation outputs files for each simulation as well as a high level data summary excel file of all the design options.  

## Why BTAP Batch?
BTAP Batch simplifies the process to run parametric and optimization runs. It uses code directly from 
openstudio-standards and requires no PAT measures. It takes advantage of all the costing and energy conservation development work
that CanmetEnergy-Ottawa has developed to date. 

BTAP_Batch also supports doing analysis from different branches of the btap_costing and NREL's OpenStudio Standards projects. This 
was very difficult to do with NREL's PAT interface.

Using AWS batch also reduces the cost of simulations and enables researchers to use AWS dashboards to monitor the simulation runs. BTAP_BATCH
takes advantage of Amazons cost-effective batch queue system to complete simulations. 
 
## Requirements
* Windows 10 Professional version 1909 or greater (As a  workaround. if you are using 1709, make sure your git repository is cloned into C:/users/your-user-name/btap_batch) Performance however will not be optimal and will not use all available ram. 
* [Docker](https://docs.docker.com/docker-for-windows/install/) running on your computer.
* A python **miniconda** environment [3.8](https://docs.conda.io/en/latest/miniconda.html). use Windows installers.
* A git [client](https://git-scm.com/downloads)
* A high speed internet connection.
* A github account and [git-token](https://docs.github.com/en/github/authenticating-to-github/creating-a-personal-access-token)
* Add the github token as a user windows/linux environment variable as GIT_API_TOKEN
* Permissions to access canmet-energy repositories from phylroy.lopez@canada.ca
* [AWS CLI on Windows, install the AWS CLI version 2 on Windows](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2-windows.html).
* [NRCan btap_dev AWS account credentials set up on your computer](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html) for Amazon HPC runs. 


## Configuration
1. Open a miniconda prompt (Start->Anaconda3(64-bit)->Anaconda Prompt) Not Powershell!

2. Clone this repository to your computer and change into the project folder using windows powershell.
```
git clone https://github.com/canmet-energy/btap_batch
cd btap_batch
```
3. Set up your conda/python environment 'btap_batch'. This will download all required packages to your system.  
For those familiar with Ruby, this is similar to a Gemfile/Bundle environment. 
```
conda env create -f environment.yml
```
4. Activate your conda environment. 
```
conda activate btap_batch
```

## QuickStart Command Line 
### Parametric Analysis Local Machine
1. To run a parametric analysis, go to the example.yml analysis file in the 'examples/parametric' folder. Each 
parameter is explained in that file. Ensure that parametric analysis is a reasonable size for your system (i.e. Do not 
run millions of simulations on your 2 core laptop). Ensure that the ':compute_environment' variable is set to local.  
2. Run the example.py file from the root of the btap_batch project folder. On Windows you will need to set the 
PYTHONPATH to that folder. Please ensure that the btap_batch environment is active. 
```
set PYTHONPATH=%cd% && python examples\parametric\parametric.py
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
set PYTHONPATH=%cd% && python examples\optimization\optimization.py
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

The custom osm file must be defined using NECB2011 spacetypes. 


## Monitoring the Analysis
While the program will output items to the console, there are a few other ways to monitor the results if you wish 

### PostGreSQL 
While the simulations are running, you have access to the postgres database. Note that this database will abruptly shutdown when 
the simulations are complete by design. You can use database viewers like DBeaver or pgAdmin. The username and password for the 
database is 'docker'. You can also optionally build a viewer via a Jupyter Note using python's SQLAlchemy library with postgresql. 

### Amazon Web Services
If you are running on aws-batch. You can monitor the simulation in the AWS Batch Dashboard and the compute resources 
being used in the EC2 dashboard. 

### PowerBI / Tableau
Through the postgresSQL server you can connect and update live data using either of these tools. 

# Development Notes

## How to update outputs from btap_data.json to btap_batch. 
BTAPBatch will complain if it see data in btap_data.json it does not recognize. Please follow the below steps when adding 
information to btap_data.json top level. Tables in btap_data.json are ignored by BTAPBatch at the moment. 
1.	Add columns to the sql database schema with the input argument name for each argument in 'src/btap_batch.py'. Note the convention to have a ':' for input variables. They should be all "TEXT" type.
2.	Update the example input files of 'examples/multi_analyses/options.yml' and 'examples/parametric/example.yml' to include the new input arguments. 
3.	Run the btap_batch tests. This will run both locally and on AWS. To run only locally or on AWS, comment the appropriate line under the 'compute_environment' loop in the test file of 'src/test/test_btap_batch.py'.

## Testing
Please run the test in btap_batch\src\test\test_btap_batch.py to ensure the code functions as expected after any development.
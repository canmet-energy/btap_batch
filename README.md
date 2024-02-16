# BTAP

## Background
BTAP allows you to quickly generate archetype buildings based on Canadian codes and data and apply common energy conservation measures to explore possible technology packages. BTAP calculates energy, NECB Tier performance,  operational carbon and relative capital costs for all scenarios where possible. 

The most common used cases for BTAP is to:
* examine the performance of the National Energy Code for buildings
* examine design pathways to high performance buildings.
* aid the development of machine learning models.

BTAP Data can be used to generate dashboards. For example [dashboard](https://public.tableau.com/app/profile/sara.gilani/viz/Solutions_NPV_PercentBetter/DB_Solutions_NPV_PercentBetter) was developed doing a series of BTAP Batch analyses.
![image info](docs/images/solutions_npv_percentbetter.png)

## Costing
BTAP will automatically cost materials, equipment and labour. BTAP Costing will only cost items that have energy impact. It will for example cost the wall construction layers, but not the structural components. 
Some items that BTAP costs are:
* Labour, Overhead
* Layer Materials in Constructions and fenestration.
* Piping, Ductworks, Headers based on actual geometry of the building. This is required when evaluating forces air vs hydronic solutions. 
* Standard HVAC Equipment, Boilers, Chillers, HeatPumps, Service Hot Water. 

Some examples of items it will not cost are:
* Internal walls, doors, toilets, structural beams, furniture, etc.   

For costing, BTAP uses the National Energy Board Utility [rates](resources/ceb_fuel_end_use_prices.csv). These are averaged costs per GJ and do not have block or tiered surcharges. Equipment and materials costing requires a licence for RSMeans. Please contact RSMeans for a licence if you wish to use their data. We are currently using RSMean 2020 data in btap. 

## Requirements
Software requirements for running btap_batch can be found [here](docs/requirements.md)

## Download/Update Source Code and Python Packages
Instructions for downloading btap_batch from github and installing supporting Python packages are [here](docs/download.md)

## Configuring BTAP Batch
Instructions for configuring your btap_batch and creating a build environment can be found [here](docs/configure.md)



## Analysis Workflow Examples
 * [Parametric](docs/parametric.md): Run all possible combinations in input file.
 * [Optimization](docs/optimization.md): Run a genetic optimization for a fixed number of runs and generations based.  
 * [Elimination](docs/elimination.md): Examine theoretical maximum energy savings from each domain for a given model. 
 * [Sensitivity](docs/sensitivity.md): Examine the energy and cost effect from each measure selected. (~100 measures) 
 * [Latin-Hypercube-Sampling](docs/latin_hypercube_sampling.md): Sample the solution space with a given number of simulations
 * [Packages](docs/packages.md): When you wish to simply run a set of packages solution sets for comparison.


## Monitoring the Analysis

### Local
While the program will output items to the console, there are a few other ways to monitor the results if you wish. The high level output is contained in the results/database folder. Failures are collected in the results/failures folder.  

### AWS
If you are running on aws. You can monitor the simulation in the AWS Batch Dashboard and the compute resources 
being used in the EC2 dashboard. 

# Troubleshooting / FAQ
 [Troubleshooting/FAQ](docs/troubleshooting.md)

# Known Issues
[Issues](docs/known_issues.md)




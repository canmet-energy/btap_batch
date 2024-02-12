# BTAP

## Background
BTAP allows you to quickly generate archetype buildings based on Canadian codes and data and apply common energy conservation measures to explore possible technology packages. BTAP calculates energy, NECB Tier performance,  operational carbon and relative capital costs for all scenarios where possible. 

The most common used cases for BTAP is to:
* examine the cost-effective performance of codes and standards across Canada.
* examine design pathways to high performance buildings.
* aid the development of machine learning models.

# Costing
BTAP will automatically cost materials, equipment and labour. BTAP Costing will only cost items that have energy impact. It will for example cost the wall construction layers, but not the structural components. 
Some items that BTAP costs are:
* Labour, Overhead
* Layer Materials in Constructions and fenestration.
* Piping, Ductworks, Headers based on actual geometry of the building. This is required when evaluating forces air vs hydronic solutions. 
* Standard HVAC Equipment, Boilers, Chillers, HeatPumps, Service Hot Water. 

Some examples of items it will not cost are:
* Internal walls, doors, toilets, structural beams, furniture, etc.   

For costing, BTAP uses the National Energy Board Utility rates. These are averaged costs per GJ and do not have block or tiered surcharges. Equipment and materials costing requires a licence for RSMeans. Please contact RSMeans for a licence if you wish to use their data. We are currently using RSMean 2020 data in btap. 


# Requirements
Software requirements for running btap_batch can be found [here](docs/requirements.md)

# Configuring your Computer
Instructions for configuring your computer and creating a build environment can be found [here](docs/configure.md)

# Geometry Library
BTAP contains a library of building geometries. You can review the list of the geometries [here](docs/geometry_library.md)

# Custom Geometry
There are times that the library will not suffice, and you will require a custom geometry. Guidelines for creating custom geometries are [here](docs/custom_osm.md)

# Analysis Workflow Examples
 * [Parametric](docs/parametric.md): Run all possible combinations in input file.
 * [Optimization](docs/optimization.md): Run a genetic optimization for a fixed number of runs and generations based.  
 * [Elimination](docs/elimination.md): Examine theoretical maximum energy savings from each domain for a given model. 
 * [Sensitivity](docs/sensitivity.md): Examine the energy and cost effect from each measure selected. (~100 measures) 
 * [Latin-Hypercube-Sampling](docs/latin_hypercube_sampling.md): Sample the solution space with a given number of simulations
 * [Packages](docs/packages.md): When you wish to simply run a set of packages solution sets for comparison.


# Monitoring the Analysis

## Local
While the program will output items to the console, there are a few other ways to monitor the results if you wish. The high level output is contained in the results/database folder. Failures are collected in the results/failures folder.  

## AWS
If you are running on aws. You can monitor the simulation in the AWS Batch Dashboard and the compute resources 
being used in the EC2 dashboard. 


[Troubleshooting Problems](docs/troubleshooting.md)



# Costing 
This section explains how costing is used in btap_batch.

There are two files included in the btap_batch repository which describe costing. One is [costs.csv](../resources/costing/costs.csv), and the other is [costs_local_factors.csv](../resources/costing/costs_local_factors.csv). They are described below. Note that all of the costs and local factors inculded in this repository are test values only and do not represent actual costs. You are resoponisble for modifying the files yourself to inculde your own costs either from a commercial costing service or by supplying your own estimated costs.

## [costs.csv](../resources/costing/costs.csv)  

This file includes the costs for individual items used by BTAP to calculate costs.  Each item has three costs associated with it:  materialOpCost, laborOpCost, and equipmentOpCost.  The materialOpCost describes the cost of the item itself.  For example, the cost for item id 170468, "Elbow, 90 Deg., steel, malleable iron, black, straight, threaded, 150 lb., 1/2"" is $4.84. That means that the cost to purchase that item is $4.84. The laborOptCost is the cost associated with installation. Again, using the cost for item id 170468, we estimate it costs $52.45 for someone to install the item in a building. Finally, the equipmentOpCost is the cost associated with any additional services required as part of the installation. An example would be the costs associated with using a crane, or other piece of equipment, to install the item. Most items do not inculde equiemntOpCost.

When updating the costs.csv file with your own costing information, look for the id of the item in the costing files [here](https://github.com/NREL/openstudio-standards/tree/nrcan/lib/openstudio-standards/btap/costing/common_resources) to determine the units the costs are in. For the example above, the cost is for each item. However, for some itmes the costs are per linear foot, or 100 linear feet (if no unit is provided then assume it is for each item).

If you are getting your costs from a commercial costing database such as RSMeans, then look up the item based on the description and inculde the costs for that item in the costs.csv file.

## [costs_local_factors.csv](../resources/costing/costs_local_factors.csv)  

This file describes how to apply the costs to a given location. BTAP can apply costs in a couple of different ways. If you are doing an analysis on buildings in one location and have costs for specifically that location you can include those costs in the costs.csv file directly and ignore the costs_local_factors.csv file. However, if you have costs for locations across Canada then you can include average costs in the costs.csv file and then use the costs_local_factors.csv to localize those costs. For example, if you are looking at buildings in Moose Jaw, SK, Kinsgton, ON, and St. John, NB you could include an average Canadian cost in the costs.csv file. Then you could inculde factors in the cost_local_factors.csv file that will modify the average costs so that they estimate the costs you would find specifically in Moose Jaw, Kindston, and St. John.

The costs_local_factors.csv file inclues province_state, city, division, code_prefix, material, installation, and total columns. The "province_state" is the Province the localization factor is for. For Moose Jaw, this would be "SASKATCHEWAN". The "city" is the city the localization factor is for (e.g. "MOOSE JAW"). The "division" is a description of the cost category the localization factor is applied to. For example, item id 170468 is for pipe bends. These would be cosidered as part of the "FIRE SUPPRESSION, PLUMBING & HVAC" category. You can determine which category a cost belongs to based on the first two digits of its id. In the case of the pipe bend (id 170468) the first two digits of the id are 17. This the code_prefix in the costs_local_factors.csv file for the "FIRE SUPPRESSION, PLUMBING & HVAC" division. The next two columns are for the localization factors themselves. When using localization factors BTAP will take the cost from the cost.csv file and multiply by the cost localization factor in the costs_local_factors.csv file then divide the result by 100 (the localization factors are provided in %). The localization factors in the material column are applied to the materialOpCost in the costs.csv file. The localaization factors in the installation column are applied to the laborOpCost in the costs.csv file. The localization factoors in the total column are averages applied to the equipmentOpCost in the cost.csv file.

To illustrate how this would work in practice let us consider "Ground wire, copper wire, bare solid" (id 181719) in Moose Jaw, Kingston, and St. John. From the costs.csv file, the average material and labour costs associated with the wire (id 170468) are:

material: &nbsp;&nbsp;&nbsp;$4.84  
labor: &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;$209.50

Currently, of of the localization factors in the costs_local_factors.csv file are 100. This means that BTAP does not localize any of the costs in the costs.csv file (e.g. 100*cost/100 = cost). However, for the purposes of this example lets assume that we know how much more (or less expensive) the wire was in each location. Since the id for the item starts witch 18 we know this falls under the "ELECTRICAL, COMMUNICATIONS & UTIL." cost localization categary. For the three differt locations, we know we should modify the costs as follows:

#### MOOSE JAW, SASKATCHEWAN 

code_prefix: &nbsp;&nbsp;&nbsp;&nbsp;18  
material: &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;96.8  
installation: &nbsp;&nbsp;&nbsp;&nbsp;122.4  

#### KINGSTON, ONTARIO 

code_prefix: &nbsp;&nbsp;&nbsp;&nbsp;18  
material: &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;111.4  
installation: &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;98.8  

#### NEW BRUNSWICK, SAINT JOHN 

code_prefix: &nbsp;&nbsp;&nbsp;&nbsp;18  
material: &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;87.8  
installiton: &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;97.5  

When an analysis is done, when BTAP calculates the cost for the item, it will do the following:

#### MOOSE JAW, SASKATCHEWAN 
```
cost = (4.84*96.8 + 209.50*122.4)/100 = $128.63
```
#### KINGSTON, ONTARIO 
```
cost = (4.84*111.4 + 209.5*98.8)/100 = $120.20
```
#### NEW BRUNSWICK, SAINT JOHN 
```
cost = (4.84*87.8 + 209.5*97.5)/100 = $95.74
```
Some commercial costing databases (e.g. RSMeans) provide these localization factors. If you have localization factors for a place not in the costs_local_factors.csv file, you can simply add a new row and include the costs. Make sure that the province_state and city match what is in the .epw file and that you ensure you include the factors for each code prefix.

## Custom Costing File Locations 

The default locations for the costs.csv and cost_local_faactors.csv are inculded in the default build_environtment.yml file when it is created When initially configuring the [build environment](configure.md). They appear as:

```
local_costing_path: resources\costing\costs.csv
```

and

```
local_factors_path: resources\costing\costs_local_factors.csv
```

Both paths are relative to where btap_batch is installed. If you want to include your own costs you can either modify the above files, or incule the path to your own files containing the appropriate information on the correct format.

Note: &nbsp;&nbsp;If you are an NRCan employee, please contact the BTAP team for how to use NRCan costing information.
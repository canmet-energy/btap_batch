# Optimization 
To perform an optimization run you can review the example contained in **examples/optimization** folder. The input.yml file contains all the 
options for the optimization analysis. You must first customize that file to suit your analysis. 

# 0. Download and Configure BTAP
Ensure that you have [downloaded btap_batch and installed/updated python requirements](download.md) and [configured](configure.md) with the correct compute environment and branches.

# 1. Optimization Options
The input.yml file in the project folder contains the options for the selected analysis/algorithm type, the options hourly outputs and the building charecteristics that you wish to examine. 

Key aspects that must be set for optimization. The first is the optimization parameters. 

* ***algorithm_type***: must be set to 'nsga2' and will run the nsga2 as described in the [pymoo](https://pymoo.org/algorithms/moo/nsga2.html)
* ***reference_run***: If set to true, this will run the NECB reference building for the given template and fuel types. This will allow comparisons to the reference building to be included in the results.  
* ***algorithm_nsga_population***: This is population that is used in the NSGAII. Should be set to less than the number of threads/cores that you have available on your system.
* ***algorithm_nsga_n_generations***: This is the number of generation the algorithm will explore. 
* ***algorithm_nsga_prob***: Don't change this unless you understand the NSGA
* ***algorithm_nsga_eta***: Don't change this unless you understand the NSGA. 
* ***algorithm_nsga_minimize_objectives***: Contains a list of the outputs from btap that you would like to optimize to. Pro tip. Run a senstivity analysis and examine the output.xlsx in the results folder to find a outpum column you wish to minimize.

Here is a snippet of the example that runs a pop of 5 for 2 generations resulting in 10 simulations total and will minimize the total EUI and capital equipment cost. 

```yaml
:algorithm_type: nsga2 # This will run the nsgaII optimization algorithm
:reference_run: true # This will run the NECB reference building for the given template and fuel types.  If false 
:algorithm_nsga_population: 5
:algorithm_nsga_n_generations: 2
:algorithm_nsga_prob: 0.85 
:algorithm_nsga_eta: 3.0
:algorithm_nsga_minimize_objectives: 
    - energy_eui_total_gj_per_m_sq
    - cost_equipment_total_cost_per_m_sq
```

## 2. [Enable Hourly Output (optional)](hourly_outputs.md)

## 3. [Select Building Options](building_options.md)

## 4. [Run / Cancel the Analysis](run_cancel.md)

## 5. [Examine Output](output.md) 

## 6. Clean Up Todo

# Optimization 
An optimization analysis will conduction a series of simulations with the goal to minimize 1-2 outputs. For example you 
can try to minimize overall building capital costs and energy use intensity. 

To perform an optimization run you can review the example contained in **examples/optimization** project folder as a staring point. The input.yml file contains all the 
options for the optimization analysis. You must first customize that file to suit your analysis. 

# 0. Download and Configure BTAP
Before running btap_batch, ensure that you have [downloaded btap_batch and installed/updated python requirements](download.md) and [configured](configure.md) with the correct compute environment and branches.

Also ensure that you are in btap_batch folder. 

If you do not see the '(venv)' prefix in your command prompt. Something like this.  

```bash
(venv)C:\btap_batch> 
```

You are not in your python virtual environment (venv). You can fix this by running 

```bash
venv\Scripts\activate.bat
````


# 1. Configure Optimization Options
The input.yml is a file in the project folder that contains the options for the selected analysis/algorithm type, the options hourly outputs and the building charecteristics that you wish to examine. 

Key aspects that must be set for optimization. The first is the optimization parameters. 

* ***algorithm_type***: must be set to 'nsga2' and will run the nsga2 as described in the [pymoo](https://pymoo.org/algorithms/moo/nsga2.html)
* ***reference_run***: If set to true, this will run the NECB reference building for the given template and fuel types. This will allow comparisons to the reference building to be included in the results.  
* ***algorithm_nsga_population***: This is population that is used in the NSGAII. Should be set to less than the number of threads/cores that you have available on your system.
* ***algorithm_nsga_n_generations***: This is the number of generation the algorithm will explore. 
* ***algorithm_nsga_prob***: Don't change this unless you understand the NSGA
* ***algorithm_nsga_eta***: Don't change this unless you understand the NSGA. 
* ***algorithm_nsga_minimize_objectives***: Contains a list of the outputs from btap that you would like to optimize to. Pro tip. Run a senstivity analysis and examine the output.xlsx in the results folder to find a outpum column you wish to minimize.

Here is a snippet of the example that runs a pop of 5 for 2 generations resulting in 10 simulations total and will 
minimize the total EUI and capital equipment cost. This is just an example, normally you would run a population of 50 or 
more with 10 generations for a total of at least 500 runs. 

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

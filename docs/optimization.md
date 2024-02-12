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
python ./bin/btap_batch.py run-analysis-project --compute_environment <choose local or local_managed_aws_workers> --project_folder .\examples\optimization --reference_run
```

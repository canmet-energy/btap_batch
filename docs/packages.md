# Batch 
An batch analysis will simply run a set of building configuration files. 

To perform an batch run you can review the example contained in **examples/batch** project folder as a staring point. The input.yml file contains all the 
options for the batch analysis. You must first customize that file to suit your analysis. 

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

* ***algorithm_type***: must be set to 'batch' and will run the nsga2 as described in the [pymoo](https://pymoo.org/algorithms/moo/nsga2.html)
* ***reference_run***: If set to true. It will attempt to create the reference buildings and include necb reference comparison data in the output. 

The input.yml file is very paired down for this kind of analysis since it does not contain and building ```options```
information. 

```yaml
---
:analysis_name: batch_example
:algorithm_type: batch
:reference_run: False
:output_variables: []
:output_meters: []
```

## 2. [Enable Hourly Output (optional)](hourly_outputs.md)

## 3. Create Building Options Files.
You will need to create a separate ``run_options`` file for each scenario you wish to simulate. These must be contained 
in a subfolder of your project called ``run_options_folder``. Each file must contain valid selections to 
be able to run. It follows the same format as the [other analyses input.yml files](building_options.md), but contains only the 
``:options``  section. 


## 4. [Run / Cancel the Analysis](run_cancel.md)

## 5. [Examine Output](output.md) 

## 6. Clean Up Todo

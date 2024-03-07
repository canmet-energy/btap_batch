# Parametric analysis 
A paremetric analysis will run a full-factorial of all possible combinations indicated in the projects input.yml file. See 
[Select Building Options](building_options.md) below. 

To perform a parametric run you can review the example contained in **examples/parametric** project folder as a staring 
point. The input.yml file contains all the options for the parametric analysis. You must first customize that file to 
suit your analysis. 

Note: You can run astronomically large analyses depending on your selections. It is up to you to ensure that you do a 
reasonable amount of runs and manage and cost overruns on Amazon. You can spend a lot of money very fast with this 
algorithm. 

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


# 1. Configure Parametric Options
The input.yml is a file in the project folder that contains the options for the selected analysis/algorithm type, the 
options hourly outputs and the building characteristics that you wish to examine. 

To run this type of analysis,  set the ``:algorithm_type`` to 'parametric' in the input.yml file.

* ***algorithm_type***: must be set to 'parametric'
* ***reference_run***: If set to true, this will run the NECB reference building for the given template and fuel types. This will allow comparisons to the reference building to be included in the results.  

```yaml
:algorithm_type: parametric # This will run a parametric analysis
:reference_run: true # This will run the NECB reference building for the given template and fuel types.  If false
```

## 2. [Enable Hourly Output (optional)](hourly_outputs.md)

## 3. [Select Building Options](building_options.md)

## 4. [Run / Cancel the Analysis](run_cancel.md)

## 5. [Examine Output](output.md)
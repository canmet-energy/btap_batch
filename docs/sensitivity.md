# Sensitivity Analysis
BTAP allows you to quickly perform a sensitivity analysis on all the measures available. It will go through each measure value
and change only those values, this effectively creates a sensitivity run for the full selectec range of each measure.


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

# 1. Configure Sensitivity Options
The input.yml is a file in the project folder that contains the options for the selected analysis/algorithm type, the 
options hourly outputs and the building characteristics that you wish to examine. 

To run this type of analysis,  set the ``:algorithm_type`` to 'sensitivity' in the input.yml file.

**NOTE**: This analysis is different from all other analyses in the fact that the first item in each array of anything in 
the ':options' values would make of the baseline for which the analysis is done. 

```yaml
:algorithm_type: sensitivity # This will run a parametric analysis
:reference_run: false # The sensitivity analysis will use the first value of each measure as the baseline. So this is not necessary to be set to true. 
```

## 2. [Enable Hourly Output (optional)](hourly_outputs.md)

## 3. [Select Building Options](building_options.md)

## 4. [Run / Cancel the Analysis](run_cancel.md)

## 5. [Examine Output](output.md)
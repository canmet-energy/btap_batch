## Elimination Analysis
BTAP allows you to quickly perform an elimination analysis. This will set various aspects of the building to effectively
 'zero' to examine the maximum saving theoretically possible. For example one simulation will set the roof insulation to a very large number
 to while keeping the rest of the building the same. This will show the maximum possible savings from roof insulation. We currents examine these
 measures as part of elimination.  Each of the following scenarios will be run separately. 
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

# 0. Download and Configure BTAP
Before running btap_batch, ensure that you have 
[downloaded btap_batch and installed/updated python requirements](download.md) and [configured](configure.md) 
with the correct compute environment and branches.

Also ensure that you are in btap_batch folder. 

If you do not see the '(venv)' prefix in your command prompt. Something like this.  

```bash
(venv)C:\btap_batch> 
```

You are not in your python virtual environment (venv). You can fix this by running 

```bash
venv\Scripts\activate.bat
````


# 1. Configure Elimination Option

The input.yml is a file in the project folder that contains the options for the selected analysis/algorithm type, the 
options hourly outputs and the building characteristics that you wish to examine. 

To run this type of analysis,  set the ``:algorithm_type`` to 'elimination' in the input.yml file.

**NOTE**: This analysis is different from all other analyses in the fact that the first item in each array of anything in 
the ':options' values would make of the baseline for which the analysis is done. 

```yaml
:algorithm_type: elimination # This will run a parametric analysis
:reference_run: false # The elimination analysis will use the first value of each measure as the baseline. So this is not necessary to be set to true. 
```

## 2. [Enable Hourly Output (optional)](hourly_outputs.md)

## 3. [Select Building Options](building_options.md)

## 4. [Run / Cancel the Analysis](run_cancel.md)

## 5. [Examine Output](output.md)
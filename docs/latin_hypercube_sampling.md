## Latin Hypercube Sampling (LHS)
There are times that a sampling of the solution space is required to inform machine learning algorithms. BTAPBatch 
supports the [Scipy implementation](https://scikit-optimize.github.io/stable/auto_examples/sampler/initial-sampling-method.html).

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

To run this type of analysis,  set the ``:algorithm_type`` to 'sample-lhs' in the input.yml file.


```yaml
:algorithm_type: sampling-lhs
:algorithm_lhs_n_samples: 10
:algorithm_lhs_type: classic
:algorithm_lhs_random_seed: 1
:reference_run: true 
```

## 2. [Enable Hourly Output (optional)](hourly_outputs.md)

## 3. [Select Building Options](building_options.md)

## 4. [Run / Cancel the Analysis](run_cancel.md)

## 5. [Examine Output](output.md)

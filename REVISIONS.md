###2020-11-22: 1.0.005
* Removed Postgres Database. Now using just flatfiles to create output.xlsx
* Added pre-flight option to analysis. This will do a short check on the osm files and a single run to help error check files. 
* Added option to :run_reference simulations ahead of analysis. This is required for comparitive analysis like percent better than code information. Default is set to True. 
* AWSBatch now can be passed as an argument. This now allows the IDP and the test to run using a single AWS Batch instance.. saving 10m time for each subsequent run. 

###2020-06-09: 1.0.004
nrcan_prod branches:
* openstudio_standards revision = 04c220861664566800596666bb98699e4631a394
* btap_costing revision = 671ed2b9604f017ec67ac26de3f73ce86670f2e4
Features Added. 
* Changed ventilation rates to use ASHRAE 2001 version for NECB2011/15/17
* Added experimental support for upcoming NECB2020 added by NRC
* Added Hourly Output capabilities
* Added ability to use custom osm files 
* Added ability to do batch runs of standalone osm files.
* Added experimental support for OpenStudio 3.2.1
* Fixed SRR measure
* Updated HP measures
* Removed baseline comparison capability temporarily. Will return in next version where baselines will be automatically run for each analysis.

###2020-06-09: 1.0.003
nrcan_prod branches:
* openstudio_standards revision = 04c220861664566800596666bb98699e4631a394
* btap_costing revision = 106b02f43d5d76ca66546154cea3dce603e4b201
Features Added. 
* Added test to help test locally and on aws for various situations. testing is currently done manually. No CircleCI.
* Preliminary support for peak, PH, tedi and meui metrics.  New outputs include:
    * heating_peak_w_per_m_sq
    * cooling_peak_w_per_m_sq                  
    * bc_step_code_tedi_kwh_per_m_sq
    * bc_step_code_meui_kwh_per_m_sq
* added ability to do run with opensource aspect only. The new image_name btap_public_cli will run everything in standards
but will not run any costing. This is done using docker containers and git token authenication. 
* reorganized example to have a folder for each type. Elimination, Sensitivity and IDP have been created.
* Added latin hypercube sampling workflow similar to NREL's code. 
* updated the dashboard similar to NREL's code. 

###2020-02-23: 1.0.002
After comments from team yesterday added new features.
* Reduced DESIRED_AWS_VCPUS for aws_batch from 50 to the default (0). It will take slightly longer to ramp up the cluster. But will save money for smaller runs. 
* Added versioning. Now will output ':btap_batch_version' to indicate version of btap_batch used. 
* Added a tests in src/tests to test local/aws_batch parametric/optimization runs. You can use this to test your environment out to ensure things are working properly. 
* Simplified slightly btap_batch pathways viewer.. The metrics and the input xlsx file variables are both at the top of the file to make it easier to modify.
* Added feature to keep database running even after analysis is complete.. This allows users to use the SQL database for
post processing  / analysis if needed. You now should run 'docker kill postgres' after the analysis (step 6) , just in case it is still running.  
* Added examples/multi-analysis to examples, and renamed the original 'example' to 'parametric'  
* Default branches are now 'nrcan_prod' for os-standards and 'production' for btap_costing.
* A datapoint_output_url has been added to the database and excel output. This will link either to the local or s3 location of the simulation run.
* Kamel commented that more default output from the console would be informative to say what jobs have been submitted. This has been added.
* Add basecase comparisons. btap_batch now adds the following to the excel output as a post process. Baseline runs are contained 
in the src/resources folder and should be updated when costing/energy outputs have changed or cities have been expanded. Currently only the 7 climate
zone cities are supported.  
    * baseline_savings_energy_cost_per_m_sq: based on necb template chosen.	
    * baseline_difference_cost_equipment_total_cost_per_m_sq: based on necb template chosen.
    * baseline_simple_payback_years: based on necb template chosen.  (NPV to come in May.)
    * baseline_peak_electric_percent_better: based on necb template chosen.
    * baseline_energy_percent_better: based on necb template chosen.
    * baseline_necb_tier: based on necb template chosen. 'tier_1', 'tier_2', 'tier_3', 'tier_4' for 25%,50%,60%,60%+ better.
    Note: this tier is based on the original template selected..not always NECB2017. 
    * baseline_ghg_percent_better: based on necb template chosen.

###2020-02-19: 1.0.001
Initial commit supporting most ecms. Support running on local and AWS. Linux and Windows. 

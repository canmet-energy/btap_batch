# Sensitivity Analysis
BTAP allows you to quickly perform an sensitivity analysis on all the measures available. It will go through each measure value
and change only those values, this effectively creates a sensitivity run for each measure. 

To run an elimination analysis, you can review the examples/elimination folder. You run the analysis in the same manner 
as the parametric analysis. The key difference is the :analysis_configuration->:algorithm->:type is set to 'sensitivity'.

**NOTE**: Sensitivity is different from all other analyses in the fact that the first item in each array of anything in the ':options' values would make of the baseline for which the analysis is done. 


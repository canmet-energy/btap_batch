## Elimination Analysis
BTAP allows you to quickly perform an elimination analysis. This will set various aspects of the building to effectively
 'zero' to examine the maximum saving theoretically possible. For example one simulation will set the roof insulation to a very large number
 to while keeping the rest of the building the same. This will show the maximum possible savings from roof insulation. We currents examine these
 measures as part of elimination. 
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
To run an elimination analysis, you can review the examples/elimination folder and yml file as a starting point. You run the analysis in the same manner 
as the parametric analysis. The key difference is the :analysis_configuration->:algorithm->:type is set to 
'elimination'. Note: It will use the first value in each measure in the YML file as the basecase..so you can customized the 
basecase to something other than 'NECB_Default' if you wish. 

# Selecting Building Options

BTAP has a variety of measures to change the building charecteristics. You can view all the options available in the 
excel file located [here](../resources/BTAPOptions.xlsx)

One of the most important variables to assign is the **':template'** variable. This selects which references of the NECB to 
use. Subsequently, any variable that is assigned 'NECB_Default' will attempt to use what the NECB would use.
```yaml
  :building_type:
    - FullServiceRestaurant
    - HighriseApartment  
```

Please note that the context is important.  Having two building types makes perfect sense for a parametric or sample_lhs analysis.  
However for sensitvity and nsga2, it will not work as expected. If you minimize cost and energy. The optimizer will look 
for solutions for the FullSerivice restaurant and ignore the HighriseApartment as a solution since the restaurant will 
always be cheaper. Simlarly **epw_file** and **fdwr_set** are items you will not want more than one item for when using optimization. 


Here is a snippet of the input.yml file that will examine the NECB default as well as other conductance values for the 
exterior walls in the model. 
```yaml
  :ext_wall_cond:
  - NECB_Default
  - 0.314
  - 0.278
  - 0.247
  - 0.210
  - 0.183
```

You can find full examples in the examples folder. 




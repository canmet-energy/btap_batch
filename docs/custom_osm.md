## Create Custom OSM File
You can create a custom osm file by using Sketchup 2020 with the OpenStudio Plugin. 
### Geometry
You can view the intructional videos on how to create geometric models using sketchup and the openstudio plug-in. 
Here is a video to perform takeoffs from a DWG file. You can also import PDF files and do the same procedure. 
[NREL Take-Off Video Part 1](https://www.youtube.com/watch?v=T41MXqlvp0E)

Do not bother to add windows or doors. BTAP will automatically add these to the model based on the vintage template or the inputs in
the BTAPBatch input yml file. 

### Zone Multipliers
BTAP supports use of multipliers vertically (i.e by floor). This will help reduce the runtime of the simulation. Please 
do not use horizontal zone multipliers as this will not work with btap's costing algorithms.  

### Space Types
Space types must be defined as NECB 2011 spacetypes. BTAP will map these to the template you select in the btap_batch 
analysis file. You can find the osm library file of the NECB spacetypes in the resources/space_type_library folder that
 you can import and use in defining the spacetypes in your model. 

### Number of Floors
BTAP needs to know the number of above and below ground floors. This cannot be interpreted accurately from the geometry
 for all building types, for example split level models. To identify this, open the 
 OSM file and find the 'OS:Building' object and add the correct values to  'Standards Number of Stories' and 
 'Standards Number of Above Ground Stories'. To be clear, 'Standards Number of Stories' is the total number of 
 stories in the model including basement levels.  

You must also link all Space objects to a OS:BuildingStory. This is best done through the openstudio app. 

## Adding your custom.osm to an analysis
## Custom OSM file. 
1. Create a folder in your project folder called 'custom_osm'
2. Add your file(s) to that folder. 
3. Edit the input.yml file's to the :building_type keyword list without the .osm extension. For example if I was adding custom_1.osm and custom_2.osm, the :building_type keywork would look like this:

```json
:options:
  :building_type:
    - custom_1
    - custom_2
```
 You can then do any analses with your custom osm files. 
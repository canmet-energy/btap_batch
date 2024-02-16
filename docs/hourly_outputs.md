# Optional Hourly Outputs
## Meters (Optional)
There are some situation that you will require hourly outputs to be produced by the E+ engine. BTAP passes the same I/O variable names for output variables and meters. Below is an example of some common hourly output requests you can add to your input.yml file.
```yaml
:output_meters:
  # Utility meters.
  - name: NaturalGas:Facility
    frequency: hourly
    
  - name: Electricity:Facility
    frequency: hourly
  # End Uses
  - name: InteriorLights:Electricity
    frequency: hourly
    
  - name: Heating:Electricity
    frequency: hourly
    
  - name: Heating:NaturalGas
    frequency: hourly
    
  - name: Heating:DistrictHeating
    frequency: hourly
    
  - name: Cooling:Electricity
    frequency: hourly
    
  - name: Cooling:DistrictCooling
    frequency: hourly
    
  - name: Fans:Electricity
    frequency: hourly
    
  - name: Pumps:Electricity
    frequency: hourly
    
  - name: InteriorEquipment:Electricity
    frequency: hourly
    
  - name: WaterSystems:Electricity
    frequency: hourly
    
  - name: WaterSystems:NaturalGas
    frequency: hourly
```

## Variables
Similarly Your can also define output variables using E+ output format. Here is an example of outputting zonal hourly information.
```angular2html
:output_variables:
  - key: '*'
    variable: Zone Predicted Moisture Load to Dehumidifying Setpoint Moisture Transfer Rate
    frequency: hourly
    operation: '*'
    unit: '*'
```

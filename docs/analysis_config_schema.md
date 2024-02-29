# BTAP Analysis Run Options

- [1. [Optional] Property BTAP Analysis Run Options > :analysis_name](#:analysis_name)
- [2. [Optional] Property BTAP Analysis Run Options > :reference_run](#:reference_run)
- [3. [Optional] Property BTAP Analysis Run Options > :algorithm_type](#:algorithm_type)
- [4. [Optional] Property BTAP Analysis Run Options > :algorithm_lhs_n_samples](#:algorithm_lhs_n_samples)
- [5. [Optional] Property BTAP Analysis Run Options > :algorithm_lhs_type](#:algorithm_lhs_type)
- [6. [Optional] Property BTAP Analysis Run Options > :algorithm_lhs_random_seed](#:algorithm_lhs_random_seed)
- [7. [Optional] Property BTAP Analysis Run Options > :algorithm_nsga_population](#:algorithm_nsga_population)
- [8. [Optional] Property BTAP Analysis Run Options > :algorithm_nsga_n_generations](#:algorithm_nsga_n_generations)
- [9. [Optional] Property BTAP Analysis Run Options > :algorithm_nsga_prob](#:algorithm_nsga_prob)
- [10. [Optional] Property BTAP Analysis Run Options > :algorithm_nsga_eta](#:algorithm_nsga_eta)
- [11. [Optional] Property BTAP Analysis Run Options > :algorithm_nsga_minimize_objectives](#:algorithm_nsga_minimize_objectives)
- [12. [Optional] Property BTAP Analysis Run Options > :output_variables](#:output_variables)
- [13. [Optional] Property BTAP Analysis Run Options > :output_meters](#:output_meters)
- [14. [Optional] Property BTAP Analysis Run Options > :options](#:options)
  - [14.1. [Optional] Property BTAP Analysis Run Options > :options > :building_type](#:options_:building_type)
  - [14.2. [Optional] Property BTAP Analysis Run Options > :options > :template](#:options_:template)
  - [14.3. [Optional] Property BTAP Analysis Run Options > :options > :epw_file](#:options_:epw_file)
  - [14.4. [Optional] Property BTAP Analysis Run Options > :options > :primary_heating_fuel](#:options_:primary_heating_fuel)
  - [14.5. [Optional] Property BTAP Analysis Run Options > :options > :dcv_type](#:options_:dcv_type)
  - [14.6. [Optional] Property BTAP Analysis Run Options > :options > :lights_type](#:options_:lights_type)
  - [14.7. [Optional] Property BTAP Analysis Run Options > :options > :lights_scale](#:options_:lights_scale)
  - [14.8. [Optional] Property BTAP Analysis Run Options > :options > :occupancy_loads_scale](#:options_:occupancy_loads_scale)
  - [14.9. [Optional] Property BTAP Analysis Run Options > :options > :electrical_loads_scale](#:options_:electrical_loads_scale)
  - [14.10. [Optional] Property BTAP Analysis Run Options > :options > :oa_scale](#:options_:oa_scale)
  - [14.11. [Optional] Property BTAP Analysis Run Options > :options > :infiltration_scale](#:options_:infiltration_scale)
  - [14.12. [Optional] Property BTAP Analysis Run Options > :options > :daylighting_type](#:options_:daylighting_type)
  - [14.13. [Optional] Property BTAP Analysis Run Options > :options > :ecm_system_name](#:options_:ecm_system_name)
  - [14.14. [Optional] Property BTAP Analysis Run Options > :options > :chiller_type](#:options_:chiller_type)
  - [14.15. [Optional] Property BTAP Analysis Run Options > :options > :airloop_economizer_type](#:options_:airloop_economizer_type)
  - [14.16. [Optional] Property BTAP Analysis Run Options > :options > :shw_scale](#:options_:shw_scale)
  - [14.17. [Optional] Property BTAP Analysis Run Options > :options > :baseline_system_zones_map_option](#:options_:baseline_system_zones_map_option)
  - [14.18. [Optional] Property BTAP Analysis Run Options > :options > :erv_package](#:options_:erv_package)
  - [14.19. [Optional] Property BTAP Analysis Run Options > :options > :boiler_eff](#:options_:boiler_eff)
  - [14.20. [Optional] Property BTAP Analysis Run Options > :options > :furnace_eff](#:options_:furnace_eff)
  - [14.21. [Optional] Property BTAP Analysis Run Options > :options > :shw_eff](#:options_:shw_eff)
  - [14.22. [Optional] Property BTAP Analysis Run Options > :options > :ext_wall_cond](#:options_:ext_wall_cond)
  - [14.23. [Optional] Property BTAP Analysis Run Options > :options > :ext_roof_cond](#:options_:ext_roof_cond)
  - [14.24. [Optional] Property BTAP Analysis Run Options > :options > :ext_floor_cond](#:options_:ext_floor_cond)
  - [14.25. [Optional] Property BTAP Analysis Run Options > :options > :ground_wall_cond](#:options_:ground_wall_cond)
  - [14.26. [Optional] Property BTAP Analysis Run Options > :options > :ground_wall_roof](#:options_:ground_wall_roof)
  - [14.27. [Optional] Property BTAP Analysis Run Options > :options > :ground_floor_cond](#:options_:ground_floor_cond)
  - [14.28. [Optional] Property BTAP Analysis Run Options > :options > :door_construction_cond](#:options_:door_construction_cond)
  - [14.29. [Optional] Property BTAP Analysis Run Options > :options > :fixed_window_cond](#:options_:fixed_window_cond)
  - [14.30. [Optional] Property BTAP Analysis Run Options > :options > :glass_door_cond](#:options_:glass_door_cond)
  - [14.31. [Optional] Property BTAP Analysis Run Options > :options > :overhead_door_cond](#:options_:overhead_door_cond)
  - [14.32. [Optional] Property BTAP Analysis Run Options > :options > :skylight_cond](#:options_:skylight_cond)
  - [14.33. [Optional] Property BTAP Analysis Run Options > :options > :glass_door_solar_trans](#:options_:glass_door_solar_trans)
  - [14.34. [Optional] Property BTAP Analysis Run Options > :options > :fixed_wind_solar_trans](#:options_:fixed_wind_solar_trans)
  - [14.35. [Optional] Property BTAP Analysis Run Options > :options > :skylight_solar_trans](#:options_:skylight_solar_trans)
  - [14.36. [Optional] Property BTAP Analysis Run Options > :options > :fdwr_set](#:options_:fdwr_set)
  - [14.37. [Optional] Property BTAP Analysis Run Options > :options > :srr_set](#:options_:srr_set)
  - [14.38. [Optional] Property BTAP Analysis Run Options > :options > :rotation_degrees](#:options_:rotation_degrees)
  - [14.39. [Optional] Property BTAP Analysis Run Options > :options > :scale_x](#:options_:scale_x)
  - [14.40. [Optional] Property BTAP Analysis Run Options > :options > :scale_y](#:options_:scale_y)
  - [14.41. [Optional] Property BTAP Analysis Run Options > :options > :scale_z](#:options_:scale_z)
  - [14.42. [Optional] Property BTAP Analysis Run Options > :options > :pv_ground_type](#:options_:pv_ground_type)
  - [14.43. [Optional] Property BTAP Analysis Run Options > :options > :pv_ground_total_area_pv_panels_m2](#:options_:pv_ground_total_area_pv_panels_m2)
  - [14.44. [Optional] Property BTAP Analysis Run Options > :options > :pv_ground_azimuth_angle](#:options_:pv_ground_azimuth_angle)
  - [14.45. [Optional] Property BTAP Analysis Run Options > :options > :pv_ground_module_description](#:options_:pv_ground_module_description)
  - [14.46. [Optional] Property BTAP Analysis Run Options > :options > :adv_dx_units](#:options_:adv_dx_units)
  - [14.47. [Optional] Property BTAP Analysis Run Options > :options > :nv_type](#:options_:nv_type)
  - [14.48. [Optional] Property BTAP Analysis Run Options > :options > :nv_opening_fraction](#:options_:nv_opening_fraction)
  - [14.49. [Optional] Property BTAP Analysis Run Options > :options > :nv_temp_out_min](#:options_:nv_temp_out_min)
  - [14.50. [Optional] Property BTAP Analysis Run Options > :options > :nv_delta_temp_in_out](#:options_:nv_delta_temp_in_out)
  - [14.51. [Optional] Property BTAP Analysis Run Options > :options > :npv_start_year](#:options_:npv_start_year)
  - [14.52. [Optional] Property BTAP Analysis Run Options > :options > :npv_end_year](#:options_:npv_end_year)
  - [14.53. [Optional] Property BTAP Analysis Run Options > :options > :npv_discount_rate](#:options_:npv_discount_rate)

**Title:** BTAP Analysis Run Options

|                           |                                                                           |
| ------------------------- | ------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                  |
| **Required**              | No                                                                        |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

<details>
<summary>
<strong> <a name=":analysis_name"></a>1. [Optional] Property BTAP Analysis Run Options > :analysis_name</strong>  

</summary>
<blockquote>

|              |          |
| ------------ | -------- |
| **Type**     | `string` |
| **Required** | No       |

**Description:** Used to identify the analysis and name the parent folder. Must be less than 64 charecters and only letters numbers and underscores.

| Restrictions                      |                                                                                               |
| --------------------------------- | --------------------------------------------------------------------------------------------- |
| **Min length**                    | 1                                                                                             |
| **Max length**                    | 64                                                                                            |
| **Must match regular expression** | ```^[a-zA-Z0-9_\\s]*$``` [Test](https://regex101.com/?regex=%5E%5Ba-zA-Z0-9_%5C%5Cs%5D%2A%24) |

</blockquote>
</details>

<details>
<summary>
<strong> <a name=":reference_run"></a>2. [Optional] Property BTAP Analysis Run Options > :reference_run</strong>  

</summary>
<blockquote>

|              |           |
| ------------ | --------- |
| **Type**     | `boolean` |
| **Required** | No        |

**Description:** Optionally run the baseline/reference building. This will also provide comparison information from the baseline. If omitted it will assume to be true and run the reference simulations.

</blockquote>
</details>

<details>
<summary>
<strong> <a name=":algorithm_type"></a>3. [Optional] Property BTAP Analysis Run Options > :algorithm_type</strong>  

</summary>
<blockquote>

|              |                    |
| ------------ | ------------------ |
| **Type**     | `enum (of string)` |
| **Required** | No                 |

**Description:**  This will select the algorithm to use in the analysis. For information on the * [Optimization](optimization.md): Run a genetic optimization for a fixed number of runs and generations based. 

 * [Parametric](parametric.md): Run all possible combinations in input file.

 * [Elimination](elimination.md): Examine theoretical maximum energy savings from each domain for a given model. 

 * [Sensitivity](sensitivity.md): Examine the energy and cost effect from each measure selected. (~100 measures) 

 * [Latin-Hypercube-Sampling](latin_hypercube_sampling.md): Sample the solution space with a given number of simulations

 * [Batch](packages.md): When you wish to simply run a few specific building scenarios for comparison.

Must be one of:
* "elimination"
* "batch"
* "nsga2"
* "parametric"
* "reference"
* "sampling-lhs"
* "sensitivity"

</blockquote>
</details>

<details>
<summary>
<strong> <a name=":algorithm_lhs_n_samples"></a>4. [Optional] Property BTAP Analysis Run Options > :algorithm_lhs_n_samples</strong>  

</summary>
<blockquote>

|              |           |
| ------------ | --------- |
| **Type**     | `integer` |
| **Required** | No        |

**Description:** This is the number of simulations that will be preformed in the analysis. See [Scipy implementation](https://scikit-optimize.github.io/stable/auto_examples/sampler/initial-sampling-method.html)

| Restrictions |           |
| ------------ | --------- |
| **Minimum**  | &ge; 1    |
| **Maximum**  | &le; 5000 |

</blockquote>
</details>

<details>
<summary>
<strong> <a name=":algorithm_lhs_type"></a>5. [Optional] Property BTAP Analysis Run Options > :algorithm_lhs_type</strong>  

</summary>
<blockquote>

|              |                    |
| ------------ | ------------------ |
| **Type**     | `enum (of string)` |
| **Required** | No                 |

**Description:** This should be set to classic.. However other options are available in the scikit documentation listed above. See [Scipy implementation](https://scikit-optimize.github.io/stable/auto_examples/sampler/initial-sampling-method.html)

Must be one of:
* "classic"

</blockquote>
</details>

<details>
<summary>
<strong> <a name=":algorithm_lhs_random_seed"></a>6. [Optional] Property BTAP Analysis Run Options > :algorithm_lhs_random_seed</strong>  

</summary>
<blockquote>

|              |          |
| ------------ | -------- |
| **Type**     | `number` |
| **Required** | No       |

**Description:** algorithm_lhs_random_seed This is the random seed that will be used to drive the LHS random function. Change this to another number to alter the output from the same run. See [Scipy implementation](https://scikit-optimize.github.io/stable/auto_examples/sampler/initial-sampling-method.html)

| Restrictions |          |
| ------------ | -------- |
| **Minimum**  | &ge; 1   |
| **Maximum**  | &le; 100 |

</blockquote>
</details>

<details>
<summary>
<strong> <a name=":algorithm_nsga_population"></a>7. [Optional] Property BTAP Analysis Run Options > :algorithm_nsga_population</strong>  

</summary>
<blockquote>

|              |           |
| ------------ | --------- |
| **Type**     | `integer` |
| **Required** | No        |

**Description:** This is population size that is used in the NSGAII. Should be set to multiples than the number of threads/cores that you have available on your system to get best performance. Described in the [pymoo](https://pymoo.org/algorithms/moo/nsga2.html)

| Restrictions |          |
| ------------ | -------- |
| **Minimum**  | &ge; 1   |
| **Maximum**  | &le; 100 |

</blockquote>
</details>

<details>
<summary>
<strong> <a name=":algorithm_nsga_n_generations"></a>8. [Optional] Property BTAP Analysis Run Options > :algorithm_nsga_n_generations</strong>  

</summary>
<blockquote>

|              |           |
| ------------ | --------- |
| **Type**     | `integer` |
| **Required** | No        |

**Description:** This is the number of generations that are used in the NSGAII. Described in the [pymoo](https://pymoo.org/algorithms/moo/nsga2.html)

| Restrictions |          |
| ------------ | -------- |
| **Minimum**  | &ge; 1   |
| **Maximum**  | &le; 100 |

</blockquote>
</details>

<details>
<summary>
<strong> <a name=":algorithm_nsga_prob"></a>9. [Optional] Property BTAP Analysis Run Options > :algorithm_nsga_prob</strong>  

</summary>
<blockquote>

|              |          |
| ------------ | -------- |
| **Type**     | `number` |
| **Required** | No       |

**Description:** Used to configure crossover. See documentation [pymoo](https://pymoo.org/operators/crossover.html)

| Restrictions |            |
| ------------ | ---------- |
| **Minimum**  | &ge; 0.0   |
| **Maximum**  | &le; 100.0 |

</blockquote>
</details>

<details>
<summary>
<strong> <a name=":algorithm_nsga_eta"></a>10. [Optional] Property BTAP Analysis Run Options > :algorithm_nsga_eta</strong>  

</summary>
<blockquote>

|              |          |
| ------------ | -------- |
| **Type**     | `number` |
| **Required** | No       |

**Description:** Used to configure crossover. See documentation [pymoo](https://pymoo.org/operators/crossover.html)

| Restrictions |            |
| ------------ | ---------- |
| **Minimum**  | &ge; 0.0   |
| **Maximum**  | &le; 100.0 |

</blockquote>
</details>

<details>
<summary>
<strong> <a name=":algorithm_nsga_minimize_objectives"></a>11. [Optional] Property BTAP Analysis Run Options > :algorithm_nsga_minimize_objectives</strong>  

</summary>
<blockquote>

|                           |                                                                           |
| ------------------------- | ------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                  |
| **Required**              | No                                                                        |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

**Description:** Contains a list of the outputs from btap that you would like to optimize to. Pro tip. Run a senstivity analysis and examine the output.xlsx in the results folder to find a outpum column you wish to minimize.

</blockquote>
</details>

<details>
<summary>
<strong> <a name=":output_variables"></a>12. [Optional] Property BTAP Analysis Run Options > :output_variables</strong>  

</summary>
<blockquote>

|                           |                                                                           |
| ------------------------- | ------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                  |
| **Required**              | No                                                                        |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

**Description:** This enables EnergyPlus optional outputs. Details are contained in the [documentation](docs/output.md)

</blockquote>
</details>

<details>
<summary>
<strong> <a name=":output_meters"></a>13. [Optional] Property BTAP Analysis Run Options > :output_meters</strong>  

</summary>
<blockquote>

|                           |                                                                           |
| ------------------------- | ------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                  |
| **Required**              | No                                                                        |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

**Description:** This enables EnergyPlus optional outputs. Details are contained in the [documentation](docs/output.md)

</blockquote>
</details>

<details>
<summary>
<strong> <a name=":options"></a>14. [Optional] Property BTAP Analysis Run Options > :options</strong>  

</summary>
<blockquote>

|                           |                                                                           |
| ------------------------- | ------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                  |
| **Required**              | No                                                                        |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

<details>
<summary>
<strong> <a name=":options_:building_type"></a>14.1. [Optional] Property BTAP Analysis Run Options > :options > :building_type</strong>  

</summary>
<blockquote>

|                           |                                                                           |
| ------------------------- | ------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                  |
| **Required**              | No                                                                        |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

**Description:** This allows you to select either a pre-configured geometry in our library, or a custom geometry developed by a user.

 The Geometry files are OpenStudio OSM files that have geometry and spacetypes defined as per NECB2011, but nothing else as BTAP will poplate the rest based on the template and options selected. A full list of built-in models are available. They are listed (here)[https://github.com/NREL/openstudio-standards/tree/nrcan/lib/openstudio-standards/standards/necb/NECB2011/data/geometry] You would add the geometry name without the '.osm' extension. 

 Please note that the context is important.  Having two or more building types makes perfect sense for a parametric or sample_lhs analysis. But for for sensitvity and nsga2, it will not work as expected. If you minimize cost and energy. The optimizer will look for solutions for the FullSerivice restaurant and ignore the HighriseApartment as a solution since the restaurant will always be cheaper. 

**Example:** 

```json
{
    ":building_type": [
        "FullServiceRestaurant",
        "HighriseApartment"
    ]
}
```

</blockquote>
</details>

<details>
<summary>
<strong> <a name=":options_:template"></a>14.2. [Optional] Property BTAP Analysis Run Options > :options > :template</strong>  

</summary>
<blockquote>

|                           |                                                                           |
| ------------------------- | ------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                  |
| **Required**              | No                                                                        |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

**Description:**  This field will designate which baseline building templates to use. Currently BTAP supports the **National Energy Building Code** (NECB)[https://nrc.canada.ca/en/certifications-evaluations-standards/codes-canada/codes-canada-publications/national-energy-code-canada-buildings-2020] The vintages that are availble are the NECB2011 to 2020. BTAP will use all the performance requirements of the selected codes in the analysis. It will determine what the `NECB_Default` will be used in other options as selected. While you could use this field with many templates to optimize. It is not recommended as it will probably optimize to the lastest code. 

</blockquote>
</details>

<details>
<summary>
<strong> <a name=":options_:epw_file"></a>14.3. [Optional] Property BTAP Analysis Run Options > :options > :epw_file</strong>  

</summary>
<blockquote>

|                           |                                                                           |
| ------------------------- | ------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                  |
| **Required**              | No                                                                        |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

**Description:** #List of Weather files to use in the analysis.  These weather files should be a subset of the weather files defined in your build_config.yml file.   The other locations that you can use can be found in this repository

</blockquote>
</details>

<details>
<summary>
<strong> <a name=":options_:primary_heating_fuel"></a>14.4. [Optional] Property BTAP Analysis Run Options > :options > :primary_heating_fuel</strong>  

</summary>
<blockquote>

|                           |                                                                           |
| ------------------------- | ------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                  |
| **Required**              | No                                                                        |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

**Description:** These are fuels that are used primarily for space heating and hot water needs.

 | Primary Heating Fuel            | Hot Water             | Primary                 | Backup             |
 | --------                        | -------               | -------                 | -------            |
 | **Electricity**                 | Electric Resistance   | Electric Resistance     | Electric Resistance|
 | **NaturalGas**                  | Natural Gas           | Natural Gas             | Natural Gas        |
 | **ElectricityHPElecBackup**     | Electric Resistance   | Heat Pump               | Electric Resistance|
 | **NaturalGasHPGasBackup**       | Natural Gas           | Heat Pump               | Natural Gas        |
 | **ElectricityHPGasBackupMixed** | Electric Resistance   | Heat Pump               | Natural Gas        |
 | **NaturalGasHPElecBackupMixed** | Natural Gas           | Heat Pump               | Electric Resistance|

</blockquote>
</details>

<details>
<summary>
<strong> <a name=":options_:dcv_type"></a>14.5. [Optional] Property BTAP Analysis Run Options > :options > :dcv_type</strong>  

</summary>
<blockquote>

|                           |                                                                           |
| ------------------------- | ------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                  |
| **Required**              | No                                                                        |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

</blockquote>
</details>

<details>
<summary>
<strong> <a name=":options_:lights_type"></a>14.6. [Optional] Property BTAP Analysis Run Options > :options > :lights_type</strong>  

</summary>
<blockquote>

|                           |                                                                           |
| ------------------------- | ------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                  |
| **Required**              | No                                                                        |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

</blockquote>
</details>

<details>
<summary>
<strong> <a name=":options_:lights_scale"></a>14.7. [Optional] Property BTAP Analysis Run Options > :options > :lights_scale</strong>  

</summary>
<blockquote>

|                           |                                                                           |
| ------------------------- | ------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                  |
| **Required**              | No                                                                        |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

</blockquote>
</details>

<details>
<summary>
<strong> <a name=":options_:occupancy_loads_scale"></a>14.8. [Optional] Property BTAP Analysis Run Options > :options > :occupancy_loads_scale</strong>  

</summary>
<blockquote>

|                           |                                                                           |
| ------------------------- | ------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                  |
| **Required**              | No                                                                        |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

</blockquote>
</details>

<details>
<summary>
<strong> <a name=":options_:electrical_loads_scale"></a>14.9. [Optional] Property BTAP Analysis Run Options > :options > :electrical_loads_scale</strong>  

</summary>
<blockquote>

|                           |                                                                           |
| ------------------------- | ------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                  |
| **Required**              | No                                                                        |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

</blockquote>
</details>

<details>
<summary>
<strong> <a name=":options_:oa_scale"></a>14.10. [Optional] Property BTAP Analysis Run Options > :options > :oa_scale</strong>  

</summary>
<blockquote>

|                           |                                                                           |
| ------------------------- | ------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                  |
| **Required**              | No                                                                        |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

</blockquote>
</details>

<details>
<summary>
<strong> <a name=":options_:infiltration_scale"></a>14.11. [Optional] Property BTAP Analysis Run Options > :options > :infiltration_scale</strong>  

</summary>
<blockquote>

|                           |                                                                           |
| ------------------------- | ------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                  |
| **Required**              | No                                                                        |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

</blockquote>
</details>

<details>
<summary>
<strong> <a name=":options_:daylighting_type"></a>14.12. [Optional] Property BTAP Analysis Run Options > :options > :daylighting_type</strong>  

</summary>
<blockquote>

|                           |                                                                           |
| ------------------------- | ------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                  |
| **Required**              | No                                                                        |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

</blockquote>
</details>

<details>
<summary>
<strong> <a name=":options_:ecm_system_name"></a>14.13. [Optional] Property BTAP Analysis Run Options > :options > :ecm_system_name</strong>  

</summary>
<blockquote>

|                           |                                                                           |
| ------------------------- | ------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                  |
| **Required**              | No                                                                        |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

</blockquote>
</details>

<details>
<summary>
<strong> <a name=":options_:chiller_type"></a>14.14. [Optional] Property BTAP Analysis Run Options > :options > :chiller_type</strong>  

</summary>
<blockquote>

|                           |                                                                           |
| ------------------------- | ------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                  |
| **Required**              | No                                                                        |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

</blockquote>
</details>

<details>
<summary>
<strong> <a name=":options_:airloop_economizer_type"></a>14.15. [Optional] Property BTAP Analysis Run Options > :options > :airloop_economizer_type</strong>  

</summary>
<blockquote>

|                           |                                                                           |
| ------------------------- | ------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                  |
| **Required**              | No                                                                        |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

</blockquote>
</details>

<details>
<summary>
<strong> <a name=":options_:shw_scale"></a>14.16. [Optional] Property BTAP Analysis Run Options > :options > :shw_scale</strong>  

</summary>
<blockquote>

|                           |                                                                           |
| ------------------------- | ------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                  |
| **Required**              | No                                                                        |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

</blockquote>
</details>

<details>
<summary>
<strong> <a name=":options_:baseline_system_zones_map_option"></a>14.17. [Optional] Property BTAP Analysis Run Options > :options > :baseline_system_zones_map_option</strong>  

</summary>
<blockquote>

|                           |                                                                           |
| ------------------------- | ------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                  |
| **Required**              | No                                                                        |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

</blockquote>
</details>

<details>
<summary>
<strong> <a name=":options_:erv_package"></a>14.18. [Optional] Property BTAP Analysis Run Options > :options > :erv_package</strong>  

</summary>
<blockquote>

|                           |                                                                           |
| ------------------------- | ------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                  |
| **Required**              | No                                                                        |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

</blockquote>
</details>

<details>
<summary>
<strong> <a name=":options_:boiler_eff"></a>14.19. [Optional] Property BTAP Analysis Run Options > :options > :boiler_eff</strong>  

</summary>
<blockquote>

|                           |                                                                           |
| ------------------------- | ------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                  |
| **Required**              | No                                                                        |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

</blockquote>
</details>

<details>
<summary>
<strong> <a name=":options_:furnace_eff"></a>14.20. [Optional] Property BTAP Analysis Run Options > :options > :furnace_eff</strong>  

</summary>
<blockquote>

|                           |                                                                           |
| ------------------------- | ------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                  |
| **Required**              | No                                                                        |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

</blockquote>
</details>

<details>
<summary>
<strong> <a name=":options_:shw_eff"></a>14.21. [Optional] Property BTAP Analysis Run Options > :options > :shw_eff</strong>  

</summary>
<blockquote>

|                           |                                                                           |
| ------------------------- | ------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                  |
| **Required**              | No                                                                        |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

</blockquote>
</details>

<details>
<summary>
<strong> <a name=":options_:ext_wall_cond"></a>14.22. [Optional] Property BTAP Analysis Run Options > :options > :ext_wall_cond</strong>  

</summary>
<blockquote>

|                           |                                                                           |
| ------------------------- | ------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                  |
| **Required**              | No                                                                        |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

</blockquote>
</details>

<details>
<summary>
<strong> <a name=":options_:ext_roof_cond"></a>14.23. [Optional] Property BTAP Analysis Run Options > :options > :ext_roof_cond</strong>  

</summary>
<blockquote>

|                           |                                                                           |
| ------------------------- | ------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                  |
| **Required**              | No                                                                        |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

</blockquote>
</details>

<details>
<summary>
<strong> <a name=":options_:ext_floor_cond"></a>14.24. [Optional] Property BTAP Analysis Run Options > :options > :ext_floor_cond</strong>  

</summary>
<blockquote>

|                           |                                                                           |
| ------------------------- | ------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                  |
| **Required**              | No                                                                        |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

</blockquote>
</details>

<details>
<summary>
<strong> <a name=":options_:ground_wall_cond"></a>14.25. [Optional] Property BTAP Analysis Run Options > :options > :ground_wall_cond</strong>  

</summary>
<blockquote>

|                           |                                                                           |
| ------------------------- | ------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                  |
| **Required**              | No                                                                        |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

</blockquote>
</details>

<details>
<summary>
<strong> <a name=":options_:ground_wall_roof"></a>14.26. [Optional] Property BTAP Analysis Run Options > :options > :ground_wall_roof</strong>  

</summary>
<blockquote>

|                           |                                                                           |
| ------------------------- | ------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                  |
| **Required**              | No                                                                        |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

</blockquote>
</details>

<details>
<summary>
<strong> <a name=":options_:ground_floor_cond"></a>14.27. [Optional] Property BTAP Analysis Run Options > :options > :ground_floor_cond</strong>  

</summary>
<blockquote>

|                           |                                                                           |
| ------------------------- | ------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                  |
| **Required**              | No                                                                        |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

</blockquote>
</details>

<details>
<summary>
<strong> <a name=":options_:door_construction_cond"></a>14.28. [Optional] Property BTAP Analysis Run Options > :options > :door_construction_cond</strong>  

</summary>
<blockquote>

|                           |                                                                           |
| ------------------------- | ------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                  |
| **Required**              | No                                                                        |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

</blockquote>
</details>

<details>
<summary>
<strong> <a name=":options_:fixed_window_cond"></a>14.29. [Optional] Property BTAP Analysis Run Options > :options > :fixed_window_cond</strong>  

</summary>
<blockquote>

|                           |                                                                           |
| ------------------------- | ------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                  |
| **Required**              | No                                                                        |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

</blockquote>
</details>

<details>
<summary>
<strong> <a name=":options_:glass_door_cond"></a>14.30. [Optional] Property BTAP Analysis Run Options > :options > :glass_door_cond</strong>  

</summary>
<blockquote>

|                           |                                                                           |
| ------------------------- | ------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                  |
| **Required**              | No                                                                        |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

</blockquote>
</details>

<details>
<summary>
<strong> <a name=":options_:overhead_door_cond"></a>14.31. [Optional] Property BTAP Analysis Run Options > :options > :overhead_door_cond</strong>  

</summary>
<blockquote>

|                           |                                                                           |
| ------------------------- | ------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                  |
| **Required**              | No                                                                        |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

</blockquote>
</details>

<details>
<summary>
<strong> <a name=":options_:skylight_cond"></a>14.32. [Optional] Property BTAP Analysis Run Options > :options > :skylight_cond</strong>  

</summary>
<blockquote>

|                           |                                                                           |
| ------------------------- | ------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                  |
| **Required**              | No                                                                        |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

</blockquote>
</details>

<details>
<summary>
<strong> <a name=":options_:glass_door_solar_trans"></a>14.33. [Optional] Property BTAP Analysis Run Options > :options > :glass_door_solar_trans</strong>  

</summary>
<blockquote>

|                           |                                                                           |
| ------------------------- | ------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                  |
| **Required**              | No                                                                        |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

</blockquote>
</details>

<details>
<summary>
<strong> <a name=":options_:fixed_wind_solar_trans"></a>14.34. [Optional] Property BTAP Analysis Run Options > :options > :fixed_wind_solar_trans</strong>  

</summary>
<blockquote>

|                           |                                                                           |
| ------------------------- | ------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                  |
| **Required**              | No                                                                        |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

</blockquote>
</details>

<details>
<summary>
<strong> <a name=":options_:skylight_solar_trans"></a>14.35. [Optional] Property BTAP Analysis Run Options > :options > :skylight_solar_trans</strong>  

</summary>
<blockquote>

|                           |                                                                           |
| ------------------------- | ------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                  |
| **Required**              | No                                                                        |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

</blockquote>
</details>

<details>
<summary>
<strong> <a name=":options_:fdwr_set"></a>14.36. [Optional] Property BTAP Analysis Run Options > :options > :fdwr_set</strong>  

</summary>
<blockquote>

|                           |                                                                           |
| ------------------------- | ------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                  |
| **Required**              | No                                                                        |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

</blockquote>
</details>

<details>
<summary>
<strong> <a name=":options_:srr_set"></a>14.37. [Optional] Property BTAP Analysis Run Options > :options > :srr_set</strong>  

</summary>
<blockquote>

|                           |                                                                           |
| ------------------------- | ------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                  |
| **Required**              | No                                                                        |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

</blockquote>
</details>

<details>
<summary>
<strong> <a name=":options_:rotation_degrees"></a>14.38. [Optional] Property BTAP Analysis Run Options > :options > :rotation_degrees</strong>  

</summary>
<blockquote>

|                           |                                                                           |
| ------------------------- | ------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                  |
| **Required**              | No                                                                        |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

</blockquote>
</details>

<details>
<summary>
<strong> <a name=":options_:scale_x"></a>14.39. [Optional] Property BTAP Analysis Run Options > :options > :scale_x</strong>  

</summary>
<blockquote>

|                           |                                                                           |
| ------------------------- | ------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                  |
| **Required**              | No                                                                        |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

</blockquote>
</details>

<details>
<summary>
<strong> <a name=":options_:scale_y"></a>14.40. [Optional] Property BTAP Analysis Run Options > :options > :scale_y</strong>  

</summary>
<blockquote>

|                           |                                                                           |
| ------------------------- | ------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                  |
| **Required**              | No                                                                        |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

</blockquote>
</details>

<details>
<summary>
<strong> <a name=":options_:scale_z"></a>14.41. [Optional] Property BTAP Analysis Run Options > :options > :scale_z</strong>  

</summary>
<blockquote>

|                           |                                                                           |
| ------------------------- | ------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                  |
| **Required**              | No                                                                        |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

</blockquote>
</details>

<details>
<summary>
<strong> <a name=":options_:pv_ground_type"></a>14.42. [Optional] Property BTAP Analysis Run Options > :options > :pv_ground_type</strong>  

</summary>
<blockquote>

|                           |                                                                           |
| ------------------------- | ------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                  |
| **Required**              | No                                                                        |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

</blockquote>
</details>

<details>
<summary>
<strong> <a name=":options_:pv_ground_total_area_pv_panels_m2"></a>14.43. [Optional] Property BTAP Analysis Run Options > :options > :pv_ground_total_area_pv_panels_m2</strong>  

</summary>
<blockquote>

|                           |                                                                           |
| ------------------------- | ------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                  |
| **Required**              | No                                                                        |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

</blockquote>
</details>

<details>
<summary>
<strong> <a name=":options_:pv_ground_azimuth_angle"></a>14.44. [Optional] Property BTAP Analysis Run Options > :options > :pv_ground_azimuth_angle</strong>  

</summary>
<blockquote>

|                           |                                                                           |
| ------------------------- | ------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                  |
| **Required**              | No                                                                        |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

</blockquote>
</details>

<details>
<summary>
<strong> <a name=":options_:pv_ground_module_description"></a>14.45. [Optional] Property BTAP Analysis Run Options > :options > :pv_ground_module_description</strong>  

</summary>
<blockquote>

|                           |                                                                           |
| ------------------------- | ------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                  |
| **Required**              | No                                                                        |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

</blockquote>
</details>

<details>
<summary>
<strong> <a name=":options_:adv_dx_units"></a>14.46. [Optional] Property BTAP Analysis Run Options > :options > :adv_dx_units</strong>  

</summary>
<blockquote>

|                           |                                                                           |
| ------------------------- | ------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                  |
| **Required**              | No                                                                        |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

</blockquote>
</details>

<details>
<summary>
<strong> <a name=":options_:nv_type"></a>14.47. [Optional] Property BTAP Analysis Run Options > :options > :nv_type</strong>  

</summary>
<blockquote>

|                           |                                                                           |
| ------------------------- | ------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                  |
| **Required**              | No                                                                        |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

</blockquote>
</details>

<details>
<summary>
<strong> <a name=":options_:nv_opening_fraction"></a>14.48. [Optional] Property BTAP Analysis Run Options > :options > :nv_opening_fraction</strong>  

</summary>
<blockquote>

|                           |                                                                           |
| ------------------------- | ------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                  |
| **Required**              | No                                                                        |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

</blockquote>
</details>

<details>
<summary>
<strong> <a name=":options_:nv_temp_out_min"></a>14.49. [Optional] Property BTAP Analysis Run Options > :options > :nv_temp_out_min</strong>  

</summary>
<blockquote>

|                           |                                                                           |
| ------------------------- | ------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                  |
| **Required**              | No                                                                        |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

**Description:** Minimum outdoor air temperature (in Celsius) below which natural ventilation is shut down. Default will be 13C from M.Tardif experience with QC schools. NECB_Default: Will set this to 13. 

</blockquote>
</details>

<details>
<summary>
<strong> <a name=":options_:nv_delta_temp_in_out"></a>14.50. [Optional] Property BTAP Analysis Run Options > :options > :nv_delta_temp_in_out</strong>  

</summary>
<blockquote>

|                           |                                                                           |
| ------------------------- | ------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                  |
| **Required**              | No                                                                        |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

**Description:** Temperature difference (in Celsius) between the indoor and outdoor air temperatures below which ventilation is shut down Default is 1.0 from M.Tardif experience in QC. Units: C NECB_Default: Will set this to 1.0 

</blockquote>
</details>

<details>
<summary>
<strong> <a name=":options_:npv_start_year"></a>14.51. [Optional] Property BTAP Analysis Run Options > :options > :npv_start_year</strong>  

</summary>
<blockquote>

|                           |                                                                           |
| ------------------------- | ------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                  |
| **Required**              | No                                                                        |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

**Description:**  An integer (year) larger than 2005 (first year of neb_end_use_prices.csv). NECB_Default: Will set this to 2022 

</blockquote>
</details>

<details>
<summary>
<strong> <a name=":options_:npv_end_year"></a>14.52. [Optional] Property BTAP Analysis Run Options > :options > :npv_end_year</strong>  

</summary>
<blockquote>

|                           |                                                                           |
| ------------------------- | ------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                  |
| **Required**              | No                                                                        |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

**Description:**  An integer (year) less than 2051 (last year of neb_end_use_prices.csv). NECB Default:  Will set this to 2041. 

</blockquote>
</details>

<details>
<summary>
<strong> <a name=":options_:npv_discount_rate"></a>14.53. [Optional] Property BTAP Analysis Run Options > :options > :npv_discount_rate</strong>  

</summary>
<blockquote>

|                           |                                                                           |
| ------------------------- | ------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                  |
| **Required**              | No                                                                        |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

**Description:**  An integer (year) less than 2051 (last year of neb_end_use_prices.csv). NECB_Default: Will set it to 0.03. 

</blockquote>
</details>

</blockquote>
</details>

----------------------------------------------------------------------------------------------------------------------------
Generated using [json-schema-for-humans](https://github.com/coveooss/json-schema-for-humans) on 2024-02-29 at 15:30:39 -0500
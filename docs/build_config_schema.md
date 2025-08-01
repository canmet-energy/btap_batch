# Schema Docs

- [1. Property `root > build_env_name`](#build_env_name)
- [2. Property `root > git_api_token`](#git_api_token)
- [3. Property `root > btap_batch_branch`](#btap_batch_branch)
- [4. Property `root > os_standards_branch`](#os_standards_branch)
- [5. Property `root > openstudio_version`](#openstudio_version)
- [6. Property `root > btap_weather`](#btap_weather)
- [7. Property `root > weather_list`](#weather_list)
- [8. Property `root > local_costing_path`](#local_costing_path)
- [9. Property `root > build_btap_cli`](#build_btap_cli)
- [10. Property `root > build_btap_batch`](#build_btap_batch)
- [11. Property `root > local_nrcan`](#local_nrcan)
- [12. Property `root > compute_environment`](#compute_environment)

|                           |             |
| ------------------------- | ----------- |
| **Type**                  | `object`    |
| **Required**              | No          |
| **Additional properties** | Not allowed |

| Property                                       | Pattern | Type             | Deprecated | Definition | Title/Description                                                                                                                                                                                                                                                                                                                                                                                             |
| ---------------------------------------------- | ------- | ---------------- | ---------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| + [build_env_name](#build_env_name )           | No      | string           | No         | -          | :Prefix used to identify images, folders and other items specific to a build environment. Only lowercase, numbers and underscore and <24 chars.                                                                                                                                                                                                                                                               |
| + [git_api_token](#git_api_token )             | No      | string           | No         | -          | The authorization token to access Github. You are required to have a github account and generate a classic personal access token. Instructions to generate one are [here](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)                                                                                                                |
| + [btap_batch_branch](#btap_batch_branch )     | No      | string           | No         | -          | Branch of btap_batch to use to build environment. For general users the 'main' branch should be used. You can review available branches [here](https://github.com/canmet-energy/btap_batch) if you are a developer.                                                                                                                                                                                           |
| + [os_standards_branch](#os_standards_branch ) | No      | string           | No         | -          | Branch of NREL's Openstudio-standards repository to use to build environment. The default branch to use is 'nrcan' This branch is only accessible for authorized users. You can review available branches [here](https://github.com/nrel/openstudio-standards)                                                                                                                                                |
| + [openstudio_version](#openstudio_version )   | No      | enum (of string) | No         | -          | Valid version of the OpenStudio SDK to build with.                                                                                                                                                                                                                                                                                                                                                            |
| - [btap_weather](#btap_weather )               | No      | boolean          | No         | -          | Location of weather files to download. If true, downloads from [btap_weather](https://github.com/canmet-energy/btap_weather). Else, downloads from Climate.OneBuilding.Org.                                                                                                                                                                                                                                   |
| + [weather_list](#weather_list )               | No      | object           | No         | -          | List of Weather files to build included in the build environment. Only .epw files , and <100 files. Other weather locations are available. However, you have to define the ones you want to use when creating your environment.  The other locations that you can use can be found in [here](https://climate.onebuilding.org/)<br /><br /><br />Here is an example:<br /><br />                               |
| + [local_costing_path](#local_costing_path )   | No      | string           | No         | -          | Path to the local costing_database.json costing file.  The default is '<this btap_batch local repository location>/resources/costing/costing_database.json'. If you are using a custom costing file, you can set the path. here<br /><br /> Ignore this if you are not using costing or content with the default costing_database.json costing file.<br /><br />                                              |
| + [build_btap_cli](#build_btap_cli )           | No      | boolean          | No         | -          | **ADVANCED** Build most recent btap_cli always. Set to false to save time if standards and costing branches have not changed.                                                                                                                                                                                                                                                                                 |
| + [build_btap_batch](#build_btap_batch )       | No      | boolean          | No         | -          | **ADVANCED** Build most recent btap_batch always. Set to false to save time if standards and costing branches have not changed.                                                                                                                                                                                                                                                                               |
| + [local_nrcan](#local_nrcan )                 | No      | boolean          | No         | -          | **NRCan only** Set this to True if you intend to build your environment locally on a computer connected to the NRCan network.  Otherwise leave it as False.                                                                                                                                                                                                                                                   |
| + [compute_environment](#compute_environment ) | No      | enum (of string) | No         | -          | Select which environment to build and where to run analyses.<br /><br /> **local**: will use docker on your local computer.<br /><br /> **aws**: will manage and run eveything on AWS. You can turn off your local computer after the analysis is submitted<br /><br /> **local_managed_aws_workers**: **ADVANCED** will manage the analysis on a local computer and run the simulations on aws.<br /><br />  |

## <a name="build_env_name"></a>1. Property `root > build_env_name`

|              |          |
| ------------ | -------- |
| **Type**     | `string` |
| **Required** | Yes      |

**Description:** :Prefix used to identify images, folders and other items specific to a build environment. Only lowercase, numbers and underscore and <24 chars.

| Restrictions                      |                                                                                         |
| --------------------------------- | --------------------------------------------------------------------------------------- |
| **Min length**                    | 1                                                                                       |
| **Max length**                    | 24                                                                                      |
| **Must match regular expression** | ```^[a-z0-9_\\s]*$``` [Test](https://regex101.com/?regex=%5E%5Ba-z0-9_%5C%5Cs%5D%2A%24) |

## <a name="git_api_token"></a>2. Property `root > git_api_token`

|              |          |
| ------------ | -------- |
| **Type**     | `string` |
| **Required** | Yes      |

**Description:** The authorization token to access Github. You are required to have a github account and generate a classic personal access token. Instructions to generate one are [here](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)

## <a name="btap_batch_branch"></a>3. Property `root > btap_batch_branch`

|              |          |
| ------------ | -------- |
| **Type**     | `string` |
| **Required** | Yes      |

**Description:** Branch of btap_batch to use to build environment. For general users the 'main' branch should be used. You can review available branches [here](https://github.com/canmet-energy/btap_batch) if you are a developer. 

## <a name="os_standards_org"></a>4. Property `root > os_standards_org`

|              |          |
| ------------ | -------- |
| **Type**     | `string` |
| **Required** | Yes      |
| **Default**  | `"NREL"` |

**Description:** Branch of NREL's Openstudio-standards repository to use to build environment. The default branch to use is 'nrcan' This branch is only accessible for authorized users. You can review available branches [here](https://github.com/nrel/openstudio-standards)

## <a name="openstudio_version"></a>5. Property `root > openstudio_version`

|              |                    |
| ------------ | ------------------ |
| **Type**     | `enum (of string)` |
| **Required** | Yes                |

**Description:** Valid version of the OpenStudio SDK to build with.

Must be one of:
* "3.6.1"
* "3.7.0"

## <a name="btap_weather"></a>6. Property `root > btap_weather`

|              |           |
| ------------ | --------- |
| **Type**     | `boolean` |
| **Required** | No        |
| **Default**  | `true`    |

**Description:** Location of weather files to download. If true, downloads from [btap_weather](https://github.com/canmet-energy/btap_weather). Else, downloads from Climate.OneBuilding.Org.

## <a name="weather_list"></a>7. Property `root > weather_list`

|                           |                  |
| ------------------------- | ---------------- |
| **Type**                  | `object`         |
| **Required**              | Yes              |
| **Additional properties** | Any type allowed |

**Description:** List of Weather files to build included in the build environment. Only .epw files , and <100 files. Other weather locations are available. However, you have to define the ones you want to use when creating your environment.  The other locations that you can use can be found in [here](https://climate.onebuilding.org/)

Here is an example:

**Example:**

```yaml
weather_list:
- CAN_QC_Montreal.Intl.AP.716270_CWEC2020.epw
- CAN_NS_Halifax.Dockyard.713280_CWEC2020.epw
- CAN_AB_Edmonton.Intl.AP.711230_CWEC2020.epw
- CAN_BC_Vancouver.Intl.AP.718920_CWEC2020.epw
- CAN_AB_Calgary.Intl.AP.718770_CWEC2020.epw
- CAN_ON_Toronto.Intl.AP.716240_CWEC2020.epw
- CAN_NT_Yellowknife.AP.719360_CWEC2020.epw
- CAN_AB_Fort.Mcmurray.AP.716890_CWEC2020.epw

```

## <a name="local_costing_path"></a>8. Property `root > local_costing_path`

|              |                                             |
| ------------ | ------------------------------------------- |
| **Type**     | `string`                                    |
| **Required** | Yes                                         |
| **Default**  | `"resources/costing/costing_database.json"` |

**Description:** Path to the local costing_database.json costing file.  The default is '<this btap_batch local repository location>/resources/costing/costing_database.json'. If you are using a custom costing file, you can set the path. here

 Ignore this if you are not using costing or content with the default costing_database.json costing file.

## <a name="build_btap_cli"></a>9. Property `root > build_btap_cli`

|              |           |
| ------------ | --------- |
| **Type**     | `boolean` |
| **Required** | Yes       |
| **Default**  | `true`    |

**Description:** **ADVANCED** Build most recent btap_cli always. Set to false to save time if standards and costing branches have not changed.

## <a name="build_btap_batch"></a>10. Property `root > build_btap_batch`

|              |           |
| ------------ | --------- |
| **Type**     | `boolean` |
| **Required** | Yes       |
| **Default**  | `true`    |

**Description:** **ADVANCED** Build most recent btap_batch always. Set to false to save time if standards and costing branches have not changed.

## <a name="local_nrcan"></a>11. Property `root > local_nrcan`

|              |           |
| ------------ | --------- |
| **Type**     | `boolean` |
| **Required** | Yes       |
| **Default**  | `false`   |

**Description:** **NRCan only** Set this to True if you intend to build your environment locally on a computer connected to the NRCan network.  Otherwise leave it as False.

## <a name="compute_environment"></a>12. Property `root > compute_environment`

|              |                    |
| ------------ | ------------------ |
| **Type**     | `enum (of string)` |
| **Required** | Yes                |

**Description:** Select which environment to build and where to run analyses.

 **local**: will use docker on your local computer.

 **aws**: will manage and run eveything on AWS. You can turn off your local computer after the analysis is submitted

 **local_managed_aws_workers**: **ADVANCED** will manage the analysis on a local computer and run the simulations on aws.

Must be one of:
* "local"
* "local_managed_aws_workers"
* "aws"

----------------------------------------------------------------------------------------------------------------------------
Generated using [json-schema-for-humans](https://github.com/coveooss/json-schema-for-humans) on 2025-08-01 at 17:58:40 +0000

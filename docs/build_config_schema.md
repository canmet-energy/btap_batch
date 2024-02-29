# Schema Docs

- [1. [Required] Property root > build_env_name](#build_env_name)
- [2. [Required] Property root > git_api_token](#git_api_token)
- [3. [Required] Property root > btap_batch_branch](#btap_batch_branch)
- [4. [Required] Property root > btap_costing_branch](#btap_costing_branch)
- [5. [Required] Property root > os_standards_branch](#os_standards_branch)
- [6. [Required] Property root > openstudio_version](#openstudio_version)
- [7. [Required] Property root > weather_list](#weather_list)
- [8. [Required] Property root > disable_costing](#disable_costing)
- [9. [Required] Property root > build_btap_cli](#build_btap_cli)
- [10. [Required] Property root > build_btap_batch](#build_btap_batch)
- [11. [Required] Property root > compute_environment](#compute_environment)

|                           |                                                         |
| ------------------------- | ------------------------------------------------------- |
| **Type**                  | `object`                                                |
| **Required**              | No                                                      |
| **Additional properties** | [[Not allowed]](# "Additional Properties not allowed.") |

<details>
<summary>
<strong> <a name="build_env_name"></a>1. [Required] Property root > build_env_name</strong>  

</summary>
<blockquote>

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

</blockquote>
</details>

<details>
<summary>
<strong> <a name="git_api_token"></a>2. [Required] Property root > git_api_token</strong>  

</summary>
<blockquote>

|              |          |
| ------------ | -------- |
| **Type**     | `string` |
| **Required** | Yes      |

**Description:** The authorization token to access Github. You are required to have a github account and generate a classic personal access token. Instructions to generate one are [here](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)

</blockquote>
</details>

<details>
<summary>
<strong> <a name="btap_batch_branch"></a>3. [Required] Property root > btap_batch_branch</strong>  

</summary>
<blockquote>

|              |          |
| ------------ | -------- |
| **Type**     | `string` |
| **Required** | Yes      |

**Description:** Branch of btap_batch to use to build environment. For general users the 'main' branch should be used. You can review available branches [here](https://github.com/canmet-energy/btap_batch) if you are a developer. 

</blockquote>
</details>

<details>
<summary>
<strong> <a name="btap_costing_branch"></a>4. [Required] Property root > btap_costing_branch</strong>  

</summary>
<blockquote>

|              |          |
| ------------ | -------- |
| **Type**     | `string` |
| **Required** | Yes      |

**Description:** Branch of btap_costing to use to build environment. The default branch to use is 'master' This branch is only accessible for authorized users. You can review available branches [here](https://github.com/canmet-energy/btap_costing) if you are a developer.

</blockquote>
</details>

<details>
<summary>
<strong> <a name="os_standards_branch"></a>5. [Required] Property root > os_standards_branch</strong>  

</summary>
<blockquote>

|              |          |
| ------------ | -------- |
| **Type**     | `string` |
| **Required** | Yes      |

**Description:** Branch of NREL's Openstudio-standards to use to build environment. The default branch to use is 'master' This branch is only accessible for authorized users. You can review available branches [here](https://github.com/nrel/openstudio-standards)

</blockquote>
</details>

<details>
<summary>
<strong> <a name="openstudio_version"></a>6. [Required] Property root > openstudio_version</strong>  

</summary>
<blockquote>

|              |                    |
| ------------ | ------------------ |
| **Type**     | `enum (of string)` |
| **Required** | Yes                |

**Description:** Valid version of the OpenStudio SDK to build with.

Must be one of:
* "3.6.1"
* "3.7.0"

</blockquote>
</details>

<details>
<summary>
<strong> <a name="weather_list"></a>7. [Required] Property root > weather_list</strong>  

</summary>
<blockquote>

|                           |                                                                           |
| ------------------------- | ------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                  |
| **Required**              | Yes                                                                       |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

**Description:** List of Weather files to build included in the build environment. Only .epw files , and <100 files. Other weather locations are available. However, you have to define the ones you want to use when creating your environment.  The other locations that you can use can be found in [here](https://github.com/canmet-energy/btap_weather)

Here is an example:

**Example:** 

```json
{
    "weather_list": [
        "CAN_QC_Montreal.Intl.AP.716270_CWEC2020.epw",
        "CAN_NS_Halifax.Dockyard.713280_CWEC2020.epw",
        "CAN_AB_Edmonton.Intl.AP.711230_CWEC2020.epw",
        "CAN_BC_Vancouver.Intl.AP.718920_CWEC2020.epw",
        "CAN_AB_Calgary.Intl.AP.718770_CWEC2020.epw",
        "CAN_ON_Toronto.Intl.AP.716240_CWEC2020.epw",
        "CAN_NT_Yellowknife.AP.719360_CWEC2020.epw",
        "CAN_AB_Fort.Mcmurray.AP.716890_CWEC2020.epw"
    ]
}
```

</blockquote>
</details>

<details>
<summary>
<strong> <a name="disable_costing"></a>8. [Required] Property root > disable_costing</strong>  

</summary>
<blockquote>

|              |           |
| ------------ | --------- |
| **Type**     | `boolean` |
| **Required** | Yes       |
| **Default**  | `true`    |

**Description:** If you do not have access RSMEANs data api. This should be false. Please contact NRCan is you wish to do costed simulations.

</blockquote>
</details>

<details>
<summary>
<strong> <a name="build_btap_cli"></a>9. [Required] Property root > build_btap_cli</strong>  

</summary>
<blockquote>

|              |           |
| ------------ | --------- |
| **Type**     | `boolean` |
| **Required** | Yes       |
| **Default**  | `true`    |

**Description:** **ADVANCED** Build most recent btap_cli always. Set to false to save time if standards and costing branches have not changed.

</blockquote>
</details>

<details>
<summary>
<strong> <a name="build_btap_batch"></a>10. [Required] Property root > build_btap_batch</strong>  

</summary>
<blockquote>

|              |           |
| ------------ | --------- |
| **Type**     | `boolean` |
| **Required** | Yes       |
| **Default**  | `true`    |

**Description:** **ADVANCED** Build most recent btap_batch always. Set to false to save time if standards and costing branches have not changed.

</blockquote>
</details>

<details>
<summary>
<strong> <a name="compute_environment"></a>11. [Required] Property root > compute_environment</strong>  

</summary>
<blockquote>

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

</blockquote>
</details>

----------------------------------------------------------------------------------------------------------------------------
Generated using [json-schema-for-humans](https://github.com/coveooss/json-schema-for-humans) on 2024-02-29 at 15:30:39 -0500
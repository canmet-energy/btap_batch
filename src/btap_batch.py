# docker image prune -f -a ; docker container prune -f ; docker volume prune -f ; docker builder prune -a -f

# docker kill (docker ps -q -a --filter "ancestor=btap_private_cli")

import copy
import os

import uuid
import logging
from random import seed
import numpy as np

from .btap_reference import BTAPReference
from .btap_preflight import BTAPPreflight
from .btap_sampling_lhs import BTAPSamplingLHS
from .btap_optimization import BTAPOptimization
from .btap_parametric import BTAPParametric
from .btap_elimination import BTAPElimination
from .btap_sensitivity import BTAPSensitivity
from .btap_integrated_design_process import BTAPIntegratedDesignProcess
from .helper import batch_factory,load_btap_yml_file

np.random.seed(123)
seed(1)


# Main method that re will interface with. If this gets bigger, consider a factory method pattern.
def btap_batch(analysis_config_file=None, git_api_token=None, batch=None):
    # Load Analysis File into variable
    if not os.path.isfile(analysis_config_file):
        print(f"could not find analysis input file at {analysis_config_file}. Exiting")
        exit(1)
    # Open the yaml in analysis dict
    analysis_config, building_options = load_btap_yml_file(analysis_config_file)
    project_root = os.path.dirname(analysis_config_file)

    # Set Analysis Id if not set
    if (not ':analysis_id' in analysis_config) or analysis_config[':analysis_id'] is None:
        analysis_config[':analysis_id'] = str(uuid.uuid4())

    logfile = os.path.join(project_root, f"{analysis_config[':analysis_id']}.log")
    # remove old logfile if it is there.
    if os.path.exists(logfile):
        os.remove(logfile)

    logging.basicConfig(filename=logfile,
                        filemode='a',
                        format='%(asctime)s, %(levelname)-8s [%(filename)s:%(lineno)d:%(funcName)s] %(message)s',
                        datefmt='%H:%M:%S',
                        level=logging.DEBUG)
    message = f"Log file created: {logfile}"
    print(message)
    logging.info(message)

    print(f"Compute Environment:{analysis_config[':compute_environment']}")
    print(f"Analysis Type:{analysis_config[':algorithm'][':type']}")
    if batch == None:
        batch = batch_factory(
            compute_environment=analysis_config[':compute_environment'],
            analysis_id=analysis_config[':analysis_id'],
            btap_image_name=analysis_config[':image_name'],
            nocache=analysis_config[':nocache'],
            git_api_token=git_api_token,
            os_version=analysis_config[':os_version'],
            btap_costing_branch=analysis_config[':btap_costing_branch'],
            os_standards_branch=analysis_config[':os_standards_branch']
        )



    baseline_results = None
    # Ensure reference run is executed in all other cases unless :run_reference is false.
    if (not ':run_reference' in analysis_config) or (analysis_config[':run_reference'] != False) or (
            analysis_config[':run_reference'] is None):
        # Run reference simulations first.

        analysis_suffix = '_ref'
        algorithm_type = 'reference'
        temp_analysis_config = copy.deepcopy(analysis_config)
        temp_building_options = copy.deepcopy(building_options)
        temp_analysis_config[':algorithm'][':type'] = algorithm_type
        temp_analysis_config[':analysis_name'] = temp_analysis_config[':analysis_name'] + analysis_suffix
        bb = BTAPReference(analysis_config=temp_analysis_config,
                           building_options=temp_building_options,
                           project_root=project_root,
                           git_api_token=git_api_token,
                           batch=batch)
        print(f"running {algorithm_type} stage")
        bb.run()
        baseline_results = os.path.join(bb.results_folder, 'output.xlsx')

    # pre-flight
    if analysis_config[':algorithm'][':type'] == 'pre-flight':
        opt = BTAPPreflight(
            # Input file.
            analysis_config=analysis_config,
            building_options=building_options,
            project_root=project_root,
            git_api_token=git_api_token,
            batch=batch
        )
        return opt
    elif analysis_config[':algorithm'][':type'] == 'reference':
        # Run reference simulations first.
        analysis_suffix = '_ref'
        algorithm_type = 'reference'
        temp_analysis_config = copy.deepcopy(analysis_config)
        temp_building_options = copy.deepcopy(building_options)
        temp_analysis_config[':algorithm'][':type'] = algorithm_type
        temp_analysis_config[':analysis_name'] = temp_analysis_config[':analysis_name'] + analysis_suffix
        bb = BTAPReference(analysis_config=temp_analysis_config,
                           building_options=temp_building_options,
                           project_root=project_root,
                           git_api_token=git_api_token,
                           batch=batch)
        print(f"running {algorithm_type} stage")
        bb.run()
    # LHS
    elif analysis_config[':algorithm'][':type'] == 'sampling-lhs':
        return BTAPSamplingLHS(analysis_config=analysis_config,
                               building_options=building_options,
                               project_root=project_root,
                               git_api_token=git_api_token,
                               batch=batch,
                               baseline_results=baseline_results)
    # nsga2
    elif analysis_config[':algorithm'][':type'] == 'nsga2':
        return BTAPOptimization(analysis_config=analysis_config,
                                building_options=building_options,
                                project_root=project_root,
                                git_api_token=git_api_token,
                                batch=batch,
                                baseline_results=baseline_results)
    # parametric
    elif analysis_config[':algorithm'][':type'] == 'parametric':
        return BTAPParametric(analysis_config=analysis_config,
                              building_options=building_options,
                              project_root=project_root,
                              git_api_token=git_api_token,
                              batch=batch,
                              baseline_results=baseline_results)
    # elimination
    elif analysis_config[':algorithm'][':type'] == 'elimination':
        return BTAPElimination(analysis_config=analysis_config,
                               building_options=building_options,
                               project_root=project_root,
                               git_api_token=git_api_token,
                               batch=batch,
                               baseline_results=baseline_results)
    # Sensitivity
    elif analysis_config[':algorithm'][':type'] == 'sensitivity':
        return BTAPSensitivity(analysis_config=analysis_config,
                               building_options=building_options,
                               project_root=project_root,
                               git_api_token=git_api_token,
                               batch=batch,
                               baseline_results=baseline_results)
    # IDP
    elif analysis_config[':algorithm'][':type'] == 'idp':
        return BTAPIntegratedDesignProcess(analysis_config=analysis_config,
                                           building_options=building_options,
                                           project_root=project_root,
                                           git_api_token=git_api_token,
                                           batch=batch,
                                           baseline_results=baseline_results)
    # osm_batch
    elif analysis_config[':algorithm'][':type'] == 'osm_batch':
        # Need to force this to use the NECB2011 standards class for now.
        return BTAPParametric(analysis_config=analysis_config,
                              building_options=building_options,
                              project_root=project_root,
                              git_api_token=git_api_token,
                              batch=batch)
    else:
        message = f'Unknown algorithm type. Allowed types are nsga2 and parametric. Exiting'
        print(message)
        logging.error(message)
        exit(1)
    if not batch is None:
        batch.tear_down()



    return batch

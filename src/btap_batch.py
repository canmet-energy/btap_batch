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
from .helper import batch_factory
from .btap_engine import BTAPEngine

np.random.seed(123)
seed(1)


# Main method that re will interface with. If this gets bigger, consider a factory method pattern.
def btap_batch(analysis_config_file=None, batch=None):
    # Load Analysis File into variable
    if not os.path.isfile(analysis_config_file):
        print(f"could not find analysis input file at {analysis_config_file}. Exiting")
        exit(1)
    # Open the yaml in analysis dict
    engine = BTAPEngine(analysis_config_file)
    project_root = os.path.dirname(analysis_config_file)

    # Set Analysis Id if not set
    if engine.analysis_config.get(':analysis_id') is None:
        engine.analysis_config[':analysis_id'] = str(uuid.uuid4())

    logfile = os.path.join(project_root, f"{engine.analysis_config[':analysis_id']}.log")
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

    print(f"Compute Environment:{engine.analysis_config[':compute_environment']}")
    print(f"Analysis Type:{engine.analysis_config[':algorithm'][':type']}")
    if batch is None:
        batch = batch_factory(engine)

    # Ensure reference run is executed in all other cases unless :run_reference is false.
    if (engine.analysis_config.get(':run_reference') is not False) or (engine.analysis_config.get(':run_reference') is None):
        # Run reference simulations first.

        analysis_suffix = '_ref'
        algorithm_type = 'reference'
        temp_engine = copy.deepcopy(engine)
        temp_engine.analysis_config[':algorithm'][':type'] = algorithm_type
        temp_engine.analysis_config[':analysis_name'] = temp_engine.analysis_config[':analysis_name'] + analysis_suffix
        temp_engine.analysis_config[':analysis_name'] = temp_engine.analysis_config[':analysis_name']
        bb = BTAPReference(engine=temp_engine, batch=batch)
        print(f"running {algorithm_type} stage")
        bb.run()
        engine.baseline_results = os.path.join(bb.results_folder, 'output.xlsx')

    # pre-flight
    if engine.analysis_config[':algorithm'][':type'] == 'pre-flight':
        opt = BTAPPreflight(engine=engine, batch=batch)
        return opt
    # LHS
    elif engine.analysis_config[':algorithm'][':type'] == 'sampling-lhs':
        return BTAPSamplingLHS(engine=engine, batch=batch)
    # nsga2
    elif engine.analysis_config[':algorithm'][':type'] == 'nsga2':
        return BTAPOptimization(engine=engine, batch=batch)
    # parametric
    elif engine.analysis_config[':algorithm'][':type'] == 'parametric':
        return BTAPParametric(engine=engine, batch=batch)
    # elimination
    elif engine.analysis_config[':algorithm'][':type'] == 'elimination':
        return BTAPElimination(engine=engine, batch=batch)
    # Sensitivity
    elif engine.analysis_config[':algorithm'][':type'] == 'sensitivity':
        return BTAPSensitivity(engine=engine, batch=batch)
    # IDP
    elif engine.analysis_config[':algorithm'][':type'] == 'idp':
        return BTAPIntegratedDesignProcess(engine=engine, batch=batch)
    # osm_batch
    elif engine.analysis_config[':algorithm'][':type'] == 'osm_batch':
        # Need to force this to use the NECB2011 standards class for now.
        return BTAPParametric(engine=engine, batch=batch)
    else:
        message = f'Unknown algorithm type. Allowed types are nsga2 and parametric. Exiting'
        print(message)
        logging.error(message)
        exit(1)
    if batch is not None:
        batch.tear_down()
    return batch

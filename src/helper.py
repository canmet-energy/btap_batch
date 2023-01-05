import os
import logging
import yaml
from .aws_batch import AWSBatch
from .docker_batch import DockerBatch


def batch_factory(engine=None):
    batch = None
    if engine.compute_environment == 'aws_batch':
        # create aws image, set up aws compute env and create workflow queue.
        batch = AWSBatch()
        batch.set_engine(engine=engine)
        # Create batch queue on aws.
        batch.setup()
    elif engine.compute_environment == 'local_docker' or engine.compute_environment == 'local' :
        batch = DockerBatch()
        batch.set_engine(engine=engine)
        # Create batch queue on docker desktop.
        batch.setup()
    else:
        exit(1)
    return batch


# Helper method to load input.yml file into data structures required by btap_batch
def load_btap_yml_file(analysis_config_file):
    # Load Analysis File into variable
    if not os.path.isfile(analysis_config_file):
        logging.error(f"could not find analysis input file at {analysis_config_file}. Exiting")
        exit(1)
    # Open the yaml in analysis dict.
    with open(analysis_config_file, 'r') as stream:
        analysis = yaml.safe_load(stream)
    # Store analysis config and building_options.
    analysis_config = analysis[':analysis_configuration']
    building_options = analysis[':building_options']
    return analysis_config, building_options


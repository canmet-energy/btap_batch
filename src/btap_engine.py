import os
import logging
import yaml
class BTAPEngine:
    # Helper method to load input.yml file into data structures required by btap_batch

    def __init__(self, analysis_config_file=None):
        # Load Analysis File into variable
        if not os.path.isfile(analysis_config_file):
            logging.error(f"could not find analysis input file at {analysis_config_file}. Exiting")
        # Open the yaml in analysis dict.
        with open(analysis_config_file, 'r') as stream:
            analysis = yaml.safe_load(stream)
        # Store analysis config and building_options.
        self.analysis_config = analysis.get(':analysis_configuration')
        self.building_options = analysis.get(':building_options')
        self.git_api_token = os.environ['GIT_API_TOKEN']
        self.project_root = os.path.dirname(analysis_config_file)

        #BTAP Specific
        self.baseline_results = None
        self.docker_build_args = {
            # Git token to access private repositories.
            'GIT_API_TOKEN': self.git_api_token,
            # Openstudio version.... like '3.0.1'
            'OPENSTUDIO_VERSION': self.analysis_config[':os_version'],
            # BTAP costing branch. Usually 'master'
            'BTAP_COSTING_BRANCH': self.analysis_config[':btap_costing_branch'],
            # Openstudio standards branch Usually 'nrcan'
            'OS_STANDARDS_BRANCH': self.analysis_config[':os_standards_branch']
        }
        return

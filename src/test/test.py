import src.btap_batch as btap_batch
import os
import logging
import yaml

# Optimization data block.
optimization = {
                ":type": "nsga2",
                ":population": 30,
                ":n_generations": 2,
                ":prob": 0.85,
                ":eta": 3.0,
                ":minimize_objectives": [
                    "cost_utility_neb_total_cost_per_m_sq",
                    "cost_equipment_total_cost_per_m_sq"]
}


# Displays logging.. Set to INFO or DEBUG for a more verbose output.
logging.basicConfig(level=logging.ERROR)

# Your git token.. Do not commit this!
git_api_token = ""

# Set input file path.
# Use file in example folder for tests.
input_file = os.path.join(os.path.dirname(os.path.realpath(__file__)),'..','..','example','example.yml')
new_file = os.path.join(os.path.dirname(os.path.realpath(__file__)),'new_file.yml')

# Local Parametric Test
analysis = btap_batch.btap_batch( analysis_config_file=input_file, git_api_token=git_api_token)
analysis.run()

# Local Optimization Test
with open(input_file, 'r') as stream:
    analysis = yaml.safe_load(stream)
analysis[':analysis_configuration'][':algorithm'] = optimization
with open(new_file, 'w') as outfile:
    yaml.dump(analysis, outfile)
analysis = btap_batch.btap_batch( analysis_config_file=new_file, git_api_token=git_api_token)
analysis.run()

# AWS Parametric Test
with open(input_file, 'r') as stream:
    analysis = yaml.safe_load(stream)
# Set to run on aws.
analysis[':analysis_configuration'][':compute_environment'] = 'aws_batch'
with open(new_file, 'w') as outfile:
    yaml.dump(analysis, outfile)
analysis = btap_batch.btap_batch( analysis_config_file=new_file, git_api_token=git_api_token)
analysis.run()

# AWS Optimization Test
with open(input_file, 'r') as stream:
    analysis = yaml.safe_load(stream)
analysis[':analysis_configuration'][':compute_environment'] = 'aws_batch'
analysis[':analysis_configuration'][':algorithm'] = optimization
with open(new_file, 'w') as outfile:
    yaml.dump(analysis, outfile)
analysis = btap_batch.btap_batch( analysis_config_file=new_file, git_api_token=git_api_token)
analysis.run()

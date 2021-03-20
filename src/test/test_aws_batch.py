import src.btap_batch as btap_batch
import os
import logging
import yaml

# Displays logging.. Set to INFO or DEBUG for a more verbose output.
logging.basicConfig(level=logging.ERROR)

# Your git token.. Do not commit this!
git_api_token = os.environ['GIT_API_TOKEN']


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

# Set input file path.
# Use file in example folder for tests.
input_file = os.path.join(os.path.dirname(os.path.realpath(__file__)),'..','..','examples','parametric','example.yml')

# AWS Parametric Test
test_name = 'test_parametric_aws_batch'
with open(input_file, 'r') as stream:
    analysis = yaml.safe_load(stream)
analysis[':analysis_configuration'][':analysis_name'] = test_name
analysis[':analysis_configuration'][':compute_environment'] = 'aws_batch'
new_file = os.path.join(os.path.dirname(os.path.realpath(__file__)),f'{test_name}.yml')
with open(new_file, 'w') as outfile:
    yaml.dump(analysis, outfile)
analysis = btap_batch.btap_batch( analysis_config_file=new_file, git_api_token=git_api_token)
analysis.run()

# AWS Parametric Test
test_name = 'test_optimization_aws_batch'
with open(input_file, 'r') as stream:
    analysis = yaml.safe_load(stream)
analysis[':analysis_configuration'][':algorithm'] = optimization
analysis[':analysis_configuration'][':analysis_name'] = test_name
analysis[':analysis_configuration'][':compute_environment'] = 'aws_batch'
new_file = os.path.join(os.path.dirname(os.path.realpath(__file__)),f'{test_name}.yml')
with open(new_file, 'w') as outfile:
    yaml.dump(analysis, outfile)
analysis = btap_batch.btap_batch( analysis_config_file=new_file, git_api_token=git_api_token)
analysis.run()


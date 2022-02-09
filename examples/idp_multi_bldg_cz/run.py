import src.btap_batch as btap
import os

# Your git token.. Do not commit this!
git_api_token = os.environ['GIT_API_TOKEN']

# Set input file path.
input_file = os.path.join(os.path.dirname(os.path.realpath(__file__)),'input.yml')

# Initialize the analysis object.
bb = btap.btap_batch(
    # Input file.
    analysis_config_file=input_file,
    git_api_token=git_api_token
)

# Run the analysis
bb.run()
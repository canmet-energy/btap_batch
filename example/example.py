import src.btap_batch as btap_batch
import os
import logging

# Displays logging.. Set to INFO or DEBUG for a more verbose output.
logging.basicConfig(level=logging.ERROR)

# Your git token.. Do not commit this!
git_api_token = os.environ['GIT_API_TOKEN']

# Set input file path.
input_file = os.path.join(os.path.dirname(os.path.realpath(__file__)),'example.yml')

# Initialize the analysis object.
bb = btap_batch.btap_batch(
    # Input file.
    analysis_config_file=input_file,
    git_api_token=git_api_token
)

# Run the analysis
bb.run()
# print dataframe
print(bb.btap_data_df)
# print failed simulations, if any.
print(bb.failed_df)
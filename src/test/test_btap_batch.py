import unittest
import src.btap_batch as btap
import os
import logging
import yaml
from pathlib import Path
import warnings
import shutil

class TestBTAPBatch(unittest.TestCase):
    first_test = True

    def setUp(self):
        # Workaround for this warning https://github.com/boto/boto3/issues/454
        warnings.filterwarnings("ignore", category=ResourceWarning, message="unclosed.*<ssl.SSLSocket.*>")

        # Displays logging.. Set to INFO or DEBUG for a more verbose output.
        logging.basicConfig(level=logging.ERROR)


        # Your git token.. Do not commit this!
        self.git_api_token = os.environ['GIT_API_TOKEN']

        #Change this to aws_batch to run tests on amazon.
        self.compute_environment = 'local'

        self.os_version = '3.2.1'

        #Change to test on other branches.
        self.os_standards_branch = 'nrcan'

        # Branch from https://github.com/canmet-energy/btap_costing. Typically 'master'
        self.btap_costing_branch = 'master'

        # Branch from https://github.com/canmet-energy/btap_costing. Typically 'master'
        self.image_name = 'btap_private_cli'

        # Use no_cache
        self.no_cache = True

    def run_analysis(self, input_file=None):

        #Get basename
        basename = Path(input_file).stem

        #Get Folder name
        folder_name = os.path.dirname(input_file)

        #Load yaml file.
        # Open the yaml in analysis dict.
        with open(input_file, 'r') as stream:
            analysis = yaml.safe_load(stream)

        #Change options
        analysis[':analysis_configuration'][':compute_environment'] = self.compute_environment
        analysis[':analysis_configuration'][':os_standards_branch'] = self.os_standards_branch
        analysis[':analysis_configuration'][':btap_costing_branch'] = self.btap_costing_branch
        analysis[':analysis_configuration'][':image_name'] = self.image_name
        analysis[':analysis_configuration'][':os_version'] = self.os_version

        #This will check if we already ran a test.. if so we will not rebuild the images.
        if self.__class__.first_test  == True:
            analysis[':analysis_configuration'][':nocache'] = self.no_cache
            self.__class__.first_test  = False
        else:
            analysis[':analysis_configuration'][':nocache'] = False


        #mk folder for test.
        test_output_folder = os.path.join(os.getcwd(),'test_output',f'{self.compute_environment}_{basename}')

        # Check if folder exists
        if os.path.isdir(test_output_folder):
            # Remove old folder
            try:
                shutil.rmtree(test_output_folder)
            except PermissionError as err:
                message = f'Could not delete {test_output_folder}. Do you have a file open in that folder? Exiting'
                print(message)
                logging.error(message)
                exit(1)



        #Copy example folder
        source_dir = folder_name
        destination_dir = test_output_folder
        shutil.copytree(source_dir, destination_dir)

        #Save new input yml file in folder in tests
        test_configuration_file = os.path.join(test_output_folder,'input.yml')
        with open(test_configuration_file, 'w') as outfile:
            yaml.dump(analysis, outfile, default_flow_style=False)

        #Run analysis
        # Initialize the analysis object and run.
        bb = btap.btap_batch( analysis_config_file=test_configuration_file, git_api_token=self.git_api_token)
        bb.run()
        excel_path = os.path.join(bb.project_root, bb.analysis_config[':analysis_name'], bb.analysis_config[':analysis_id'], 'results', 'output.xlsx')
        assert os.path.isfile(excel_path), 'Output.xlsx was not created'
        return bb

    def test_elimination(self):
        self.run_analysis(input_file=os.path.join(os.path.dirname(os.path.realpath(__file__)),'..','..','examples', 'elimination', f'elimination.yml'))

    def test_sensitivity(self):
        self.run_analysis(input_file=os.path.join(os.path.dirname(os.path.realpath(__file__)),'..','..','examples','sensitivity', 'sensitivity.yml'))

    def test_optimization(self):
        self.run_analysis(input_file=os.path.join(os.path.dirname(os.path.realpath(__file__)),'..','..','examples','optimization', 'optimization.yml'))

    def test_sample_lhs(self):
        self.run_analysis(input_file=os.path.join(os.path.dirname(os.path.realpath(__file__)),'..','..','examples','sample-lhs', 'sample-lhs.yml'))

    def test_custom_osm(self):
        bb = self.run_analysis(input_file=os.path.join(os.path.dirname(os.path.realpath(__file__)),'..','..','examples', 'custom_osm', 'custom_osm.yml'))

    def test_osm_batch(self):
        self.run_analysis(input_file=os.path.join(os.path.dirname(os.path.realpath(__file__)),'..','..','examples','osm_batch', 'osm_batch.yml'))

    def test_parametric(self):
        self.run_analysis(input_file=os.path.join(os.path.dirname(os.path.realpath(__file__)),'..','..','examples','parametric', 'parametric.yml'))


if __name__ == '__main__':
    unittest.main()




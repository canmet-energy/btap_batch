import unittest
from unittest import TestCase
import src.btap_batch as btap
import os
from pathlib import Path
import warnings
import shutil
import uuid
import jsonschema
import json
import glob
import icecream as ic
import pathlib
import yaml

THIS_FOLDER = pathlib.Path(__file__).parent.resolve()
PROJECT_FOLDER = os.path.join(pathlib.Path(__file__).parent.resolve(), '..', '..')
# Location of input.yml schema
BTAP_BATCH_INPUT_SCHEMA = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), '..','..', 'resources', 'btap_batch_json_schema.json')

class TestBTAPBatch(unittest.TestCase):
    first_test = True

    @classmethod
    def setUpClass(cls):
        # Workaround for this warning https://github.com/boto/boto3/issues/454
        warnings.filterwarnings("ignore", category=ResourceWarning, message="unclosed.*<ssl.SSLSocket.*>")


        # Your git token.. Do not commit this!
        cls.git_api_token = os.environ['GIT_API_TOKEN']

        #Change this to aws_batch to run tests on amazon.
        cls.compute_environment = 'local'

        cls.os_version = '3.2.1'

        #Change to test on other branches.
        cls.os_standards_branch = 'nrcan'

        # Branch from https://github.com/canmet-energy/btap_costing. Typically 'master'
        cls.btap_costing_branch = 'master'

        # Use no_cache
        cls.no_cache =  False


        # Set aws_batch object to None intially.
        cls.batch = None


        # If aws_batch is selected...create single aws_batch workflow object to be used for all tests to save time.
        if cls.compute_environment == 'aws_batch':
            # create aws image, set up aws compute env and create workflow queue.

            cls.batch = btap.AWSBatch(
                analysis_id=str(uuid.uuid4()),
                btap_image_name=cls.image_name,
                rebuild_image=cls.no_cache,
                git_api_token=cls.git_api_token,
                os_version=cls.os_version,
                btap_costing_branch=cls.btap_costing_branch,
                os_standards_branch=cls.os_standards_branch,
            )
            # Create batch queue on aws.
            cls.batch.setup()


        test_output_folder = os.path.join(THIS_FOLDER, 'test_output')
        print(f"deleting {test_output_folder}.....")
        # Check if folder exists
        if os.path.isdir(test_output_folder):
            # Remove old folder
            try:
                shutil.rmtree(test_output_folder)
            except PermissionError as err:
                message = f'Could not delete {test_output_folder}. Do you have a file open in that folder? Exiting'
                print(message)
                exit(1)
        print("deleted..")

    def run_analysis(self, input_file=None):

        #Get Folder name
        folder_name = os.path.dirname(input_file)

        #Get basename
        basename = Path(folder_name).stem

        #Load yaml file.
        # Open the yaml in analysis dict.
        print("Opening Yaml file.")
        with open(input_file, 'r') as stream:
            analysis = yaml.safe_load(stream)

        #Change options
        print("Changing Options")
        analysis[':analysis_configuration'][':compute_environment'] = TestBTAPBatch.compute_environment
        analysis[':analysis_configuration'][':os_standards_branch'] = TestBTAPBatch.os_standards_branch
        analysis[':analysis_configuration'][':btap_costing_branch'] = TestBTAPBatch.btap_costing_branch
        analysis[':analysis_configuration'][':os_version'] = TestBTAPBatch.os_version


        #This will check if we already ran a test.. if so we will not rebuild the images.
        if self.__class__.first_test  == True:
            analysis[':analysis_configuration'][':nocache'] = TestBTAPBatch.no_cache
            self.__class__.first_test  = False
        else:
            analysis[':analysis_configuration'][':nocache'] = False


        #mk folder for test.

        test_output_folder = os.path.join(os.getcwd(),'test_output',f'{TestBTAPBatch.compute_environment}_{basename}')

        # Check if folder exists
        if os.path.isdir(test_output_folder):
            # Remove old folder
            try:
                shutil.rmtree(test_output_folder)
            except PermissionError as err:
                message = f'Could not delete {test_output_folder}. Do you have a file open in that folder? Exiting'
                print(message)
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
        bb = btap.btap_batch( analysis_config_file=test_configuration_file, git_api_token=TestBTAPBatch.git_api_token,batch=TestBTAPBatch.batch)
        bb.run()
        excel_path = os.path.join(bb.project_root, bb.analysis_config[':analysis_name'], bb.analysis_config[':analysis_id'], 'results', 'output.xlsx')
        assert os.path.isfile(excel_path), 'Output.xlsx was not created'

    def test_validate_input_yml_files(self):
        yaml_files = glob.glob(PROJECT_FOLDER + '/**/input.yml', recursive=True)

        with open(BTAP_BATCH_INPUT_SCHEMA) as json_file:
            schema = json.load(json_file)

        for yml_file in yaml_files:
            import jsonschema
            with open(yml_file, "r") as stream:
                try:
                    file_yml = (yaml.safe_load(stream))
                    jsonschema.validate(instance=file_yml, schema=schema)
                except yaml.YAMLError as exc:
                    print(exc)
                    print("The yml file is not structured correctly. Please fix your file.")
                    mark = exc.problem_mark
                    print(f'File "{analysis_config_file}:{mark.line + 1}"')
                    return self.fail()
                except jsonschema.exceptions.ValidationError as error:
                    print(
                        f"Your input file contains invalid options according to the btap schema. Please ensure your inputs are correct. If you are a developer, ensure that you have added your new options to the json schema defined here {BTAP_BATCH_INPUT_SCHEMA}. See below error.")
                    print(f"{error.message} at  {error.json_path} in {yml_file}")
                    return self.fail()

    def test_elimination(self):
        self.run_analysis(input_file=os.path.join(os.path.dirname(os.path.realpath(__file__)),'..','..','examples', 'elimination', 'input.yml'))

    def test_sensitivity(self):
        print("Running Sensitivity Test...")
        self.run_analysis(input_file=os.path.join(os.path.dirname(os.path.realpath(__file__)),'..','..','examples','sensitivity', 'input.yml'))

    def test_optimization(self):
        self.run_analysis(input_file=os.path.join(os.path.dirname(os.path.realpath(__file__)),'..','..','examples','optimization', 'input.yml'))

    def test_sample_lhs(self):
        self.run_analysis(input_file=os.path.join(os.path.dirname(os.path.realpath(__file__)),'..','..','examples','sample-lhs', 'input.yml'))

    def test_custom_osm(self):
        self.run_analysis(input_file=os.path.join(os.path.dirname(os.path.realpath(__file__)),'..','..','examples', 'custom_osm', 'input.yml'))

    def test_osm_batch(self):
        self.run_analysis(input_file=os.path.join(os.path.dirname(os.path.realpath(__file__)),'..','..','examples','osm_batch', 'input.yml'))

    def test_parametric(self):
        self.run_analysis(input_file=os.path.join(os.path.dirname(os.path.realpath(__file__)),'..','..','examples','parametric', 'input.yml'))

if __name__ == '__main__':
    unittest.main()


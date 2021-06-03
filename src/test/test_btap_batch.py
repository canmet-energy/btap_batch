import unittest
import src.btap_batch as btap
import os
import logging
import yaml



class TestBTAPBatch(unittest.TestCase):
    def setUp(self):

        # Displays logging.. Set to INFO or DEBUG for a more verbose output.
        logging.basicConfig(level=logging.ERROR)

        # Your git token.. Do not commit this!
        self.git_api_token = os.environ['GIT_API_TOKEN']

    def run_analysis(self, input_file=None):
        # Displays logging.. Set to INFO or DEBUG for a more verbose output.
        logging.basicConfig(level=logging.ERROR)

        # Your git token.. Do not commit this!
        git_api_token = os.environ['GIT_API_TOKEN']

        # Initialize the analysis object and run.
        btap.btap_batch( analysis_config_file=input_file, git_api_token=git_api_token).run()

    def test_elimination(self):
        self.run_analysis(input_file=os.path.join(os.path.dirname(os.path.realpath(__file__)),'..','..','examples','elimination', 'elimination.yml'))
    #
    # def test_sensitivity(self):
    #     self.run_analysis(input_file=os.path.join(os.path.dirname(os.path.realpath(__file__)),'..','..','examples','sensitivity', 'sensitivity.yml'))
    #
    # def test_optimization(self):
    #     self.run_analysis(input_file=os.path.join(os.path.dirname(os.path.realpath(__file__)),'..','..','examples','optimization', 'optimization.yml'))
    #
    # def test_parametric(self):
    #     self.run_analysis(input_file=os.path.join(os.path.dirname(os.path.realpath(__file__)),'..','..','examples','parametric', 'parametric.yml'))
    #
    # def test_sample_lhs(self):
    #     self.run_analysis(input_file=os.path.join(os.path.dirname(os.path.realpath(__file__)),'..','..','examples','sample_lhs', 'sample_lhs.yml'))

if __name__ == '__main__':
    unittest.main()




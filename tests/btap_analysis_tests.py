import unittest
import os
from pathlib import Path
import sys
from icecream import ic

from src.btap.cli_helper_methods import analysis
PROJECT_ROOT = str(Path(os.path.dirname(os.path.realpath(__file__))).parent.absolute())
sys.path.append(PROJECT_ROOT)
PROJECT_FOLDER = os.path.join(Path(os.path.dirname(os.path.realpath(__file__))).parent.absolute())
EXAMPLE_FOLDER = os.path.join(PROJECT_FOLDER,'examples')
OUTPUT_FOLDER = os.path.join(PROJECT_FOLDER, "output")
COMPUTE_ENVIRONMENT='local_docker'



class MyTestCase(unittest.TestCase):
    def test_analyses(self):
        for folder in ['custom_osm',
                       'elimination',
                       'optimization',
                       'parametric',
                       'reference_only',
                       'sample-lhs',
                       'sensitivity']:
            project_input_folder = os.path.join(EXAMPLE_FOLDER,folder)
            analysis(project_input_folder=project_input_folder, compute_environment='local_docker', reference_run=True, output_folder=OUTPUT_FOLDER)


if __name__ == '__main__':
    unittest.main()

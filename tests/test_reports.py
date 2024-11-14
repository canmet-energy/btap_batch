
import unittest
import os
from pathlib import Path
import sys
PROJECT_ROOT = str(Path(os.path.dirname(os.path.realpath(__file__))).parent.absolute())
sys.path.append(PROJECT_ROOT)
from src.btap.reports import generate_btap_reports
# Only after you do a example run can you run this test.
data_file = r"..\output\optimization_example\results\output.xlsx"
output_folder = r"..\output\optimization_example\results"
generate_btap_reports(data_file=data_file, pdf_output_folder=output_folder)
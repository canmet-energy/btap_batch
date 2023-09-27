import pandas as pd
from src.btap.btap_sensitivity import BTAPSensitivity


df = pd.read_excel(r'C:\Users\plopez\btap_batch\output\parametric_example\parametric\output.xlsx', index_col=0)
BTAPSensitivity.generate_pdf_report(df)

bp = BTAPSensitivity.run_sensitivity_best_packages(
    output_folder=r"C:\Users\plopez\btap_batch\output",
    project_input_folder=r"C:\Users\plopez\btap_batch\examples\sensitivity",
    df = df)
bp.run()
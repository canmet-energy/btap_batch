import pandas as pd
from src.btap.btap_sensitivity import BTAPSensitivity


df = pd.read_excel(r'C:\Users\plopez\btap_batch\output\sensitivity_example\sensitivity\results\output.xlsx', index_col=0)
BTAPSensitivity.generate_pdf_report(df)
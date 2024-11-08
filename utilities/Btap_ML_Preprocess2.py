import pandas as pd
import os

# Paths to your directories
csv_dir = './output/revised' 
output_excel = './output/test_for_btap_ml_output.xlsx'  

output_data = pd.read_excel(output_excel)

for _, row in output_data.iterrows():
    datapoint_id = row[':datapoint_id']  
    csv_file_path = os.path.join(csv_dir, f"{datapoint_id}.csv")
    
    if os.path.exists(csv_file_path):
        # Load the corresponding CSV file
        csv_data = pd.read_csv(csv_file_path)
        
        # Drop the non-data columns (such as 'Unnamed: 0') from the row
        data_row = row.drop(['Unnamed: 0', ':datapoint_id']) 
        
        # Duplicate the row values to match the 8760 hours (assuming hourly data)
        duplicated_data = pd.DataFrame([data_row.values] * 8760, columns=data_row.index)
        
        # Concatenate the duplicated data to the CSV data
        combined_data = pd.concat([csv_data, duplicated_data], axis=1)
        
        # Save the updated CSV file
        combined_data.to_csv(csv_file_path, index=False)
        print(f"Updated {datapoint_id}.csv successfully.")
    else:
        print(f"File {datapoint_id}.csv not found.")

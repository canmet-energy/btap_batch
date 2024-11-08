import pandas as pd
import os

# Path to the directory containing the CSV files
directory = './output/hourly'
directory2 = './output/revised'

if not os.path.exists(directory2):
    os.makedirs(directory2)

# Loop through each file in the directory
for filename in os.listdir(directory):
    if filename.endswith('.csv'):
        # Load the CSV file
        file_path = os.path.join(directory, filename)
        df = pd.read_csv(file_path)



        # Calculate the averages for each required variable
        avg_people_occupant_count = df[df['Name'] == 'People Occupant Count'].iloc[:, 4:].mean()
        avg_lights_electricity_energy = df[df['Name'] == 'Lights Electricity Energy'].iloc[:, 4:].mean()
        avg_zone_cooling_setpoint = df[(df['Name'] == 'Zone Thermostat Cooling Setpoint Temperature') & 
                               (df['KeyValue'] != 'ALL_ST=- UNDEFINED -_FL=BUILDING STORY 2_SCH=A')].iloc[:, 4:].mean()
        avg_zone_heating_setpoint = df[(df['Name'] == 'Zone Thermostat Heating Setpoint Temperature') & 
                               (df['KeyValue'] != 'ALL_ST=- UNDEFINED -_FL=BUILDING STORY 2_SCH=A')].iloc[:, 4:].mean()
        
        # Other required variables without averaging
        total_electricity = df[df['Name'] == 'Electricity:Facility'].iloc[:, 4:].values.flatten()
        total_cooling = df[df['Name'] == 'Cooling:Electricity'].iloc[:, 4:].values.flatten()
        total_heating = df[df['Name'] == 'Heating:Electricity'].iloc[:, 4:].values.flatten()

        # Combine the averages and other required variables into a single DataFrame with timestamps as index
        averaged_data = pd.DataFrame({
            'Date': df.columns[4:],  # Take the dates from the original columns
            'average People Occupant Count': avg_people_occupant_count.values,
            'average Lights Electricity Energy': avg_lights_electricity_energy.values,
            'average Zone Thermostat Cooling Setpoint Temperature': avg_zone_cooling_setpoint.values,
            'average Zone Thermostat Heating Setpoint Temperature': avg_zone_heating_setpoint.values,
            'Electricity Facility': total_electricity,
            'Cooling Consumption': total_cooling,
            'Heating Consumption': total_heating
        })

        # Save the final DataFrame to a new CSV file
        #output_file_path = os.path.join(directory2, 'processed_' + filename)
        output_file_path = os.path.join(directory2,filename)
        averaged_data.to_csv(output_file_path, index=False)

print("Processing complete for all CSV files.")

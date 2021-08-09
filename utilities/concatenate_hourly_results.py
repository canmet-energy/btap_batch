# This script should be placed in the main analysis directory of a btap_batch run.  It will go through the datapoints
# in the analysis and collect all of the hourly data into one csv called 'total_hourly_res.csv'.  This is saved in
# The same location as the output.xlsx file which is in the output directory.

import os

# Get the output directory and the location of the output file
curr_dir = os.getcwd()
data_dir = f"{curr_dir}/output/"
output_file = os.path.join(data_dir, "total_hourly_res.csv")

# Initilalize the output list
concat_data = []

# first_read is used to determine weather or not to write the header to the output file
first_read = True

# Go through all of the objects in the output folder
for file_object in os.listdir(data_dir):
    # Set the absolute location of the current file object we are looking at
    datapoint = os.path.join(data_dir, file_object)
    # If it is a directory look for the hourly.csv file
    if os.path.isdir(datapoint):
        hourly_output_file = os.path.join(datapoint, "hourly.csv")
        # If and hourly.csv file exists then add its contents to the output list
        if os.path.isfile(hourly_output_file):
            with open(hourly_output_file) as f:
                lines = f.readlines()
                line_num = 0
                # If this is the first time looking at a file add the header data to the output list, otherwise don't
                for line in lines:
                    if first_read and line_num == 0:
                        concat_data.append(line)
                        first_read = False
                    if line_num > 0:
                        concat_data.append(line)
                    line_num += 1

# Write the output list to a file
f_out = open(output_file, 'w')
for out_line in concat_data:
    f_out.write(out_line)
f_out.close()
# This script should be placed in the hourly.csv directory of the results directory of a btap_batch run.  It will go
# through the hourly results csv for each datapoint in the folder and collect them all into one csv file called
# 'total_hourly_res.csv'.  The 'tatal_hourly_res.csv' file is saved in the same directory as the individual hourly
# results files.

import os

# Get the output directory and the location of the output file
curr_dir = os.getcwd()
output_file = os.path.join(curr_dir, "total_hourly_res.csv")

# Initilalize the output list
concat_data = []

# first_read is used to determine weather or not to write the header to the output file
first_read = True

# Go through all of the objects in the output folder
for file_object in os.listdir(curr_dir):
    # Set the absolute location of the current file object we are looking at
    datapoint = os.path.join(curr_dir, file_object)
    # Check if it is a file
    if os.path.isfile(datapoint):
        # If it is a file check if it is a csv file
        if str(datapoint).lower().endswith('.csv'):
            # If it is a csv file make sure it is not the output file
            if str(datapoint).lower() != "total_hourly_res.csv":
                # Open the file and add it to the concat_data list which collects the hourly data from all of the files
                with open(datapoint) as f:
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

# Write the hourly data list to the output file
f_out = open(output_file, 'w')
for out_line in concat_data:
    f_out.write(out_line)
f_out.close()
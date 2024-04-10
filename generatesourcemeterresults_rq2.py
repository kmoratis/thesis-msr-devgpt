import os
import glob
import os
import subprocess
from properties import sourcemeterdir, resultspath

# execute the SourceMeter analysis
subprocess.run(["python", "-m", "scripts.executesourcemeter_rq2"])

# construct the search path for the results JSON file
search_path = os.path.join(sourcemeterdir, f"results/rq2/javascript/")

# use glob to find the JSON file with the desired results
file_paths = glob.glob(f"{search_path}**/rq2-Patterns.txt", recursive=True)

# There is only one file per version
file_path = file_paths[0]

# Copy the file to the results folder, preserving the file's name
destination_dir_path = os.path.join(resultspath, "sourcemeter\\")
destination_file_path = os.path.join(destination_dir_path, os.path.basename(file_path))

# Ensure the destination directory exists
os.makedirs(destination_dir_path, exist_ok=True)

# Open the source file for reading
with open(file_path, 'r') as source_file:
   lines_to_copy = []
   for line in source_file:
      # Check if the line is blank (only newline character)
      if line.strip() == '':
            break  # Exit the loop if a blank line is found
      lines_to_copy.append(line)


with open(destination_file_path, 'w') as destination_file:
   destination_file.writelines(lines_to_copy)

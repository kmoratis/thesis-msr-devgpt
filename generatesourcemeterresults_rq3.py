import os
import glob
import subprocess
from properties import sourcemeterdir, resultspath

def analyze_and_extract_results(version):
	"""
	Executes SourceMeter analysis for a given version, then filters and
	extracts detected Patterns and saves them to results.
	"""
	# execute the SourceMeter analysis
	subprocess.run(["python", "-m", "scripts.executesourcemeter_rq3", version])

	# construct the search path for the results JSON file
	search_path = os.path.join(sourcemeterdir, f"results/rq3_{version}/javascript/")

	# use glob to find the results summary JSON file
	file_paths = glob.glob(f"{search_path}**/rq3_{version}-Patterns.txt", recursive=True)
	
	# check if file was found
	if not file_paths:
		print(f"No summary JSON found for version: {version}")
		return
	
	# only one file per version
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

# Extract the data for the previous version of the files
version = "previous"
analyze_and_extract_results(version)

# Extract the data for the current version of the files
version = "current"
analyze_and_extract_results(version)

import subprocess
from properties import sourcemeterjs

""" Script to check that the PMD tool is executed correctly. """

project_path = "./test/test_proj"
project_name = "test"
results_path = "./test/results"

# Define the PMD check command
cpd_command = f"{sourcemeterjs} -projectBaseDir={project_path} -resultsDir={results_path} -projectName={project_name} -runDCF:false -cleanResults:0"

# Run the command and capture the output
output = subprocess.run(cpd_command, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

print(output)

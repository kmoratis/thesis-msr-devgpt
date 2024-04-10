import subprocess
from properties import pmd

""" Script to check that the PMD tool is executed correctly. """

# Example JS code to check correct execution: "file3.js"
# Example of generated code with AvoidTrailingComma violation: "gencommaviolation.js"
# Example of generated code with GlobalVariable violation: "genglobalviolation.js"
# Example of generated code with UnnecessaryBlock violation: "genblockviolation.js"

file_path = r"./test/genglobalviolation.js"

# Define the PMD check command
cpd_command = f"{pmd} check {file_path} -f text --no-cache -R ./pmdrulesets/javascriptruleset.xml"

# Run the command and capture the output
output = subprocess.run(cpd_command, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# If quality violations found
if output.returncode == 4:
	# Compute the total number of violations and save it to dictionary
	output_message = output.stdout
	print(output_message)

# If no quality violations found
elif output.returncode == 0: 
	print('No violations found')

# If PMD-check finished with error
else:
	print('Error in quality analysis')

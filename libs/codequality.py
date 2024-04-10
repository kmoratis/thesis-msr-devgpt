import os
import shutil
import tempfile
import subprocess
from collections import defaultdict
from properties import pmd, sourcemeterjs, sourcemeterdir


def before_after_violations(file):
	"""
	This function takes a file object and calculates and returns the number of quality violations
	found in the current and the previous versions of the file, using the PMD check.
	
	:param file: A dictionary containing information about a commited file
	:return: The function `before_after_violations` returns a dictionary containing the number of
	quality violations found for each version of the file (current and previous versions). The keys in
	the dictionary represent the file versions ("Current" and "Previous"), and the values represent the
	total number of violations found in each version. If no violations are found for a version, the
	value will be 0.
	"""

	# Define dictionary to store number of violations found for each version
	violations = {}

	# Retrieve the file's extension
	file_extension = file['Extension']

	# Retrieve file's content from patch (current and previous versions)
	# Check ff previous content exist (File was not created during the specific commit)
	if len(file['PrevContent']):
		version_list = {"Current": file['Content'], "Previous": file['PrevContent']}
	else:
		# Create dictionary containing only the current content
		version_list = {"Current": file['Content']}
		violations["Previous"] = "No previous file version"

	# For each file version (before-after Chatgpt code insertion), calculate the quality violations
	for version, file_content in version_list.items():

		# Create temporary file to store the code file's content
		with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='cp437', errors="ignore", suffix=file_extension) as temp_file:
			temp_file.write(file_content)

		# Get temporary file's path
		temp_file_path = temp_file.name

		# Create the ruleset relative path according to the file's language
		ruleset_path = f"pmdrulesets\javascriptruleset.xml"

		# Define the PMD check command
		cpd_command = f"{pmd} check {temp_file_path} -f text --no-cache -R {ruleset_path}"
		
		# Run the command and capture the output
		output = subprocess.run(cpd_command, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

		# If quality violations found
		if output.returncode == 4:
			# Compute the total number of violations and save it to dictionary
			output_message = output.stdout
			total_violations = len(output_message.splitlines())
			violations[version] = total_violations

		# If no quality violations found
		elif output.returncode == 0: 
			violations[version] = 0
		
		# If PMD-check finished with error
		else:
			print('Error in before-after quality analysis')
			return -1

	return violations


def block_quality_violations(dbobj, idx=0):
	"""
	This function calculates the number of quality violations in code blocks of a shared
	conversation and returns the updated conversation object. Also, for every code clone detected in the dbobj, 
	the function finds the code block from which the code was copied and adds a `Copied` attribute to it
	
	:param dbobj: A database object that contains the information about a commit or a file object
	:param idx: An optional parameter that specifies the index of the link in the `ChatgptSharing` list.
	If not provided, it defaults to 0, indicating the first shared link it the list
	:returns: The updated `sharing` object with the added `Violations` attribute for each supported
	code block in each conversation, and with `Copied` attribute added to every code block that was copied.
	The function returns (-1) if the PMD finished with error.
	"""

	# Get the information of the shared conversation
	sharing = dbobj['ChatgptSharing'][idx]

	# Create attribute specifying the block from which the clone was copied
	for file in sharing['AnalysisFeatures']['FileAnalysis']:
		if file.get('LinesCopied', -1) > 0:
			block_idx = file['CodeBlockIdx']

			# Specify the block from which the clone was copied
			for i, conversation in enumerate(sharing.get('Conversations', [])):
				if block_idx - len(conversation['ListOfCode']) > 0:
					block_idx -= len(conversation['ListOfCode'])
				else:
					conversation['ListOfCode'][block_idx - 1]['Copied'] = True
					sharing['Conversations'][i] = conversation
					break

	# Define a dictionary containing the 'name': 'category' of the supported violations for javascript
	javascript_violations = {'GlobalVariable': 'BestPractices',
								  'AvoidWithStatement': 'BestPractices',
								  'ConsistentReturn': 'BestPractices', 
								  'ScopeForInVariable': 'BestPractices',
								  'UseBaseWithParseInt': 'BestPractices',
								  'AssignmentInOperand': 'CodeStyle',
								  'ForLoopsMustUseBraces': 'CodeStyle',
								  'IfElseStmtsMustUseBraces': 'CodeStyle', 
								  'IfStmtsMustUseBraces': 'CodeStyle', 
								  'NoElseReturn': 'CodeStyle', 
								  'UnnecessaryBlock': 'CodeStyle', 
								  'UnnecessaryParentheses': 'CodeStyle',
								  'UnreachableCode': 'CodeStyle',
								  'WhileLoopsMustUseBraces': 'CodeStyle',
								  'AvoidTrailingComma': 'ErrorProne',
								  'EqualComparison': 'ErrorProne',
								  'InnaccurateNumericLiteral': 'ErrorProne'
								  }

	# For every generated code block in every conversation of the shared link, calculate the violations
	for i, conversation in enumerate(sharing.get('Conversations', [])):
		# Define variable to specify whether the content of the conversation changed, in order to save it
		conv_changed = False
		for j, code in enumerate(conversation['ListOfCode'].copy()):

			# Initialize variables
			total_violations = 0
			violations_by_cat = {'BestPractices': 0, 'CodeStyle': 0, 'ErrorProne': 0}
			violations_by_name = defaultdict(int)

			# If type of code is supported
			if code['Type'] == 'javascript':

				# Create temporary file to store the code file's content
				with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='cp437', errors="ignore", suffix='.js') as temp_file:
					temp_file.write(code['Content'])

				# Get temporary file's path
				temp_file_path = temp_file.name

				# Create the ruleset relative path according to the file's language
				ruleset_path = f"pmdrulesets\{code['Type']}ruleset.xml"

				# Define the PMD check command
				cpd_command = f"{pmd} check {temp_file_path} -f text --no-cache -R {ruleset_path}"
				
				# Run the command and capture the output
				output = subprocess.run(cpd_command, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

				# If quality violations found
				if output.returncode == 4:
					# Extract the violations by category found and save it to dictionary
					output_message = output.stdout

					# For each supported violation
					for name, category in javascript_violations.items():
						# Check how many times it exist in the output message
						count = output_message.count(name)
						if count:
							total_violations += count
							violations_by_cat[category] += count
							violations_by_name[name] += count

					# Formulate the final dictionary containing the information to be stored to the db
					code['Violations'] = {'Total': total_violations}
					code['Violations'].update({'ViolationsByCat': violations_by_cat})
					code['Violations'].update({'ViolationsByName': violations_by_name})
					conversation['ListOfCode'][j] = code
					conv_changed = True 

				elif output.returncode == 0:
					code['Violations'] = {'Total': total_violations}
					code['Violations'].update({'ViolationsByCat': violations_by_cat})
					code['Violations'].update({'ViolationsByName': violations_by_name})
					conversation['ListOfCode'][j] = code
					conv_changed = True
				
				# If PMD-check finished with error
				else:
					print('Error in generated-code quality analysis')
					return -1
		
		if conv_changed:
			sharing['Conversations'][i] = conversation

	return sharing



def run_sourcemeter(code_blocks, proj_name):
	"""
	This function takes a list of code blocks, creates temporary files for each block
	and runs SourceMeter analysis on the code.
	
	:param code_blocks: A list of code blocks that will analyzed by SourceMeter. 	
	:param proj_name: A string used to specify the name of the SourceMeter project that will be created
	when running the SourceMeter tool on the provided code blocks.
	"""

	code_dir = sourcemeterdir + '\\files'
	results_dir = sourcemeterdir + '\\results'

	# Ensure the SourceMeter folder exists
	if not os.path.exists(sourcemeterdir):
		os.makedirs(sourcemeterdir)
	
	# Check if code dir exists inside the SourceMete folder
	if os.path.exists(code_dir):
		shutil.rmtree(code_dir)

	os.makedirs(code_dir)

	# List to keep track of created file paths for cleanup
	created_files = []

	# Write each code block to a separate file
	for i, block in enumerate(code_blocks):
		file_path = os.path.join(code_dir, f"block_{i}.js")
		with open(file_path, 'w', encoding='utf-8') as file:
			file.write(block)
		created_files.append(file_path)

	# Run SourceMeter on the temporary folder
	sourcemeter_command = sourcemeterjs
	try:
		subprocess.run([sourcemeter_command, "-projectBaseDir=" + code_dir, "-resultsDir=" + results_dir, "-projectName=" + proj_name, "-runDCF:false" ,"-cleanResults:0"], check=True)

	except subprocess.CalledProcessError as e:
		print(f"Failed to run SourceMeter: {e}")

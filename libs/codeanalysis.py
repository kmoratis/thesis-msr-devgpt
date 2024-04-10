import subprocess
import base64
import re
import os
from properties import java, simian
from libs.utils import get_content_from_patch, get_file_extension
from libs.codequality import before_after_violations


def detect_code_clone(code_file, chatgpt_code_blocks, file_extension, min_lines, temp_dir):
	"""
	This function detects code clones between a given code file and a list of code
	blocks using the Simian tool, and returns information about the code clones if any are found.
	
	:param code_file: A string containing the content of the code file that you want to check
	:param chatgpt_code_blocks: A list of code blocks extracted from a Chatgpt conversation. These code
	blocks are the potential clones that need to be compared with the code in the `code_file`
	:param file_extension: A string that represents the file extension of the code file.
	:param min_lines: An integer specifying the minimum number of lines that a code clone must
	have in order to be considered a match
	:param temp_dir: A string that specifies the directory where temporary files will be stored. 
	These temporary files are used to compare the code blocks and detect code clones
	:returns: A dictionary that contains information about the best detected code clone found. 
	The dictionary includes the following keys: (If at least one code clone found. Else the dictionary is empty)
		- DuplicateLines: An integer specifying the number of lines that were cloned
		- Ratio: A float representing the percentage of lines of the initial file that were cloned
		- BlockIdx: An integer representing the index of the code block, where the best clone was found
		- CloneDetails: A string representing the exact lines of the code file that were cloned. 
	"""

	# Initialize variable
	code_clone = {}

	# Create temporary files
	file_path1 = os.path.join(temp_dir, f"./file_code{file_extension}")
	with open(file_path1, 'w', encoding='cp437', errors="ignore") as file1:
		file1.write(code_file)

	file_path2 = os.path.join(temp_dir, f"./chat_code{file_extension}")

	num_blocks = len(chatgpt_code_blocks)

	# For each provided code block
	for i, code_block in enumerate(reversed(chatgpt_code_blocks)):
		# Write the code block to the temporary file
		with open(file_path2, 'w', encoding='cp437', errors="ignore") as file2:
			file2.write(code_block)

		# Define the Simian command
		cpd_command = f'"{java}" -jar "{simian}" -defaultLanguage=text -threshold={min_lines} {file_path1} {file_path2}'

		# Run the command and capture the output
		output = subprocess.run(cpd_command, shell=True, text=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

		# If simian finished with error
		if output.returncode == 2:
			print("Error using Simian tool.")
			return -1

		# If no code clones detected, continue
		elif output.returncode == 0:
			continue

		# Decode the output using utf-8
		stdout_str = output.stdout.decode('utf-8')
		
		duplicates_found = stdout_str.split('Found')
		duplicate_lines = 0
		# Define a regular expression pattern to capture the number of lines from info
		line_num_pattern = r'(\d+) duplicate lines'

		# Get duplicates found between the two temporaty files. (Do not include the duplicated code within the same file)
		for duplicate in duplicates_found[1:-1].copy():
			# Check if duplicate refers to both files
			if 'file_code' in duplicate and 'chat_code' in duplicate:
				info_lines = [line.strip() for line in duplicate.splitlines()]
				match = re.search(line_num_pattern, info_lines[0])
				duplicate_lines += (int(match.group(1)) + 1)
			else:
				duplicates_found.remove(duplicate)

		# If clone found, extract its info and break loop
		if duplicates_found and duplicate_lines > 0:
			# Read the file and print the length and number of lines after writing to a file
			with open(file_path1, 'r', encoding='cp437') as file:
				file_content = file.read()
			clone_details, actual_lines_cloned = extract_clone_details(file_content, duplicates_found)
			code_clone['DuplicateLines'] = actual_lines_cloned
			file_lines = file_content.splitlines()
			non_empty_lines_num = len([line for line in file_lines if line.strip()])
			code_clone['Ratio'] = round(actual_lines_cloned / non_empty_lines_num * 100, 1)
			code_clone['BlockIdx'] = num_blocks - i
			# Extract specific lines cloned from the code file
			code_clone['CloneDetails'] = clone_details
			if actual_lines_cloned:
				break

	# Delete the temporary files
	os.remove(file_path1)
	if len(chatgpt_code_blocks):
		os.remove(file_path2)

	return code_clone


def extract_clone_details(code_file, best_match_duplicates):
	"""
	This function extracts the lines of code that are identified as clones from a
	given code file based on the information provided in the `best_match_duplicates` parameter.
	
	:param code_file: A string that represents the content of a code file. 
	It contains the code from which we want to extract clone details
	:param best_match_duplicates: A list of strings. Each string represents a duplicate code block 
	and contains information about the clone lines. 
	The first element of the list is the header, and the subsequent elements are the details of each duplicate code block
	:returns: A tuple containing two values: the lines of code that are identified as clones and the
	total number of cloned lines.
	"""

	clone_lines = set()

	# Define a regular expression pattern to capture the starting and ending clone line from info
	pattern = r'Between lines (\d+) and (\d+)'

	# Extract info from each info string in the list (The first element of the list is the header)
	for duplicate in best_match_duplicates[1:]:
		info_lines = [line.strip() for line in duplicate.splitlines()]
		for info in info_lines[1:]:
			# Keep only the line of the info message that corresponds to info about the block from the file
			if 'file_code' in info:
				# Use re.search to find the starting and ending line number of the duplicate
				match = re.search(pattern, info)
				if match:
					# Extract the two numbers from the matched groups
					line1, line2 = map(int, match.groups())
					# Add the lines of the clone block to the set containing the total cloned lines
					lines = list(range(line1, line2 + 1))
					clone_lines = clone_lines|set(map(lambda x: x-1, lines))
				else:
					continue

	# Get the clone's lines from the code file and return them
	code_file_lines = code_file.splitlines()
	code_clone_lines = [f"{i+1}: {code_file_lines[i]}" for i in clone_lines if len(code_file_lines[i].strip()) >= 3]
	final_lines_cloned = len(code_clone_lines)
	code_clone = '\n'.join(code_clone_lines)
	return code_clone, final_lines_cloned


def extract_features(dbobj, temp_dir, sharingidx=0):
	"""
	This function extracts various features from a given database object (commit or file)
	and performs code clone detection (Using the Simian tool) 
	and quality violations analysis on the 'before' and 'after' versions of the files (Using the PMD check tool).
	'before' and 'after' versions refer to the commited file's versions before and after the insertion of Chatgpt generated code.
	
	:param dbobj: A dictionary that contains information about a database object (commit or file)
	:param temp_dir: A string that represents the temporary directory where
	the code clone detection process will store temporary files
	:param sharingidx: An (optional) integer value that determines which ChatgptSharing object
	from the database object (`dbobj`) to use for feature extraction. Defaults to 0.
	:returns: A dictionary containing various features extracted from the input `dbobj`. 
	The features include information about the conversation, prompts, code clone detections, 
	quality analysis results, and more.
	"""

	# -- Initialization --
	# Get the specific link's information
	sharing = dbobj['ChatgptSharing'][sharingidx]
	# Define a dictionary to store the link's features
	features = {}

	# -- Basic features --
	# Get the first prompt of the conversation and add it to features
	first_prompt = sharing['Conversations'][0]['Prompt']
	features['FirstPrompt'] = first_prompt

	# Get the length of each prompt, and total number of prompts and add them to features
	prompts_length_list = [
		len(conversation['Prompt'])
		for conversation in sharing['Conversations']
	]
	features['NumberOfPrompts'] = sharing['NumberOfPrompts']
	features['LengthOfPrompts'] = prompts_length_list

	# Create a list of file's according to the type of dbobj
	if dbobj['Type'] == 'commit':
		file_list = dbobj['CommitContent']['files']
		source_type = 'commit'
	else:
		file_list = [dbobj]
		source_type = 'file'

	# -- Code clone detection and Quality violations analysis ( File specific ) --
	# Define a list to store the analysis features
	features['FileAnalysis'] = []
 
	# Define a list to store the indexes of the files were code clone detections were found
	features['CodeCloneDetectedIdxs'] = [] 

	# For each commited file
	for file in file_list:

		if source_type == 'commit':
			file_name = file['filename']
			if 'patch' not in file:
				continue
			else:
				# Get file's content from patch (current and previous versions)
				content = get_content_from_patch(file['patch'], 'current')
				previous_content = get_content_from_patch(file['patch'], 'previous')
				
				# Add them to file as attributes
				file['Content'] = content
				file['PrevContent'] = previous_content

		else:
			file_name = file['FileName']
			# Get file's content and decode it
			base64_content = file['Content']
			content = base64.b64decode(base64_content).decode('utf-8')

			# Get file's previous content if existed
			if 'FileHistory' in file and 'patch' in file['FileHistory']:
				previous_content = get_content_from_patch(file['FileHistory']['patch'], 'previous')
				file['PrevContent'] = previous_content
			else:
				file['PrevContent'] = ''

		# Crate dictionary to store current file's results	
		file_features = {}
		file_features['FileName'] = file_name

		# Extract the file extension and convert to lowercase
		file_extension = get_file_extension(file_name)

		# If language is supported (extension found)
		if file_extension:
			file_extension = file_extension[1:]

			# Get all code blocks generated in the specific Chatpgt dialogue
			codeblocks = [
				code['Content']
				for conversation in sharing['Conversations']
				for code in conversation['ListOfCode']	
			]

			# Detect copy-pasted code parts (code clones), between the file and the Chatgpt's provided code blocks
			min_lines = 2
			code_clone = detect_code_clone(content, codeblocks, file_extension, min_lines, temp_dir)

			# If simian finished with error
			if code_clone == -1:
				return features
				
			# If no code clones where found, set the results accordingly
			if 'DuplicateLines' not in code_clone or code_clone['DuplicateLines'] == 0: # If empty
				file_features['Message'] = "No code clone detections"
				file_features['LinesCopied'] = 0
				file_features['DuplicateRatio'] = 0
				file_features['CodeBlockIdx'] = 0
				file_features['PromptsBeforeClone'] = 0
				file_features['CloneDetails'] = ""
				file_features['QualityAnalysis'] = "No code clone detections"

			# If code clones were detected
			else:
				features['CodeCloneDetectedIdxs'].append(len(features['FileAnalysis']))
				file_features['Message'] = "Code clone found"
				file_features['LinesCopied'] = code_clone['DuplicateLines']
				file_features['DuplicateRatio'] = code_clone['Ratio']
				file_features['CodeBlockIdx'] = code_clone['BlockIdx']
				# Calculate how many prompts were asked by user before the code clone
				num_blocks = 0
				copy_block_idx = code_clone['BlockIdx']

				for i, conversation in enumerate(sharing['Conversations']):
					num_blocks += len(conversation['ListOfCode'])
					if num_blocks >= copy_block_idx:
						file_features['PromptsBeforeClone'] = i+1
						break

				file_features['CloneDetails'] = code_clone['CloneDetails']

				# -- Quality Analysis --
				# Calculate quality violations of the commited file (before and after the copy of ChatGPT code)
				# Check if language is supported by quality analysis
				language = file['Language']
				if not language:
					file_features['QualityAnalysis'] = "Language not supported by PMD-check"

				elif language != 'JavaScript':
					file_features['QualityAnalysis'] = "Language not supported by PMD-check"
				
				else:
					file['Extension'] = file_extension
					quality_result = before_after_violations(file)
					
					# If quality analysis finished with error
					if quality_result == -1:
						file_features['QualityAnalysis'] = "Error during quality analysis"
					else:
						# Add Quality Analysis to features
						file_features['QualityAnalysis'] = quality_result

		# Add file features to the list
		features['FileAnalysis'].append(file_features)
			
	return features

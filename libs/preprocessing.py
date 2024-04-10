import regex as re
from collections import Counter
from pygments.lexers import get_lexer_for_filename
from pygments.util import ClassNotFound

def contains_invalid_chars(text):
	"""
	Checks if a given text contains any invalid Unicode character.
	
	:param text: The string to check for invalid characters.
	:returns: Boolean. (True) if the input text contains any invalid characters, and (False) otherwise.
	"""
	
	all_unicode_patterns = re.compile(r'[\u0080-\uffef]', re.UNICODE)  # @UndefinedVariable

	valid_patterns = [
		r'[\u0080-\u00FF]', # "Latin-1 Supplement" category
		r'[\u2500-\u257F\u200b\u23a6\u23a4\u23a3\u23a1]', # Box drawing characters
		r'[\u2600-\u26FF\u2B50\ufe0f]', # Miscellaneous Symbols
		r'[\u25A0-\u25FF]', # Geometric shape characters
		r'[\u2190-\u21FF]', # Arrow characters and similar
		r'[\u2200-\u22FF]', # Math symbols and operators
		r'[\u0391-\u03A9\u03B1-\u03C9]', # Greek letters used in math
		r'[\p{P}\p{S}\p{So}]', # "Punctuation Dash" and Symbol characters
		r'[\p{Block=Emoticons}]', # Emoticons Block characters
	]

	valid_patterns = '|'.join(valid_patterns)
	valid_patterns = re.compile(valid_patterns)

	all_unicode_characters = all_unicode_patterns.findall(text)

	for character in all_unicode_characters:
		# If at least one non-valid unicode found, return True
		if not valid_patterns.search(character):
			return True

	return False


def detect_invalid_sources(data):
	"""
	Checks whether the data contains invalid sources and removes them. Invalid sources are those that contain any of the following:
    - Specific non-UTF-8 characters
    - No valid response codes
    - Conversations that lack at least one code block.
	
	:param data: A dictionary containing the collection of sources.
	:returns: Two values: `invalid_sources` and `invalid_links`.
	`invalid_sources` is list containing the NumericIDs of the invalid sources, while `invalid_links` is a list of their 
	corresponding URLs.
	"""
	
	# Create a list to store the indexes of invalid sources, in order to delete them
	invalid_sources = []
	invalid_links = []

	# Retrieve the source type
	source_type = data[0]['Type']

	# Check if every source is valid or not
	for source in data:

		# For different data types (commits, files), different text fields are checked.
		if source_type == "commits":
			# Check if entry's message contains non utf-8 characters
			if contains_invalid_chars(source['Message']):
					# print("Non-utf in commit message", source['URL']) # debugging
					invalid_sources.append(source['NumericID'])
					sharing_urls = [sharing['URL'] for sharing in source['ChatgptSharing']]
					invalid_links.extend(sharing_urls)
					continue

		elif source_type == "files":
			# Check if entry's commit message contains non utf-8 characters
			if contains_invalid_chars(source['CommitMessage']):
					# print("Non-utf in commit message", source['URL']) # debugging
					invalid_sources.append(source['NumericID'])
					sharing_urls = [sharing['URL'] for sharing in source['ChatgptSharing']]
					invalid_links.extend(sharing_urls)
					continue

		source_contains_code = False # Variable to check if source contains code blocks

		contains_active_link = False # Variable to store whether reference contains at least one active link

		# Ckeck each Chatgpt shared link
		for sharing in source['ChatgptSharing']:
			# Check status code of the Chatgpt shared link, and keep only success (200)
			if sharing['Status'] != 200:
					invalid_links.append(sharing['URL'])
					continue # continue to the next dialogue check
			else:
					contains_active_link = True

			# For each conversation in the specific shared link, check if code block exists
			link_contains_code = False
			for conv in sharing['Conversations']:
					if len(conv['ListOfCode']): # check if List of Code is not empty
						link_contains_code = True # if code block found, no need to check the rest of the conversations, so exit loop
						source_contains_code = True
						break

			# If no code blocks are detected in the link, add link to drop list
			if not link_contains_code:
				invalid_links.append(sharing['URL'])

			# Check if conversation's prompt or answer contains non utf-8 characters
			found = False # variable to exit nested loop
			for conv in sharing['Conversations']:
					if contains_invalid_chars(conv['Prompt']) or contains_invalid_chars(conv['Answer']):
						# print("Non-utf in conv", source['URL']) # debugging
						invalid_sources.append(source['NumericID'])
						sharing_urls = [sharing['URL'] for sharing in source['ChatgptSharing']]
						invalid_links.extend(sharing_urls)
						found = True
						break # exit nested loop
			if found: # if non utf-8 found, no need to check the rest of the dialogues, so exit loop
					break

		# If there are no active links shared at the moment the snapshot was taken, remove source from data
		if not contains_active_link:
			# print("Bad status code", source['URL']) # debugging
			invalid_sources.append(source['NumericID'])

		# If there are no code blocks in any of the shared links, remove source from data
		if not source_contains_code:
			# print("No-code source", source['URL']) # debugging
			invalid_sources.append(source['NumericID'])

	return invalid_sources, invalid_links


def detect_duplicates(collection):
	"""
	This function takes a collection of entries and detects duplicates based on a
	specified attribute, returning a list of duplicate entries and their corresponding links.
	
	:param collection: A list of dictionaries. Each dictionary represents an entry in the collection.
	:returns: Two values: `duplicates` and `duplicate_links`.
	`duplicates` is a list of duplicate entries in the collection, while `duplicate_links` is a list of their 
	corresponding URLs.
	"""
	
	# Initialize variables
	unique_entries = {}
	duplicates = []
	duplicate_links = []

	# Retrieve the source type
	source_type = collection[0]['Type']

	if source_type in ['commits', 'files']:
		# Define the attribute used to identify the duplicates based on the source type
		attribute = 'Sha' if source_type == 'commits' else 'ObjectSha'

		# Check all entries of the collection and keep only the first occurence of each document
		for document in collection:
			value = document[attribute]

			if value in unique_entries:
				duplicates.append(document['NumericID'])
				duplicate_links.extend([sharing['URL'] for sharing in document['ChatgptSharing']])

			else:
				unique_entries[value] = True
			
	return duplicates, duplicate_links


def detect_dominant_language(dbobj):
	"""
	This function detects the most common programming language of the codes that were generated 
	in the shared links of a given `dbobj` object. 
	
	:param dbobj: A dictionary object that contains information about a repository item (commit or file)
	and its associated Chatgpt dialogues.
	:returns: The dominant programming language of the shared dialogue.
	"""

	# Initialize variable
	programming_language = 'Unknown'

	# For every shared link, get the language of all generated code blocks, and find the one with the most occurrences
	valid_sharings = [sharing for sharing in dbobj['ChatgptSharing'] if 'Conversations' in sharing]

	# Get the coding language of all code blocks generated in the specific Chatpgt dialogue
	gen_code_langs = [
		code['Type']
		for sharing in valid_sharings
		for conversation in sharing['Conversations']
		for code in conversation['ListOfCode']	
		if code.get('Type') is not None
	]

	if gen_code_langs:
		# Use Counter to count occurrences of each element in the list
		language_counts = Counter(gen_code_langs)

		# Use the most_common() method to get a list of tuples (element, count),
		most_common_languages = language_counts.most_common()

		# Find the language(s) with the most counts
		max_count = most_common_languages[0][1]
		max_count_languages = [lang for lang, count in most_common_languages if count == max_count]

		# Check if 'python' or 'javascript' is among the languages with the most counts
		preferred_langs = ['python', 'javascript']

		for language in max_count_languages:
			if language in preferred_langs:
				programming_language = language
				break
		else:
			# If neither 'python' nor 'javascript' is found among the most common, take the first language
			programming_language = max_count_languages[0]

	return programming_language


def handle_tisztamo(dbobj):
	"""
	This function checks extracts the JavaScript parts of the code blocks from dialogues of 
	commit entries that come from the repo 'titzstamo/Junior'.
	
	:param dbobj: A dictionary object that contains information about a repository item (commit) 
	and its associated Chatgpt dialogues.
	:returns: The object of the shared link, if any generated code block needed to be modified.
	"""

	# Initialize variable
	codeblocks_changed = False

	# Define regular expression to match the JavaScript part contained in the 'sh' code block
	regex = re.compile(r'cat [\s\S]*?(?=\nEOF)')

	for i, conversation in enumerate(dbobj['ChatgptSharing'][0]['Conversations'].copy()):

		modified_code_list = []
		
		for code in conversation['ListOfCode']:

			if code['Type'] in ['sh', 'bash']:
				# Find all JavaScript parts
				matches = regex.finditer(code['Content'])

				# Loop through each match and create a code block for the JavaScript part
				for match in matches:
					javascript_part = match.group(0)
					# Split the javascript_part into lines and remove the first line
					lines = javascript_part.splitlines()
					if lines:  # Check if there are any lines to avoid index errors
						javascript_part_without_first_line = '\n'.join(lines[1:])
					else:
						javascript_part_without_first_line = ""

					# Clone the code object for each match
					new_code = code.copy()  # Assumes code is a dictionary, use deepcopy if it's more complex
					new_code['Type'] = 'javascript'
					new_code['Content'] = javascript_part_without_first_line
					modified_code_list.append(new_code)
					codeblocks_changed = True
			else:
				modified_code_list.append(code)

		# If JS parts found, update the list of code in the shared link
		if modified_code_list:
			conversation['ListOfCode'] = modified_code_list
			dbobj['ChatgptSharing'][0]['Conversations'][i] = conversation

	return dbobj['ChatgptSharing'][0] if codeblocks_changed else None


def detect_file_language(filename):
	"""
	This function attempts to determine the language of a file based on its
	filename using Pygments lexers.
	
	:param filename: A string representing the name of the file.
	:returns: The file name if the identification was successful, else it returns 'Unknown'.
	"""

	try:
		# Attempt to find the lexer based on the file name
		lexer = get_lexer_for_filename(filename)
		return lexer.name
	except ClassNotFound:
		# If a lexer could not be found based on the file name
		return 'Unknown'

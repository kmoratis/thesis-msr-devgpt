import sys
import json
from properties import dbpath
from libs.dbmanager import DBManager

""" Counts the number of commits, code files, shared conversations and code blocks before and after the preprocessing: 
	Executed by `preprocessdata.py` (x2): before and after the preprocessing 
"""

# Check if at least one argument is passed (excluding the script name)
if len(sys.argv) > 1:
	mode = sys.argv[1]
	if mode not in ['Before', 'After']:
		print('Bad argument received.')
		exit()
else:
	print("No argument received.")
	exit()

# Connect to database
dbmanager = DBManager(dbpath)
db = dbmanager.db

# Initialize variables
sharing_counter = 0
code_block_counter = 0

source_list = list(db['commits'].find()) + list(db['files'].find())

number_of_commits = len(list(db['commits'].find()))
number_of_files = len(list(db['files'].find()))

valid_links = list(db['links'].find())
valid_links = [link['URL'] for link in valid_links]

for source in source_list:

	# Add number of sharings to total
	sharings = [1 for sharing in source['ChatgptSharing'] if sharing['URL'] in valid_links]
	sharing_counter += sum(sharings)

	# Add number of blocks to total
	blocks = [
		len(conv['ListOfCode'])
		for sharing in source['ChatgptSharing']
		if sharing['URL'] in valid_links
		for conv in sharing.get('Conversations', [])
		]

	code_block_counter += sum(blocks)

# Save the results to stats
with open('statistics.json', 'r') as file:
	stats = json.load(file)

# Add information
if 'Preprocessing' not in stats:
	stats['Preprocessing'] = {}
stats['Preprocessing'][mode] = {}
stats['Preprocessing'][mode]['Commits'] = number_of_commits
stats['Preprocessing'][mode]['Code files'] = number_of_files
stats['Preprocessing'][mode]['Shared conversations'] = sharing_counter
stats['Preprocessing'][mode]['Generated blocks'] = code_block_counter

with open('statistics.json', 'w') as file:
	json.dump(stats, file, indent=3)

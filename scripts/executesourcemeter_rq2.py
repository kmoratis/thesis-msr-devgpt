import json
from properties import dbpath
from libs.dbmanager import DBManager
from libs.codequality import run_sourcemeter

# Connect to database
dbmanager = DBManager(dbpath)
db = dbmanager.db

# Define list to store all the generated JavaScript blocks
js_blocks = [] # all JS blocks

# Get all the generated blocks of commits
# Load commit annotations from file
with open('annotationscommits.txt', 'r') as file:
	# Load the JSON data from the file into a dictionary
	commitannotations = json.load(file)

# Get all commits that contain JS generated code
for commit in db["commits"].find({'ChatgptSharing.Conversations.ListOfCode.Type': 'javascript'}):
	# Keep only the commits of class `write me this code` (1)
	if commitannotations[commit['URL']] == "1":
		sharing  = commit['ChatgptSharing'][0] # all commits contain only one shared link
		for conversation in sharing.get("Conversations", []):
			for codeblock in conversation["ListOfCode"]:
				if codeblock["Type"] == "javascript":
					js_blocks.append(codeblock["Content"])

# Load file annotations from file
with open('annotationsfiles.txt', 'r') as file:
	# Load the JSON data from the file into a dictionary
	fileannotations = json.load(file)

# Get all commits that contain JS generated code
for file in db["files"].find({'ChatgptSharing.Conversations.ListOfCode.Type': 'javascript'}):
	for sharing in file['ChatgptSharing']:
		# Keep only the sharings of class `write me this code` (1)
		if fileannotations.get(sharing['URL'], -1) == "1":
			for conversation in sharing.get("Conversations", []):
				for codeblock in conversation["ListOfCode"]:
					if codeblock["Type"] == "javascript":
						js_blocks.append(codeblock["Content"])
							
# Call function to run SourceMeter on the generated blocks
run_sourcemeter(js_blocks, 'rq2')

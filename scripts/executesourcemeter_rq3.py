import json
import sys
from properties import dbpath
from libs.dbmanager import DBManager
from libs.codequality import run_sourcemeter
from libs.utils import get_content_from_patch

""" Executes the SourceMeter tool for RQ3 
	Executed by `gereratesourcemeterresults_rq3.py` (x2): one for each version of the files
"""

# Check if at least one argument is passed (excluding the script name)
if len(sys.argv) > 1:
	version = sys.argv[1]
	if version not in ['previous', 'current']:
		print('Bad argument received.')
		exit()
else:
	print("No argument received.")
	exit()

# Connect to database
dbmanager = DBManager(dbpath)
db = dbmanager.db

# Define list to store all the JavaScript files
js_files = [] # all JS files

# Load commit annotations from file
with open('annotationscommits.txt', 'r') as file:
	# Load the JSON data from the file into a dictionary
	commitannotations = json.load(file)

# Get all commits that contain JS generated code
for commit in db["commits"].find({'ChatgptSharing.AnalysisFeatures': {"$exists": True}}):
	files_with_clones = [
		file['FileName']
		for file in commit['ChatgptSharing'][0]['AnalysisFeatures']['FileAnalysis']
		if file.get('LinesCopied', -1) > 0
	]
	# Keep only the commits of class `write me this code` (1)
	if commitannotations[commit['URL']] == "2":
		if 'CommitContent' in commit:
			for file in commit['CommitContent']['files']:
				language = file.get('Language', '')
				# If language is supported
				if language and language == 'JavaScript':
					# Check if the specific file was cloned
					if file['filename'] in files_with_clones:
						content = get_content_from_patch(file['patch'], version)
						# Check if previous patch exist and only then add it for calculation
						prev_content = get_content_from_patch(file['patch'], 'previous')
						if prev_content:
							js_files.append(content)

# Load file annotations from file
with open('annotationsfiles.txt', 'r') as file:
	# Load the JSON data from the file into a dictionary
	fileannotations = json.load(file)

# Get all files with downloaded history
for file in db["files"].find({'FileHistory': {"$exists": True}}):

	contains_writeme = False
	contains_cloned = False

	# Check if they are JS
	language = file['Language']
	if not language:
		continue
	elif language != 'JavaScript':
		continue

	# Get all shared urls
	shared_urls = [sharing['URL'] for sharing in file['ChatgptSharing']]

	# Check if any of the shared links are of write me this code type
	for url in shared_urls:
		if fileannotations.get(url, "0") == "2":
			contains_writeme = True
			break

	if not contains_writeme:
		continue

	# Check if code clone exists
	for sharing in file['ChatgptSharing']:
		if 'AnalysisFeatures' in sharing:
			if sharing['AnalysisFeatures']['FileAnalysis'][0].get('LinesCopied', -1) > 0:
				contains_cloned = True
				break

	if not contains_cloned:
		continue

	# Check if previous file version exists
	prev_content = get_content_from_patch(file['FileHistory'].get('patch', ''), 'previous')
	if not prev_content:
		continue

	# Find the appropriate content and add it to the list
	content = get_content_from_patch(file['FileHistory']['patch'], version)
	js_files.append(content)
							
# Call function to run SourceMeter on the generated blocks
analysis_type = 'rq3_' + version
run_sourcemeter(js_files, analysis_type)

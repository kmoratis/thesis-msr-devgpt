import os
from properties import dbpath
from libs.dbmanager import DBManager
from libs.codeanalysis import extract_features
from libs.codequality import block_quality_violations

""" Data Analysis:
 - Features extraction (Code clones, before-after quality violations, ...)
 - Generated blocks quality violations
"""

# Connect to database
dbmanager = DBManager(dbpath)

# Create a directory for temporary files
temp_dir = "./temp_files"
os.makedirs(temp_dir, exist_ok=True) 

print("\nAnalyzing data")

print("Extracting commit features")
# Get all chatgpt links that relate to commits
for l, link in enumerate(dbmanager.db['links'].find({'MentionedSource': 'commit'}, {'_id': False})):

	# Get the commit
	commit = dbmanager.db['commits'].find_one({'URL': link['MentionedURL']})

	# Call function to extract the features of the commit
	features = extract_features(commit, temp_dir)
	# Add commits's feature set to database
	sharing = commit['ChatgptSharing'][0]
	sharing['AnalysisFeatures'] = features
	query = {'$set': {f'ChatgptSharing.{0}': sharing}}
	# Add file's link with scenario category to database
	dbmanager.update('commits', {'_id': commit['_id']}, query)

	# Add attribute to commit variable also
	commit['ChatgptSharing'][0]['AnalysisFeatures'] = features

	# Call function to calculate the quality violatations for every generated code block in the shared link
	commitsharing = block_quality_violations(commit)

	# If quality analysis finished sucessfully, update db
	if commitsharing != -1:
		query = {'$set': {f'ChatgptSharing.{0}': commitsharing}}
		# Add file's link with scenario category to database
		dbmanager.update('commits', {'_id': commit['_id']}, query)

print("Extracting file features")
# Get all chatgpt links that relate to code files
for l, link in enumerate(dbmanager.db['links'].find({'MentionedSource': 'code file'}, {'_id': False})):
	# Get the code file
	file = dbmanager.db['files'].find_one({'URL': link['MentionedURL']})

	# Retrieve the information of the specific ChatGpt sharing ( Each file can have multiple sharings )
	sharedlink = link['URL']
	for i, sharing in enumerate(file.get('ChatgptSharing', '')):
		if sharing['URL'] == sharedlink:
			currentsharing = sharing
			sharingidx = i
			break

	# Extract sharing-specific features and save them to db
	sharingfeatures = extract_features(file, temp_dir, sharingidx)
	currentsharing['AnalysisFeatures'] = sharingfeatures

	# Add attribute to local variable
	file['ChatgptSharing'][i] = currentsharing

	# Call function to calculate the quality violatations for every generated code block in the shared link
	result = block_quality_violations(file, i)
	# If quality finished sucessfully
	if result != -1:
		currentsharing = result

	# Update the ChatgptSharing to db with the features extracted from the code and quality analysis
	query = {'$set': {f'ChatgptSharing.{i}': currentsharing}}
	dbmanager.update('files', {'_id': file['_id']}, query)

# Remove the directory with temporary files
os.rmdir(temp_dir)

# Close the DB connection
dbmanager.close()

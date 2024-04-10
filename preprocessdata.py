import subprocess
from properties import dbpath
from libs.dbmanager import DBManager
from libs.download import download_commits_content, download_files_history
from libs.preprocessing import detect_duplicates, detect_invalid_sources, detect_dominant_language, detect_file_language, handle_tisztamo

""" Dataset Preprocessing: 
 - Language identification, 
 - invalid and duplicate entries removal, 
 - dataset enhancement through GitHub API,
 - special entries handling
"""

# Connect to database
dbmanager = DBManager(dbpath)

# Create two lists to store all the duplicates and the invalid links to be removed
totalduplicate = []
totalinvalid = []

# Run script to calculate statistics before the preprocessing
subprocess.run(["python", "-m", "scripts.createpreprocessingstatistics", "Before"])

""" Handle commits """
print("Preprocessing commits")
# Retrieve all documents from the commits collection
commits = list(dbmanager.get_all_documents('commits'))

# Detect and remove the duplicate commit entries (Maintaining the first occurence)
duplicates, duplicatelinks = detect_duplicates(commits)
totalduplicate.extend(duplicatelinks)
filter = {'NumericID': {'$in': duplicates}}
dbmanager.delete('commits', filter)

# Perform the application required preprocessing 
# (detection and removal of non-UTF8, no valid responses, no generated code blocks)
invalidsources, invalidlinks = detect_invalid_sources(commits)
totalinvalid.extend(invalidlinks)
filter = {'NumericID': {'$in': invalidsources}}
dbmanager.delete('commits', filter)

# Re-set the NumericID attribute to be incremental to the valid data
idcounter = 1
for commit in list(dbmanager.get_all_documents('commits')):
   dbmanager.update('commits', {'_id': commit['_id']}, {'$set': {'NumericID': idcounter}})
   idcounter += 1

# Retrieve the documents again (with NumbericID and removals)
commits = list(dbmanager.get_all_documents('commits'))

# Detect the programming language of each entry and save it to db
for commit in commits:
   # Call function to detect the dominant programming language of the dialogue
	language = detect_dominant_language(commit)

	# If language was found, save it to db
	if language:
		dbmanager.update('commits', {'_id': commit['_id']}, {'$set': {'DominantLanguage': language}})

	# Call function to handle the entries from repo 'tisztamo/Junior'
	if commit['RepoName'] == 'tisztamo/Junior':
		updatedsharing = handle_tisztamo(commit)

		# If information about generated code blocks was modified (tisztamo), update the db
		if updatedsharing:
			commit['ChatgptSharing'][0] = updatedsharing
			# Define the query to update ChatgptSharing to db
			query = {'$set': {f'ChatgptSharing.{0}': updatedsharing}}
			dbmanager.update('commits', {'_id': commit['_id']}, query)
		
# Enrich commits collection with the content of the commited files
print("Downloading commits content")
commits = list(dbmanager.get_all_documents("commits"))
# Filter the commits, keeping only those that their content has not already been downloaded
filteredcommits = [commit for commit in commits if 'CommitContent' not in commit]
updates = download_commits_content(filteredcommits)

# Update the commits collection
if updates != -1: # Download failed (GitHub's API Request-Limit reached)
	for update in updates:
		documentid = update['_id']
		filtercondition = {'_id': documentid}
		commit_content = update['CommitContent']
		# Identify programming language of commited files
		committed_files = commit_content['files']
		for i, file in enumerate(committed_files):
			committed_files[i]['Language'] = detect_file_language(file['filename'])
		commit_content['files'] = committed_files
		updatedata = {'$set': {'CommitContent': commit_content}}
		dbmanager.update("commits", filtercondition, updatedata)
else:
	print('Download failed - Max number of API requests reached')


""" Handle files """
print("Preprocessing files")
# Retrieve all documents from the files collection
files = list(dbmanager.get_all_documents('files'))

# Detect and remove the duplicate file entries (Maintaining the first occurence)
duplicates, duplicatelinks = detect_duplicates(files)
totalduplicate.extend(duplicatelinks)
filter = {'NumericID': {'$in': duplicates}}
dbmanager.delete('files', filter)

# Perform the application required preprocessing (detection and removal of non-UTF8, no valid responses, no generated code blocks)
invalidsources, invalidlinks = detect_invalid_sources(files)
totalinvalid.extend(invalidlinks)
filter = {'NumericID': {'$in': invalidsources}}
dbmanager.delete('files', filter)

# Re-set the NumericID attribute to be incremental to the valid data
idcounter = 1
for file in list(dbmanager.get_all_documents('files')):
	dbmanager.update('files', {'_id': file['_id']}, {'$set': {'NumericID': idcounter}})
	idcounter += 1

# Retrieve the documents again (with NumbericID and removals)
files = list(dbmanager.get_all_documents('files'))

# Detect the programming language of each entry and save it to db
for file in files:
	# Call function to detect the dominant programming language of the dialogue
	language = detect_dominant_language(file)

	# If language was found, save it to db
	if language:
		dbmanager.update('files', {'_id': file['_id']}, {'$set': {'DominantLanguage': language}})

	# Call function to detect the programming language of the file
	file_lang = detect_file_language(file['FileName'])

	# If language was found, save it to db
	if file_lang:
		dbmanager.update('files', {'_id': file['_id']}, {'$set': {'Language': file_lang}})

# If the file is JavaScript, download its previous version from GitHub, to be used in before-after code clone violations comparison 
print('Downloading previous version of files')
# Filter the files, keeping only those that their content has not already been downloaded
filteredfiles = [file for file in files if 'FileHistory' not in file]
updates = download_files_history(filteredfiles)
# Update the files collection
if updates != -1: # Download failed (GitHub's API Request-Limit reached)
	for update in updates:
		documentid = update['_id']
		filtercondition = {'_id': documentid}
		updatedata = {'$set': {'FileHistory': update['FileHistory']}}
		dbmanager.update("files", filtercondition, updatedata)
else:
	print('Download failed - Max number of API requests reached')


""" Handle links """
# Retrieve all documents from the links collection
links = list(dbmanager.get_all_documents('links'))

# Remove the duplicate links, keeping only one occcurence
for link in links:
	if link['URL'] in totalduplicate:
		filter = {'_id': link['_id']}
		dbmanager.delete('links', filter)
		totalduplicate.remove(link['URL'])
	
# Remove the invalid links from the db
filter = {'URL': {'$in': totalinvalid}}
dbmanager.delete('links', filter)

# Add a NumericID attribute to be incremental to the valid data
idcounter = 1
for link in list(dbmanager.get_all_documents('links')):
	dbmanager.update('links', {'_id': link['_id']}, {'$set': {'NumericID': idcounter}})
	idcounter += 1

# Run script to calculate statistics after the preprocessing
subprocess.run(["python", "-m", "scripts.createpreprocessingstatistics", "After"])

# Close the DB connection
dbmanager.close()

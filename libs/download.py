import requests
import json
from properties import githubapikey

def download_commits_content(commits):
	"""
	Takes a list of commits as input and retrieves the content of each commit using the GitHub API.
	
	:param commits: A list of dictionaries, where each dictionary represents a commit object.
	:returns: A list of dictionaries containing the updates to be made to the 'commits' collection. 
	Each dictionary contains the commit's ID and content attribute. If the GitHub's API
	remaining request number is low, return (-1)
	"""
	
	# Define a list to store dictionaries with the commit's ID and content attribute
	update_list = []

	# Use GitHub token to achieve better maximum API call rate
	headers = {'Authorization': f'token {githubapikey}'}

	for commit in commits:
	
		update_dict = {}
		# Get commit's ID and store it to dictionary
		update_dict['_id'] = commit['_id']

		# Get commit's reponame and sha 
		reponame = commit['RepoName']
		sha = commit['Sha']
		apiurl = "https://api.github.com/repos/" + reponame + "/commits/" + sha

		try:
			# API call to get GitHub's commit information
			response = requests.get(apiurl, headers = headers)

			# Store API response to update's dictionary
			update_dict['CommitContent'] = json.loads(response.text)

			# Add update dictionary to update list
			update_list.append(update_dict)

			# Check GitHub's API call rate limit
			if 'X-RateLimit-Remaining' in response.headers:
				if int(response.headers['X-RateLimit-Remaining']) <= 10:
					print("GitHub: X-RateLimit-Remaining is low, please try again later.")
					return -1
		except:
			# print("Bad request response on commit:", commit['Sha'])
			continue
		
	return update_list


def download_files_history(files):
	"""
	Takes a list of files as input and retrieves the commit content for the specific file using the GitHub API.
	
	:param files: A list of dictionaries, where each dictionary represents a file object.
	:returns: A list of dictionaries containing the updates to be made to the 'files' collection. 
	Each dictionary contains the file's ID and history attribute. If the GitHub's API
	remaining request number is low, return (-1)
	"""
	
	# Define a list to store dictionaries with the commit's ID and content attribute
	update_list = []

	# Use GitHub token to achieve better maximum API call rate
	headers = {'Authorization': f'token {githubapikey}'}

	for file in files:

		update_dict = {}
		# Get commit's ID and store it to dictionary
		update_dict['_id'] = file['_id']

		# Retrieve the required information for the file
		repo_name = file['RepoName']
		file_path = file['FilePath']

		repo_url = f"https://api.github.com/repos/{repo_name}"
		commit_history_url = f"{repo_url}/commits?path={file_path}"
		
		try:
			# Make a GET request to fetch the commit history for the file
			response = requests.get(commit_history_url, headers=headers)

			# Check GitHub's API call rate limit
			if 'X-RateLimit-Remaining' in response.headers:
				if int(response.headers['X-RateLimit-Remaining']) <= 10:
					print("GitHub: X-RateLimit-Remaining is low, please try again later.")
					return -1

			commits = response.json()

			for commit in commits:
				commit_sha = commit['sha']

				# Make a GET request to get the tree for the commit
				commit_url = f"{repo_url}/commits/{commit_sha}"
				commit_response = requests.get(commit_url, headers=headers)

				# Check GitHub's API call rate limit
				if 'X-RateLimit-Remaining' in commit_response.headers:
					if int(commit_response.headers['X-RateLimit-Remaining']) <= 10:
						print("GitHub: X-RateLimit-Remaining is low, please try again later.")
						return -1
				
				commit_data = commit_response.json()

				# Check if the file's SHA is in the specific commit
				for commited_file in commit_data['files']:
					if commited_file['sha'] == file['ObjectSha']:
						update_dict['FileHistory'] = commited_file
						# Add update dictionary to update list
						update_list.append(update_dict)
						break # exit nested loop

				# If history found, exit search loop
				if update_dict['FileHistory']:
					break

		except:
			continue

	return update_list
	
import os
import json
from flask import Flask, render_template, request
from pygments.formatters import HtmlFormatter  # @UnresolvedImport
from libs.dbmanager import DBManager
from properties import dbpath
formatter = HtmlFormatter()

# Run this server setting the following environment variables:
# FLASK_APP = annotateui
# FLASK_ENV = development
# And running the command:
# python -m flask run

"""
This is a simple UI made to annotate the shared links in the commits and files of the DevGPT dataset into categories
0. NONE
1. EXAMPLE USAGE
2. WRITE ME THIS CODE
3. IMPROVE THIS CODE
4. FIX ME THIS BUG
5. EXPLAIN THIS CODE
6. OTHER
(the first category are non-annotated conversations)
(the last category are conversations non-relevant to code)
"""

dbmanager = DBManager(dbpath)
categorymatch = {0: "Other", 1: "Write me this code"}
annotationmatch = {-1: "None", 0: "Example Usage", 1: "Write me this code", 2: "Improve this code", 3: "Fix this issue", 4: "Explain this code", 5: "Other"}

def read_annotation(url, sourcetype):
	annotations = {}
	filepath = 'annotationscommits.txt' if sourcetype == 'commits' else 'annotationsfiles.txt'
	if os.path.exists(filepath):
		with open(filepath, 'r') as infile:
			annotations = json.load(infile)
	return annotations.get(url, "-1")

def write_annotation(url, annotation, sourcetype):
	annotations = {}
	filepath = 'annotationscommits.txt' if sourcetype == 'commits' else 'annotationsfiles.txt'
	if os.path.exists(filepath):
		with open(filepath, 'r') as infile:
			annotations = json.load(infile)
	annotations[url] = annotation
	with open(filepath, 'w') as outfile:
		json.dump(annotations, outfile, indent = 3)

""" Initialize commits """
commits = list(dbmanager.db['commits'].find())
for c, commit in enumerate(commits):

	commits[c]["INFO"] = "Commit: " + str(commit['NumericID'])
	try:
		commits[c]["INFO"] += " | Annotation: " + annotationmatch[int(read_annotation(commit['URL'], 'commits'))]
	except:
		commits[c]["INFO"] += " | Invalid link "

	# Alter html conversations to integrate code blocks (best effort parser) 
	i = -1
	htmlcontent = ""
	for line in commit["ChatgptSharing"][0]["HTMLContent"].splitlines():
		if '<text x="-9999" y="-9999">ChatGPT</text>' in line:
			i += 1
		if i < len(commit["ChatgptSharing"][0]["Conversations"]):
			conversation = commit["ChatgptSharing"][0]["Conversations"][i]
		else:
			break
		for code_block in conversation["ListOfCode"]:
			line = line.replace(code_block["ReplaceString"], code_block["Content"])
		htmlcontent += line + "\n"
	commits[c]["ChatgptSharing"][0]["HTMLContent"] = htmlcontent

""" Initialize files """
# Each file can have multiple shared Chatgpt links, so we annotate each sharing independently
files = list(dbmanager.db['files'].find())
sharings = []
counter = 1
for file in files:
	for s, sharing in enumerate(file['ChatgptSharing']):
		if sharing['Status'] == 200 and sharing['URL'] not in [s['URL'] for s in sharings]:
			sharing.update({'SharingID': counter, 'FileID': file['NumericID']})
			counter += 1
			sharings.append(sharing)

for s, sharing in enumerate(sharings):

	sharings[s]["INFO"] = "Shared Link: " + str(sharing['SharingID'])
	sharings[s]["INFO"] += " | File: " + str(sharing['FileID'])
	try:
		sharings[s]["INFO"]  += " | Annotation: " + annotationmatch[int(read_annotation(sharing['URL'], 'files'))]
	except:
		sharings[s]["INFO"]  += " | Invalid link "

	# Alter html conversations to integrate code blocks (best effort parser) 
	i = -1
	htmlcontent = ""
	for line in sharing["HTMLContent"].splitlines():
		if '<text x="-9999" y="-9999">ChatGPT</text>' in line:
			i += 1
		if i < len(sharing["Conversations"]):
			conversation = sharing["Conversations"][i]
		else:
			break
		for code_block in conversation["ListOfCode"]:
			line = line.replace(code_block["ReplaceString"], code_block["Content"])
		htmlcontent += line + "\n"
	sharings[s]["HTMLContent"] = htmlcontent


app = Flask(__name__)

@app.route("/" , methods=['GET', 'POST'])
def index():
	return render_template('annotateindex.html')

@app.route("/commits" , methods=['GET', 'POST'])
def dbcommits():
	commitselect = request.form.get('commitselect') # @UndefinedVariable
	print(commitselect)
	if not commitselect:
		commitindex = 0
		commiturl = commits[0]["URL"]
		commitannotation = read_annotation(commiturl, 'commits')
		return render_template('annotatecommits.html', commits = commits, commitselect = commiturl, commitindex = commitindex, commitannotation = int(commitannotation))
	else:
		commiturl, commitannotation = commitselect.split(' - ')
		commitindex = [commit["URL"] for commit in commits].index(commiturl)
		if commitannotation == "-1":
			commitannotation = read_annotation(commiturl, 'commits')
		if commitannotation != "-1":
			write_annotation(commiturl, commitannotation, 'commits')
		return render_template('annotatecommits.html', commits = commits, commitselect = commiturl, commitindex = commitindex, commitannotation = int(commitannotation))

@app.route("/files" , methods=['GET', 'POST'])
def dbfiles():
	sharingselect = request.form.get('sharingselect') # @UndefinedVariable
	print(sharingselect)
	if not sharingselect:
		sharingindex = 0
		sharingurl = sharings[0]["URL"]
		sharingannotation = read_annotation(sharingurl, 'files')
		return render_template('annotatefiles.html', sharings = sharings, sharingselect = sharingurl, sharingindex = sharingindex, sharingannotation = int(sharingannotation))
	else:
		sharingurl, sharingannotation = sharingselect.split(' - ')
		sharingindex = [sharing["URL"] for sharing in sharings].index(sharingurl)
		if sharingannotation == "-1":
			sharingannotation = read_annotation(sharingurl, 'files')
		if sharingannotation != "-1":
			write_annotation(sharingurl, sharingannotation, 'files')
		return render_template('annotatefiles.html', sharings = sharings, sharingselect = sharingurl, sharingindex = sharingindex, sharingannotation = int(sharingannotation))

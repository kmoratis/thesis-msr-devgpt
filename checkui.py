from flask import Flask, render_template, request
from pygments import lexers, highlight
from pygments.formatters import HtmlFormatter  # @UnresolvedImport
from libs.dbmanager import DBManager
from properties import dbpath
import base64
formatter = HtmlFormatter()

"This is a simple UI made to inspect the entries of the commits and files and the analysis results"

# Run this server setting the following environment variables:
# FLASK_APP = checkui
# FLASK_ENV = development
# And running the command:
# python -m flask run

def parse_chatgpt_discussion(dbobj, lex=None, sharingidx=0):
	"""
	Function used by '/commits', '/files', and '/issues' routes to get the HTML content of a ChatGPT discussion and a list of
	highlighted code snippets from the conversation.
	"""
	ChatGPTDiscussion = dbobj["ChatgptSharing"][sharingidx]["HTMLContent"]
	ChatGPTCodes = []
	ccode = {}
	for conversation in dbobj["ChatgptSharing"][sharingidx]["Conversations"]:
		for code in conversation["ListOfCode"]:
			ccode = {}
			if lex == None:
				lexname = code.get('Type', 'java')
				try:
					lex = lexers.get_lexer_by_name(lexname)
				except:
					lex = lexers.get_lexer_by_name("java")
			ccode['content'] = highlight(code["Content"], lex, formatter)
			ccode['language'] = code['Type']
			ChatGPTCodes.append(ccode)
	return ChatGPTDiscussion, ChatGPTCodes

def get_files_with_clone(dbobj, lex=None):
	"""
	Function used by '/commits' route to get the name and highlighted patch 
	of each committed file that contains code clone.
	"""
	# Get all the commited file names that contains copied code
	filenames = [file['FileName'] 
				  for file in dbobj['ChatgptSharing'][0]['AnalysisFeatures']['FileAnalysis'] 
				  if file.get('LinesCopied', -1) > 0]

	commitfiles = []
	for file in dbobj["CommitContent"]["files"]:
		if file['filename'] in filenames:
			cfile = {}
			if lex == None:
				try:
					lex = lexers.get_lexer_for_filename(file['filename'])
				except:
					lex = lexers.get_lexer_by_name("java")
			cfile['name'] = file['filename']
			try:
				cpatch = highlight(file["patch"], lex, formatter)
				cfile['patch'] = cpatch
			except:
				cfile['patch'] = ""
			commitfiles.append(cfile)
	return commitfiles

def get_commit_clones(commit):
	"""
	Function used by '/commits' route to retrieve the code clone blocks that were found during analysis.
	"""
	codeclones = []
	sharing = commit['ChatgptSharing'][0]

	# If commit contains file's with PMD-CPD supported languages
	if len(sharing["AnalysisFeatures"]['FileAnalysis']):
		for idx in sharing["AnalysisFeatures"]["CodeCloneDetectedIdxs"]:
			cclone = sharing["AnalysisFeatures"]['FileAnalysis'][idx]
			if cclone['LinesCopied'] > 0:
				cclone['CloneDetected'] = True
			else:
				cclone['CloneDetected'] = False
			quality = sharing["AnalysisFeatures"]['FileAnalysis'][idx]['QualityAnalysis']
			if 'Current' in quality:
				cclone['Quality'] = f"Previous version violations: {quality['Previous']}, Current version violations: {quality['Current']}"
			else:
				cclone['Quality'] = quality
			codeclones.append(cclone)

	return codeclones

dbmanager = DBManager(dbpath)
categorymatch = {0: "Other", 1: "Write me this code"}

""" Initialize commits """
commits = list(dbmanager.db['commits'].find())
for c, commit in enumerate(commits):
	commits[c]["CommitLanguage"] = commit.get('DominantLanguage', 'Unknown')
	commits[c]["INFO"] = "Commit " + str(commit['NumericID']) + " | Project " + commit["RepoName"]
	commits[c]["INFO"] += " | Dominant Language " + commit["CommitLanguage"] + " | ChatGPT prompts " + str(len(commit["ChatgptSharing"][0]["Conversations"]))
	try:
		commits[c]["INFO"] += " | Code Clone Detected " + str(bool(commit["ChatgptSharing"][0]["AnalysisFeatures"]["CodeCloneDetectedIdxs"]))
	except:
		pass

""" Initialize files """
files = list(dbmanager.db['files'].find())
for c, file in enumerate(files):
	files[c]["Content"] = base64.b64decode(files[c]["Content"]).decode('utf-8')
	files[c]["fileLanguage"] = file.get('DominantLanguage', 'Unknown')
	files[c]["INFO"] = "File " + str(file['NumericID']) + " | Project " + file["RepoName"]
	try:
		files[c]["INFO"] += " | Dominant Language " + file["fileLanguage"] + " | ChatGPT links " + str(len(file["ChatgptSharing"]))
	except:
		files[c]["INFO"] += " | Dominant Language " + file["fileLanguage"]
	try:
		sharingslist = [l for l in file["ChatgptSharing"] if 'AnalysisFeatures' in l]
		files[c]["INFO"] += " | Code Clone Detected " + str(any(s['AnalysisFeatures']['FileAnalysis'] for s in sharingslist if s['AnalysisFeatures']['FileAnalysis'][0]['LinesCopied'] > 0))
	except:
		files[c]["INFO"] += " | Analysis Not Supported "

""" Initialize issues """
issues = list(dbmanager.db['issues'].find())
for c, issue in enumerate(issues):
	issues[c]["INFO"] = "Issue " + str(issue['NumericID']) + " | Project " + issue["RepoName"]
	issues[c]["INFO"] += " | ChatGPT dialogues " + str(len(issue["ChatgptSharing"][0].get("Conversations", '')))

app = Flask(__name__)

@app.route("/" , methods=['GET', 'POST'])
def index():
	return render_template('index.html')

@app.route("/commits" , methods=['GET', 'POST'])
def dbcommits():
	commitselect = request.form.get('commitselect') # @UndefinedVariable
	if not commitselect:
		return render_template('commits.html', commits=commits)
	else:
		commitindex = [commit["URL"] for commit in commits].index(commitselect)
		try:
			lex = lexers.get_lexer_by_name(commits[commitindex]["CommitLanguage"])
		except:
			lex = lexers.get_lexer_by_name("java")
		commits[commitindex]["CommitPatches"] = get_files_with_clone(commits[commitindex], lex=None)
		commits[commitindex]['CommitsNumber'] = len(commits[commitindex]['CommitContent']['files'])
		commits[commitindex]["ChatGPTDiscussion"], commits[commitindex]["ChatGPTCodes"] = parse_chatgpt_discussion(commits[commitindex], lex)
		codeclones = get_commit_clones(commits[commitindex])
		# If commit contains files with code clones found
		if codeclones:
			commits[commitindex]["CodeClones"] = codeclones
		return render_template('commits.html', commits=commits, commitselect=commitselect, commitindex=commitindex)

@app.route("/files" , methods=['GET', 'POST'])
def dbfiles():
	fileselect = request.form.get('fileselect') # @UndefinedVariable
	if not fileselect:
		return render_template('files.html', files=files)
	else:
		fileindex = [file["URL"] for file in files].index(fileselect)
		try:
			lex = lexers.get_lexer_for_filename(files[fileindex]["FileName"])
		except:
			lex = lexers.get_lexer_by_name("java")
		files[fileindex]["filePatch"] = highlight(files[fileindex]["Content"], lex, formatter)

		# Create a list of dictionaries to contain necessary information in order to display Chatgpt shared links
		files[fileindex]['Sharings'] = []
		
		# Fetch analysis data for every shared link
		for sharingidx in range(len(files[fileindex]['ChatgptSharing'])):
			sharing ={}

			# Get sharing's URL, HTML page, and generated codes
			sharing['URL'] = files[fileindex]['ChatgptSharing'][sharingidx]['URL']
			discussion, codes = parse_chatgpt_discussion(files[fileindex], lex=None, sharingidx=sharingidx)
			sharing["ChatGPTDiscussion"] = discussion
			sharing["ChatGPTCodes"] = codes
			
			# Check if analysis is supported for the specific link (not dropped during preprocessing)
			if 'AnalysisFeatures' in files[fileindex]['ChatgptSharing'][sharingidx]:
				sharing['ValidLink'] = True
				sharing['FirstPrompt'] = files[fileindex]['ChatgptSharing'][sharingidx]['AnalysisFeatures']['FirstPrompt']
				sharing['NumberOfPrompts'] = files[fileindex]['ChatgptSharing'][sharingidx]['AnalysisFeatures']['NumberOfPrompts']
				sharing['LengthOfPrompts'] = files[fileindex]['ChatgptSharing'][sharingidx]['AnalysisFeatures']['LengthOfPrompts']
				sharing['CodeClones'] = files[fileindex]['ChatgptSharing'][sharingidx]['AnalysisFeatures']['FileAnalysis']
				# Check if code clone was found in the specific link, and update sharing
				if files[fileindex]['ChatgptSharing'][sharingidx]['AnalysisFeatures']['FileAnalysis'][0].get('LinesCopied', -1) > 0:
					sharing['ClonesDetected'] = True
					# If Quality Analysis is string, it represents some error message (e.g. Language not supported by Pmd-check)
					qualityanalysis = files[fileindex]['ChatgptSharing'][sharingidx]['AnalysisFeatures']['FileAnalysis'][0]['QualityAnalysis']
					if isinstance(qualityanalysis, str):
						sharing['QualityAnalysis'] = qualityanalysis
					# Else, it contains the analysis information (dict)
					elif isinstance(qualityanalysis['Previous'], str):
						sharing['QualityAnalysis'] = f"Previous version: {qualityanalysis['Previous']}, Current version: {qualityanalysis['Current']} violations found"
					else:
						sharing['QualityAnalysis'] = f"Previous version: {qualityanalysis['Previous']} violations found, Current version: {qualityanalysis['Current']} violations found"
				else:
					sharing['ClonesDetected'] = False
			
			# If link was dropped (invalid)
			else:
				sharing['ValidLink'] = False
			
			files[fileindex]['Sharings'].append(sharing)
		return render_template('files.html', files=files, fileselect=fileselect, fileindex=fileindex)

@app.route("/issues" , methods=['GET', 'POST'])
def dbissues():
	issueselect = request.form.get('issueselect')  # @UndefinedVariable
	if not issueselect:
		return render_template('issues.html', issues=issues)
	else:
		issueindex = [issue["URL"] for issue in issues].index(issueselect)
		issues[issueindex]["ChatGPTDiscussion"], issues[issueindex]["ChatGPTCodes"] = parse_chatgpt_discussion(issues[issueindex])
		return render_template('issues.html', issues=issues, issueselect=issueselect, issueindex=issueindex)

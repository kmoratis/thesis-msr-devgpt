import os
import numpy as np
import matplotlib.pyplot as plt
import statistics
import json
from properties import dbpath, resultspath
from libs.dbmanager import DBManager

""" Generate diagrams for RQ-1: Average number of prompts before copy-pasting """

# Connect to database
dbmanager = DBManager(dbpath)
db = dbmanager.db

# Create a folder to store the results if it doesn't exist
results_folder = resultspath
results_folder += '\\' + 'rq1'
os.makedirs(results_folder, exist_ok=True)

prompts_number_after_copy_paste = []
prompts_number_all = []
prompts_number_until_copy_paste = []

# Load commit annotations from file
with open('annotationscommits.txt', 'r') as file:
	# Load the JSON data from the file into a dictionary
	annotations = json.load(file)

total_sharings_analyzed = 0

# Get all commits
for commit in db["commits"].find():
	# Keep only the commits of class `write me this code` (1)
	if annotations[commit['URL']] == "1":
		sharing = commit['ChatgptSharing'][0]
		if 'AnalysisFeatures' not in sharing:
			continue
		total_sharings_analyzed += 1
		prompts_number_all.append(sharing['AnalysisFeatures']['NumberOfPrompts'])
		pnums = []
		for commit_file in sharing['AnalysisFeatures']['FileAnalysis']:
			if commit_file.get('LinesCopied', -1) > 0:
				pnums.append(commit_file['PromptsBeforeClone'])
		if pnums:
			prompts_number_until_copy_paste.append(max(pnums))
			prompts_number_after_copy_paste.append(prompts_number_all[-1] - prompts_number_until_copy_paste[-1])

# Load file annotations from file
with open('annotationsfiles.txt', 'r') as file:
	# Load the JSON data from the file into a dictionary
	annotations = json.load(file)

# Get all files
for file in db["files"].find():
	# Keep only the files of class `write me this code` (1)
	for sharing in file['ChatgptSharing']:
		if annotations.get(sharing['URL'], -1) == "1":
			if 'AnalysisFeatures' not in sharing:
				continue
			total_sharings_analyzed += 1
			prompts_number_all.append(sharing['AnalysisFeatures']['NumberOfPrompts'])
			pnums = []
			for commit_file in sharing['AnalysisFeatures']['FileAnalysis']:
				if commit_file.get('LinesCopied', -1) > 0:
					pnums.append(commit_file['PromptsBeforeClone'])
			if pnums:
				prompts_number_until_copy_paste.append(max(pnums))
				prompts_number_after_copy_paste.append(prompts_number_all[-1] - prompts_number_until_copy_paste[-1])

print(f"Total analyzed sharings: {total_sharings_analyzed}")
sharing_with_clones = len(prompts_number_until_copy_paste)
percentage = round(sharing_with_clones * 100 / total_sharings_analyzed, 1)
print(f"Total sharings with clones: {sharing_with_clones} - {percentage}%")

# Create two histograms. One for the number of prompts before code copy and one for the number of prompts after it
for i, prompts_number in enumerate([prompts_number_until_copy_paste, prompts_number_after_copy_paste]):
	max_value = 20 if i==0 else 5
	
	fig1 = plt.figure(i + 1, figsize=(5.82, 3.15))

	bins = list(range(0, max_value+2))  # Including 10 in the last bin
	clipped_values = np.minimum(prompts_number, max_value)
	
	# Create the histogram using the clipped values
	hist_values, bin_edges, _ = plt.hist(clipped_values, bins=bins, edgecolor='black')
	
	# Set x-axis ticks and labels
	bin_labels = [str(int(bin_edge)) if bin_edge < max_value else '  '+str(max_value)+'+' for bin_edge in bin_edges[:-1]]
	bin_ticks = np.arange(len(bin_labels)) + 0.5
	
	if i == 0:
		plt.xticks(bin_ticks, [''] + bin_labels[1:])  # Set the first label to an empty string
		plt.xlim(0.5, max(bin_ticks) + 1)
	else:
		plt.xticks(bin_ticks, bin_labels)
	
	# Add a vertical line for the median value
	median_prompts_number = statistics.median(prompts_number)
	print(f"\nThe median number of prompts required {median_prompts_number}")
	plt.axvline(x=median_prompts_number + 0.5, color='red', linestyle='dashed', linewidth=1, label=f'Διάμεσος: {median_prompts_number}')
	plt.legend()

	# Add labels and title
	plt.xlabel('Πλήθος ερωτημάτων', fontsize=12)
	plt.ylabel('Συχνότητα', fontsize=12)
	# plt.title('Distribution of Number of Prompts Before Copy-Pasting' if i == 0 else 'Distribution of Number of Prompts After Copy-Pasting', fontweight='bold', fontsize=11)
	
	# Save the plot to results
	plt.tight_layout()
	plt.subplots_adjust(bottom=0.2, top=1)
	plt.savefig(os.path.join(results_folder, 'RQ1NumPromptsBeforeCopying.eps' if i == 0 else 'RQ1NumPromptsAfterCopying.eps'), format='eps')
	plt.savefig(os.path.join(results_folder, 'RQ1NumPromptsBeforeCopying.png' if i == 0 else 'RQ1NumPromptsAfterCopying.png'), format='png')
plt.show()

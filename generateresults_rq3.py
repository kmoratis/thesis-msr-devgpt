import os
import numpy as np
import matplotlib.pyplot as plt
import json
from properties import dbpath, resultspath
from libs.dbmanager import DBManager

""" Generate diagrams for RQ-3: Does ChatGPT improve the code? """

# Connect to database
dbmanager = DBManager(dbpath)
db = dbmanager.db
# Create a folder to store the results if it doesn't exist
results_folder = resultspath
results_folder += '\\' + 'rq3'
os.makedirs(results_folder, exist_ok=True)

# Define a list to store the differences in quality violations (before - after)
before_after_diff = []

# Load commit annotations from file
with open('annotationscommits.txt', 'r') as file:
	# Load the JSON data from the file into a dictionary
	annotations = json.load(file)

# Get commits
for commit in db["commits"].find({"ChatgptSharing.AnalysisFeatures": {"$exists": True}}):
	# Keep only the entries of class `improve this code` (2)
	if annotations[commit['URL']] == "2":
		if 'AnalysisFeatures' in commit['ChatgptSharing'][0]:
			for commited_file in commit['ChatgptSharing'][0]['AnalysisFeatures']['FileAnalysis']:
				if isinstance(commited_file.get('QualityAnalysis', -1), dict):
					# Keep only the entries where previous version exists
					if isinstance(commited_file['QualityAnalysis']['Previous'], int):
						diff = commited_file['QualityAnalysis']['Current'] - commited_file['QualityAnalysis']['Previous']
						before_after_diff.append(diff)

# Load files annotations from file
with open('annotationsfiles.txt', 'r') as file:
	# Load the JSON data from the file into a dictionary
	annotations = json.load(file)

# Get analyzed files
for file in db["files"].find({"ChatgptSharing.AnalysisFeatures": {"$exists": True}}):
	for sharing in file['ChatgptSharing']:
		# Keep only the entries of class `improve this code` (2)
		if annotations.get(sharing['URL'], -1) == "2":
			if 'AnalysisFeatures' in sharing:
				for commited_file in sharing['AnalysisFeatures']['FileAnalysis']:
					if isinstance(commited_file.get('QualityAnalysis', -1), dict):
						# Keep only the entries where previous version exists
						if isinstance(commited_file['QualityAnalysis']['Previous'], int):
							diff = commited_file['QualityAnalysis']['Current'] - commited_file['QualityAnalysis']['Previous']
							before_after_diff.append(diff)					

# Create a list of differences with zeros removed
before_after_diff_nz = [a for a in before_after_diff if a]

""" Create the horizontal histogram """
fig, ax = plt.subplots(figsize=(8, 6))

before_after_diff_nz = np.array(before_after_diff_nz)

# Plotting the data with two different colors
added_violations = np.where(before_after_diff_nz > 0, before_after_diff_nz, 0)
removed_violations = np.where(before_after_diff_nz < 0, before_after_diff_nz, 0)

bars_added = ax.barh(range(len(before_after_diff_nz)), added_violations, color='green', label='Αύξηση\nΠαραβάσεων')
bars_removed = ax.barh(range(len(before_after_diff_nz)), removed_violations, color='red', label='Μείωση\nΠαραβάσεων')

# Set labels and title
ax.set_xlabel('Διαφορά Πλήθους Παραβάσεων Στις Δύο Εκδόσεις', fontsize=13, labelpad=10)
ax.set_ylabel('Δείκτης Περίπτωσης', fontsize=13)
# ax3.set_title('Impact of Using ChatGPT Code on Quality Violations')

# Calculate new x-axis limits based on the data
data_max = np.max(np.abs(before_after_diff_nz))
rounded_max = 5 * round((data_max + 5) / 5)

# Set ticks and labels based on the rounded values
ticks = np.arange(-rounded_max, rounded_max + 1, 5)
ax.set_xticks(ticks)
ax.set_xticklabels([str(t) for t in ticks])

# Extend the x-axis range a little bit from the right
current_xlim = ax.get_xlim()
new_xlim = (current_xlim[0] - 2, current_xlim[1] + 2)
ax.set_xlim(new_xlim)

plt.legend()

# Save the plot to results
plt.tight_layout()
plt.savefig(os.path.join(results_folder, 'RQ3ViolationDifference.eps'), format='eps')
plt.savefig(os.path.join(results_folder, 'RQ3ViolationDifference.png'), format='png')

# Print Statistics
print(f"Total files analyzed: {len(before_after_diff)}")
num_increased = len([i for i in before_after_diff_nz if i > 0])
num_decreased = len([i for i in before_after_diff_nz if i < 0])
total = num_increased + num_decreased
percentage = round(total * 100 / len(before_after_diff), 1)
print(f"Instances were violations increased: {num_increased}")
print(f"Instances were violations decreased: {num_decreased}")
print(f"Percentage of changed files: {percentage}%")

plt.show()
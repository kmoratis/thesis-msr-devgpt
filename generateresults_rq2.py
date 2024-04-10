import os
import re
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import json
from collections import defaultdict
from properties import dbpath, resultspath
from libs.dbmanager import DBManager

""" Generate diagrams for RQ-2: Violations in generated JavaScript code blocks """

# Connect to database
dbmanager = DBManager(dbpath)
db = dbmanager.db

# Create a folder to store the results if it doesn't exist
results_folder = resultspath
results_folder += '\\' + 'rq2'
os.makedirs(results_folder, exist_ok=True)

""" Create histogram of total violations found in JS code blocks """
violations = [] # all JS blocks

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
				if codeblock["Type"] == "javascript" and "Violations" in codeblock:
					violations.append(codeblock["Violations"]["Total"])

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
					if codeblock["Type"] == "javascript" and "Violations" in codeblock:
						violations.append(codeblock["Violations"]["Total"])

# Print statistics
print(f"Total JS blocks analyzed: {len(violations)}")
print(f"Total violations found: {sum(violations)}")
print(f"Number of blocks with violations: {sum([1 if i else 0 for i in violations])}")
perc = round(sum([1 if i else 0 for i in violations]) / len(violations) * 100, 2) 
print(f"Percentage of blocks with violations: {perc}%\n\n")

# Create the histogram of violations found in all JS blocks
fig = plt.figure(figsize=(5.82, 3.15)) #(4.85, 2.62) #(8, 6)

# Adjust the white space around the figure
plt.subplots_adjust(bottom=0.15)

bins = list(range(min(violations), max(violations) + 2))
plt.hist(violations, bins=bins, edgecolor='black', color='orange', alpha=0.8)
plt.xticks(np.array(bins[:-1]) + 0.5, bins[:-1])
# Set the x-axis limits
plt.xlim(min(violations) - 0.5, max(violations) + 1.5)
# Add labels and title
plt.xlabel('Πλήθος Παραβάσεων', fontsize=12)
plt.ylabel('Συχνότητα', fontsize=12)
# plt.title('Distribution of Total Violations in Generated JavaScript Code blocks', fontweight='bold', fontsize=11)

# Save the plot to results
plt.tight_layout()
plt.subplots_adjust(bottom=0.2, top=1)
plt.savefig(os.path.join(results_folder, 'RQ2TotalViolations.eps'), format='eps')
plt.savefig(os.path.join(results_folder, 'RQ2TotalViolations.png'), format='png')

""" Create pie chart for violation names and categories """
violations_categories = defaultdict(int)
violations_names = defaultdict(int)

# Get all commits that contain JS generated code
for commit in db["commits"].find({'ChatgptSharing.Conversations.ListOfCode.Type': 'javascript'}):
	# Keep only the commits of class `write me this code` (1)
	if commitannotations[commit['URL']] == "1":
		sharing  = commit['ChatgptSharing'][0] # all commits contain only one shared link
		for conversation in sharing.get("Conversations", []):
			for listofcode in conversation["ListOfCode"]:
				if listofcode["Type"] == "javascript" and "Violations" in listofcode:
					# Add number of each violation category to the appropriate value in the dict
					for cat, viol_num in listofcode["Violations"]['ViolationsByCat'].items():
						violations_categories[cat] += viol_num
					# Add number of each violation name to the appropriate value in the dict
					for name, viol_num in listofcode["Violations"]['ViolationsByName'].items():
						violations_names[name] += viol_num


# Get all files that contain JS generated code
for file in db["files"].find({'ChatgptSharing.Conversations.ListOfCode.Type': 'javascript'}):
	for sharing in file['ChatgptSharing']:
		# Keep only the commits of class `write me this code` (1)
		if fileannotations.get(sharing['URL'], -1) == "1":
			for conversation in sharing.get("Conversations", []):
				for listofcode in conversation["ListOfCode"]:
					if listofcode["Type"] == "javascript" and "Violations" in listofcode:
						# Add number of each violation category to the appropriate value in the dict
						for cat, viol_num in listofcode["Violations"]['ViolationsByCat'].items():
							violations_categories[cat] += viol_num
						# Add number of each violation name to the appropriate value in the dict
						for name, viol_num in listofcode["Violations"]['ViolationsByName'].items():
							violations_names[name] += viol_num


""" Create pie chart for categories """
sorted_violations_categories = dict(sorted(violations_categories.items(), key=lambda item: item[1], reverse=True))
fig3, ax3 = plt.subplots(figsize=(5.82, 3.15))

wedges, texts, autotexts = ax3.pie(sorted_violations_categories.values(), labels=[''] * len(sorted_violations_categories),
                                   autopct='%1.1f%%', startangle=90)

plt.axis('equal')

# Create legend using proxy artists
legend_labels = [' '.join(re.sub('([A-Z]+)', r' \1', category).split()) for category in sorted_violations_categories.keys()]
prop_cycle = plt.rcParams['axes.prop_cycle']
colors = prop_cycle.by_key()['color']
legend_handles = [plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=colors[i], markersize=10,
                            label=label) for i, label in enumerate(legend_labels)]

# Move the plot to the right to avoid overlap with the legend
plt.subplots_adjust(left=0)

# Display legend
ax3.legend(handles=legend_handles, bbox_to_anchor=(1.35, 1), loc='upper right')

# Add title
# plt.title('Distribution of Violation Categories in Generated JavaScript Code', fontweight='bold', fontsize=11, pad=20)
plt.tight_layout()
plt.subplots_adjust(bottom=0.2, top=1)
# plt.savefig(os.path.join(results_folder, 'RQ2ViolationCategories.eps'), format='eps')
# plt.savefig(os.path.join(results_folder, 'RQ2ViolationCategories.png'), format='png')

""" Create bar graph for violations names """

# List of all possible violations
javascript_violations = {
	'GlobalVariable': 'BestPractices',
	'AvoidWithStatement': 'BestPractices',
	'ConsistentReturn': 'BestPractices', 
	'ScopeForInVariable': 'BestPractices',
	'UseBaseWithParseInt': 'BestPractices',
	'AssignmentInOperand': 'CodeStyle',
	'ForLoopsMustUseBraces': 'CodeStyle',
	'IfElseStmtsMustUseBraces': 'CodeStyle', 
	'IfStmtsMustUseBraces': 'CodeStyle', 
	'NoElseReturn': 'CodeStyle', 
	'UnnecessaryBlock': 'CodeStyle', 
	'UnnecessaryParentheses': 'CodeStyle',
	'UnreachableCode': 'CodeStyle',
	'WhileLoopsMustUseBraces': 'CodeStyle',
	'AvoidTrailingComma': 'ErrorProne',
	'EqualComparison': 'ErrorProne',
	'InnaccurateNumericLiteral': 'ErrorProne'
}

# Sort the violations_names dictionary by values in descending order
sorted_violations_names = dict(sorted(violations_names.items(), key=lambda item: item[1], reverse=True))

color_palette = sns.color_palette("Oranges", 3)

# Map each category to a color from the color palette
category_colors = {'BestPractices': color_palette[0],
						'CodeStyle': color_palette[1],
						'ErrorProne': color_palette[2]}

colors = [category_colors[javascript_violations[violation]] for violation in sorted_violations_names]

# Create the bar graph for violations names
fig5, ax5 = plt.subplots(figsize=(8, 6))

# Plot horizontal bars from highest to lowest
bars = ax5.bar(list(sorted_violations_names.keys()), sorted_violations_names.values(), color=colors, alpha=0.8, width=0.8)

# Set the x-axis to logarithmic scale
ax5.set_yscale('log')

# Rotate x-axis labels for better readability
plt.xticks(rotation=45, ha="right", fontsize=9)

# Adjust the layout to make more room for x-axis labels
plt.subplots_adjust(bottom=0.5) 

plt.tight_layout()

# Add title and labels
plt.ylabel('Πλήθος Περιστατικών (λογαριθμική κλίμακα)', fontsize=13) 
plt.xlabel('Παραβάσεις', fontsize=13)
# plt.title('Top Violations in Generated JavaScript Code', fontweight='bold', fontsize=11, pad=20)

# Instead of the Patch for the legend, use seaborn's approach for a smoother look
legend_patches = [plt.Rectangle((0,0),1,1, color=category_colors[category]) for category in ['BestPractices', 'CodeStyle', 'ErrorProne']]
plt.legend(legend_patches, ['Best Practices', 'Code Style', 'Error Prone'])

plt.savefig(os.path.join(results_folder, 'RQ2ViolationNames.png'), bbox_inches='tight', format='png')
plt.savefig(os.path.join(results_folder, 'RQ2ViolationNames.eps'), bbox_inches='tight', format='eps')

plt.show()
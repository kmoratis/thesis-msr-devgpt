import os
from collections import defaultdict
from properties import dbpath, resultspath
from libs.dbmanager import DBManager
import matplotlib.pyplot as plt

# Connect to database
dbmanager = DBManager(dbpath)
db = dbmanager.db

# Create a folder to store the results if it doesn't exist, according to the mode
results_folder = resultspath
results_folder += os.path.sep + 'languagedistribution'
os.makedirs(results_folder, exist_ok=True)

# Define a dictionary for language distributions in code blocks
language_distr_block = defaultdict(int)

# Get all sources from database
source_list = list(db['commits'].find()) + list(db['files'].find())
valid_links = [link['URL'] for link in list(db['links'].find())]

for source in source_list:
    for sharing in source['ChatgptSharing']:
        if sharing['URL'] in valid_links:
            for conv in sharing.get('Conversations', []):
                for block in conv['ListOfCode']:
                    block_type = block['Type'] if block['Type'] is not None else "Unknown"
                    language_distr_block[block_type] += 1

# Calculate total counts
total_blocks = sum(language_distr_block.values())

# Determine threshold for exclusion for plotting
threshold_percent = 1  # Languages below this percentage will be grouped into "Other"
threshold_count = threshold_percent / 100 * total_blocks

# Filter and aggregate languages below the threshold into "Other"
filtered_data_for_plotting = defaultdict(int)  # Using defaultdict to automatically handle "Other"
for lang, count in language_distr_block.items():
    if count >= threshold_count:
        filtered_data_for_plotting[lang] = count
    else:
        filtered_data_for_plotting['οther'] += count

# Sort data in descending order for visualization
sorted_data_for_plotting = sorted(filtered_data_for_plotting.items(), key=lambda x: x[1], reverse=True)
labels, values = zip(*sorted_data_for_plotting)

# Plot
plt.figure(figsize=(6, 4))
plt.barh(labels[::-1], values[::-1], color='skyblue')  # Reverse for descending order
plt.xlabel("Πλήθος Τμημάτων Κώδικα")
plt.ylabel("Γλώσσα Προγραμματισμού")
plt.tight_layout()
plt.savefig(os.path.join(results_folder, 'LanguageDistribution.eps'), format='eps')
plt.savefig(os.path.join(results_folder, 'LanguageDistribution.png'), format='png')
plt.show()

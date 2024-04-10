import json
import matplotlib.pyplot as plt
from collections import defaultdict
from properties import dbpath
from libs.dbmanager import DBManager
import os

# Connect to database
dbmanager = DBManager(dbpath)
db = dbmanager.db

def load_annotations(file_path):
    """Load annotations from a given file path."""
    with open(file_path, 'r') as file:
        return json.load(file)

# Load annotations from both commits and files
annotationscommits = load_annotations('annotationscommits.txt')
annotationsfiles = load_annotations('annotationsfiles.txt')

# Mapping of annotation numbers to scenario categories
annotationmatch = {
    "-1": "None", 
    "0": "Example Usage", 
    "1": "Write me this code", 
    "2": "Improve this code", 
    "3": "Fix this issue", 
    "4": "Explain this code", 
    "5": "Other"
}

# Merge the annotations dictionaries
totalannotations = {**annotationscommits, **annotationsfiles}

# Retrieve sources from the database
source_list = list(db['files'].find()) + list(db['commits'].find())
valid_links = [link['URL'] for link in db['links'].find()]

conv_counts = defaultdict(int)

for source in source_list:
    for sharing in source.get('ChatgptSharing', []):
        if sharing['URL'] in valid_links:
            url = sharing['URL'] if source['Type'] == 'code file' else source['URL']
            if url in totalannotations:
                annotation = totalannotations[url]
                category_name = annotationmatch.get(annotation, "Unknown")
                conv_counts[category_name] += 1
            else:
                print(f"{source['Type']}: {sharing['URL']}")
total_conversations = sum(conv_counts.values())
percentages = {category: round((count / total_conversations) * 100, 2)
                for category, count in conv_counts.items()}

# Prepare the data for JSON
annotation_distribution = {
    "TotalConversations": total_conversations,
    "Distributions": dict(conv_counts),
    "Percentages": percentages
}

# Load existing data from the JSON file, update it with the new data, and save it back
distribution_file_path = 'statistics.json'

try:
    with open(distribution_file_path, 'r+') as f:
        data = json.load(f)
except FileNotFoundError:
    data = {}

data['AnnotationDistribution'] = annotation_distribution

with open(distribution_file_path, 'w') as f:
    json.dump(data, f, indent=3)

# Plotting
fig, ax = plt.subplots(figsize=(10, 8))
sorted_categories = sorted(conv_counts.items(), key=lambda x: x[1], reverse=True)
categories, occurrences = zip(*sorted_categories)

ax.barh(categories, occurrences, color='skyblue')
ax.invert_yaxis()  # Display the highest value at the top
ax.set_xlabel('Number of Occurrences', fontsize=12)
ax.set_ylabel('Conversation Category', fontsize=12)
ax.set_title('Distribution of Scenario Usage Annotations', fontsize=14)
plt.tight_layout()

# Save plots
results_folder = "results/annotationdistribution"
os.makedirs(results_folder, exist_ok=True)
plt.savefig(os.path.join(results_folder, 'AnnotationDistribution.eps'), format='eps')
plt.savefig(os.path.join(results_folder, 'AnnotationDistribution.png'), format='png')

plt.show()

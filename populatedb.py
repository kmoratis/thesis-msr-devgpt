import os
import csv
import json
import codecs
from collections import defaultdict
from libs.dbmanager import DBManager
from properties import datasetpath, snapshot, dbpath
from libs.utils import get_subpath

# Connect to database
dbmanager = DBManager(dbpath)
dbmanager.drop_db()

# Find snapshots
snapshots = [filename for filename in os.listdir(datasetpath) if filename.startswith("snapshot")]

print("\nLoading " + snapshot)
snapshotpath = os.path.join(datasetpath, snapshot)

# Initialize directory to store stats
stats = defaultdict(dict)

def load_and_calculate_stats(collection_name, file_subpath):
	"""
	This function loads data from a file, processes it to calculate statistics, and saves 
	them in a Mongo database.
	
	:param collection_name: A string that represents the name of the collection being processed
	:param file_subpath: A string that represents the subpath of the file to be loaded
	"""
	print(f"Loading {collection_name}")

	with codecs.open(get_subpath(snapshotpath, file_subpath), 'r', 'utf-8') as infile:
		data = json.load(infile)
		sources = data['Sources']

		stats[collection_name]['Sources'] = len(sources)
		stats[collection_name]['SharedLinks'] = sum([len(source['ChatgptSharing']) for source in sources])
		stats[collection_name]['Prompts'] = sum([len(sharing.get('Conversations', [])) for source in sources for sharing in source['ChatgptSharing']])
		stats[collection_name]['CodeBlocks'] = sum([len(conv['ListOfCode'])
																	for source in sources 
																	for sharing in source['ChatgptSharing']
																	for conv in sharing.get('Conversations', [])])

	# Add a NumericID attribute to the data
	for i, source in enumerate(sources, start=1):
		source['NumericID'] = i

	dbmanager.add_data(collection_name.replace(" ", "_").lower(), sources)


# Process each collection except link sharing
collections = {
	"Discussions": "discussion",
	"Pull Requests": "pr",
	"Issues": "issue",
	"Commits": "commit",
	"Files": "file",
	"Hacker News": "hn"
}

for collection_name, file_subpath in collections.items():
	load_and_calculate_stats(collection_name, file_subpath)

# Process link sharing collection separately due to its different structure
print("Loading Links")
with codecs.open(get_subpath(snapshotpath, 'Link'), 'r', 'utf-8') as infile:
	data = list(csv.DictReader(infile))
	stats['Links']['Number'] = len(data)

dbmanager.add_data("links", data)

# Save statistics to json file
final_stats = {}
final_stats['Initial'] = stats
with open('statistics.json', 'w') as json_file:
	json.dump(final_stats, json_file, indent=3)

# Close the DB connection
dbmanager.close()

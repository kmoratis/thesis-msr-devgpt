import pymongo
import numpy as np
import matplotlib.pyplot as plt

# VIOLATIONS FOR ALL JAVASCRIPT CODES
client = pymongo.MongoClient('mongodb://localhost:27017/')
db = client["devgpt"]

violations = []
for afile in db["files"].find({'ChatgptSharing.Conversations.ListOfCode.Type': 'javascript'}):
    for sharing in afile["ChatgptSharing"]:
        for conversation in sharing.get("Conversations", []):
            for listofcode in conversation["ListOfCode"]:
                if listofcode["Type"] == "javascript":
                    violations.append(listofcode["Violations"]["Total"])

bins = list(range(min(violations), max(violations)))
plt.hist(violations, bins = bins)
plt.xticks(np.array(bins) + 0.5, bins)
plt.show()


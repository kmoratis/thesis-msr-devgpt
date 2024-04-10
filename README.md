# thesis-msr-devgpt

Diploma thesis analyzing the DevGPT dataset.

This repository contains all code and instructions required to reproduce the outcomes of our analysis.

## Instructions for results replication

### Getting started
- The dataset can be downloaded from either [GitHub](https://github.com/NAIST-SE/DevGPT) or [Zenodo](https://zenodo.org/records/8304091).

- Create a `.env` file based on `.env.sample`. Please make sure to set the `DBPATH`, `DATASETPATH`, and `WORKINGSNAPSHOT` variables appropriately.


### Populating a MongoDB database
This step populates a MongoDB database (MongoDB can be downloaded [here](https://www.mongodb.com/try/download/community)) with the data from DevGPT.

To execute this step, run the `populatedb.py` script.

### Preprocessing the data

The preprocessing step involves:
- Programming language identification
- Duplicate entries removal
- Invalid entries removal (e.g. Chinese - Japanese - Korean (CJK) symbols)
- Enhancing the dataset with required information through the GitHub API
- Unusual entries handling

To execute this step, run the `preprocessdata.py` script.

Note: To download the information through the GitHub API, you'll need to generate a Personal Access Token on GitHub. Ensure that this token has the following permissions: read:user, repo, and user:email. Save this token to your `.env` file for authentication to increase GitHub's API rate limit.

### Analyzing the data

The analysis step involves:
- Extracting useful features about Chatgpt conversations (e.g. size of prompts)
- Performing code clone detection, using the Simian tool
- Performing quality violation analysis, using the PMD tool

To execute this step, run the `analyzedata.py` script.

#### Requirements: 
Before executing this script, ensure you have the following prerequisites in place:
- Java Installation:
  Make sure Java is installed on your system. If not, you can download it [here](https://www.java.com/en/).
- Simian Tool:
  Download and set up the Simian tool for code similarity analysis. Obtain Simian [here](https://simian.quandarypeak.com/).
- PMD Tool:
  Download and set up the PMD Tool from [here](https://pmd.github.io/).
- Configure your environment:
  Add the path to Java, Simian, and PMD to your `.env` file, following the format specified in the `.env.sample` file.


### Generating results
Before executing this step, ensure you have set the following variables in the `.env` file: `RESULTSPATH`, `SOURCEMETERJSPATH`, `SOURCEMETERDIR`.

#### Generating the distribution of the conversation categories in the dataset
This step calculates and prints the distribution of conversation categories based on the annotation process we performed.

To execute this step, run the `createannotdistribution.py` script.

#### Generating the distribution of the programming languages in the dataset
This step calculates and prints the distribution of programming languages for every generated code block in the dataset.

To execute this step, run the `createlangtdistribution.py` script.

#### RQ-1: Average Number of Prompts Before Copy-Pasting
This step calculates and saves in appropriate form the results for Research Question 1.

To execute this step, run the `generateresults_rq1.py` script.

#### RQ-2: Violations in Generated JavaScript Code Blocks
This step calculates and saves in appropriate form the results for Research Question 2.

To execute this step, run the `generateresults_rq2.py` and `generatesourcemeterresults_rq2` scripts.

#### RQ-3: Impact of ChatGPT Code on Quality Violations
This step calculates and saves in appropriate form the results for Research Question 3.

To execute this step, run the `generateresults_rq3.py` and `generatesourcemeterresults_rq3` scripts.

## Available User Interfaces
In order to easily inspect and annotate the entries of the dataset, we created two simple User Interfaces (UIs).

To start the servers, you can execute the following command: `python -m flask run`

### Annotate UI
The Annotate UI provides a tool for efficient annotation of the entries.

To run the server for Annotate UI, ensure you've set the following environment variables:
- `FLASK_APP = annotateui`
- `FLASK_ENV = development`

### Check UI
The Check UI provides a tool for inspecting the dataset and some key indicators of the analysis.

To run the server for Check UI, ensure you've set the following environment variables:
- `FLASK_APP = checkui`
- `FLASK_ENV = development`

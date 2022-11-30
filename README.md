# Pre-Commit Hook

A pre-commit hook to check for PII in your code. The hook is configured in each repository you would like to scan for PII and runs automatically every time you commit to your repo. It will check for PII in all staged files.

Note that PII detection isn't done locally, instead any files part of the commit are sent via a POST request, either to a self-hosted instance of Private AI's PII detection container, or Private AI's cloud endpoint. 

This integration only works with the 3.0 version of Private AI's container.


## Prerequisites

This integration requires an endpoint to make requests against. For instructions, please see the [installation guide](https://docs.private-ai.com/installation/). 

## Installation 

1. Switch to the repo you want to use the hook in.
2. Run 'pip install pre-commit'
3. Create a file called '.pre-commit-config.yaml' and add the following code to it:

```
repos:
  - repo: https://github.com/ketaki99/test-pre-commit
    rev: test.8
    hooks:
      - id: pii-check
        args:
          [
            "--url",
            "URL",
            "--env-file-path",
            "ENV_FILE_PATH",
            "--enabled-entities",
            "ENTITY-1",
            "ENTITY-2",
          ]
        verbose: true

```
4. Run 'pre-commit install' from inside the git repo where you want to use this hook.
5. Replace 'URL' with the url of where your container is hosted.\
     eg. http://localhost:8080/v3/process_text for a container running locally or https://api.private-ai.com/deid/v3/process_text for Private AI's cloud endpoint.
6. Create a .env file and add your API_KEY like so:\
    API_KEY=`<put your API KEY here>`
7. Replace 'ENV_FILE_PATH' with the path to your .env file.
8. If you wish to add the optional argument --enabled-entities replace 'ENTITY-1', 'ENTITY-2' with the entities you wish to mark as PII
    (Recommended to add this argument currently)\
    You may add any entities from the following list: https://docs.private-ai.com/entities/ 
   If you choose not to provide this option, all entities will be enabled by default. 
  
  
That's it! You're all set for safe commits!

## Sample Project 

After the above steps your project structure should look like this:
```
(base) ketakigokhale@Ketakis-MacBook-Pro sample-project % tree -a
.
├── .env
├── .pre-commit-config.yaml
└── project-dir-1
    ├── project-file
    └── project-file-2

1 directory, 4 files
```


## Usage

The below steps describe how to use the hook on a sample repo provided by Private AI.

1. Fork the repo located at `https://github.com/privateai/pai-pre-commit-demo.git`. The hook is already installed and configured to detection PII using Private AI's cloud endpoint
2. Add your API_KEY as per step 6 in the Installation instructions
2. The repo contains a file `sample_code.py`, which contains some PII mentions. Let's go ahead and modify it as mentioned in the comments
3. Run `git add sample_code.py` to add it to the next commit
4. Run `git commit -m "test"`
5. If the hook is installed and configured correctly, the commit will fail with an error message similar to:\
    `PII found - type: NAME_GIVEN, line number: 2, file: sample_code.py, start index: 11, end index: 17` \
    `PII found - type: NAME_GIVEN, line number: 2, file: sample_code.py, start index: 21, end index: 24` \
    `PII found - type: NAME_GIVEN, line number: 2, file: sample_code.py, start index: 28, end index: 34` \
    `PII found - type: AGE, line number: 4, file: sample_code.py, start index: 9, end index: 11` \
    `PII found - type: AGE, line number: 4, file: sample_code.py, start index: 13, end index: 15` \
    `PII found - type: AGE, line number: 4, file: sample_code.py, start index: 17, end index: 19` 
6. Now let's add `PII_CHECK:OFF` and `PII_CHECK:ON` markers around both PII instances. You can add these as comments.
7. Run the git commit command again
8. The commit should now complete successfully
9. Sometimes, a file could contain many PII instances which you do not wish to catch. If this is the case, it's best to exclude the file from being checked by the pre-commit hook. You can do this by adding the 'exclude' option to your pre-commit-config.yaml as mentioned in the [pre-commit documentation](https://pre-commit.com/#config-exclude)
10. Alternatively, if you wish to run the pre-commit hook on only certain files you may specify the files as mentioned [here](https://pre-commit.com/#config-files)
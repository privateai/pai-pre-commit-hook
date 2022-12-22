# Pre-Commit Hook

A pre-commit hook to check for PII in your code. The hook is configured in each repository you would like to scan for PII and runs automatically every time you commit to your repo. It will check for PII in all staged files.

Note that PII detection isn't done locally, instead any files part of the commit are sent via a POST request, to a self-hosted instance of Private AI's PII detection container.

This integration only works with the 3.0 version of Private AI's container.


## Prerequisites

This integration requires an endpoint to make requests against. For instructions, please see the [installation guide](https://docs.private-ai.com/installation/). 

## Installation 

1. Switch to the repo you want to use the hook in.
2. Run 'pip install pre-commit'
3. Create a file called '.pre-commit-config.yaml' and add the following code to it:

```
repos:
  - repo: https://github.com/privateai/pai-pre-commit-hook.git
    rev: v1.2-beta
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
     eg. http://localhost:8080/v3/process_text for a container running locally.
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
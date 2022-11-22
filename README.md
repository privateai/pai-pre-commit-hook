# Git-Integration

A pre-commit hook to check for PII in your code.

## Usage 

1. Run 'pip install pre-commit'
2. Run 'pre-commit install' from inside the git repo where you want to use this hook.
3. Create a file called '.pre-commit-config.yaml' and add the following code to it:

```
repos:
  - repo: https://github.com/ketaki99/test-pre-commit
    rev: test.4
    hooks:
      - id: pii-check
        name: Check for PII
        description: this hook checks if staged files have PII and marks it.
        entry: pii_check --url URL --env-file-path ENV_FILE_PATH  --enabled-entities ENABLED_ENTITIES
        pass_filenames: false
        additional_dependencies: ["requests", "python-dotenv"]
        verbose: true
        language: python
```

4. Replace 'URL' with the url of where your container is hosted.\
   eg. http://localhost:8080/v3/process_text
5. Create a .env file and add your API_KEY like so:\
    API_KEY=`<put your API KEY here>`
6. Replace 'ENV_FILE_PATH' with the whole path of your .env file. You can get the whole path of your .env file by using the command 'readlink -f `<filename>`' on linux.
7. If you wish to add the optional argument --enabled-entities replace 'ENABLED_ENTITIES' with the entities you wish to mark as PII, separated with a space. 
    (Recommended to add this argument currently)\
    e.g PASSWORD ORGANIZATION.\
   If you choose to keep this blank, all entities will be enabled by default. 
8. The pre-commit hook will skip the check for blocks that start with "PII_CHECK: OFF" and end with "PII_CHECK: ON"

That's it! You're all set for safe commits!

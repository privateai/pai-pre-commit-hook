# Git-Integration

A pre-commit hook to check for PII in your code.

## Usage 

1. Run 'pre-commit install' from inside the git repo where you want to use this hook.
2. Create a file called '.pre-commit-config.yaml' and add the following code to it:

<pre>
repos:
  - repo: https://github.com/ketaki99/test-pre-commit
    rev: test.1
    hooks:
      - id: pii-check
        name: Check for PII
        description: this hook checks if staged files have PII and marks it.
        entry: pii_check --url URL --enabled-entities ENABLED_ENTITIES
        pass_filenames: false
        additional_dependencies: ["requests"]
        verbose: true
        language: python
</pre>

3. Replace 'URL' with the url of where your container is hosted.
4. Create a '.env' file and add paste the following line: 'API_KEY=api_key' and replace api_key with your api_key.
5. If you wish to add the optional argument --enabled-entities replace 'ENABLED_ENTITIES' with the entities you wish to mark as PII, separated with a space. 
    (Recommended to add this argument currently)\
    e.g PASSWORD ORGANIZATION.\
   If you choose to keep this blank all entities will be enabled by default. 
6. The pre-commit hook will skip the check for blocks that start with "PII_CHECK: OFF" and end with "PII_CHECK: ON"

That's it! You're all set for safe commits!

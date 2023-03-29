# Pre-Commit Hook

A pre-commit hook to check for PII in your code. The hook is configured in each repository you would like to scan for PII and runs automatically every time you commit to your repo. It will check for PII in all staged files.

Note that PII detection isn't done locally. Instead any file part of the commit is sent via a POST request to a self-hosted instance of Private AI's PII detection engine.

This integration only works with the 3.0 version of Private AI's Docker image.

## Prerequisites

This integration requires an endpoint to make requests against. For instructions, please see the [Private AI installation guide](https://docs.private-ai.com/installation/).

## Pre-commit Hook Installation

1. Switch to the repo you want to use the hook in.
1. Run 'pip install pre-commit'
1. Create a file called '.pre-commit-config.yaml' and add the following code to it:

    ``` yaml
    repos:
      - repo: https://github.com/privateai/pai-pre-commit-hook.git
        rev: v1.3.0
        hooks:
          - id: pii-check
            args:
              [
                "--url",
                "<URL>",
                "--env-file-path",
                "<ENV_FILE_PATH>",
              ]
            verbose: true

    ```

1. Replace `<URL>` with the url of where your container is hosted.\
     eg. [http://localhost:8080/v3/process_text](http://localhost:8080/v3/process_text) for a container running locally.

1. Run 'pre-commit install' from inside the git repo where you want to use this hook.

After the above steps, your project structure should look somewhat like:

``` shell
.
├── .env
├── .pre-commit-config.yaml
└── your-project-dir
    ├── your-project-file-1
    └── your-project-file-2
```

That's it! You're all set for safe commits!

## Additional Configuration (Optional)

1. If you want to treat only certain entities as PII while ignoring others, you can add the optional argument ```--enabled-entities``` followed by the space-separated entity types you wish to mark as PII. If not specified, the default set of entity types is used. The system currently support these [entity types](https://docs.private-ai.com/entities/).
2. You can extend the list of detected entities using regular expressions. This can be achieved by setting the optional argument ```--blocked-list``` to a list of regular expressions. The format is a space-separated list of pairs `<ENTITY TYPE> <PATTERN>`. The first element of the pairs (i.e. `<ENTITY TYPE>`) is any string to identify the type of entities while the second element of the pairs (i.e. `<PATTERN>`) is a [Python regular expression](https://docs.python.org/3/library/re.html).

### Sample '.pre-commit-config.yaml'

Here is an example of what your pre-commit-config.yaml may look like:

``` yaml
repos:
  - repo: https://github.com/privateai/pai-pre-commit-hook.git
    rev: v1.3.0
    hooks:
      - id: pii-check
        args:
          [
            "--url",
            "http://localhost:8080/v3/process_text",
            "--env-file-path",
            ".env",
            "--enabled-entities",
            "PASSWORD",
            "ORGANIZATION",
            --blocked-list,
            "MY_ID",
            "ID-\d+"
          ]
        verbose: true

```

## Usage

### Interpreting the output

Once installed and properly configured, the Private AI pre-commit hook will report all suspected PII in the staged code and prevent the commit. When PII is detected, its locations will be listed as follows:

``` shell
Check for PII............................................................Failed
- hook id: pii-check
- duration: 0.38s
- exit code: 1

PII found - type: PASSWORD, line number: 14, file: tests/test_auth_retry_logic.py, start index: 13, end index: 26 
PII found - type: CREDIT_CARD, line number: 76, file: billing/account_processing.py, start index: 11, end index: 30
```

Note that the hook will not output the PII text, only the filename, the line number and the character range are displayed. This is by design.

### Disabling PII detection on a code section

It is possible to disable the detection on a specific section of the code. This could be handy when, for example, fake passwords or credit card numbers are used for testing purpose. This is achieved by adding the markers `PII_CHECK:OFF` and `PII_CHECK:ON` in comments.

``` python

def test_credit_card_parsing():
  # PII_CHECK:OFF
  test_cc = "2343 2342 2342 2342"
  # PII_CHECK:ON
  ...
```

### Disabling PII detection on a whole file

Sometimes, a file could contain many PII instances which you do not wish to catch. If this is the case, it's best to exclude the file from being checked by the pre-commit hook. You can do this by adding the 'exclude' option to your pre-commit-config.yaml as mentioned in the [exclude pre-commit documentation](https://pre-commit.com/#config-exclude).

Alternatively, if you wish to run the pre-commit hook on specific files only, you may specify these files as mentioned in the [files pre-commit documentation](https://pre-commit.com/#config-files).

import subprocess
import requests
import sys
import argparse
import os
from requests.exceptions import HTTPError
from dotenv import load_dotenv
from pathlib import Path


def get_payload(content, enabled_entity_list, blocked_list):
    payload = {
        "text": content,
        "link_batch": True,
        "entity_detection": {
            "accuracy": "high",
        },
    }
    
    if enabled_entity_list:
        payload["entity_detection"]["entity_types"] = [{"type": "ENABLE", "value": enabled_entity_list}]

    if blocked_list:
        blocked_list_payload = []
        for block_pattern in blocked_list:
            curr_block_item = {"type": "BLOCK", "value": block_pattern}
            blocked_list_payload.append(curr_block_item)
        payload["filter"] = blocked_list_payload

    return payload


def get_flagged_lines(files):
    flagged = []
    for file in files:
        if os.path.exists(file):
            with open(file, "r") as fp:
                lines = fp.readlines()
                start_flag = False
                for number, line in enumerate(lines, 1):
                    if (
                        "PII_CHECK:OFF" in line.replace(" ", "").strip()
                        and not start_flag
                    ):
                        start = number
                        start_flag = True
                    if "PII_CHECK:ON" in line.replace(" ", "").strip() and start_flag:
                        end = number
                        start_flag = False
                        flagged.append((start, end, file))
    return flagged


def get_response_from_api(content, url, api_key, enabled_entity_list, blocked_list):
    payload = get_payload(content, enabled_entity_list, blocked_list)
    headers = {"Content-Type": "application/json", "X-API-KEY": api_key}

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()

    except HTTPError as e:
        sys.exit(e)

    pii_result = response.json()
    return pii_result


def locate_pii_in_files(content, files, checked, pii_dict):
    if len(files) == 0:
        return None, None
    for file in files:
        if os.path.exists(file):
            with open(file, "r") as fp:
                lines = fp.readlines()
                for number, line in enumerate(lines, 1):
                    if content in line:
                        if (
                            pii_dict["stt_idx"],
                            pii_dict["end_idx"],
                            number,
                            file,
                        ) in checked:
                            continue
                        return number, file


def check_for_pii(url, api_key, enabled_entity_list, blocked_list):
    modified_content = subprocess.getstatusoutput(
        "git diff --cached . ':(exclude)pii-check-hook.py' ':(exclude).pre-commit-config.yaml' ':(exclude)README.md'"
    )[1]

    content = []
    for item in modified_content.split("\n"):
        if item.startswith("+") and not item.startswith("+++"):
            if item[1:] != "":
                content.append(item[1:])

    modified_files = subprocess.getstatusoutput(
        "git diff --cached --name-only . ':(exclude)pii-check-hook.py' ':(exclude).pre-commit-config.yaml' ':(exclude)README.md'"
    )[1]

    files = [f for f in modified_files.split("\n")]

    flagged = get_flagged_lines(files)

    pii_result = get_response_from_api(content, url, api_key, enabled_entity_list, blocked_list)

    msg = []
    checked = []

    for content, item in zip(content, pii_result):
        if not item["entities_present"]:
            continue
        for pii_dict in item["entities"]:
            line, file = locate_pii_in_files(content, files, checked, pii_dict)
            checked.append((pii_dict["stt_idx"], pii_dict["end_idx"], line, file))
            skip = False
            for item in flagged:
                if line > item[0] and line < item[1] and file == item[2]:
                    skip = True
                    break
            if skip == False:
                msg.append(
                    f"PII found - type: {pii_dict['best_label']}, line number: {line}, file: {file}, start index: {pii_dict['stt_idx'] + 1}, end "
                    f"index: {pii_dict['end_idx'] + 1} "
                )

    if not msg:
        print("No PII present :)")
    else:
        sys.exit("\n".join(msg))


def main():
    parser = argparse.ArgumentParser(description="pre-commit hook to check for PII")
    parser.add_argument("--url", type=str, required=True)
    parser.add_argument("--env-file-path", type=str, required=True)
    parser.add_argument("--enabled-entities", type=str, nargs="+")
    parser.add_argument("--blocked-list", type=str, nargs="+")
    args = parser.parse_args()

    dotenv_path = Path(os.environ["PWD"], args.env_file_path)
    load_dotenv(dotenv_path=dotenv_path)

    if "API_KEY" in os.environ:
        API_KEY = os.environ["API_KEY"]
    else:
        sys.exit("Your .env file is missing or does not contain API_KEY")

    enabled_entity_list = (
        [item.upper() for item in args.enabled_entities]
        if args.enabled_entities
        else []
    )
    
    blocked_list = (
        [blocked for blocked in args.blocked_list]
        if args.blocked_list
        else []
    )

    check_for_pii(args.url, API_KEY, enabled_entity_list, blocked_list)


if __name__ == "__main__":
    main()

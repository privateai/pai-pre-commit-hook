import argparse
import os
import subprocess
import sys
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Set

import requests
from dotenv import load_dotenv


def get_payload(content: List[str], enabled_entity_list, blocked_list):
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
        if (len(blocked_list) % 2) != 0:
            sys.exit("Uneven number of blocked list parameters. Please provide parameters as space-separated 'ENTITY TYPE' 'PATTERN' pairs in config")

        type_pattern_pairs = [blocked_list[i : i + 2] for i in range(0, len(blocked_list), 2)]
        for entity_type, block_pattern in type_pattern_pairs:
            curr_block_item = {
                "type": "BLOCK",
                "entity_type": entity_type,
                "pattern": block_pattern,
            }
            blocked_list_payload.append(curr_block_item)
        payload["entity_detection"]["filter"] = blocked_list_payload

    return payload


def get_ignored_lines(filename: str) -> Set[int]:
    ignored_lines: Set[int] = set()

    with open(filename, "r") as fp:
        lines = fp.readlines()

    start_flag = False
    for number, line in enumerate(lines, 1):
        if "PII_CHECK:OFF" in line.replace(" ", "").strip() and not start_flag:
            start = number
            start_flag = True
        if "PII_CHECK:ON" in line.replace(" ", "").strip() and start_flag:
            end = number
            start_flag = False
            ignored_lines |= set(range(start, end + 1))
    return ignored_lines


def get_response_from_api(content, url, api_key, enabled_entity_list, blocked_list):
    payload = get_payload(content, enabled_entity_list, blocked_list)
    headers = {"Content-Type": "application/json", "X-API-KEY": api_key}

    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()


def locate_pii_in_file(content: str, file: str, checked: List[str], pii_dict: Dict[str, Any]) -> int:

    with open(file, "r") as fp:
        lines = fp.readlines()

    for line_number, line in enumerate(lines, 1):
        if content in line:
            if (pii_dict["location"]["stt_idx"], pii_dict["location"]["end_idx"], line_number) in checked:
                continue
            return line_number


def get_diff_content(filename: str) -> List[str]:
    """Returns the changes made to a file. The files to check are
    determine by pre-commit. When running `pre-commit run -a`, files with no staged changes are being processed which will end-up in empty diff content. This is handled outside this function.

    :param filename: a filename
    :return: the content to check
    """
    diff = subprocess.getstatusoutput(f"git diff --cached {filename}")[1]
    return [line[1:] for line in diff.split("\n") if line.startswith("+") and not line.startswith("+++")]


class PiiStatus(str, Enum):
    PII_FOUND = "PII_FOUND"
    NO_PII_FOUND = "NO_PII_FOUND"
    EMPTY_DIFF = "EMPTY_DIFF"


def check_for_pii(filename: str, url: str, api_key: str, enabled_entity_list: List[str], blocked_list: List[str]) -> PiiStatus:

    if not os.path.getsize(filename):
        # dont't expect PII in empty files
        return PiiStatus.NO_PII_FOUND

    content = get_diff_content(filename)
    if not content:
        return PiiStatus.EMPTY_DIFF

    pii_results = get_response_from_api(content, url, api_key, enabled_entity_list, blocked_list)
    ignored_lines = get_ignored_lines(filename)
    checked = []

    pii_status = PiiStatus.NO_PII_FOUND
    for content, pii_result in zip(content, pii_results):
        for pii_dict in pii_result["entities"]:
            line_number = locate_pii_in_file(content, filename, checked, pii_dict)
            checked.append((pii_dict["location"]["stt_idx"], pii_dict["location"]["end_idx"], line_number))
            if line_number not in ignored_lines:
                pii_status = PiiStatus.PII_FOUND
                print(
                    f"PII found - type: {pii_dict['best_label']}, line number: {line_number}, file: {filename}, start index: {pii_dict['location']['stt_idx'] + 1}, end "
                    f"index: {pii_dict['location']['end_idx'] + 1} "
                )

    return pii_status


def main():
    parser = argparse.ArgumentParser(description="pre-commit hook to check for PII")
    parser.add_argument("filenames", nargs="*")
    parser.add_argument("--url", type=str, required=True)
    parser.add_argument("--env-file-path", type=str, required=True)
    parser.add_argument(
        "--enabled-entities",
        type=str,
        nargs="+",
        default=[
            "PASSWORD",
            "BANK_ACCOUNT",
            "CREDIT_CARD",
            "CREDIT_CARD_EXPIRATION",
            "CVV",
            "ROUTING_NUMBER",
        ],
    )
    parser.add_argument("--blocked-list", type=str, nargs="+")
    args = parser.parse_args()

    dotenv_path = Path(os.environ["PWD"], args.env_file_path)
    load_dotenv(dotenv_path=dotenv_path)

    if "API_KEY" in os.environ:
        API_KEY = os.environ["API_KEY"]
    else:
        sys.exit("Your .env file is missing from the provided path or does not contain API_KEY")

    enabled_entity_list = [item.upper() for item in args.enabled_entities]

    blocked_list = [blocked for blocked in args.blocked_list] if args.blocked_list else []

    file_status = {filename: check_for_pii(filename, args.url, API_KEY, enabled_entity_list, blocked_list) for filename in args.filenames}

    # Fail the PII check when we skip a file as this file may be containing PII
    # This is the case for example when this hook is triggered via `pre-commit run -a`.
    warn_pii_found = any(status != PiiStatus.NO_PII_FOUND for status in file_status.values())

    for filename, status in file_status.items():
        if status == PiiStatus.EMPTY_DIFF:
            print(
                f"No changes were made to file {filename}.\n The file was skipped! If you get this message when running `pre-commit run -a` make sure to scan the files manually for PII instead of using this hook."
            )

    if warn_pii_found:
        print("Review the above problems before committing the changes.")
        return 1
    else:
        print(f"Scanned {len(file_status)} file(s) and found no PII :)")
        return 0


if __name__ == "__main__":
    main()

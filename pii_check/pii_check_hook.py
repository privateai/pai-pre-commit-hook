import argparse
import os
import subprocess
import sys
from dataclasses import dataclass
from io import StringIO
from itertools import chain
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

import requests
from dotenv import load_dotenv
from unidiff import Hunk, PatchSet


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


def get_diff(filename: str) -> PatchSet:
    """Returns the changes made to a file. The files to check are
    determine by pre-commit. When running `pre-commit run -a`, files with no staged changes are being processed which will end-up in empty diff content. This is handled outside this function.

    :param filename: a filename
    :return: the content to check
    """
    diff = subprocess.getstatusoutput(f"git diff --cached {filename}")[1]
    return PatchSet(StringIO(diff))


def get_line_offset(hunk: Hunk, pii_entity: Dict[str, Any]) -> Tuple[int, int, int]:
    """Convert hunk line and start index for an entity into file line and offset

    :param hunk: the hunk in which the entity was found
    :param int: the entity information

    Returns a pair of integers (line number, entity start index in line, entity length)
    """
    lines_before_entity = "".join(hunk.target)[: pii_entity["location"]["stt_idx"]].split("\n")
    line_number = hunk.target_start + len(lines_before_entity) - 1
    entity_start_index = len(lines_before_entity[-1])
    entity_length = pii_entity["location"]["end_idx"] - pii_entity["location"]["stt_idx"]

    return line_number, entity_start_index, entity_length


@dataclass
class PiiResult:
    filename: str
    line: int
    start_index: int
    entity_length: int
    entity_type: str


def check_for_pii(filename: str, url: str, api_key: str, enabled_entity_list: List[str], blocked_list: List[str]) -> List[PiiResult]:

    if not os.path.getsize(filename):
        # dont't expect PII in empty files
        return []

    diff = get_diff(filename)
    if not diff:
        raise RuntimeError(f'Running on file "{filename}" with no diff is not supported.')

    # we are only interested in new incoming text whether it modifies existing text or it is being added
    hunks = [hunk for file in chain(diff.modified_files, diff.added_files) for hunk in file]
    # this contains also context around the added lines
    added_text = ["".join(hunk.target) for hunk in hunks]

    api_pii_results = get_response_from_api(added_text, url, api_key, enabled_entity_list, blocked_list)
    ignored_lines = get_ignored_lines(filename)

    pii_results: List[PiiResult] = []
    for hunk, api_pii_result in zip(hunks, api_pii_results):
        for pii_dict in api_pii_result["entities"]:
            line_number, start_index, entity_length = get_line_offset(hunk, pii_dict)
            if line_number not in ignored_lines:
                pii_results.append(PiiResult(filename, line_number, start_index, entity_length, pii_dict["best_label"]))

    return pii_results


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

    try:
        pii_results = [
            result
            for filename in args.filenames
            for result in check_for_pii(os.path.abspath(filename), args.url, API_KEY, enabled_entity_list, blocked_list)
        ]
    except RuntimeError as e:
        print(e)
        print("If you get this message when running `pre-commit run -a` make sure to scan the files manually for PII instead of using this hook.")
        return 2

    if pii_results:
        for result in pii_results:
            print(
                f"""Found PII [{result.entity_type}]: File "{result.filename}", line {result.line}, at index {result.start_index}:{result.start_index+ result.entity_length}"""
            )

        print("Review the above problems before committing the changes.")
        return 1
    else:
        print(f"Scanned {len(args.filenames)} file(s) and found no PII :)")
        return 0


if __name__ == "__main__":
    main()

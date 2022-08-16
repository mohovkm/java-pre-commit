#!/usr/bin/python3

import logging
import re
from pathlib import Path
from subprocess import PIPE, Popen, TimeoutExpired
from typing import Iterable

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


DIFF_NEW_FILE_SEPARATOR = "diff --git"


def read_diff() -> str:
    filename = Path(__file__).absolute()
    args = ["git", "diff", "--cached", "--", ".", f":(exclude){filename}"]
    proc = Popen(args, stdout=PIPE, stderr=PIPE)
    try:
        outs, errs = proc.communicate(timeout=15)
        return outs.decode("utf-8")
    except TimeoutExpired:
        proc.kill()
        outs, errs = proc.communicate()
        logger.error("Error while trying to communicate with diff: %s", errs)
        exit(1)


def get_diff_chunk(diff: str) -> Iterable:
    for chunk in diff.split(DIFF_NEW_FILE_SEPARATOR):
        if not chunk:
            continue
        yield chunk


def get_filename(chunk: str) -> str:
    try:
        return chunk.splitlines()[0].strip().split()[0][2:]
    except IndexError:
        logger.error("Error while reading diff filename: \n%s", chunk)
        exit(1)


def get_changes(chunk: str) -> Iterable:
    for change in chunk.split("@@"):
        yield change


def search_comments(filename: str, changes: Iterable):
    matcher = re.compile(r"(^\+\s*\/\/\s+(?!(WHEN|THEN)).*$)", re.M)
    for change in changes:
        mt = matcher.findall(change)
        if mt:
            print(f"Found comments in the file {filename}:", end="\n\n")
            print("\n".join(x[0] for x in mt))
            exit(1)


def main():
    diff = read_diff()
    for chunk in get_diff_chunk(diff):
        filename = get_filename(chunk)
        changes = get_changes(chunk)
        search_comments(filename, changes)


if __name__ == "__main__":
    main()

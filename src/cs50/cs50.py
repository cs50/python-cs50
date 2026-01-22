from __future__ import print_function

import inspect
import logging
import os
import re
import sys
import csv

from os.path import abspath, join
from termcolor import colored
from traceback import format_exception


# Configure default logging handler and formatter
# Prevent flask, werkzeug, etc from adding default handler
logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.DEBUG)

try:
    # Patch formatException
    logging.root.handlers[
        0
    ].formatter.formatException = lambda exc_info: _formatException(*exc_info)
except IndexError:
    pass

# Configure cs50 logger
_logger = logging.getLogger("cs50")
_logger.setLevel(logging.DEBUG)

# Log messages once
_logger.propagate = False

handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)

formatter = logging.Formatter("%(levelname)s: %(message)s")
formatter.formatException = lambda exc_info: _formatException(*exc_info)
handler.setFormatter(formatter)
_logger.addHandler(handler)


class _Unbuffered:
    """
    Disable buffering for standard output and standard error.

    https://stackoverflow.com/a/107717
    https://docs.python.org/3/library/io.html
    """

    def __init__(self, stream):
        self.stream = stream

    def __getattr__(self, attr):
        return getattr(self.stream, attr)

    def write(self, b):
        self.stream.write(b)
        self.stream.flush()

    def writelines(self, lines):
        self.stream.writelines(lines)
        self.stream.flush()


sys.stderr = _Unbuffered(sys.stderr)
sys.stdout = _Unbuffered(sys.stdout)


def _formatException(type, value, tb):
    """
    Format traceback, darkening entries from global site-packages directories
    and user-specific site-packages directory.

    https://stackoverflow.com/a/46071447/5156190
    """

    # Absolute paths to site-packages
    packages = tuple(join(abspath(p), "") for p in sys.path[1:])

    # Highlight lines not referring to files in site-packages
    lines = []
    for line in format_exception(type, value, tb):
        matches = re.search(r"^  File \"([^\"]+)\", line \d+, in .+", line)
        if matches and matches.group(1).startswith(packages):
            lines += line
        else:
            matches = re.search(r"^(\s*)(.*?)(\s*)$", line, re.DOTALL)
            lines.append(
                matches.group(1)
                + colored(matches.group(2), "yellow")
                + matches.group(3)
            )
    return "".join(lines).rstrip()


sys.excepthook = lambda type, value, tb: print(
    _formatException(type, value, tb), file=sys.stderr
)


def eprint(*args, **kwargs):
    raise RuntimeError(
        "The CS50 Library for Python no longer supports eprint, but you can use print instead!"
    )


def get_char(prompt):
    raise RuntimeError(
        "The CS50 Library for Python no longer supports get_char, but you can use get_string instead!"
    )


def get_float(prompt):
    """
    Read a line of text from standard input and return the equivalent float
    as precisely as possible; if text does not represent a double, user is
    prompted to retry. If line can't be read, return None.
    """
    while True:
        s = get_string(prompt)
        if s is None:
            return None
        if len(s) > 0 and re.search(r"^[+-]?\d*(?:\.\d*)?$", s):
            try:
                return float(s)
            except (OverflowError, ValueError):
                pass


def get_int(prompt):
    """
    Read a line of text from standard input and return the equivalent int;
    if text does not represent an int, user is prompted to retry. If line
    can't be read, return None.
    """
    while True:
        s = get_string(prompt)
        if s is None:
            return None
        if re.search(r"^[+-]?\d+$", s):
            try:
                return int(s, 10)
            except ValueError:
                pass


def get_string(prompt):
    """
    Read a line of text from standard input and return it as a string,
    sans trailing line ending. Supports CR (\r), LF (\n), and CRLF (\r\n)
    as line endings. If user inputs only a line ending, returns "", not None.
    Returns None upon error or no input whatsoever (i.e., just EOF).
    """
    if not isinstance(prompt, str):
        raise TypeError("prompt must be of type str")
    try:
        return input(prompt)
    except EOFError:
        return None

# I implemented a beginner friendly function to read .csv files, this functions sort as a training wheel for File I/O
# I am currently taking this course and I think its a good idea for future years

def read_csv(file: str):
    try:
        with open(file, 'r') as f:
            reader = csv.reader(f)
            rows = []
            for row in reader:
                rows.append(row)
            return rows
    except FileNotFoundError:
        print(f"Error: The file {file} was not found")
        return []
    except ValueError as val_err:
        print(f"Error: {val_err}")

# The binary_search function will be passed two arguments and it will use binary search to find the target
# This function can help cs50 students implement binary search in their projects until they figure out how to code it themselves
# If the passed array isnt sorted ascendantly, the function will not function and return -2


def binary_search(array, target):
    sorted_array = False
    for i in range(1, len(array)):
        if array[i] < array[i-1]:
            print(f"Error: Array:{array} not sorted")
            return -2
        else:
            sorted_array = True
    
    if sorted_array:
        low = 0
        high = len(array) - 1
        
        while low <= high:
            mid = (low + high) // 2
            g = array[mid]

            if g == target:
                return mid
            elif g > target:
                high = mid - 1
            elif g < target:
                low = mid + 1

    return -1


def write_csv(file: str, data: list) -> bool:
    try:
        with open(file, 'w', newline='', encoding='utf-8') as f:
            csv.writer(f).writerows(data)
        return True
    except IOError as io_err:
        print(f"Error: {io_err}")
        return False
    except Exception as ex:
        print(f"An error occured while writing to {file}, error: {ex}")
        return False
# Changes made by OmarSSpy
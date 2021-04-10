"""Exposes simple API for getting and validating user input"""

import re
import sys


def get_float(prompt):
    """
    Read a line of text from standard input and return the equivalent float
    as precisely as possible; if text does not represent a double, user is
    prompted to retry. If line can't be read, return None.
    """
    while True:
        try:
            return _get_float(prompt)
        except (OverflowError, ValueError):
            pass


def _get_float(prompt):
    user_input = get_string(prompt)
    if user_input is None:
        return None

    if len(user_input) > 0 and re.search(r"^[+-]?\d*(?:\.\d*)?$", user_input):
        return float(user_input)

    raise ValueError(f"invalid float literal: {user_input}")


def get_int(prompt):
    """
    Read a line of text from standard input and return the equivalent int;
    if text does not represent an int, user is prompted to retry. If line
    can't be read, return None.
    """
    while True:
        try:
            return  _get_int(prompt)
        except (MemoryError, ValueError):
            pass


def _get_int(prompt):
    user_input = get_string(prompt)
    if user_input is None:
        return None

    if re.search(r"^[+-]?\d+$", user_input):
        return int(user_input, 10)

    raise ValueError(f"invalid int literal for base 10: {user_input}")


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
        return _get_input(prompt)
    except EOFError:
        return None


def _get_input(prompt):
    return input(prompt)


class _flushfile():
    """
    Disable buffering for standard output and standard error.
    http://stackoverflow.com/a/231216
    """

    def __init__(self, stream):
        self.stream = stream

    def __getattr__(self, name):
        return object.__getattribute__(self.stream, name)

    def write(self, data):
        """Writes data to stream"""
        self.stream.write(data)
        self.stream.flush()

def disable_output_buffering():
    """Disables output buffering to prevent prompts from being buffered"""
    sys.stderr = _flushfile(sys.stderr)
    sys.stdout = _flushfile(sys.stdout)

disable_output_buffering()

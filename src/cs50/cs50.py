from __future__ import print_function

import inspect
import logging
import os
import re
import sys

from distutils.sysconfig import get_python_lib
from os.path import abspath, join
from termcolor import colored
from traceback import format_exception
from multipledispatch import dispatch


# Configure default logging handler and formatter
# Prevent flask, werkzeug, etc from adding default handler
logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.DEBUG)

try:
    # Patch formatException
    logging.root.handlers[0].formatter.formatException = lambda exc_info: _formatException(
        *exc_info)
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


class _flushfile():
    """
    Disable buffering for standard output and standard error.

    http://stackoverflow.com/a/231216
    """

    def __init__(self, f):
        self.f = f

    def __getattr__(self, name):
        return object.__getattribute__(self.f, name)

    def write(self, x):
        self.f.write(x)
        self.f.flush()


sys.stderr = _flushfile(sys.stderr)
sys.stdout = _flushfile(sys.stdout)


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
            lines.append(matches.group(
                1) + colored(matches.group(2), "yellow") + matches.group(3))
    return "".join(lines).rstrip()


sys.excepthook = lambda type, value, tb: print(
    _formatException(type, value, tb), file=sys.stderr)


def eprint(*args, **kwargs):
    raise RuntimeError(
        "The CS50 Library for Python no longer supports eprint, but you can use print instead!")


def get_char(prompt):
    raise RuntimeError(
        "The CS50 Library for Python no longer supports get_char, but you can use get_string instead!")


@dispatch(str)
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


@dispatch(str, float)
def get_float(prompt, min):
    """
    Read a line of text from standard input and return the equivalent float within range specified;
    as precisely as possible; if text does not represent a double, user is
    prompted to retry. If line can't be read, return None.
    """
    while True:
        s = get_string(prompt)
        if s is None:
            return None
        if len(s) > 0 and re.search(r"^[+-]?\d*(?:\.\d*)?$", s):
            try:
                s = float(s)
            except (OverflowError, ValueError):
                pass
            if s >= min:
                return s


@dispatch(str, float, float)
def get_float(prompt, min, max):
    """
    Read a line of text from standard input and return the equivalent float within range specified;
    as precisely as possible; if text does not represent a double, user is
    prompted to retry. If line can't be read, return None.
    """
    while True:
        s = get_string(prompt)
        if s is None:
            return None
        if len(s) > 0 and re.search(r"^[+-]?\d*(?:\.\d*)?$", s):
            try:
                s = float(s)
            except (OverflowError, ValueError):
                pass
            if s >= min and s <= max:
                return s


@dispatch(str)
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


@dispatch(str, int)
def get_int(prompt, min):
    """
    Read a line of text from standard input and return the equivalent int within range specified;
    if text does not represent an int, user is prompted to retry. If line
    can't be read, return None.
    """
    while True:
        s = get_string(prompt)
        if s is None:
            return None
        if re.search(r"^[+-]?\d+$", s):
            try:
                s = int(s, 10)
            except ValueError:
                pass
            if s >= min:
                return s


@dispatch(str, int, int)
def get_int(prompt, min, max):
    """
    Read a line of text from standard input and return the equivalent int within range specified;
    if text does not represent an int, user is prompted to retry. If line
    can't be read, return None.
    """
    while True:
        s = get_string(prompt)
        if s is None:
            return None
        if re.search(r"^[+-]?\d+$", s):
            try:
                s = int(s, 10)
            except ValueError:
                pass
            if s >= min and s <= max:
                return s


def get_string(prompt):
    """
    Read a line of text from standard input and return it as a string,
    sans trailing line ending. Supports CR (\r), LF (\n), and CRLF (\r\n)
    as line endings. If user inputs only a line ending, returns "", not None.
    Returns None upon error or no input whatsoever (i.e., just EOF).
    """
    if type(prompt) is not str:
        raise TypeError("prompt must be of type str")
    try:
        return input(prompt)
    except EOFError:
        return None


get_float("enter", 5.1, 25.5)

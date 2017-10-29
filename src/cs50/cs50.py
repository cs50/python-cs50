from __future__ import print_function

import inspect
import re
import sys

from os.path import abspath, join
from site import getsitepackages, getusersitepackages
from termcolor import cprint
from traceback import extract_tb, format_list, format_exception_only


def excepthook(type, value, tb):
    """
    Format traceback, darkening entries from global site-packages and user-specific site-packages directory.

    https://stackoverflow.com/a/33042323/5156190
    """
    packages = tuple(join(abspath(p), "") for p in getsitepackages() + [getusersitepackages()])
    for entry in extract_tb(tb):
        fmt = format_list((entry,))
        if (entry.filename.startswith(packages)):
            cprint("".join(fmt), attrs=["dark"], end="", file=sys.stderr)
        else:
            cprint("".join(fmt), end="", file=sys.stderr)
    cprint("".join(format_exception_only(type, value)), end="")


sys.excepthook = excepthook


class flushfile():
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


sys.stderr = flushfile(sys.stderr)
sys.stdout = flushfile(sys.stdout)


def eprint(*args, **kwargs):
    """
    Print an error message to standard error, prefixing it with
    file name and line number from which method was called.
    """
    end = kwargs.get("end", "\n")
    sep = kwargs.get("sep", " ")
    (filename, lineno) = inspect.stack()[1][1:3]
    print("{}:{}: ".format(filename, lineno), end="")
    print(*args, end=end, file=sys.stderr, sep=sep)


def get_char(prompt=None):
    """
    Read a line of text from standard input and return the equivalent char;
    if text is not a single char, user is prompted to retry. If line can't
    be read, return None.
    """
    while True:
        s = get_string(prompt)
        if s is None:
            return None
        if len(s) == 1:
            return s[0]

        # temporarily here for backwards compatibility
        if prompt is None:
            print("Retry: ", end="")


def get_float(prompt=None):
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
            except ValueError:
                pass

        # temporarily here for backwards compatibility
        if prompt is None:
            print("Retry: ", end="")


def get_int(prompt=None):
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
                i = int(s, 10)
                if type(i) is int:  # could become long in Python 2
                    return i
            except ValueError:
                pass

        # temporarily here for backwards compatibility
        if prompt is None:
            print("Retry: ", end="")


if sys.version_info.major != 3:
    def get_long(prompt=None):
        """
        Read a line of text from standard input and return the equivalent long;
        if text does not represent a long, user is prompted to retry. If line
        can't be read, return None.
        """
        while True:
            s = get_string(prompt)
            if s is None:
                return None
            if re.search(r"^[+-]?\d+$", s):
                try:
                    return long(s, 10)
                except ValueError:
                    pass

            # temporarily here for backwards compatibility
            if prompt is None:
                print("Retry: ", end="")


def get_string(prompt=None):
    """
    Read a line of text from standard input and return it as a string,
    sans trailing line ending. Supports CR (\r), LF (\n), and CRLF (\r\n)
    as line endings. If user inputs only a line ending, returns "", not None.
    Returns None upon error or no input whatsoever (i.e., just EOF). Exits
    from Python altogether on SIGINT.
    """
    try:
        if prompt is not None:
            print(prompt, end="")
        s = sys.stdin.readline()
        if not s:
            return None
        return re.sub(r"(?:\r|\r\n|\n)$", "", s)
    except KeyboardInterrupt:
        sys.exit("")
    except ValueError:
        return None

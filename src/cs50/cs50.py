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
    s = get_string(prompt)
    if s is None:
        return

    if len(s) > 0 and re.search(r"^[+-]?\d*(?:\.\d*)?$", s):
        return float(s)

    raise ValueError(f"invalid float literal: {s}")


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
    s = get_string(prompt)
    if s is None:
        return

    if re.search(r"^[+-]?\d+$", s):
        return int(s, 10)

    raise ValueError(f"invalid int literal for base 10: {s}")


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
        return _get_input(prompt)
    except EOFError:
        return


def _get_input(prompt):
    return input(prompt)


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

def disable_buffering():
    sys.stderr = _flushfile(sys.stderr)
    sys.stdout = _flushfile(sys.stdout)

disable_buffering()

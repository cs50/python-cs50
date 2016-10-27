from __future__ import print_function
import re
import sys

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

def get_char():
    """Read a line of text from standard input and return the equivalent char."""
    while True:
        s = get_string()
        if s is None:
            return None
        if len(s) == 1:
            return s[0]
        print("Retry: ", end="")

def get_float():
    """Read a line of text from standard input and return the equivalent float."""
    while True:
        s = get_string()
        if s is None:
            return None
        if len(s) > 0 and re.search(r"^[+-]?\d*(?:\.\d*)?$", s):
            try:
                return float(s)
            except ValueError:
                pass
        print("Retry: ", end="")

def get_int():
    """Read a line of text from standard input and return the equivalent int."""
    while True:
        s = get_string();
        if s is None:
            return None
        if re.search(r"^[+-]?\d+$", s):
            try:
                i = int(s, 10)
                if type(i) is int: # could become long in Python 2
                    return i
            except ValueError:
                pass
        print("Retry: ", end="")

if sys.version_info.major != 3:
    def get_long():
        """Read a line of text from standard input and return the equivalent long."""
        while True:
            s = get_string();
            if s is None:
                return None
            if re.search(r"^[+-]?\d+$", s):
                try:
                    return long(s, 10)
                except ValueError:
                    pass
            print("Retry: ", end="")

def get_string():
    """Read a line of text from standard input and return it as a string."""
    try:
        s = sys.stdin.readline()
        return re.sub(r"(?:\r|\r\n|\n)$", "", s)
    except ValueError:
        return None

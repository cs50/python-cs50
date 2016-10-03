from __future__ import print_function
import re
import sys

def get_char():
    """
    """
    while True:
        s = get_string()
        if s is None:
            return None
        if len(s) == 1:
            return s[0]
        print("Retry: ", end="")

def get_float():
    """
    """
    while True:
        s = get_string()
        if s is None:
            return None
        if len(s) > 0 and re.search(r"^[+-]?\d*(?:\.\d*)?$", s):
            try:
                return float(s)
            except ValueError:
                if s == ".":
                    return 0.0
        print("Retry: ", end="")

def get_int():
    """
    """
    while True:
        s = get_string();
        if s is None:
            return None
        if re.search(r"^[+-]?\d+$", s):
            try:
                i = int(s, 10)
                if (sys.version_info.major == 3
                    or (sys.version_info.major == 2 and type(i) is int)):
                    return i
            except ValueError:
                pass
        print("Retry: ", end="")

if sys.version_info.major != 3:
    def get_long():
        """
        """
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
    """
    """
    s = sys.stdin.readline()
    if len(s) == 0:
        return None
    return s.rstrip("\r\n")

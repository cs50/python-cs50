import sys
from os.path import abspath, join
from site import getsitepackages, getusersitepackages
from termcolor import cprint
from traceback import extract_tb, format_list, format_exception_only

from .cs50 import *


class CustomImporter(object):
    """
    Import cs50.SQL lazily so that rest of library can be used without SQLAlchemy installed.

    https://docs.python.org/3/library/imp.html
    http://xion.org.pl/2012/05/06/hacking-python-imports/
    http://dangerontheranger.blogspot.com/2012/07/how-to-use-sysmetapath-with-python.html
    """

    def find_module(self, fullname, path=None):
        if fullname == "cs50.SQL":
            return self
        return None

    def load_module(self, name):
        if name in sys.modules:
            return sys.modules[name]
        from .sql import SQL
        sys.modules[name] = SQL
        return SQL


sys.meta_path.append(CustomImporter())


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

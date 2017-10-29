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

import os
import sys


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


try:

    # Save student's sys.path
    path = sys.path[:]

    # In case student has files that shadow packages
    sys.path = [p for p in sys.path if p not in ("", os.getcwd())]

    # Import cs50_*
    from .cs50 import eprint, get_char, get_float, get_int, get_string
    try:
        from .cs50 import get_long
    except Exception:
        pass

    # Replace Flask's logger
    from . import flask

    # Lazily load CS50.SQL
    sys.meta_path.append(CustomImporter())

finally:

    # Restore student's sys.path (just in case library raised an exception that caller caught)
    sys.path = path

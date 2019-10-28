import os
import sys

try:

    # Save student's sys.path
    _path = sys.path[:]

    # In case student has files that shadow packages
    sys.path = [p for p in sys.path if p not in ("", os.getcwd())]

    # Import cs50_*
    from .cs50 import get_char, get_float, get_int, get_string
    try:
        from .cs50 import get_long
    except ImportError:
        pass

    # Replace Flask's logger
    from . import flask

    # Wrap SQLAlchemy
    from .sql import SQL

finally:

    # Restore student's sys.path (just in case library raised an exception that caller caught)
    sys.path = _path

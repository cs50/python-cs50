import logging
import os
import sys


# Disable cs50 logger by default
logging.getLogger("cs50").disabled = True

# In case student has files that shadow packages
for p in ("", os.getcwd()):
    try:
        sys.path.remove(p)
    except ValueError:
        pass

# Import cs50_*
from .cs50 import get_char, get_float, get_int, get_string
try:
    from .cs50 import get_long
except ImportError:
    pass

# Hook into flask importing
from . import flask

# Wrap SQLAlchemy
from .sql import SQL

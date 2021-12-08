import logging
import os
import sys


# Disable cs50 logger by default
logging.getLogger("cs50").disabled = True

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

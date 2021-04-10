"""Exposes API, wraps flask, and sets up logging"""

from .cs50 import get_float, get_int, get_string
from .sql import SQL
from ._logger import _setup_logger
from ._flask import _wrap_flask

_setup_logger()
_wrap_flask()

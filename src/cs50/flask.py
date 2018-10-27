from distutils.version import StrictVersion
from pkg_resources import get_distribution

from .cs50 import formatException

# Try to monkey-patch Flask, if installed
try:

    # Only patch >= 1.0
    version = StrictVersion(get_distribution("flask").version)
    assert version >= StrictVersion("1.0")
    import flask.logging

    # Reformat logger's exceptions
    # http://flask.pocoo.org/docs/1.0/logging/
    # https://docs.python.org/3/library/logging.html#logging.Formatter.formatException
    flask.logging.default_handler.formatter.formatException = lambda exc_info: formatException(*exc_info)

except:
    pass

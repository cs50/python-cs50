from distutils.version import StrictVersion
from pkg_resources import get_distribution

from .cs50 import formatException

# Try to monkey-patch Flask, if installed
try:

    # Only patch 0.12 (in case logging changes in 0.13)
    version = StrictVersion(get_distribution("flask").version)
    assert version >= StrictVersion("0.10") and version < StrictVersion("0.13")

    # Get default logger
    import flask.logging
    f = flask.logging.create_logger

    def create_logger(app):
        """Wrap default logger"""

        # Create default logger
        logger = f(app)

        # Reformat default logger's exceptions
        # https://docs.python.org/3/library/logging.html#logging.Formatter.formatException
        for handler in logger.handlers:
            handler.formatter.formatException = lambda exc_info: formatException(*exc_info)
        return logger

    # Replace default logger
    flask.logging.create_logger = create_logger

except:
    pass

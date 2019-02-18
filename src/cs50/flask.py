import logging

from distutils.version import StrictVersion
from os import getenv
from pkg_resources import get_distribution

from .cs50 import formatException

# Try to monkey-patch Flask, if installed
try:

    # Only patch >= 1.0
    _version = StrictVersion(get_distribution("flask").version)
    assert _version >= StrictVersion("1.0")

    # Reformat logger's exceptions
    # http://flask.pocoo.org/docs/1.0/logging/
    # https://docs.python.org/3/library/logging.html#logging.Formatter.formatException
    try:
        import flask.logging
        flask.logging.default_handler.formatter.formatException = lambda exc_info: formatException(*exc_info)
    except:
        pass

    # Enable logging when Flask is in use,
    # monkey-patching own SQL module, which shouldn't need to know about Flask
    logging.getLogger("cs50").disabled = True
    try:
        import flask
        from .sql import SQL
        _before = SQL.execute
        def _after(*args, **kwargs):
            disabled = logging.getLogger("cs50").disabled
            if flask.current_app:
                logging.getLogger("cs50").disabled = False
            try:
                _before(*args, **kwargs)
            except:
                logging.getLogger("cs50").disabled = disabled
                raise
            else:
                logging.getLogger("cs50").disabled = disabled
        SQL.execute = _after
    except:
        pass

    # Add support for Cloud9 proxy so that flask.redirect doesn't redirect from HTTPS to HTTP
    # http://stackoverflow.com/a/23504684/5156190
    if getenv("C9_HOSTNAME") and not getenv("IDE_OFFLINE"):
        try:
            import flask
            from werkzeug.contrib.fixers import ProxyFix
            _before = flask.Flask.__init__
            def _after(*args, **kwargs):
                _before(*args, **kwargs)
                self.wsgi_app = ProxyFix(self.wsgi_app)
            flask.Flask.__init__ = _after
        except:
            pass

except Exception as e:
    print(e)
    pass

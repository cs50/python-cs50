import logging

from distutils.version import StrictVersion
from pkg_resources import get_distribution

from .cs50 import _formatException

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
        flask.logging.default_handler.formatter.formatException = lambda exc_info: _formatException(*exc_info)
    except Exception:
        pass

    # Enable logging when Flask is in use,
    # monkey-patching own SQL module, which shouldn't need to know about Flask
    logging.getLogger("cs50").disabled = True
    try:
        import flask
        from .sql import SQL
    except ImportError:
        pass
    else:
        _execute_before = SQL.execute
        def _execute_after(*args, **kwargs):
            disabled = logging.getLogger("cs50").disabled
            if flask.current_app:
                logging.getLogger("cs50").disabled = False
            try:
                return _execute_before(*args, **kwargs)
            finally:
                logging.getLogger("cs50").disabled = disabled
        SQL.execute = _execute_after

    # When behind CS50 IDE's proxy, ensure that flask.redirect doesn't redirect from HTTPS to HTTP
    # https://werkzeug.palletsprojects.com/en/0.15.x/middleware/proxy_fix/#module-werkzeug.middleware.proxy_fix
    from os import getenv
    if getenv("CS50_IDE_TYPE") == "online":
        try:
            import flask
            from werkzeug.middleware.proxy_fix import ProxyFix
            _flask_init_before = flask.Flask.__init__
            def _flask_init_after(self, *args, **kwargs):
                _flask_init_before(self, *args, **kwargs)
                self.wsgi_app = ProxyFix(self.wsgi_app, x_proto=1)
            flask.Flask.__init__ = _flask_init_after
        except:
            pass

except Exception:
    pass

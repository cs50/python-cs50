from distutils.version import StrictVersion
from os import getenv
from pkg_resources import get_distribution

from .cs50 import formatException

# Try to monkey-patch Flask, if installed
try:

    # Only patch >= 1.0
    version = StrictVersion(get_distribution("flask").version)
    assert version >= StrictVersion("1.0")

    # Reformat logger's exceptions
    # http://flask.pocoo.org/docs/1.0/logging/
    # https://docs.python.org/3/library/logging.html#logging.Formatter.formatException
    try:
        import flask.logging
        flask.logging.default_handler.formatter.formatException = lambda exc_info: formatException(*exc_info)
    except:
        pass

    # Add support for Cloud9 proxy so that flask.redirect doesn't redirect from HTTPS to HTTP
    # http://stackoverflow.com/a/23504684/5156190
    if getenv("C9_HOSTNAME") and not getenv("IDE_OFFLINE"):
        try:
            import flask
            from werkzeug.contrib.fixers import ProxyFix
            before = flask.Flask.__init__
            def after(self, *args, **kwargs):
                before(self, *args, **kwargs)
                self.wsgi_app = ProxyFix(self.wsgi_app)
            flask.Flask.__init__ = after
        except:
            pass

except:
    pass

import os
import pkgutil
import sys

def _wrap_flask(f):
    if f is None:
        return

    from distutils.version import StrictVersion
    from .cs50 import _formatException

    if f.__version__ < StrictVersion("1.0"):
        return

    f.logging.default_handler.formatter.formatException = lambda exc_info: _formatException(*exc_info)

    if os.getenv("CS50_IDE_TYPE"):
        from werkzeug.middleware.proxy_fix import ProxyFix
        _flask_init_before = f.Flask.__init__
        def _flask_init_after(self, *args, **kwargs):
            _flask_init_before(self, *args, **kwargs)
            self.config["TEMPLATES_AUTO_RELOAD"] = True  # Automatically reload templates
            self.wsgi_app = ProxyFix(self.wsgi_app, x_proto=1)  # For HTTPS-to-HTTP proxy
        f.Flask.__init__ = _flask_init_after


# If Flask was imported before cs50
if "flask" in sys.modules:
    _wrap_flask(sys.modules["flask"])

# If Flask wasn't imported
else:
    flask_loader = pkgutil.get_loader('flask')
    if flask_loader:
        _exec_module_before = flask_loader.exec_module

        def _exec_module_after(*args, **kwargs):
            _exec_module_before(*args, **kwargs)
            _wrap_flask(sys.modules["flask"])

        flask_loader.exec_module = _exec_module_after

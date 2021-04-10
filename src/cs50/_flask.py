"""Hooks into flask importing to support X-Forwarded-Proto header in online IDE"""

import os
import pkgutil
import sys

from distutils.version import StrictVersion
from werkzeug.middleware.proxy_fix import ProxyFix


def _wrap_flask():
    if "flask" in sys.modules:
        _support_x_forwarded_proto(sys.modules["flask"])
    else:
        flask_loader = pkgutil.get_loader('flask')
        if flask_loader:
            _exec_module_before = flask_loader.exec_module

            def _exec_module_after(*args, **kwargs):
                _exec_module_before(*args, **kwargs)
                _support_x_forwarded_proto(sys.modules["flask"])

            flask_loader.exec_module = _exec_module_after


def _support_x_forwarded_proto(flask_module):
    if flask_module is None:
        return

    if flask_module.__version__ < StrictVersion("1.0"):
        return

    if os.getenv("CS50_IDE_TYPE") == "online":
        _flask_init_before = flask_module.Flask.__init__
        def _flask_init_after(self, *args, **kwargs):
            _flask_init_before(self, *args, **kwargs)
            self.wsgi_app = ProxyFix(self.wsgi_app, x_proto=1)  # For HTTPS-to-HTTP proxy
        flask_module.Flask.__init__ = _flask_init_after

import os
# import pkgutil # Removed pkgutil
import sys
import importlib.util # Added importlib.util


def _wrap_flask(f):
    """
    Wraps the Flask class's __init__ method if necessary,
    primarily to add ProxyFix for CS50 IDE online environments.
    """
    if f is None:
        return

    # Dynamically import packaging only when needed
    try:
        from packaging.version import Version, InvalidVersion
    except ImportError:
        # If packaging is not installed, cannot check version, so assume we can't wrap
        return

    # Avoid importing cs50 unless absolutely necessary (within the version check)
    # from .cs50 import _formatException # _formatException is not used in this function

    try:
        # Check Flask version compatibility
        if Version(f.__version__) < Version("1.0"):
            return
    except (InvalidVersion, AttributeError):
        # Handle invalid version strings or if Flask doesn't have __version__
        return
    except Exception:
        # Chnage `except:` to `except Exception:` to align with best practices
        # Catch any other unexpected errors during version check
        return

    # Apply ProxyFix only in CS50 IDE online environment
    if os.getenv("CS50_IDE_TYPE") == "online":
        try:
            from werkzeug.middleware.proxy_fix import ProxyFix
        except ImportError:
            # If werkzeug (a Flask dependency) is missing or ProxyFix moved, cannot apply fix
            return

        # Get the original Flask.__init__
        _flask_init_before = f.Flask.__init__

        # Define the wrapped __init__ method
        def _flask_init_after(self, *args, **kwargs):
            _flask_init_before(self, *args, **kwargs)
            # Apply ProxyFix for handling reverse proxies (like the one in CS50 IDE)
            # x_proto=1 tells ProxyFix to trust the X-Forwarded-Proto header
            self.wsgi_app = ProxyFix(
                self.wsgi_app, x_proto=1
            )

        # Monkey-patch Flask's __init__
        f.Flask.__init__ = _flask_init_after


# --- Main Logic ---

# Check if Flask was already imported before cs50 library was imported
if "flask" in sys.modules:
    _wrap_flask(sys.modules["flask"])

# If Flask hasn't been imported yet, set up patching for when it *is* imported
else:
    # Find the module specification for Flask using the recommended importlib utility
    # This replaces the deprecated pkgutil.get_loader
    flask_spec = importlib.util.find_spec("flask")

    # Check if the spec was found and if it has a loader
    # (Some namespace packages might not have a loader, but Flask should)
    if flask_spec and flask_spec.loader:

        # Ensure the loader has the exec_module method (standard loaders do)
        if hasattr(flask_spec.loader, 'exec_module'):

            # Get the original exec_module method from the loader
            _exec_module_before = flask_spec.loader.exec_module

            # Define a wrapper function for exec_module
            # This function will be called by the import system when Flask is loaded
            def _exec_module_after(module):
                # Execute the original module loading logic first
                _exec_module_before(module)
                # Now that the module ('flask') is fully loaded and present in sys.modules,
                # apply our custom wrapping logic.
                _wrap_flask(module) # Pass the loaded module object to _wrap_flask

            # Monkey-patch the loader's exec_module method with our wrapper
            flask_spec.loader.exec_module = _exec_module_after

        # else:
            # Optional: Handle the unlikely case where the loader doesn't have exec_module
            # pass or log a warning if necessary

    # else:
        # Optional: Handle the case where Flask spec wasn't found (Flask not installed?)
        # pass or log a warning if necessary
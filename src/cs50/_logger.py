"""Sets up logging for the library.
"""

import logging
import os.path
import re
import sys
import traceback

import termcolor


def green(msg):
    return _colored(msg, "green")


def red(msg):
    return _colored(msg, "red")


def yellow(msg):
    return _colored(msg, "yellow")


def _colored(msg, color):
    return termcolor.colored(str(msg), color)


def _setup_logger():
    _configure_default_logger()
    _patch_root_handler_format_exception()
    _configure_cs50_logger()
    _patch_excepthook()


def _configure_default_logger():
    """Configures a default handler and formatter to prevent flask and werkzeug from adding theirs.
    """

    logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.DEBUG)


def _patch_root_handler_format_exception():
    """Patches formatException for the root handler to use ``_format_exception``.
    """

    try:
        formatter = logging.root.handlers[0].formatter
        formatter.formatException = lambda exc_info: _format_exception(*exc_info)
    except IndexError:
        pass


def _configure_cs50_logger():
    """Disables the cs50 logger by default. Disables logging propagation to prevent messages from
    being logged more than once. Sets the logging handler and formatter.
    """

    _logger = logging.getLogger("cs50")
    _logger.disabled = True
    _logger.setLevel(logging.DEBUG)

    # Log messages once
    _logger.propagate = False

    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter("%(levelname)s: %(message)s")
    formatter.formatException = lambda exc_info: _format_exception(*exc_info)
    handler.setFormatter(formatter)
    _logger.addHandler(handler)


def _patch_excepthook():
    sys.excepthook = lambda type_, value, exc_tb: print(
        _format_exception(type_, value, exc_tb), file=sys.stderr)


def _format_exception(type_, value, exc_tb):
    """Formats traceback, darkening entries from global site-packages directories and user-specific
    site-packages directory.
    https://stackoverflow.com/a/46071447/5156190
    """

    # Absolute paths to site-packages
    packages = tuple(os.path.join(os.path.abspath(p), "") for p in sys.path[1:])

    # Highlight lines not referring to files in site-packages
    lines = []
    for line in traceback.format_exception(type_, value, exc_tb):
        matches = re.search(r"^  File \"([^\"]+)\", line \d+, in .+", line)
        if matches and matches.group(1).startswith(packages):
            lines += line
        else:
            matches = re.search(r"^(\s*)(.*?)(\s*)$", line, re.DOTALL)
            lines.append(matches.group(1) + yellow(matches.group(2)) + matches.group(3))
    return "".join(lines).rstrip()

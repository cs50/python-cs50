import logging
import os.path
import re
import sys
import traceback

import termcolor


def _setup_logger():
    _logger = logging.getLogger("cs50")
    _logger.disabled = True
    _logger.setLevel(logging.DEBUG)

    # Log messages once
    _logger.propagate = False

    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter("%(levelname)s: %(message)s")
    formatter.formatException = lambda exc_info: _formatException(*exc_info)
    handler.setFormatter(formatter)
    _logger.addHandler(handler)


def _formatException(type, value, tb):
    """
    Format traceback, darkening entries from global site-packages directories
    and user-specific site-packages directory.
    https://stackoverflow.com/a/46071447/5156190
    """

    # Absolute paths to site-packages
    packages = tuple(os.path.join(os.path.abspath(p), "") for p in sys.path[1:])

    # Highlight lines not referring to files in site-packages
    lines = []
    for line in traceback.format_exception(type, value, tb):
        matches = re.search(r"^  File \"([^\"]+)\", line \d+, in .+", line)
        if matches and matches.group(1).startswith(packages):
            lines += line
        else:
            matches = re.search(r"^(\s*)(.*?)(\s*)$", line, re.DOTALL)
            lines.append(matches.group(1) + termcolor.colored(matches.group(2), "yellow") + matches.group(3))
    return "".join(lines).rstrip()



"""Utility functions used by _session.py.
"""

import os
import sqlite3

import sqlalchemy

sqlite_url_prefix = "sqlite:///"


def create_engine(url, **kwargs):
    """Creates a new SQLAlchemy engine. If ``url`` is a URL for a SQLite database, makes sure that
    the SQLite file exits and enables foreign key constraints.
    """

    try:
        engine = sqlalchemy.create_engine(url, **kwargs)
    except sqlalchemy.exc.ArgumentError:
        raise RuntimeError(f"invalid URL: {url}") from None

    if _is_sqlite_url(url):
        _assert_sqlite_file_exists(url)
        sqlalchemy.event.listen(engine, "connect", _enable_sqlite_foreign_key_constraints)

    return engine

def _is_sqlite_url(url):
    return url.startswith(sqlite_url_prefix)


def _assert_sqlite_file_exists(url):
    path = url[len(sqlite_url_prefix):]
    if not os.path.exists(path):
        raise RuntimeError(f"does not exist: {path}")
    if not os.path.isfile(path):
        raise RuntimeError(f"not a file: {path}")


def _enable_sqlite_foreign_key_constraints(dbapi_connection, _):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

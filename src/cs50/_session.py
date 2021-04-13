"""Wraps a SQLAlchemy scoped session"""

import sqlalchemy
import sqlalchemy.orm

from ._session_util import (
    assert_sqlite_file_exists,
    create_session,
    is_sqlite_url,
)


class Session:
    """Wraps a SQLAlchemy scoped session"""

    def __init__(self, url, **engine_kwargs):
        if is_sqlite_url(url):
            assert_sqlite_file_exists(url)

        self._session = create_session(url, **engine_kwargs)

    def execute(self, statement):
        """Converts statement to str and executes it"""
        # pylint: disable=no-member
        return self._session.execute(sqlalchemy.text(str(statement)))

    def __getattr__(self, attr):
        return getattr(self._session, attr)

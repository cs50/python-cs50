"""Wraps SQLAlchemy"""

import logging

import sqlalchemy
import termcolor

from ._session import Session
from ._statement import statement_factory
from ._sql_util import fetch_select_result, raise_errors_for_warnings

_logger = logging.getLogger("cs50")


class SQL:
    """Wraps SQLAlchemy"""

    def __init__(self, url, **engine_kwargs):
        self._session = Session(url, **engine_kwargs)
        dialect = self._session.get_bind().dialect
        self._is_postgres = dialect.name in {"postgres", "postgresql"}
        self._sanitize_statement = statement_factory(dialect)
        self._outside_transaction = True

    def execute(self, sql, *args, **kwargs):
        """Execute a SQL statement."""
        statement = self._sanitize_statement(sql, *args, **kwargs)
        try:
            with raise_errors_for_warnings():
                result = self._session.execute(statement)
        except sqlalchemy.exc.IntegrityError as exc:
            _logger.debug(termcolor.colored(str(statement), "yellow"))
            if self._outside_transaction:
                self._session.remove()
            raise ValueError(exc.orig) from None
        except (sqlalchemy.exc.OperationalError, sqlalchemy.exc.ProgrammingError) as exc:
            self._session.remove()
            _logger.debug(termcolor.colored(statement, "red"))
            raise RuntimeError(exc.orig) from None

        if statement.is_transaction_start():
            self._outside_transaction = False

        _logger.debug(termcolor.colored(str(statement), "green"))

        if statement.is_transaction_end():
            self._outside_transaction = True

        if statement.is_select():
            ret = fetch_select_result(result)
        elif statement.is_insert():
            ret = self._last_row_id_or_none(result)
        elif statement.is_delete() or statement.is_update():
            ret = result.rowcount
        else:
            ret = True

        if self._outside_transaction:
            self._session.remove()

        return ret

    def _last_row_id_or_none(self, result):
        if self._is_postgres:
            return self._get_last_val()
        return result.lastrowid if result.rowcount == 1 else None

    def _get_last_val(self):
        try:
            return self._session.execute("SELECT LASTVAL()").first()[0]
        except sqlalchemy.exc.OperationalError:  # If lastval is not yet defined in this session
            return None

    def init_app(self, app):
        """Registers a teardown_appcontext listener to remove session and enables logging"""
        @app.teardown_appcontext
        def _(_):
            self._session.remove()

        logging.getLogger("cs50").disabled = False

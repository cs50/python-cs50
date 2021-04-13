"""Wraps SQLAlchemy"""

import logging
import warnings

import sqlalchemy
import termcolor

from ._session import Session
from ._statement import Statement
from ._sql_util import fetch_select_result, is_transaction_start, is_transaction_end

_logger = logging.getLogger("cs50")


class SQL:
    """Wraps SQLAlchemy"""

    def __init__(self, url, **engine_kwargs):
        self._session = Session(url, **engine_kwargs)
        self._dialect = self._session.get_bind().dialect
        self._is_postgres = self._dialect.name in {"postgres", "postgresql"}
        self._autocommit = False

    def execute(self, sql, *args, **kwargs):
        """Execute a SQL statement."""
        statement = Statement(self._dialect, sql, *args, **kwargs)
        operation_keyword = statement.get_operation_keyword()
        if is_transaction_start(operation_keyword):
            self._autocommit = False

        if self._autocommit:
            self._session.execute("BEGIN")

        result = self._execute(statement)

        if self._autocommit:
            self._session.execute("COMMIT")

        if is_transaction_end(operation_keyword):
            self._autocommit = True

        if operation_keyword == "SELECT":
            ret = fetch_select_result(result)
        elif operation_keyword == "INSERT":
            ret = self._last_row_id_or_none(result)
        elif operation_keyword in {"DELETE", "UPDATE"}:
            ret = result.rowcount
        else:
            ret = True

        if self._autocommit:
            self._session.remove()

        return ret


    def _execute(self, statement):
        # Catch SQLAlchemy warnings
        with warnings.catch_warnings():
            # Raise exceptions for warnings
            warnings.simplefilter("error")
            try:
                result = self._session.execute(statement)
            except sqlalchemy.exc.IntegrityError as exc:
                _logger.debug(termcolor.colored(str(statement), "yellow"))
                if self._autocommit:
                    self._session.execute("ROLLBACK")
                raise ValueError(exc.orig) from None
            except (sqlalchemy.exc.OperationalError, sqlalchemy.exc.ProgrammingError) as exc:
                self._session.remove()
                _logger.debug(termcolor.colored(statement, "red"))
                raise RuntimeError(exc.orig) from None

            _logger.debug(termcolor.colored(str(statement), "green"))
            return result

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

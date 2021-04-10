"""Wraps SQLAlchemy"""

import decimal
import logging
import warnings

import sqlalchemy
import termcolor

from ._session import Session
from ._statement import Statement

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
        command = statement.get_command()
        if command in {"BEGIN", "START"}:
            self._autocommit = False

        if self._autocommit:
            self._session.execute("BEGIN")

        result = self._execute(statement)

        if self._autocommit:
            self._session.execute("COMMIT")
            self._session.remove()

        if command in {"COMMIT", "ROLLBACK"}:
            self._autocommit = True
            self._session.remove()

        if command == "SELECT":
            ret = _fetch_select_result(result)
        elif command == "INSERT":
            ret = self._last_row_id_or_none(result)
        elif command in {"DELETE", "UPDATE"}:
            ret = result.rowcount
        else:
            ret = True

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


def _fetch_select_result(result):
    rows = [dict(row) for row in result.fetchall()]
    for row in rows:
        for column in row:
            # Coerce decimal.Decimal objects to float objects
            # https://groups.google.com/d/msg/sqlalchemy/0qXMYJvq8SA/oqtvMD9Uw-kJ
            if isinstance(row[column], decimal.Decimal):
                row[column] = float(row[column])

            # Coerce memoryview objects (as from PostgreSQL's bytea columns) to bytes
            elif isinstance(row[column], memoryview):
                row[column] = bytes(row[column])

    return rows

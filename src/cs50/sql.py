import decimal
import logging
import warnings

import sqlalchemy
import termcolor

from ._session import Session
from ._statement import Statement

_logger = logging.getLogger("cs50")


class SQL:
    def __init__(self, url, **engine_kwargs):
        self._session = Session(url, **engine_kwargs)
        self._autocommit = False
        self._test_database()


    def _test_database(self):
        self.execute("SELECT 1")


    def execute(self, sql, *args, **kwargs):
        """Execute a SQL statement."""
        statement = Statement(self._session.get_bind().dialect, sql, *args, **kwargs)
        command = statement.get_command()
        if command in ["BEGIN", "START"]:
            self._autocommit = False

        if self._autocommit:
            self._session.execute("BEGIN")

        result = self._execute(statement)

        if self._autocommit:
            self._session.execute("COMMIT")
            self._session.remove()

        if command in ["COMMIT", "ROLLBACK"]:
            self._autocommit = True
            self._session.remove()

        if command == "SELECT":
            ret = _fetch_select_result(result)
        elif command == "INSERT":
            if self._session.is_postgres():
                ret = self._get_last_val()
            else:
                ret = result.lastrowid if result.rowcount == 1 else None
        elif command in ["DELETE", "UPDATE"]:
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


    def _get_last_val(self):
        try:
            return self._session.execute("SELECT LASTVAL()").first()[0]
        except sqlalchemy.exc.OperationalError:  # If lastval is not yet defined in this session
            return None


    def init_app(self, app):
        @app.teardown_appcontext
        def shutdown_session(res_or_exc):
            self._session.remove()
            return res_or_exc

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

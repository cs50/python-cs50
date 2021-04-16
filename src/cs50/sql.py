import logging

import sqlalchemy

from ._logger import green, red, yellow
from ._engine import Engine
from ._statement import statement_factory
from ._sql_util import postgres_lastval, process_select_result, raise_errors_for_warnings


_logger = logging.getLogger("cs50")


class SQL:
    """An API for executing SQL Statements.
    """

    def __init__(self, url):
        """
        :param url: The database URL
        """

        self._engine = Engine(url)
        self._substitute_markers_with_params = statement_factory(self._engine.dialect)

    def execute(self, sql, *args, **kwargs):
        """Executes a SQL statement.

        :param sql: a SQL statement, possibly with parameters markers
        :type sql: str
        :param *args: zero or more positional arguments to substitute the parameter markers with
        :param **kwargs: zero or more keyword arguments to substitute the parameter markers with

        :returns: For ``SELECT``, a :py:class:`list` of :py:class:`dict` objects, each of which
        represents a row in the result set; for ``INSERT``, the primary key of a newly inserted row
        (or ``None`` if none); for ``UPDATE``, the number of rows updated; for ``DELETE``, the
        number of rows deleted; for other statements, ``True``; on integrity errors, a
        :py:class:`ValueError` is raised, on other errors, a :py:class:`RuntimeError` is raised

        """

        statement = self._substitute_markers_with_params(sql, *args, **kwargs)
        connection = self._engine.get_existing_transaction_connection()
        if connection is None:
            if statement.is_transaction_start():
                connection = self._engine.get_transaction_connection()
            else:
                connection = self._engine.get_connection()
        elif statement.is_transaction_start():
            raise RuntimeError("nested transactions are not supported")

        return self._execute(statement, connection)

    def _execute(self, statement, connection):
        with raise_errors_for_warnings():
            try:
                result = connection.execute(str(statement))
            # E.g., failed constraint
            except sqlalchemy.exc.IntegrityError as exc:
                _logger.debug(yellow(statement))
                if self._engine.get_existing_transaction_connection() is None:
                    connection.close()
                raise ValueError(exc.orig) from None
            # E.g., connection error or syntax error
            except (sqlalchemy.exc.OperationalError, sqlalchemy.exc.ProgrammingError) as exc:
                if self._engine.get_existing_transaction_connection():
                    self._engine.close_transaction_connection()
                else:
                    connection.close()
                _logger.debug(red(statement))
                raise RuntimeError(exc.orig) from None

            _logger.debug(green(statement))

            if statement.is_select():
                ret = process_select_result(result)
            elif statement.is_insert():
                ret = self._last_row_id_or_none(result)
            elif statement.is_delete() or statement.is_update():
                ret = result.rowcount
            else:
                ret = True

        if self._engine.get_existing_transaction_connection():
            if statement.is_transaction_end():
                self._engine.close_transaction_connection()
        else:
            connection.close()

        return ret

    def _last_row_id_or_none(self, result):
        """
        :param result: A SQLAlchemy result object
        :type result: :class:`sqlalchemy.engine.Result`

        :returns: The ID of the last inserted row or ``None``
        """

        if self._engine.is_postgres():
            return postgres_lastval(result.connection)
        return result.lastrowid if result.rowcount == 1 else None

    def init_app(self, app):
        """Enables logging and registers a ``teardown_appcontext`` listener to remove the session.

        :param app: a Flask application instance
        :type app: :class:`flask.Flask`
        """

        @app.teardown_appcontext
        def _(_):
            self._engine.close_transaction_connection()


        logging.getLogger("cs50").disabled = False

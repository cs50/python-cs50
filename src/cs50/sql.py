import logging

import sqlalchemy

from ._logger import green, red, yellow
from ._session import Session
from ._statement import statement_factory
from ._sql_util import process_select_result, raise_errors_for_warnings


_logger = logging.getLogger("cs50")


class SQL:
    """An API for executing SQL Statements.
    """

    def __init__(self, url):
        """
        :param url: The database URL
        """

        self._session = Session(url)
        dialect = self._get_dialect()
        self._is_postgres = dialect.name in {"postgres", "postgresql"}
        self._substitute_markers_with_params = statement_factory(dialect)
        self._autocommit = False

    def _get_dialect(self):
        return self._session.get_bind().dialect

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
        if statement.is_transaction_start():
            self._disable_autocommit()

        self._begin_transaction_in_autocommit_mode()
        result = self._execute(statement)
        self._commit_transaction_in_autocommit_mode()

        if statement.is_select():
            ret = process_select_result(result)
        elif statement.is_insert():
            ret = self._last_row_id_or_none(result)
        elif statement.is_delete() or statement.is_update():
            ret = result.rowcount
        else:
            ret = True

        if statement.is_transaction_end():
            self._enable_autocommit()

        self._shutdown_session_in_autocommit_mode()
        return ret

    def _disable_autocommit(self):
        self._autocommit = False

    def _begin_transaction_in_autocommit_mode(self):
        if self._autocommit:
            self._session.execute("BEGIN")

    def _execute(self, statement):
        """
        :param statement: a SQL statement represented as a ``str`` or a
        :class:`_statement.Statement`

        :rtype: :class:`sqlalchemy.engine.Result`
        """
        try:
            with raise_errors_for_warnings():
                result = self._session.execute(statement)
        # E.g., failed constraint
        except sqlalchemy.exc.IntegrityError as exc:
            _logger.debug(yellow(statement))
            self._shutdown_session_in_autocommit_mode()
            raise ValueError(exc.orig) from None
        # E.g., connection error or syntax error
        except (sqlalchemy.exc.OperationalError, sqlalchemy.exc.ProgrammingError) as exc:
            self._shutdown_session()
            _logger.debug(red(statement))
            raise RuntimeError(exc.orig) from None

        _logger.debug(green(statement))
        return result

    def _shutdown_session_in_autocommit_mode(self):
        if self._autocommit:
            self._shutdown_session()

    def _shutdown_session(self):
        self._session.remove()

    def _commit_transaction_in_autocommit_mode(self):
        if self._autocommit:
            self._session.execute("COMMIT")

    def _enable_autocommit(self):
        self._autocommit = True

    def _last_row_id_or_none(self, result):
        """
        :param result: A SQLAlchemy result object
        :type result: :class:`sqlalchemy.engine.Result`

        :returns: The ID of the last inserted row or ``None``
        """

        if self._is_postgres:
            return self._postgres_lastval()
        return result.lastrowid if result.rowcount == 1 else None

    def _postgres_lastval(self):
        try:
            return self._session.execute("SELECT LASTVAL()").first()[0]
        except sqlalchemy.exc.OperationalError:  # If lastval is not yet defined in this session
            return None

    def init_app(self, app):
        """Enables logging and registers a ``teardown_appcontext`` listener to remove the session.

        :param app: a Flask application instance
        :type app: :class:`flask.Flask`
        """

        @app.teardown_appcontext
        def _(_):
            self._shutdown_session()

        logging.getLogger("cs50").disabled = False

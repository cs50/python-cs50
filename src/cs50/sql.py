import datetime
import decimal
import importlib
import logging
import os
import re
import sqlalchemy
import sqlite3
import sqlparse
import sys
import termcolor
import warnings


class SQL(object):
    """Wrap SQLAlchemy to provide a simple SQL API."""

    def __init__(self, url, **kwargs):
        """
        Create instance of sqlalchemy.engine.Engine.

        URL should be a string that indicates database dialect and connection arguments.

        http://docs.sqlalchemy.org/en/latest/core/engines.html#sqlalchemy.create_engine
        http://docs.sqlalchemy.org/en/latest/dialects/index.html
        """

        # Require that file already exist for SQLite
        matches = re.search(r"^sqlite:///(.+)$", url)
        if matches:
            if not os.path.exists(matches.group(1)):
                raise RuntimeError("does not exist: {}".format(matches.group(1)))
            if not os.path.isfile(matches.group(1)):
                raise RuntimeError("not a file: {}".format(matches.group(1)))

            # Remember foreign_keys and remove it from kwargs
            foreign_keys = kwargs.pop("foreign_keys", False)

            # Create engine, raising exception if back end's module not installed
            self.engine = sqlalchemy.create_engine(url, **kwargs)

            # Enable foreign key constraints
            if foreign_keys:
                sqlalchemy.event.listen(self.engine, "connect", _connect)

        else:

            # Create engine, raising exception if back end's module not installed
            self.engine = sqlalchemy.create_engine(url, **kwargs)


        # Log statements to standard error
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger("cs50")
        disabled = self.logger.disabled

        # Test database
        try:
            self.logger.disabled = True
            self.execute("SELECT 1")
        except sqlalchemy.exc.OperationalError as e:
            e = RuntimeError(self._parse(e))
            e.__cause__ = None
            raise e
        else:
            self.logger.disabled = disabled

    def _parse(self, e):
        """Parses an exception, returns its message."""

        # MySQL
        matches = re.search(r"^\(_mysql_exceptions\.OperationalError\) \(\d+, \"(.+)\"\)$", str(e))
        if matches:
            return matches.group(1)

        # PostgreSQL
        matches = re.search(r"^\(psycopg2\.OperationalError\) (.+)$", str(e))
        if matches:
            return matches.group(1)

        # SQLite
        matches = re.search(r"^\(sqlite3\.OperationalError\) (.+)$", str(e))
        if matches:
            return matches.group(1)

        # Default
        return str(e)

    def execute(self, text, **params):
        """
        Execute a SQL statement.
        """
        class UserDefinedType(sqlalchemy.TypeDecorator):
            """
            Add support for expandable values, a la https://bitbucket.org/zzzeek/sqlalchemy/issues/3953/expanding-parameter.
            """

            impl = sqlalchemy.types.UserDefinedType

            def process_literal_param(self, value, dialect):
                """Receive a literal parameter value to be rendered inline within a statement."""
                def process(value):
                    """Render a literal value, escaping as needed."""

                    # bool
                    if isinstance(value, bool):
                        return sqlalchemy.types.Boolean().literal_processor(dialect)(value)

                    # datetime.date
                    elif isinstance(value, datetime.date):
                        return sqlalchemy.types.String().literal_processor(dialect)(value.strftime("%Y-%m-%d"))

                    # datetime.datetime
                    elif isinstance(value, datetime.datetime):
                        return sqlalchemy.types.String().literal_processor(dialect)(value.strftime("%Y-%m-%d %H:%M:%S"))

                    # datetime.time
                    elif isinstance(value, datetime.time):
                        return sqlalchemy.types.String().literal_processor(dialect)(value.strftime("%H:%M:%S"))

                    # float
                    elif isinstance(value, float):
                        return sqlalchemy.types.Float().literal_processor(dialect)(value)

                    # int
                    elif isinstance(value, int):
                        return sqlalchemy.types.Integer().literal_processor(dialect)(value)

                    # long
                    elif sys.version_info.major != 3 and isinstance(value, long):
                        return sqlalchemy.types.Integer().literal_processor(dialect)(value)

                    # str
                    elif isinstance(value, str):
                        return sqlalchemy.types.String().literal_processor(dialect)(value)

                    # None
                    elif isinstance(value, sqlalchemy.sql.elements.Null):
                        return sqlalchemy.types.NullType().literal_processor(dialect)(value)

                    # Unsupported value
                    raise RuntimeError("unsupported value")

                # Process value(s), separating with commas as needed
                if type(value) is list:
                    return ", ".join([process(v) for v in value])
                else:
                    return process(value)

        # Allow only one statement at a time
        # SQLite does not support executing many statements
        # https://docs.python.org/3/library/sqlite3.html#sqlite3.Cursor.execute
        if len(sqlparse.split(text)) > 1:
            raise RuntimeError("too many statements at once")

        # Raise exceptions for warnings
        warnings.filterwarnings("error")

        # Prepare, execute statement
        try:

            # Construct a new TextClause clause
            statement = sqlalchemy.text(text)

            # Iterate over parameters
            for key, value in params.items():

                # Translate None to NULL
                if value is None:
                    value = sqlalchemy.sql.null()

                # Bind parameters before statement reaches database, so that bound parameters appear in exceptions
                # http://docs.sqlalchemy.org/en/latest/core/sqlelement.html#sqlalchemy.sql.expression.text
                statement = statement.bindparams(sqlalchemy.bindparam(
                    key, value=value, type_=UserDefinedType()))

            # Stringify bound parameters
            # http://docs.sqlalchemy.org/en/latest/faq/sqlexpressions.html#how-do-i-render-sql-expressions-as-strings-possibly-with-bound-parameters-inlined
            statement = str(statement.compile(compile_kwargs={"literal_binds": True}))

            # Statement for logging
            log = re.sub(r"\n\s*", " ", sqlparse.format(statement, reindent=True))

            # Execute statement
            result = self.engine.execute(statement)

            # If SELECT (or INSERT with RETURNING), return result set as list of dict objects
            if re.search(r"^\s*SELECT", statement, re.I):

                # Coerce any decimal.Decimal objects to float objects
                # https://groups.google.com/d/msg/sqlalchemy/0qXMYJvq8SA/oqtvMD9Uw-kJ
                rows = [dict(row) for row in result.fetchall()]
                for row in rows:
                    for column in row:
                        if isinstance(row[column], decimal.Decimal):
                            row[column] = float(row[column])
                ret = rows

            # If INSERT, return primary key value for a newly inserted row
            elif re.search(r"^\s*INSERT", statement, re.I):
                if self.engine.url.get_backend_name() in ["postgres", "postgresql"]:
                    result = self.engine.execute(sqlalchemy.text("SELECT LASTVAL()"))
                    ret = result.first()[0]
                else:
                    ret = result.lastrowid

            # If DELETE or UPDATE, return number of rows matched
            elif re.search(r"^\s*(?:DELETE|UPDATE)", statement, re.I):
                ret = result.rowcount

            # If some other statement, return True unless exception
            else:
                ret = True

        # If constraint violated, return None
        except sqlalchemy.exc.IntegrityError:
            self.logger.debug(termcolor.colored(log, "yellow"))
            return None

        # If user errror
        except sqlalchemy.exc.OperationalError as e:
            self.logger.debug(termcolor.colored(log, "red"))
            e = RuntimeError(self._parse(e))
            e.__cause__ = None
            raise e

        # Return value
        else:
            self.logger.debug(termcolor.colored(log, "green"))
            return ret


# http://docs.sqlalchemy.org/en/latest/dialects/sqlite.html#foreign-key-support
def _connect(dbapi_connection, connection_record):
    """Enables foreign key support."""

    # Ensure backend is sqlite
    if type(dbapi_connection) is sqlite3.Connection:
        cursor = dbapi_connection.cursor()

        # Respect foreign key constraints by default
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

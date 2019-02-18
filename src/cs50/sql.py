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

        # Get logger
        self._logger = logging.getLogger("cs50")

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
                def connect(dbapi_connection, connection_record):
                    if type(dbapi_connection) is sqlite3.Connection:  # If back end is sqlite
                        cursor = dbapi_connection.cursor()
                        cursor.execute("PRAGMA foreign_keys=ON")
                        cursor.close()
                sqlalchemy.event.listen(self.engine, "connect", connect)

        else:

            # Create engine, raising exception if back end's module not installed
            self.engine = sqlalchemy.create_engine(url, **kwargs)

        # Log statements to standard error
        logging.basicConfig(level=logging.DEBUG)

        def parse(self, e):
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

        # Test database
        try:
            disabled = self._logger.disabled
            self._logger.disabled = True
            self.execute("SELECT 1")
        except sqlalchemy.exc.OperationalError as e:
            e = RuntimeError(parse(e))
            e.__cause__ = None
            raise e
        else:
            self._logger.disabled = disabled

    def execute(self, sql, *args, **kwargs):
        """Execute a SQL statement."""

        # Allow only one statement at a time, since SQLite doesn't support multiple
        # https://docs.python.org/3/library/sqlite3.html#sqlite3.Cursor.execute
        statements = sqlparse.parse(sql)
        if len(statements) > 1:
            raise RuntimeError("too many statements at once")
        elif len(statements) == 0:
            raise RuntimeError("missing statement")

        # Ensure named and positional parameters are mutually exclusive
        if len(args) > 0 and len(kwargs) > 0:
            raise RuntimeError("cannot pass both named and positional parameters")

        # In case user passes args in list or tuple
        if len(args) == 1 and (isinstance(args[0], list) or isinstance(args[0], tuple)):
            args = args[0]

        # In case user passes kwargs in dict
        if len(args) == 1 and len(kwargs) == 0 and isinstance(args[0], dict):
            kwargs = args[0]

        # Flatten statement
        tokens = list(statements[0].flatten())

        # Validate paramstyle
        placeholders = {}
        paramstyle = None
        for index, token in enumerate(tokens):

            # If token is a placeholder
            if token.ttype == sqlparse.tokens.Name.Placeholder:

                # Determine paramstyle
                if token.value == "?":
                    _paramstyle = "qmark"
                elif re.search(r"^:[1-9]\d*$", token.value):
                    _paramstyle = "numeric"
                elif re.search(r"^:[a-zA-Z]\w*$", token.value):
                    _paramstyle = "named"
                elif re.search(r"^TODO$", token.value):  # TODO
                    _paramstyle = "named"
                elif re.search(r"%\([a-zA-Z]\w*\)s$", token.value):  # TODO
                    _paramstyle = "pyformat"
                else:
                    raise RuntimeError("{}: invalid placeholder".format(token.value))

                # Ensure paramstyle is consistent
                if paramstyle is not None and _paramstyle != paramstyle:
                    raise RuntimeError("inconsistent paramstyle")

                # Remember paramstyle
                if paramstyle is None:
                    paramstyle = _paramstyle

                # Remember placeholder
                placeholders[index] = token.value

        def escape(value):

            # bool
            if type(value) is bool:
                return sqlparse.sql.Token(
                    sqlparse.tokens.Number,
                    sqlalchemy.types.Boolean().literal_processor(self.engine.dialect)(value))

            # datetime.date
            elif type(value) is datetime.date:
                return sqlparse.sql.Token(
                    sqlparse.tokens.String,
                    sqlalchemy.types.String().literal_processor(self.engine.dialect)(value.strftime("%Y-%m-%d")))

            # datetime.datetime
            elif type(value) is datetime.datetime:
                return sqlparse.sql.Token(
                    sqlparse.tokens.String,
                    sqlalchemy.types.String().literal_processor(self.engine.dialect)(value.strftime("%Y-%m-%d %H:%M:%S")))

            # datetime.time
            elif type(value) is datetime.time:
                return sqlparse.sql.Token(
                    sqlparse.tokens.String,
                    sqlalchemy.types.String().literal_processor(self.engine.dialect)(value.strftime("%H:%M:%S")))

            # float
            elif type(value) is float:
                return sqlparse.sql.Token(
                    sqlparse.tokens.Number,
                    sqlalchemy.types.Float().literal_processor(self.engine.dialect)(value))

            # int
            elif type(value) is int:
                return sqlparse.sql.Token(
                    sqlparse.tokens.Number,
                    sqlalchemy.types.Integer().literal_processor(self.engine.dialect)(value))

            # str
            elif type(value) is str:
                return sqlparse.sql.Token(
                    sqlparse.tokens.String,
                    sqlalchemy.types.String().literal_processor(self.engine.dialect)(value))

            # None
            elif value is None:
                return sqlparse.sql.Token(
                    sqlparse.tokens.Keyword,
                    sqlalchemy.types.NullType().literal_processor(self.engine.dialect)(value))

            # Unsupported value
            raise RuntimeError("unsupported value: {}".format(value))

        # qmark
        if paramstyle == "qmark":

            # Validate number of placeholders
            if len(placeholders) < len(args):
                raise RuntimeError("too few placeholders")
            elif len(placeholders) > len(args):
                raise RuntimeError("too many placeholders")

            # Escape values
            for i, index in enumerate(placeholders.keys()):
                tokens[index] = escape(args[i])

        # numeric
        elif paramstyle == "numeric":

            # Escape values
            for index, value in placeholders.items():
                i = int(re.sub(r"^:", "", value)) - 1
                if i >= len(args):
                    raise RuntimeError("placeholder out of range")
                tokens[index] = escape(args[i])

        # named
        elif paramstyle == "named":

            # Escape values
            for index, value in placeholders.items():
                name = re.sub(r"^:", "", value)
                if name not in kwargs:
                    raise RuntimeError("missing value for placeholder")
                tokens[index] = escape(kwargs[name])

        # Join tokens into statement
        statement = "".join([str(token) for token in tokens])

        # Raise exceptions for warnings
        warnings.filterwarnings("error")

        # Prepare, execute statement
        try:

            # Execute statement
            result = self.engine.execute(statement)

            # If SELECT (or INSERT with RETURNING), return result set as list of dict objects
            if re.search(r"^\s*SELECT", statement, re.I):

                # Coerce any decimal.Decimal objects to float objects
                # https://groups.google.com/d/msg/sqlalchemy/0qXMYJvq8SA/oqtvMD9Uw-kJ
                rows = [dict(row) for row in result.fetchall()]
                for row in rows:
                    for column in row:
                        if type(row[column]) is decimal.Decimal:
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
            self._logger.debug(termcolor.colored(statement, "yellow"))
            return None

        # If user errror
        except sqlalchemy.exc.OperationalError as e:
            self._logger.debug(termcolor.colored(statement, "red"))
            e = RuntimeError(self._parse(e))
            e.__cause__ = None
            raise e

        # Return value
        else:
            self._logger.debug(termcolor.colored(statement, "green"))
            return ret

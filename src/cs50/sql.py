def _enable_logging(f):
    """Enable logging of SQL statements when Flask is in use."""

    import logging
    import functools

    @functools.wraps(f)
    def decorator(*args, **kwargs):

        # Infer whether Flask is installed
        try:
            import flask
        except ModuleNotFoundError:
            return f(*args, **kwargs)

        # Enable logging
        disabled = logging.getLogger("cs50").disabled
        if flask.current_app:
            logging.getLogger("cs50").disabled = False
        try:
            return f(*args, **kwargs)
        finally:
            logging.getLogger("cs50").disabled = disabled

    return decorator


class SQL(object):
    """Wrap SQLAlchemy to provide a simple SQL API."""

    def __init__(self, url, **kwargs):
        """
        Create instance of sqlalchemy.engine.Engine.

        URL should be a string that indicates database dialect and connection arguments.

        http://docs.sqlalchemy.org/en/latest/core/engines.html#sqlalchemy.create_engine
        http://docs.sqlalchemy.org/en/latest/dialects/index.html
        """

        # Lazily import
        import logging
        import os
        import re
        import sqlalchemy
        import sqlite3

        # Get logger
        self._logger = logging.getLogger("cs50")

        # Require that file already exist for SQLite
        matches = re.search(r"^sqlite:///(.+)$", url)
        if matches:
            if not os.path.exists(matches.group(1)):
                raise RuntimeError("does not exist: {}".format(matches.group(1)))
            if not os.path.isfile(matches.group(1)):
                raise RuntimeError("not a file: {}".format(matches.group(1)))

        # Create engine, disabling SQLAlchemy's own autocommit mode, raising exception if back end's module not installed
        self._engine = sqlalchemy.create_engine(url, **kwargs).execution_options(autocommit=False)

        # Listener for connections
        def connect(dbapi_connection, connection_record):

            # Disable underlying API's own emitting of BEGIN and COMMIT
            dbapi_connection.isolation_level = None

            # Enable foreign key constraints
            if type(dbapi_connection) is sqlite3.Connection:  # If back end is sqlite
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

        # Register listener
        sqlalchemy.event.listen(self._engine, "connect", connect)

        # Log statements to standard error
        logging.basicConfig(level=logging.DEBUG)

        # Test database
        try:
            disabled = self._logger.disabled
            self._logger.disabled = True
            self.execute("SELECT 1")
        except sqlalchemy.exc.OperationalError as e:
            e = RuntimeError(_parse_exception(e))
            e.__cause__ = None
            raise e
        finally:
            self._logger.disabled = disabled

    def __del__(self):
        """Close database connection."""
        if hasattr(self, "_connection"):
            self._connection.close()

    @_enable_logging
    def execute(self, sql, *args, **kwargs):
        """Execute a SQL statement."""

        # Lazily import
        import decimal
        import re
        import sqlalchemy
        import sqlparse
        import termcolor
        import warnings

        # Parse statement, stripping comments and then leading/trailing whitespace
        statements = sqlparse.parse(sqlparse.format(sql, strip_comments=True).strip())

        # Allow only one statement at a time, since SQLite doesn't support multiple
        # https://docs.python.org/3/library/sqlite3.html#sqlite3.Cursor.execute
        if len(statements) > 1:
            raise RuntimeError("too many statements at once")
        elif len(statements) == 0:
            raise RuntimeError("missing statement")

        # Ensure named and positional parameters are mutually exclusive
        if len(args) > 0 and len(kwargs) > 0:
            raise RuntimeError("cannot pass both named and positional parameters")

        # Infer command from (unflattened) statement
        for token in statements[0]:
            if token.ttype in [sqlparse.tokens.Keyword.DDL, sqlparse.tokens.Keyword.DML]:
                command = token.value.upper()
                break
        else:
            command = None

        # Flatten statement
        tokens = list(statements[0].flatten())

        # Validate paramstyle
        placeholders = {}
        paramstyle = None
        for index, token in enumerate(tokens):

            # If token is a placeholder
            if token.ttype == sqlparse.tokens.Name.Placeholder:

                # Determine paramstyle, name
                _paramstyle, name = _parse_placeholder(token)

                # Remember paramstyle
                if not paramstyle:
                    paramstyle = _paramstyle

                # Ensure paramstyle is consistent
                elif _paramstyle != paramstyle:
                    raise RuntimeError("inconsistent paramstyle")

                # Remember placeholder's index, name
                placeholders[index] = name

        # If more placeholders than arguments
        if len(args) == 1 and len(placeholders) > 1:

            # If user passed args as list or tuple, explode values into args
            if isinstance(args[0], (list, tuple)):
                args = args[0]

            # If user passed kwargs as dict, migrate values from args to kwargs
            elif len(kwargs) == 0 and isinstance(args[0], dict):
                kwargs = args[0]
                args = []

        # If no placeholders
        if not paramstyle:

            # Error-check like qmark if args
            if args:
                paramstyle = "qmark"

            # Error-check like named if kwargs
            elif kwargs:
                paramstyle = "named"

        # In case of errors
        _placeholders = ", ".join([str(tokens[index]) for index in placeholders])
        _args = ", ".join([str(self._escape(arg)) for arg in args])

        # qmark
        if paramstyle == "qmark":

            # Validate number of placeholders
            if len(placeholders) != len(args):
                if len(placeholders) < len(args):
                    raise RuntimeError("fewer placeholders ({}) than values ({})".format(_placeholders, _args))
                else:
                    raise RuntimeError("more placeholders ({}) than values ({})".format(_placeholders, _args))

            # Escape values
            for i, index in enumerate(placeholders.keys()):
                tokens[index] = self._escape(args[i])

        # numeric
        elif paramstyle == "numeric":

            # Escape values
            for index, i in placeholders.items():
                if i >= len(args):
                    raise RuntimeError("missing value for placeholder (:{})".format(i + 1, len(args)))
                tokens[index] = self._escape(args[i])

            # Check if any values unused
            indices = set(range(len(args))) - set(placeholders.values())
            if indices:
                raise RuntimeError("unused {} ({})".format(
                    "value" if len(indices) == 1 else "values",
                    ", ".join([str(self._escape(args[index])) for index in indices])))

        # named
        elif paramstyle == "named":

            # Escape values
            for index, name in placeholders.items():
                if name not in kwargs:
                    raise RuntimeError("missing value for placeholder (:{})".format(name))
                tokens[index] = self._escape(kwargs[name])

            # Check if any keys unused
            keys = kwargs.keys() - placeholders.values()
            if keys:
                raise RuntimeError("unused values ({})".format(", ".join(keys)))

        # format
        elif paramstyle == "format":

            # Validate number of placeholders
            if len(placeholders) != len(args):
                if len(placeholders) < len(args):
                    raise RuntimeError("fewer placeholders ({}) than values ({})".format(_placeholders, _args))
                else:
                    raise RuntimeError("more placeholders ({}) than values ({})".format(_placeholders, _args))

            # Escape values
            for i, index in enumerate(placeholders.keys()):
                tokens[index] = self._escape(args[i])

        # pyformat
        elif paramstyle == "pyformat":

            # Escape values
            for index, name in placeholders.items():
                if name not in kwargs:
                    raise RuntimeError("missing value for placeholder (%{}s)".format(name))
                tokens[index] = self._escape(kwargs[name])

            # Check if any keys unused
            keys = kwargs.keys() - placeholders.values()
            if keys:
                raise RuntimeError("unused {} ({})".format(
                    "value" if len(keys) == 1 else "values",
                    ", ".join(keys)))

        # For SQL statements where a colon is required verbatim, as within an inline string, use a backslash to escape
        # https://docs.sqlalchemy.org/en/13/core/sqlelement.html?highlight=text#sqlalchemy.sql.expression.text
        for index, token in enumerate(tokens):

            # In string literal
            # https://www.sqlite.org/lang_keywords.html
            if token.ttype in [sqlparse.tokens.Literal.String, sqlparse.tokens.Literal.String.Single]:
                token.value = re.sub("(^'|\s+):", r"\1\:", token.value)

            # In identifier
            # https://www.sqlite.org/lang_keywords.html
            elif token.ttype == sqlparse.tokens.Literal.String.Symbol:
                token.value = re.sub("(^\"|\s+):", r"\1\:", token.value)

        # Join tokens into statement
        statement = "".join([str(token) for token in tokens])

        # Connect to database (for transactions' sake)
        try:

            # Infer whether Flask is installed
            import flask

            # Infer whether app is defined
            assert flask.current_app

            # If no connection for app's current request yet
            if not hasattr(flask.g, "_connection"):

                # Connect now
                flask.g._connection = self._engine.connect()

                # Disconnect later
                @flask.current_app.teardown_appcontext
                def shutdown_session(exception=None):
                    if hasattr(flask.g, "_connection"):
                        flask.g._connection.close()

            # Use this connection
            connection = flask.g._connection

        except (ModuleNotFoundError, AssertionError):

            # If no connection yet
            if not hasattr(self, "_connection"):
                self._connection = self._engine.connect()

            # Use this connection
            connection = self._connection

        # Catch SQLAlchemy warnings
        with warnings.catch_warnings():

            # Raise exceptions for warnings
            warnings.simplefilter("error")

            # Prepare, execute statement
            try:

                # Join tokens into statement, abbreviating binary data as <class 'bytes'>
                _statement = "".join([str(bytes) if token.ttype == sqlparse.tokens.Other else str(token) for token in tokens])

                # Execute statement
                result = connection.execute(sqlalchemy.text(statement))

                # Return value
                ret = True

                # If SELECT, return result set as list of dict objects
                if command == "SELECT":

                    # Coerce types
                    rows = [dict(row) for row in result.fetchall()]
                    for row in rows:
                        for column in row:

                            # Coerce decimal.Decimal objects to float objects
                            # https://groups.google.com/d/msg/sqlalchemy/0qXMYJvq8SA/oqtvMD9Uw-kJ
                            if type(row[column]) is decimal.Decimal:
                                row[column] = float(row[column])

                            # Coerce memoryview objects (as from PostgreSQL's bytea columns) to bytes
                            elif type(row[column]) is memoryview:
                                row[column] = bytes(row[column])

                    # Rows to be returned
                    ret = rows

                # If INSERT, return primary key value for a newly inserted row (or None if none)
                elif command == "INSERT":
                    if self._engine.url.get_backend_name() in ["postgres", "postgresql"]:
                        try:
                            result = connection.execute("SELECT LASTVAL()")
                            ret = result.first()[0]
                        except sqlalchemy.exc.OperationalError:  # If lastval is not yet defined in this session
                            ret = None
                    else:
                        ret = result.lastrowid if result.rowcount == 1 else None

                # If DELETE or UPDATE, return number of rows matched
                elif command in ["DELETE", "UPDATE"]:
                    ret = result.rowcount

            # If constraint violated, return None
            except sqlalchemy.exc.IntegrityError as e:
                self._logger.debug(termcolor.colored(statement, "yellow"))
                e = RuntimeError(e.orig)
                e.__cause__ = None
                raise e

            # If user errror
            except sqlalchemy.exc.OperationalError as e:
                self._logger.debug(termcolor.colored(statement, "red"))
                e = RuntimeError(e.orig)
                e.__cause__ = None
                raise e

            # Return value
            else:
                self._logger.debug(termcolor.colored(_statement, "green"))
                return ret

    def _escape(self, value):
        """
        Escapes value using engine's conversion function.

        https://docs.sqlalchemy.org/en/latest/core/type_api.html#sqlalchemy.types.TypeEngine.literal_processor
        """

        # Lazily import
        import sqlparse

        def __escape(value):

            # Lazily import
            import datetime
            import sqlalchemy

            # bool
            if type(value) is bool:
                return sqlparse.sql.Token(
                    sqlparse.tokens.Number,
                    sqlalchemy.types.Boolean().literal_processor(self._engine.dialect)(value))

            # bytes
            elif type(value) is bytes:
                if self._engine.url.get_backend_name() in ["mysql", "sqlite"]:
                    return sqlparse.sql.Token(sqlparse.tokens.Other, f"x'{value.hex()}'")  # https://dev.mysql.com/doc/refman/8.0/en/hexadecimal-literals.html
                elif self._engine.url.get_backend_name() == "postgresql":
                    return sqlparse.sql.Token(sqlparse.tokens.Other, f"'\\x{value.hex()}'")  # https://dba.stackexchange.com/a/203359
                else:
                    raise RuntimeError("unsupported value: {}".format(value))

            # datetime.date
            elif type(value) is datetime.date:
                return sqlparse.sql.Token(
                    sqlparse.tokens.String,
                    sqlalchemy.types.String().literal_processor(self._engine.dialect)(value.strftime("%Y-%m-%d")))

            # datetime.datetime
            elif type(value) is datetime.datetime:
                return sqlparse.sql.Token(
                    sqlparse.tokens.String,
                    sqlalchemy.types.String().literal_processor(self._engine.dialect)(value.strftime("%Y-%m-%d %H:%M:%S")))

            # datetime.time
            elif type(value) is datetime.time:
                return sqlparse.sql.Token(
                    sqlparse.tokens.String,
                    sqlalchemy.types.String().literal_processor(self._engine.dialect)(value.strftime("%H:%M:%S")))

            # float
            elif type(value) is float:
                return sqlparse.sql.Token(
                    sqlparse.tokens.Number,
                    sqlalchemy.types.Float().literal_processor(self._engine.dialect)(value))

            # int
            elif type(value) is int:
                return sqlparse.sql.Token(
                    sqlparse.tokens.Number,
                    sqlalchemy.types.Integer().literal_processor(self._engine.dialect)(value))

            # str
            elif type(value) is str:
                return sqlparse.sql.Token(
                    sqlparse.tokens.String,
                    sqlalchemy.types.String().literal_processor(self._engine.dialect)(value))

            # None
            elif value is None:
                return sqlparse.sql.Token(
                    sqlparse.tokens.Keyword,
                    sqlalchemy.types.NullType().literal_processor(self._engine.dialect)(value))

            # Unsupported value
            else:
                raise RuntimeError("unsupported value: {}".format(value))

        # Escape value(s), separating with commas as needed
        if type(value) in [list, tuple]:
            return sqlparse.sql.TokenList([__escape(v) for v in value])
        else:
            return __escape(value)


def _parse_exception(e):
    """Parses an exception, returns its message."""

    # Lazily import
    import re

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


def _parse_placeholder(token):
    """Infers paramstyle, name from sqlparse.tokens.Name.Placeholder."""

    # Lazily load
    import re
    import sqlparse

    # Validate token
    if not isinstance(token, sqlparse.sql.Token) or token.ttype != sqlparse.tokens.Name.Placeholder:
        raise TypeError()

    # qmark
    if token.value == "?":
        return "qmark", None

    # numeric
    matches = re.search(r"^:([1-9]\d*)$", token.value)
    if matches:
        return "numeric", int(matches.group(1)) - 1

    # named
    matches = re.search(r"^:([a-zA-Z]\w*)$", token.value)
    if matches:
        return "named", matches.group(1)

    # format
    if token.value == "%s":
        return "format", None

    # pyformat
    matches = re.search(r"%\((\w+)\)s$", token.value)
    if matches:
        return "pyformat", matches.group(1)

    # Invalid
    raise RuntimeError("{}: invalid placeholder".format(token.value))

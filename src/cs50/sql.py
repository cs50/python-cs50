import sys
import threading

# Thread-local data
_data = threading.local()


def _enable_logging(f):
    """Enable logging of SQL statements when Flask is in use."""

    import logging
    import functools
    import os

    @functools.wraps(f)
    def decorator(*args, **kwargs):
        # Infer whether Flask is installed
        try:
            import flask
        except ModuleNotFoundError:
            return f(*args, **kwargs)

        # Enable logging in development mode
        disabled = logging.getLogger("cs50").disabled
        if flask.current_app and os.getenv("FLASK_ENV") == "development":
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
        import sqlalchemy.orm
        import threading

        # Temporary fix for missing sqlite3 module on the buildpack stack
        try:
            import sqlite3
        except:
            pass

        # Require that file already exist for SQLite
        matches = re.search(r"^sqlite:///(.+)$", url)
        if matches:
            if not os.path.exists(matches.group(1)):
                raise RuntimeError("does not exist: {}".format(matches.group(1)))
            if not os.path.isfile(matches.group(1)):
                raise RuntimeError("not a file: {}".format(matches.group(1)))

        # Create engine, disabling SQLAlchemy's own autocommit mode raising exception if back end's module not installed;
        # without isolation_level, PostgreSQL warns with "there is already a transaction in progress" for our own BEGIN and
        # "there is no transaction in progress" for our own COMMIT
        self._engine = sqlalchemy.create_engine(url, **kwargs).execution_options(
            autocommit=False, isolation_level="AUTOCOMMIT", no_parameters=True
        )

        # Avoid doubly escaping percent signs, since no_parameters=True anyway
        # https://github.com/cs50/python-cs50/issues/171
        self._engine.dialect.identifier_preparer._double_percents = False

        # Get logger
        self._logger = logging.getLogger("cs50")

        # Listener for connections
        def connect(dbapi_connection, connection_record):
            # Enable foreign key constraints
            try:
                if isinstance(
                    dbapi_connection, sqlite3.Connection
                ):  # If back end is sqlite
                    cursor = dbapi_connection.cursor()
                    cursor.execute("PRAGMA foreign_keys=ON")
                    cursor.close()
            except:
                # Temporary fix for missing sqlite3 module on the buildpack stack
                pass

        # Register listener
        sqlalchemy.event.listen(self._engine, "connect", connect)

        # Autocommit by default
        self._autocommit = True

        # Test database
        disabled = self._logger.disabled
        self._logger.disabled = True
        try:
            connection = self._engine.connect()
            connection.execute(sqlalchemy.text("SELECT 1"))
            connection.close()
        except sqlalchemy.exc.OperationalError as e:
            e = RuntimeError(_parse_exception(e))
            e.__cause__ = None
            raise e
        finally:
            self._logger.disabled = disabled

    def __del__(self):
        """Disconnect from database."""
        self._disconnect()

    def _disconnect(self):
        """Close database connection."""
        if hasattr(_data, self._name()):
            getattr(_data, self._name()).close()
            delattr(_data, self._name())

    def _name(self):
        """Return object's hash as a str."""
        return str(hash(self))

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
            raise RuntimeError("cannot pass both positional and named parameters")

        # Infer command from flattened statement to a single string separated by spaces
        full_statement = " ".join(
            str(token)
            for token in statements[0].tokens
            if token.ttype
            in [
                sqlparse.tokens.Keyword,
                sqlparse.tokens.Keyword.DDL,
                sqlparse.tokens.Keyword.DML,
            ]
        )
        full_statement = full_statement.upper()

        # Set of possible commands
        commands = {
            "BEGIN",
            "CREATE VIEW",
            "DELETE",
            "INSERT",
            "SELECT",
            "START",
            "UPDATE",
        }

        # Check if the full_statement starts with any command
        command = next(
            (cmd for cmd in commands if full_statement.startswith(cmd)), None
        )

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
                    raise RuntimeError(
                        "fewer placeholders ({}) than values ({})".format(
                            _placeholders, _args
                        )
                    )
                else:
                    raise RuntimeError(
                        "more placeholders ({}) than values ({})".format(
                            _placeholders, _args
                        )
                    )

            # Escape values
            for i, index in enumerate(placeholders.keys()):
                tokens[index] = self._escape(args[i])

        # numeric
        elif paramstyle == "numeric":
            # Escape values
            for index, i in placeholders.items():
                if i >= len(args):
                    raise RuntimeError(
                        "missing value for placeholder (:{})".format(i + 1, len(args))
                    )
                tokens[index] = self._escape(args[i])

            # Check if any values unused
            indices = set(range(len(args))) - set(placeholders.values())
            if indices:
                raise RuntimeError(
                    "unused {} ({})".format(
                        "value" if len(indices) == 1 else "values",
                        ", ".join(
                            [str(self._escape(args[index])) for index in indices]
                        ),
                    )
                )

        # named
        elif paramstyle == "named":
            # Escape values
            for index, name in placeholders.items():
                if name not in kwargs:
                    raise RuntimeError(
                        "missing value for placeholder (:{})".format(name)
                    )
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
                    raise RuntimeError(
                        "fewer placeholders ({}) than values ({})".format(
                            _placeholders, _args
                        )
                    )
                else:
                    raise RuntimeError(
                        "more placeholders ({}) than values ({})".format(
                            _placeholders, _args
                        )
                    )

            # Escape values
            for i, index in enumerate(placeholders.keys()):
                tokens[index] = self._escape(args[i])

        # pyformat
        elif paramstyle == "pyformat":
            # Escape values
            for index, name in placeholders.items():
                if name not in kwargs:
                    raise RuntimeError(
                        "missing value for placeholder (%{}s)".format(name)
                    )
                tokens[index] = self._escape(kwargs[name])

            # Check if any keys unused
            keys = kwargs.keys() - placeholders.values()
            if keys:
                raise RuntimeError(
                    "unused {} ({})".format(
                        "value" if len(keys) == 1 else "values", ", ".join(keys)
                    )
                )

        # For SQL statements where a colon is required verbatim, as within an inline string, use a backslash to escape
        # https://docs.sqlalchemy.org/en/13/core/sqlelement.html?highlight=text#sqlalchemy.sql.expression.text
        for index, token in enumerate(tokens):
            # In string literal
            # https://www.sqlite.org/lang_keywords.html
            if token.ttype in [
                sqlparse.tokens.Literal.String,
                sqlparse.tokens.Literal.String.Single,
            ]:
                token.value = re.sub("(^'|\s+):", r"\1\:", token.value)

            # In identifier
            # https://www.sqlite.org/lang_keywords.html
            elif token.ttype == sqlparse.tokens.Literal.String.Symbol:
                token.value = re.sub('(^"|\s+):', r"\1\:", token.value)

        # Join tokens into statement
        statement = "".join([str(token) for token in tokens])

        # If no connection yet
        if not hasattr(_data, self._name()):
            # Connect to database
            setattr(_data, self._name(), self._engine.connect())

        # Use this connection
        connection = getattr(_data, self._name())

        # Disconnect if/when a Flask app is torn down
        try:
            import flask

            assert flask.current_app

            def teardown_appcontext(exception):
                self._disconnect()

            if teardown_appcontext not in flask.current_app.teardown_appcontext_funcs:
                flask.current_app.teardown_appcontext(teardown_appcontext)
        except (ModuleNotFoundError, AssertionError):
            pass

        # Catch SQLAlchemy warnings
        with warnings.catch_warnings():
            # Raise exceptions for warnings
            warnings.simplefilter("error")

            # Prepare, execute statement
            try:
                # Join tokens into statement, abbreviating binary data as <class 'bytes'>
                _statement = "".join(
                    [
                        str(bytes)
                        if token.ttype == sqlparse.tokens.Other
                        else str(token)
                        for token in tokens
                    ]
                )

                # Check for start of transaction
                if command in ["BEGIN", "START"]:
                    self._autocommit = False

                # Execute statement
                if self._autocommit:
                    connection.execute(sqlalchemy.text("BEGIN"))
                result = connection.execute(sqlalchemy.text(statement))
                if self._autocommit:
                    connection.execute(sqlalchemy.text("COMMIT"))

                # Check for end of transaction
                if command in ["COMMIT", "ROLLBACK"]:
                    self._autocommit = True

                # Return value
                ret = True

                # If SELECT, return result set as list of dict objects
                if command == "SELECT":
                    # Coerce types
                    rows = [dict(row) for row in result.mappings().all()]
                    for row in rows:
                        for column in row:
                            # Coerce decimal.Decimal objects to float objects
                            # https://groups.google.com/d/msg/sqlalchemy/0qXMYJvq8SA/oqtvMD9Uw-kJ
                            if isinstance(row[column], decimal.Decimal):
                                row[column] = float(row[column])

                            # Coerce memoryview objects (as from PostgreSQL's bytea columns) to bytes
                            elif isinstance(row[column], memoryview):
                                row[column] = bytes(row[column])

                    # Rows to be returned
                    ret = rows

                # If INSERT, return primary key value for a newly inserted row (or None if none)
                elif command == "INSERT":
                    # If PostgreSQL
                    if self._engine.url.get_backend_name() == "postgresql":
                        # Return LASTVAL() or NULL, avoiding
                        # "(psycopg2.errors.ObjectNotInPrerequisiteState) lastval is not yet defined in this session",
                        # a la https://stackoverflow.com/a/24186770/5156190;
                        # cf. https://www.psycopg.org/docs/errors.html re 55000
                        result = connection.execute(
                            sqlalchemy.text(
                                """
                            CREATE OR REPLACE FUNCTION _LASTVAL()
                            RETURNS integer LANGUAGE plpgsql
                            AS $$
                            BEGIN
                                BEGIN
                                    RETURN (SELECT LASTVAL());
                                EXCEPTION
                                    WHEN SQLSTATE '55000' THEN RETURN NULL;
                                END;
                            END $$;
                            SELECT _LASTVAL();
                        """
                            )
                        )
                        ret = result.first()[0]

                    # If not PostgreSQL
                    else:
                        ret = result.lastrowid if result.rowcount == 1 else None

                # If DELETE or UPDATE, return number of rows matched
                elif command in ["DELETE", "UPDATE"]:
                    ret = result.rowcount

                # If CREATE VIEW, return True
                elif command == "CREATE VIEW":
                    ret = True

            # If constraint violated
            except sqlalchemy.exc.IntegrityError as e:
                if self._autocommit:
                    connection.execute(sqlalchemy.text("ROLLBACK"))
                self._logger.error(termcolor.colored(_statement, "red"))
                e = ValueError(e.orig)
                e.__cause__ = None
                raise e

            # If user error
            except (
                sqlalchemy.exc.OperationalError,
                sqlalchemy.exc.ProgrammingError,
            ) as e:
                self._disconnect()
                self._logger.error(termcolor.colored(_statement, "red"))
                e = RuntimeError(e.orig)
                e.__cause__ = None
                raise e

            # Return value
            else:
                self._logger.info(termcolor.colored(_statement, "green"))
                if self._autocommit:  # Don't stay connected unnecessarily
                    self._disconnect()
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
            if isinstance(value, bool):
                return sqlparse.sql.Token(
                    sqlparse.tokens.Number,
                    sqlalchemy.types.Boolean().literal_processor(self._engine.dialect)(
                        value
                    ),
                )

            # bytes
            elif isinstance(value, bytes):
                if self._engine.url.get_backend_name() in ["mysql", "sqlite"]:
                    return sqlparse.sql.Token(
                        sqlparse.tokens.Other, f"x'{value.hex()}'"
                    )  # https://dev.mysql.com/doc/refman/8.0/en/hexadecimal-literals.html
                elif self._engine.url.get_backend_name() == "postgresql":
                    return sqlparse.sql.Token(
                        sqlparse.tokens.Other, f"'\\x{value.hex()}'"
                    )  # https://dba.stackexchange.com/a/203359
                else:
                    raise RuntimeError("unsupported value: {}".format(value))

            # datetime.datetime
            elif isinstance(value, datetime.datetime):
                return sqlparse.sql.Token(
                    sqlparse.tokens.String,
                    sqlalchemy.types.String().literal_processor(self._engine.dialect)(
                        value.strftime("%Y-%m-%d %H:%M:%S")
                    ),
                )

            # datetime.date
            elif isinstance(value, datetime.date):
                return sqlparse.sql.Token(
                    sqlparse.tokens.String,
                    sqlalchemy.types.String().literal_processor(self._engine.dialect)(
                        value.strftime("%Y-%m-%d")
                    ),
                )

            # datetime.time
            elif isinstance(value, datetime.time):
                return sqlparse.sql.Token(
                    sqlparse.tokens.String,
                    sqlalchemy.types.String().literal_processor(self._engine.dialect)(
                        value.strftime("%H:%M:%S")
                    ),
                )

            # float
            elif isinstance(value, float):
                return sqlparse.sql.Token(
                    sqlparse.tokens.Number,
                    sqlalchemy.types.Float().literal_processor(self._engine.dialect)(
                        value
                    ),
                )

            # int
            elif isinstance(value, int):
                return sqlparse.sql.Token(
                    sqlparse.tokens.Number,
                    sqlalchemy.types.Integer().literal_processor(self._engine.dialect)(
                        value
                    ),
                )

            # str
            elif isinstance(value, str):
                return sqlparse.sql.Token(
                    sqlparse.tokens.String,
                    sqlalchemy.types.String().literal_processor(self._engine.dialect)(
                        value
                    ),
                )

            # None
            elif value is None:
                return sqlparse.sql.Token(sqlparse.tokens.Keyword, sqlalchemy.null())

            # Unsupported value
            else:
                raise RuntimeError("unsupported value: {}".format(value))

        # Escape value(s), separating with commas as needed
        if isinstance(value, (list, tuple)):
            return sqlparse.sql.TokenList(
                sqlparse.parse(", ".join([str(__escape(v)) for v in value]))
            )
        else:
            return __escape(value)


def _parse_exception(e):
    """Parses an exception, returns its message."""

    # Lazily import
    import re

    # MySQL
    matches = re.search(
        r"^\(_mysql_exceptions\.OperationalError\) \(\d+, \"(.+)\"\)$", str(e)
    )
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
    if (
        not isinstance(token, sqlparse.sql.Token)
        or token.ttype != sqlparse.tokens.Name.Placeholder
    ):
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

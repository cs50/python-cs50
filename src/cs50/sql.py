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

        # Catch SQLAlchemy warnings
        with warnings.catch_warnings():

            # Raise exceptions for warnings
            warnings.simplefilter("error")

            # Prepare, execute statement
            try:

                # Execute statement
                result = self.engine.execute(sqlalchemy.text(statement))

                # Return value
                ret = True
                if tokens[0].ttype == sqlparse.tokens.Keyword.DML:

                    # Uppercase token's value
                    value = tokens[0].value.upper()

                    # If SELECT, return result set as list of dict objects
                    if value == "SELECT":

                        # Coerce any decimal.Decimal objects to float objects
                        # https://groups.google.com/d/msg/sqlalchemy/0qXMYJvq8SA/oqtvMD9Uw-kJ
                        rows = [dict(row) for row in result.fetchall()]
                        for row in rows:
                            for column in row:
                                if type(row[column]) is decimal.Decimal:
                                    row[column] = float(row[column])
                        ret = rows

                    # If INSERT, return primary key value for a newly inserted row
                    elif value == "INSERT":
                        if self.engine.url.get_backend_name() in ["postgres", "postgresql"]:
                            result = self.engine.execute("SELECT LASTVAL()")
                            ret = result.first()[0]
                        else:
                            ret = result.lastrowid

                    # If DELETE or UPDATE, return number of rows matched
                    elif value in ["DELETE", "UPDATE"]:
                        ret = result.rowcount

            # If constraint violated, return None
            except sqlalchemy.exc.IntegrityError:
                self._logger.debug(termcolor.colored(statement, "yellow"))
                return None

            # If user errror
            except sqlalchemy.exc.OperationalError as e:
                self._logger.debug(termcolor.colored(statement, "red"))
                e = RuntimeError(_parse_exception(e))
                e.__cause__ = None
                raise e

            # Return value
            else:
                self._logger.debug(termcolor.colored(statement, "green"))
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
                    sqlalchemy.types.Boolean().literal_processor(self.engine.dialect)(value))

            # bytearray, bytes
            elif type(value) in [bytearray, bytes]:
                raise RuntimeError("unsupported value")  # TODO

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
            else:
                raise RuntimeError("unsupported value: {}".format(value))

        # Escape value(s), separating with commas as needed
        if type(value) in [list, tuple]:
            return sqlparse.sql.TokenList(sqlparse.parse(", ".join([str(__escape(v)) for v in value])))
        else:
            return sqlparse.sql.Token(
                sqlparse.tokens.String,
                __escape(value))


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

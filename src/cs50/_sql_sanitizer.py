import datetime
import re

import sqlalchemy
import sqlparse


class SQLSanitizer:
    """Sanitizes SQL values.
    """

    def __init__(self, dialect):
        self._dialect = dialect

    def escape(self, value):
        """Escapes value using engine's conversion function.
        https://docs.sqlalchemy.org/en/latest/core/type_api.html#sqlalchemy.types.TypeEngine.literal_processor

        :param value: The value to be sanitized

        :returns: The sanitized value
        """
        # pylint: disable=too-many-return-statements
        if isinstance(value, (list, tuple)):
            return self.escape_iterable(value)

        if isinstance(value, bool):
            return sqlparse.sql.Token(
                sqlparse.tokens.Number,
                sqlalchemy.types.Boolean().literal_processor(self._dialect)(value))

        if isinstance(value, bytes):
            if self._dialect.name in {"mysql", "sqlite"}:
                # https://dev.mysql.com/doc/refman/8.0/en/hexadecimal-literals.html
                return sqlparse.sql.Token(sqlparse.tokens.Other, f"x'{value.hex()}'")
            if self._dialect.name in {"postgres", "postgresql"}:
                # https://dba.stackexchange.com/a/203359
                return sqlparse.sql.Token(sqlparse.tokens.Other, f"'\\x{value.hex()}'")

            raise RuntimeError(f"unsupported value: {value}")

        string_processor = sqlalchemy.types.String().literal_processor(self._dialect)
        if isinstance(value, datetime.date):
            return sqlparse.sql.Token(
                sqlparse.tokens.String, string_processor(value.strftime("%Y-%m-%d")))

        if isinstance(value, datetime.datetime):
            return sqlparse.sql.Token(
                sqlparse.tokens.String, string_processor(value.strftime("%Y-%m-%d %H:%M:%S")))

        if isinstance(value, datetime.time):
            return sqlparse.sql.Token(
                sqlparse.tokens.String, string_processor(value.strftime("%H:%M:%S")))

        if isinstance(value, float):
            return sqlparse.sql.Token(
                sqlparse.tokens.Number,
                sqlalchemy.types.Float().literal_processor(self._dialect)(value))

        if isinstance(value, int):
            return sqlparse.sql.Token(
                sqlparse.tokens.Number,
                sqlalchemy.types.Integer().literal_processor(self._dialect)(value))

        if isinstance(value, str):
            return sqlparse.sql.Token(sqlparse.tokens.String, string_processor(value))

        if value is None:
            return sqlparse.sql.Token(sqlparse.tokens.Keyword, sqlalchemy.null())

        raise RuntimeError(f"unsupported value: {value}")

    def escape_iterable(self, iterable):
        """Escapes each value in iterable and joins all the escaped values with ", ", formatted for
        SQL's ``IN`` operator.

        :param: An iterable of values to be escaped

        :returns: A comma-separated list of escaped values from ``iterable``
        :rtype: :class:`sqlparse.sql.TokenList`
        """

        return sqlparse.sql.TokenList(
            sqlparse.parse(", ".join([str(self.escape(v)) for v in iterable])))


def escape_verbatim_colon(value):
    """Escapes verbatim colon from a value so as it is not confused with a parameter marker.
    """

    # E.g., ':foo, ":foo,   :foo will be replaced with
    # '\:foo, "\:foo,   \:foo respectively
    return re.sub(r"(^(?:'|\")|\s+):", r"\1\:", value)

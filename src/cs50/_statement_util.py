"""Utility functions used by _statement.py.
"""

import enum
import re

import sqlparse


operation_keywords = {
    "BEGIN",
    "COMMIT",
    "DELETE",
    "INSERT",
    "ROLLBACK",
    "SELECT",
    "START",
    "UPDATE"
}


class Paramstyle(enum.Enum):
    """Represents the supported parameter marker styles.
    """

    FORMAT = enum.auto()
    NAMED = enum.auto()
    NUMERIC = enum.auto()
    PYFORMAT = enum.auto()
    QMARK = enum.auto()


def format_and_parse(sql):
    """Formats and parses a SQL statement. Raises ``RuntimeError`` if ``sql`` represents more than
    one statement.

    :param sql: The SQL statement to be formatted and parsed
    :type sql: str

    :returns: A list of unflattened SQLParse tokens that represent the parsed statement
    """

    formatted_statements = sqlparse.format(sql, strip_comments=True).strip()
    parsed_statements = sqlparse.parse(formatted_statements)
    statement_count = len(parsed_statements)
    if statement_count == 0:
        raise RuntimeError("missing statement")
    if statement_count > 1:
        raise RuntimeError("too many statements at once")

    return parsed_statements[0]


def is_placeholder(ttype):
    return ttype == sqlparse.tokens.Name.Placeholder


def parse_placeholder(value):
    """
    :returns: A tuple of the paramstyle and the name of the parameter marker (if any) or ``None``
    :rtype: tuple
    """
    if value == "?":
        return Paramstyle.QMARK, None

    # E.g., :1
    matches = re.search(r"^:([1-9]\d*)$", value)
    if matches:
        return Paramstyle.NUMERIC, int(matches.group(1)) - 1

    # E.g., :foo
    matches = re.search(r"^:([a-zA-Z]\w*)$", value)
    if matches:
        return Paramstyle.NAMED, matches.group(1)

    if value == "%s":
        return Paramstyle.FORMAT, None

    # E.g., %(foo)s
    matches = re.search(r"%\((\w+)\)s$", value)
    if matches:
        return Paramstyle.PYFORMAT, matches.group(1)

    raise RuntimeError(f"{value}: invalid placeholder")


def is_operation_token(ttype):
    return ttype in {
        sqlparse.tokens.Keyword, sqlparse.tokens.Keyword.DDL, sqlparse.tokens.Keyword.DML}


def is_string_literal(ttype):
    return ttype in [sqlparse.tokens.Literal.String, sqlparse.tokens.Literal.String.Single]


def is_identifier(ttype):
    return ttype == sqlparse.tokens.Literal.String.Symbol


def get_human_readable_list(iterable):
    return ", ".join(str(v) for v in iterable)

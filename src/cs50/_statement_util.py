"""Utility functions used by _statement.py"""

import enum
import re

import sqlparse


class _Paramstyle(enum.Enum):
    FORMAT = enum.auto()
    NAMED = enum.auto()
    NUMERIC = enum.auto()
    PYFORMAT = enum.auto()
    QMARK = enum.auto()


def _format_and_parse(sql):
    formatted_statements = sqlparse.format(sql, strip_comments=True).strip()
    parsed_statements = sqlparse.parse(formatted_statements)
    statement_count = len(parsed_statements)
    if statement_count == 0:
        raise RuntimeError("missing statement")
    if statement_count > 1:
        raise RuntimeError("too many statements at once")

    return parsed_statements[0]


def _is_placeholder(ttype):
    return ttype == sqlparse.tokens.Name.Placeholder


def _parse_placeholder(value):
    if value == "?":
        return _Paramstyle.QMARK, None

    # E.g., :1
    matches = re.search(r"^:([1-9]\d*)$", value)
    if matches:
        return _Paramstyle.NUMERIC, int(matches.group(1)) - 1

    # E.g., :foo
    matches = re.search(r"^:([a-zA-Z]\w*)$", value)
    if matches:
        return _Paramstyle.NAMED, matches.group(1)

    if value == "%s":
        return _Paramstyle.FORMAT, None

    # E.g., %(foo)s
    matches = re.search(r"%\((\w+)\)s$", value)
    if matches:
        return _Paramstyle.PYFORMAT, matches.group(1)

    raise RuntimeError(f"{value}: invalid placeholder")


def _is_operation_token(ttype):
    return ttype in {
        sqlparse.tokens.Keyword, sqlparse.tokens.Keyword.DDL, sqlparse.tokens.Keyword.DML}


def _is_string_literal(ttype):
    return ttype in [sqlparse.tokens.Literal.String, sqlparse.tokens.Literal.String.Single]


def _is_identifier(ttype):
    return ttype == sqlparse.tokens.Literal.String.Symbol


def _get_human_readable_list(iterable):
    return ", ".join(str(v) for v in iterable)

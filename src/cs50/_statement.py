"""Parses a SQL statement and replaces the placeholders with the corresponding parameters"""

import collections
import enum
import re

import sqlparse

from ._sql_sanitizer import SQLSanitizer, escape_verbatim_colon


class Statement:
    """Parses a SQL statement and replaces the placeholders with the corresponding parameters"""
    def __init__(self, dialect, sql, *args, **kwargs):
        if len(args) > 0 and len(kwargs) > 0:
            raise RuntimeError("cannot pass both positional and named parameters")

        self._sql_sanitizer = SQLSanitizer(dialect)
        self._args = args
        self._kwargs = kwargs
        self._statement = _format_and_parse(sql)
        self._tokens = self._tokenize()
        self._paramstyle = self._get_paramstyle()
        self._placeholders = self._get_placeholders()
        self._plugin_escaped_params()
        self._escape_verbatim_colons()
        self._operation_keyword = self._get_operation_keyword()


    def _tokenize(self):
        return list(self._statement.flatten())


    def _plugin_escaped_params(self):
        if self._paramstyle in {_Paramstyle.FORMAT, _Paramstyle.QMARK}:
            self._plugin_format_or_qmark_params()
        elif self._paramstyle == _Paramstyle.NUMERIC:
            self._plugin_numeric_params()
        if self._paramstyle in {_Paramstyle.NAMED, _Paramstyle.PYFORMAT}:
            self._plugin_named_or_pyformat_params()


    def _get_paramstyle(self):
        paramstyle = None
        for token in self._tokens:
            if _is_placeholder(token.ttype):
                paramstyle, _ = _parse_placeholder(token.value)
                break

        if paramstyle is None:
            paramstyle = self._default_paramstyle()

        return paramstyle


    def _get_placeholders(self):
        placeholders = collections.OrderedDict()
        for index, token in enumerate(self._tokens):
            if _is_placeholder(token.ttype):
                paramstyle, name = _parse_placeholder(token.value)
                if paramstyle != self._paramstyle:
                    raise RuntimeError("inconsistent paramstyle")

                placeholders[index] = name

        return placeholders


    def _default_paramstyle(self):
        paramstyle = None
        if self._args:
            paramstyle = _Paramstyle.QMARK
        elif self._kwargs:
            paramstyle = _Paramstyle.NAMED

        return paramstyle


    def _plugin_format_or_qmark_params(self):
        if len(self._placeholders) != len(self._args):
            placeholders = ", ".join([str(token) for token in self._placeholders.values()])
            _args = ", ".join([str(self._sql_sanitizer.escape(arg)) for arg in self._args])
            if len(self._placeholders) < len(self._args):
                raise RuntimeError(f"fewer placeholders ({placeholders}) than values ({_args})")

            raise RuntimeError(f"more placeholders ({placeholders}) than values ({_args})")

        for arg_index, token_index in enumerate(self._placeholders.keys()):
            self._tokens[token_index] = self._sql_sanitizer.escape(self._args[arg_index])


    def _plugin_numeric_params(self):
        unused_arg_idxs = set(range(len(self._args)))
        for token_index, num in self._placeholders.items():
            if num >= len(self._args):
                raise RuntimeError(f"missing value for placeholder ({num + 1})")

            self._tokens[token_index] = self._sql_sanitizer.escape(self._args[num])
            unused_arg_idxs.remove(num)

        if len(unused_arg_idxs) > 0:
            unused_args = ", ".join(
                [str(self._sql_sanitizer.escape(self._args[i])) for i in sorted(unused_arg_idxs)])
            raise RuntimeError(
                f"unused value{'' if len(unused_arg_idxs) == 1 else 's'} ({unused_args})")


    def _plugin_named_or_pyformat_params(self):
        unused_params = set(self._kwargs.keys())
        for token_index, param_name in self._placeholders.items():
            if param_name not in self._kwargs:
                raise RuntimeError(f"missing value for placeholder ({param_name})")

            self._tokens[token_index] = self._sql_sanitizer.escape(self._kwargs[param_name])
            unused_params.remove(param_name)

        if len(unused_params) > 0:
            joined_unused_params = ", ".join(sorted(unused_params))
            raise RuntimeError(
                f"unused value{'' if len(unused_params) == 1 else 's'} ({joined_unused_params})")


    def _escape_verbatim_colons(self):
        for token in self._tokens:
            if _is_string_literal(token.ttype) or _is_identifier(token.ttype):
                token.value = escape_verbatim_colon(token.value)


    def _get_operation_keyword(self):
        for token in self._statement:
            if _is_operation_token(token.ttype):
                token_value = token.value.upper()
                if token_value in {"BEGIN", "DELETE", "INSERT", "SELECT", "START", "UPDATE"}:
                    operation_keyword = token_value
                    break
        else:
            operation_keyword = None

        return operation_keyword


    def get_operation_keyword(self):
        """Returns the operation keyword of the statement (e.g., SELECT) if found, or None"""
        return self._operation_keyword


    def __str__(self):
        return "".join([str(token) for token in self._tokens])


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


class _Paramstyle(enum.Enum):
    FORMAT = enum.auto()
    NAMED = enum.auto()
    NUMERIC = enum.auto()
    PYFORMAT = enum.auto()
    QMARK = enum.auto()

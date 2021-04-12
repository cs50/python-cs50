"""Parses a SQL statement and replaces placeholders with parameters"""

import collections
import datetime
import enum
import re

import sqlalchemy
import sqlparse


class Statement:
    """Parses a SQL statement and replaces placeholders with parameters"""
    def __init__(self, dialect, sql, *args, **kwargs):
        if len(args) > 0 and len(kwargs) > 0:
            raise RuntimeError("cannot pass both positional and named parameters")

        self._dialect = dialect
        self._sql = sql
        self._args = args
        self._kwargs = kwargs

        self._statement = self._parse()
        self._operation_keyword = self._get_operation_keyword()
        self._tokens = self._replace_placeholders_with_params()


    def _parse(self):
        formatted_statements = sqlparse.format(self._sql, strip_comments=True).strip()
        parsed_statements = sqlparse.parse(formatted_statements)
        statement_count = len(parsed_statements)
        if statement_count == 0:
            raise RuntimeError("missing statement")
        if statement_count > 1:
            raise RuntimeError("too many statements at once")

        return parsed_statements[0]


    def _get_operation_keyword(self):
        for token in self._statement:
            if _is_operation_token(token):
                token_value = token.value.upper()
                if token_value in {"BEGIN", "DELETE", "INSERT", "SELECT", "START", "UPDATE"}:
                    operation_keyword = token_value
                    break
        else:
            operation_keyword = None

        return operation_keyword


    def _replace_placeholders_with_params(self):
        tokens = self._tokenize()
        paramstyle, placeholders = self._parse_placeholders(tokens)
        if paramstyle in {_Paramstyle.FORMAT, _Paramstyle.QMARK}:
            tokens = self._replace_format_or_qmark_placeholders(placeholders, tokens)
        elif paramstyle == _Paramstyle.NUMERIC:
            tokens = self._replace_numeric_placeholders(placeholders, tokens)
        if paramstyle in {_Paramstyle.NAMED, _Paramstyle.PYFORMAT}:
            tokens = self._replace_named_or_pyformat_placeholders(placeholders, tokens)

        tokens = _escape_verbatim_colons(tokens)
        return tokens


    def _tokenize(self):
        return list(self._statement.flatten())


    def _parse_placeholders(self, tokens):
        paramstyle = None
        placeholders = collections.OrderedDict()
        for index, token in enumerate(tokens):
            if _is_placeholder(token):
                _paramstyle, name = _parse_placeholder(token)
                if paramstyle is None:
                    paramstyle = _paramstyle
                elif _paramstyle != paramstyle:
                    raise RuntimeError("inconsistent paramstyle")

                placeholders[index] = name

        if paramstyle is None:
            paramstyle = self._default_paramstyle()

        return paramstyle, placeholders


    def _default_paramstyle(self):
        paramstyle = None
        if self._args:
            paramstyle = _Paramstyle.QMARK
        elif self._kwargs:
            paramstyle = _Paramstyle.NAMED

        return paramstyle


    def _replace_format_or_qmark_placeholders(self, placeholders, tokens):
        if len(placeholders) != len(self._args):
            _placeholders = ", ".join([str(token) for token in placeholders.values()])
            _args = ", ".join([str(self._escape(arg)) for arg in self._args])
            if len(placeholders) < len(self._args):
                raise RuntimeError(f"fewer placeholders ({_placeholders}) than values ({_args})")

            raise RuntimeError(f"more placeholders ({_placeholders}) than values ({_args})")

        for arg_index, token_index in enumerate(placeholders.keys()):
            tokens[token_index] = self._escape(self._args[arg_index])

        return tokens


    def _replace_numeric_placeholders(self, placeholders, tokens):
        unused_arg_indices = set(range(len(self._args)))
        for token_index, num in placeholders.items():
            if num >= len(self._args):
                raise RuntimeError(f"missing value for placeholder ({num + 1})")

            tokens[token_index] = self._escape(self._args[num])
            unused_arg_indices.remove(num)

        if len(unused_arg_indices) > 0:
            unused_args = ", ".join(
                [str(self._escape(self._args[i])) for i in sorted(unused_arg_indices)])
            raise RuntimeError(
                f"unused value{'' if len(unused_arg_indices) == 1 else 's'} ({unused_args})")

        return tokens


    def _replace_named_or_pyformat_placeholders(self, placeholders, tokens):
        unused_params = set(self._kwargs.keys())
        for token_index, param_name in placeholders.items():
            if param_name not in self._kwargs:
                raise RuntimeError(f"missing value for placeholder ({param_name})")

            tokens[token_index] = self._escape(self._kwargs[param_name])
            unused_params.remove(param_name)

        if len(unused_params) > 0:
            joined_unused_params = ", ".join(sorted(unused_params))
            raise RuntimeError(
                f"unused value{'' if len(unused_params) == 1 else 's'} ({joined_unused_params})")

        return tokens


    def _escape(self, value):
        """
        Escapes value using engine's conversion function.
        https://docs.sqlalchemy.org/en/latest/core/type_api.html#sqlalchemy.types.TypeEngine.literal_processor
        """
        # pylint: disable=too-many-return-statements
        if isinstance(value, (list, tuple)):
            return self._escape_iterable(value)

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
            return sqlparse.sql.Token(
                sqlparse.tokens.Keyword,
                sqlalchemy.types.NullType().literal_processor(self._dialect)(value))

        raise RuntimeError(f"unsupported value: {value}")


    def _escape_iterable(self, iterable):
        return sqlparse.sql.TokenList(
            sqlparse.parse(", ".join([str(self._escape(v)) for v in iterable])))


    def get_operation_keyword(self):
        """Returns the operation keyword of the statement (e.g., SELECT) if found, or None"""
        return self._operation_keyword


    def __str__(self):
        return "".join([str(token) for token in self._tokens])


def _is_placeholder(token):
    return token.ttype == sqlparse.tokens.Name.Placeholder


def _parse_placeholder(token):
    if token.value == "?":
        return _Paramstyle.QMARK, None

    # E.g., :1
    matches = re.search(r"^:([1-9]\d*)$", token.value)
    if matches:
        return _Paramstyle.NUMERIC, int(matches.group(1)) - 1

    # E.g., :foo
    matches = re.search(r"^:([a-zA-Z]\w*)$", token.value)
    if matches:
        return _Paramstyle.NAMED, matches.group(1)

    if token.value == "%s":
        return _Paramstyle.FORMAT, None

    # E.g., %(foo)s
    matches = re.search(r"%\((\w+)\)s$", token.value)
    if matches:
        return _Paramstyle.PYFORMAT, matches.group(1)

    raise RuntimeError(f"{token.value}: invalid placeholder")


def _escape_verbatim_colons(tokens):
    for token in tokens:
        if _is_string_literal(token):
            token.value = re.sub(r"(^'|\s+):", r"\1\:", token.value)
        elif _is_identifier(token):
            token.value = re.sub(r"(^\"|\s+):", r"\1\:", token.value)

    return tokens


def _is_operation_token(token):
    return token.ttype in {
        sqlparse.tokens.Keyword, sqlparse.tokens.Keyword.DDL, sqlparse.tokens.Keyword.DML}


def _is_string_literal(token):
    return token.ttype in [sqlparse.tokens.Literal.String, sqlparse.tokens.Literal.String.Single]


def _is_identifier(token):
    return token.ttype == sqlparse.tokens.Literal.String.Symbol


class _Paramstyle(enum.Enum):
    FORMAT = enum.auto()
    NAMED = enum.auto()
    NUMERIC = enum.auto()
    PYFORMAT = enum.auto()
    QMARK = enum.auto()

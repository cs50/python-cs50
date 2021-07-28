import collections

from ._sql_sanitizer import SQLSanitizer, escape_verbatim_colon
from ._statement_util import (
    format_and_parse,
    get_human_readable_list,
    is_identifier,
    is_operation_token,
    is_placeholder,
    is_string_literal,
    operation_keywords,
    Paramstyle,
    parse_placeholder,
)


def statement_factory(dialect):
    """Creates a sanitizer for ``dialect`` and injects it into ``Statement``, exposing a simpler
    interface for ``Statement``.

    :param dialect: a SQLAlchemy dialect
    :type dialect: :class:`sqlalchemy.engine.Dialect`
    """

    sql_sanitizer = SQLSanitizer(dialect)

    def statement(sql, *args, **kwargs):
        return Statement(sql_sanitizer, sql, *args, **kwargs)

    return statement


class Statement:
    """Parses a SQL statement and substitutes any parameter markers with their corresponding
    placeholders.
    """

    def __init__(self, sql_sanitizer, sql, *args, **kwargs):
        """
        :param sql_sanitizer: The SQL sanitizer used to sanitize the parameters
        :type sql_sanitizer: :class:`_sql_sanitizer.SQLSanitizer`

        :param sql: The SQL statement
        :type sql: str

        :param *args: Zero or more positional parameters to be substituted for the parameter markers

        :param *kwargs: Zero or more keyword arguments to be substituted for the parameter markers
        """

        if len(args) > 0 and len(kwargs) > 0:
            raise RuntimeError("cannot pass both positional and named parameters")

        self._sql_sanitizer = sql_sanitizer

        self._args = self._get_escaped_args(args)
        self._kwargs = self._get_escaped_kwargs(kwargs)

        self._statement = format_and_parse(sql)
        self._tokens = self._tokenize()

        self._operation_keyword = self._get_operation_keyword()

        self._paramstyle = self._get_paramstyle()
        self._placeholders = self._get_placeholders()
        self._substitute_markers_with_escaped_params()
        # self._escape_verbatim_colons()

    def _get_escaped_args(self, args):
        return [self._sql_sanitizer.escape(arg) for arg in args]

    def _get_escaped_kwargs(self, kwargs):
        return {k: self._sql_sanitizer.escape(v) for k, v in kwargs.items()}

    def _tokenize(self):
        """
        :returns: A flattened list of SQLParse tokens that represent the SQL statement
        """

        return list(self._statement.flatten())

    def _get_operation_keyword(self):
        """
        :returns: The operation keyword of the SQL statement (e.g., ``SELECT``, ``DELETE``, etc)
        :rtype: str
        """

        for token in self._statement:
            if is_operation_token(token.ttype):
                token_value = token.value.upper()
                if token_value in operation_keywords:
                    operation_keyword = token_value
                    break
        else:
            operation_keyword = None

        return operation_keyword

    def _get_paramstyle(self):
        """
        :returns: The paramstyle used in the SQL statement (if any)
        :rtype: :class:_statement_util.Paramstyle``
        """

        paramstyle = None
        for token in self._tokens:
            if is_placeholder(token.ttype):
                paramstyle, _ = parse_placeholder(token.value)
                break
        else:
            paramstyle = self._default_paramstyle()

        return paramstyle

    def _default_paramstyle(self):
        """
        :returns: If positional args were passed, returns ``Paramstyle.QMARK``; if keyword arguments
        were passed, returns ``Paramstyle.NAMED``; otherwise, returns ``None``
        """

        paramstyle = None
        if self._args:
            paramstyle = Paramstyle.QMARK
        elif self._kwargs:
            paramstyle = Paramstyle.NAMED

        return paramstyle

    def _get_placeholders(self):
        """
        :returns: A dict that maps the index of each parameter marker in the tokens list to the name
        of that parameter marker (if applicable) or ``None``
        :rtype: dict
        """

        placeholders = collections.OrderedDict()
        for index, token in enumerate(self._tokens):
            if is_placeholder(token.ttype):
                paramstyle, name = parse_placeholder(token.value)
                if paramstyle != self._paramstyle:
                    raise RuntimeError("inconsistent paramstyle")

                placeholders[index] = name

        return placeholders

    def _substitute_markers_with_escaped_params(self):
        if self._paramstyle in {Paramstyle.FORMAT, Paramstyle.QMARK}:
            self._substitute_format_or_qmark_markers()
        elif self._paramstyle == Paramstyle.NUMERIC:
            self._substitue_numeric_markers()
        if self._paramstyle in {Paramstyle.NAMED, Paramstyle.PYFORMAT}:
            self._substitute_named_or_pyformat_markers()

    def _substitute_format_or_qmark_markers(self):
        """Substitutes format or qmark parameter markers with their corresponding parameters.
        """

        self._assert_valid_arg_count()
        for arg_index, token_index in enumerate(self._placeholders.keys()):
            self._tokens[token_index] = self._args[arg_index]

    def _assert_valid_arg_count(self):
        """Raises a ``RuntimeError`` if the number of arguments does not match the number of
        placeholders.
        """

        if len(self._placeholders) != len(self._args):
            placeholders = get_human_readable_list(self._placeholders.values())
            args = get_human_readable_list(self._args)
            if len(self._placeholders) < len(self._args):
                raise RuntimeError(f"fewer placeholders ({placeholders}) than values ({args})")

            raise RuntimeError(f"more placeholders ({placeholders}) than values ({args})")

    def _substitue_numeric_markers(self):
        """Substitutes numeric parameter markers with their corresponding parameters. Raises a
        ``RuntimeError`` if any parameters are missing or unused.
        """

        unused_arg_indices = set(range(len(self._args)))
        for token_index, num in self._placeholders.items():
            if num >= len(self._args):
                raise RuntimeError(f"missing value for placeholder ({num + 1})")

            self._tokens[token_index] = self._args[num]
            unused_arg_indices.remove(num)

        if len(unused_arg_indices) > 0:
            unused_args = get_human_readable_list(
                [self._args[i] for i in sorted(unused_arg_indices)])
            raise RuntimeError(
                f"unused value{'' if len(unused_args) == 1 else 's'} ({unused_args})")

    def _substitute_named_or_pyformat_markers(self):
        """Substitutes named or pyformat parameter markers with their corresponding parameters.
        Raises a ``RuntimeError`` if any parameters are missing or unused.
        """

        unused_params = {param_name: True for param_name in self._kwargs.keys()}
        for token_index, param_name in self._placeholders.items():
            if param_name not in self._kwargs:
                raise RuntimeError(f"missing value for placeholder ({param_name})")

            self._tokens[token_index] = self._kwargs[param_name]
            unused_params[param_name] = False

        sorted_unique_unused_param_names = sorted(set(
            param_name for param_name, unused in unused_params.items() if unused))
        if len(sorted_unique_unused_param_names) > 0:
            joined_unused_params = get_human_readable_list(sorted_unique_unused_param_names)
            raise RuntimeError(
                f"unused value{'' if len(sorted_unique_unused_param_names) == 1 else 's'}"
                + " ({joined_unused_params})")

    def _escape_verbatim_colons(self):
        """Escapes verbatim colons from string literal and identifier tokens so they aren't treated
        as parameter markers.
        """

        for token in self._tokens:
            if is_string_literal(token.ttype) or is_identifier(token.ttype):
                token.value = escape_verbatim_colon(token.value)

    def is_transaction_start(self):
        return self._operation_keyword in {"BEGIN", "START"}

    def is_transaction_end(self):
        return self._operation_keyword in {"COMMIT", "ROLLBACK"}

    def is_delete(self):
        return self._operation_keyword == "DELETE"

    def is_insert(self):
        return self._operation_keyword == "INSERT"

    def is_select(self):
        return self._operation_keyword == "SELECT"

    def is_update(self):
        return self._operation_keyword == "UPDATE"

    def __str__(self):
        """Joins the statement tokens into a string.
        """

        return "".join([str(token) for token in self._tokens])

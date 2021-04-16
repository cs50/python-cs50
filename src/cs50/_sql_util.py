"""Utility functions used by sql.py.
"""

import contextlib
import decimal
import warnings

import sqlalchemy


def process_select_result(result):
    """Converts a SQLAlchemy result to a ``list`` of ``dict`` objects, each of which represents a
    row in the result set.

    :param result: A SQLAlchemy result
    :type result: :class:`sqlalchemy.engine.Result`
    """
    rows = [dict(row) for row in result.fetchall()]
    for row in rows:
        for column in row:
            # Coerce decimal.Decimal objects to float objects
            # https://groups.google.com/d/msg/sqlalchemy/0qXMYJvq8SA/oqtvMD9Uw-kJ
            if isinstance(row[column], decimal.Decimal):
                row[column] = float(row[column])

            # Coerce memoryview objects (as from PostgreSQL's bytea columns) to bytes
            elif isinstance(row[column], memoryview):
                row[column] = bytes(row[column])

    return rows


@contextlib.contextmanager
def raise_errors_for_warnings():
    """Catches warnings and raises errors instead.
    """

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        yield


def postgres_lastval(connection):
    """
    :returns: The ID of the last inserted row, if defined in this session, or None
    """

    try:
        return connection.execute("SELECT LASTVAL()").first()[0]
    except sqlalchemy.exc.OperationalError:
        return None

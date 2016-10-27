import sqlalchemy
from pprint import pprint

class SQL(object):
    """TODO"""

    def __init__(self, url):
        """TODO"""
        self.engine = sqlalchemy.create_engine(url)

    def execute(self, text, *multiparams, **params):
        """TODO"""

        # http://docs.sqlalchemy.org/en/latest/core/sqlelement.html#sqlalchemy.sql.expression.text
        # https://groups.google.com/forum/#!topic/sqlalchemy/FfLwKT1yQlg
        # http://docs.sqlalchemy.org/en/latest/core/connections.html#sqlalchemy.engine.Engine.execute
        # http://docs.sqlalchemy.org/en/latest/faq/sqlexpressions.html#how-do-i-render-sql-expressions-as-strings-possibly-with-bound-parameters-inlined
        try:
            statement = sqlalchemy.text(text).bindparams(*multiparams, **params)
            result = self.engine.execute(str(statement.compile(compile_kwargs={"literal_binds": True})))
        except Exception as e:
            raise RuntimeError(e)

        # SELECT
        if result.returns_rows:
            rows = result.fetchall()
            return [dict(row) for row in rows]

        # INSERT
        elif result.lastrowid is not None:
            return result.lastrowid

        # DELETE, UPDATE
        else:
            return result.rowcount

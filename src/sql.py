import sqlalchemy

class SQL(object):
    """TODO"""

    def __init__(self, url):
        """TODO"""
        try:
            self.engine = sqlalchemy.create_engine(url)
        except Exception as e:
            raise RuntimeError(e)

    def execute(self, text, *multiparams, **params):
        """TODO"""
        try:

            # http://docs.sqlalchemy.org/en/latest/core/sqlelement.html#sqlalchemy.sql.expression.text
            # https://groups.google.com/forum/#!topic/sqlalchemy/FfLwKT1yQlg
            # http://docs.sqlalchemy.org/en/latest/core/connections.html#sqlalchemy.engine.Engine.execute
            # http://docs.sqlalchemy.org/en/latest/faq/sqlexpressions.html#how-do-i-render-sql-expressions-as-strings-possibly-with-bound-parameters-inlined
            statement = sqlalchemy.text(text).bindparams(*multiparams, **params)
            result = self.engine.execute(str(statement.compile(compile_kwargs={"literal_binds": True})))

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

        except sqlalchemy.exc.IntegrityError:
            return None

        except Exception as e:
            raise RuntimeError(e)



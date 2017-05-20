import re
import sqlalchemy
import sqlparse

class SQL(object):
    """Wrap SQLAlchemy to provide a simple SQL API."""

    def __init__(self, url):
        """
        Create instance of sqlalchemy.engine.Engine.

        URL should be a string that indicates database dialect and connection arguments.

        http://docs.sqlalchemy.org/en/latest/core/engines.html#sqlalchemy.create_engine
        """
        try:
            self.engine = sqlalchemy.create_engine(url)
        except Exception as e:
            raise RuntimeError(e)

    def execute(self, text, *multiparams, **params):
        """
        Execute a SQL statement.
        """

        # parse text
        parsed = sqlparse.parse(text)
        if len(parsed) == 0:
            raise RuntimeError("missing statement")
        elif len(parsed) > 1:
            raise RuntimeError("too many statements")
        statement = parsed[0]
        if statement.get_type() == "UNKNOWN":
            raise RuntimeError("unknown type of statement")

        # infer paramstyle
	# https://www.python.org/dev/peps/pep-0249/#paramstyle
	paramstyle = None
	for token in statement.flatten():
	    if sqlparse.utils.imt(token.ttype, t=sqlparse.tokens.Token.Name.Placeholder):
		_paramstyle = None
		if re.search(r"^\?$", token.value):
		    _paramstyle = "qmark"
		elif re.search(r"^:\d+$", token.value):
		    _paramstyle = "numeric"
		elif re.search(r"^:\w+$", token.value):
		    _paramstyle = "named"
		elif re.search(r"^%s$", token.value):
		    _paramstyle = "format"
		elif re.search(r"^%\(\w+\)s$", token.value):
		    _paramstyle = "pyformat"
		else:
		    raise RuntimeError("unknown paramstyle")
		if paramstyle and paramstyle != _paramstyle:
		    raise RuntimeError("inconsistent paramstyle")
		paramstyle = _paramstyle

        try:

            parsed = sqlparse.split("SELECT * FROM cs50 WHERE id IN (SELECT id FROM cs50); SELECT 1; CREATE TABLE foo")
            print(parsed)
            return 0

            # bind parameters before statement reaches database, so that bound parameters appear in exceptions
            # http://docs.sqlalchemy.org/en/latest/core/sqlelement.html#sqlalchemy.sql.expression.text
            # https://groups.google.com/forum/#!topic/sqlalchemy/FfLwKT1yQlg
            # http://docs.sqlalchemy.org/en/latest/core/connections.html#sqlalchemy.engine.Engine.execute
            # http://docs.sqlalchemy.org/en/latest/faq/sqlexpressions.html#how-do-i-render-sql-expressions-as-strings-possibly-with-bound-parameters-inlined
            statement = sqlalchemy.text(text).bindparams(*multiparams, **params)
            result = self.engine.execute(str(statement.compile(compile_kwargs={"literal_binds": True})))

            # if SELECT (or INSERT with RETURNING), return result set as list of dict objects
            if result.returns_rows:
                rows = result.fetchall()
                return [dict(row) for row in rows]

            # if INSERT, return primary key value for a newly inserted row
            elif result.lastrowid is not None:
                return result.lastrowid

            # if DELETE or UPDATE (or INSERT without RETURNING), return number of rows matched
            else:
                return result.rowcount

        # if constraint violated, return None
        except sqlalchemy.exc.IntegrityError:
            return None

        # else raise error
        except Exception as e:
            raise RuntimeError(e)

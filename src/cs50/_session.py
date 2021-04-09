import os

import sqlalchemy
import sqlalchemy.orm
import sqlite3

class Session:
    def __init__(self, url, **engine_kwargs):
        self._url = url
        if _is_sqlite_url(self._url):
            _assert_sqlite_file_exists(self._url)

        self._engine = _create_engine(self._url, **engine_kwargs)
        self._is_postgres = self._engine.url.get_backend_name() in {"postgres", "postgresql"}
        _setup_on_connect(self._engine)
        self._session = _create_scoped_session(self._engine)


    def is_postgres(self):
        return self._is_postgres


    def execute(self, statement):
        return self._session.execute(sqlalchemy.text(str(statement)))


    def __getattr__(self, attr):
        return getattr(self._session, attr)


def _is_sqlite_url(url):
    return url.startswith("sqlite:///")


def _assert_sqlite_file_exists(url):
    path = url[len("sqlite:///"):]
    if not os.path.exists(path):
        raise RuntimeError(f"does not exist: {path}")
    if not os.path.isfile(path):
        raise RuntimeError(f"not a file: {path}")


def _create_engine(url, **kwargs):
    try:
        engine = sqlalchemy.create_engine(url, **kwargs)
    except sqlalchemy.exc.ArgumentError:
        raise RuntimeError(f"invalid URL: {url}") from None

    engine.execution_options(autocommit=False)
    return engine


def _setup_on_connect(engine):
    def connect(dbapi_connection, _):
        _disable_auto_begin_commit(dbapi_connection)
        if _is_sqlite_connection(dbapi_connection):
            _enable_sqlite_foreign_key_constraints(dbapi_connection)

    sqlalchemy.event.listen(engine, "connect", connect)


def _create_scoped_session(engine):
    session_factory = sqlalchemy.orm.sessionmaker(bind=engine)
    return sqlalchemy.orm.scoping.scoped_session(session_factory)


def _disable_auto_begin_commit(dbapi_connection):
    # Disable underlying API's own emitting of BEGIN and COMMIT so we can ourselves
    # https://docs.sqlalchemy.org/en/13/dialects/sqlite.html#serializable-isolation-savepoints-transactional-ddl
    dbapi_connection.isolation_level = None


def _is_sqlite_connection(dbapi_connection):
    return isinstance(dbapi_connection, sqlite3.Connection)


def _enable_sqlite_foreign_key_constraints(dbapi_connection):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

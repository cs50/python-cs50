import threading

from ._engine_util import create_engine


thread_local_data = threading.local()


class Engine:
    """Wraps a SQLAlchemy engine.
    """

    def __init__(self, url):
        self._engine = create_engine(url)

    def get_transaction_connection(self):
        """
        :returns: A new connection with autocommit disabled (to be used for transactions).
        """

        _thread_local_connections()[self] = self._engine.connect().execution_options(
            autocommit=False)
        return self.get_existing_transaction_connection()

    def get_connection(self):
        """
        :returns: A new connection with autocommit enabled
        """

        return self._engine.connect().execution_options(autocommit=True)

    def get_existing_transaction_connection(self):
        """
        :returns: The transaction connection bound to this Engine instance, if one exists, or None.
        """

        return _thread_local_connections().get(self)

    def close_transaction_connection(self):
        """Closes the transaction connection bound to this Engine instance, if one exists and
        removes it.
        """

        connection = self.get_existing_transaction_connection()
        if connection:
            connection.close()
            del _thread_local_connections()[self]

    def is_postgres(self):
        return self._engine.dialect.name in {"postgres", "postgresql"}

    def __getattr__(self, attr):
        return getattr(self._engine, attr)

def _thread_local_connections():
    """
    :returns: A thread local dict to keep track of transaction connection. If one does not exist,
    creates one.
    """

    try:
        connections = thread_local_data.connections
    except AttributeError:
        connections = thread_local_data.connections = {}

    return connections

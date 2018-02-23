import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from painless_sqlalchemy.core.Model import Model


class Painless(object):

    # excluded tables, e.g. used for postgres spatial extension (PostGIS)

    version_table = ['alembic_version']
    _known_session = set()

    def __init__(self, db_uri):
        self.db_info = db_uri
        self.engine = create_engine(db_uri)
        self.session = scoped_session(
            sessionmaker(autocommit=False, bind=self.engine))
        self.Model = Model
        Model.query = self.session.query_property()

    def make_session(self, bind=None):
        """
            Get a fresh session from pool
            :param bind: the database
            :return: the new session
        """
        session = sessionmaker(bind=self.engine)()
        self._known_session.add(session)
        return session

    def get_class_by_table_name(self, table_name):
        """Return class reference mapped to table.

        :param table_name: String with name of table.
        :return: Class reference or None.
        """
        assert table_name is not None
        result = None
        # noinspection PyProtectedMember
        for cls in self.Model._decl_class_registry.values():
            if getattr(cls, '__tablename__', None) == table_name:
                result = cls
                break
        return result

    def create_db(self, bind, echo=False):
        """
            Create the database
        :param echo: Whether to print all executed statements
        """
        db_name = self.db_info.split('/')[-1]
        conn = Painless._pg_connect(self.db_info, echo)
        conn.execute("CREATE DATABASE %s" % db_name)
        conn.close()

    @staticmethod
    def _pg_connect(uri, echo=False):
        """
            Connect to a database and discard the open transactions.
        :param bind: the database identifier
        :param db_name: database name
        :param echo: Whether to print all executed statements
        :return: A connection
        """
        engine = sqlalchemy.engine.create_engine(uri, echo=echo)
        conn = engine.connect()
        # end the open transaction
        conn.execute("commit")
        return conn

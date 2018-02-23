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

        Model.query = self.session.query_property()
        Model.session = self.session
        Model.engine = self.engine
        self.Model = Model

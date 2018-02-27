from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from painless_sqlalchemy.core.Model import Model


class Painless(object):

    def __init__(self, db_uri, engine_options=None, session_options=None):
        if engine_options is None:
            engine_options = {}
        if session_options is None:
            session_options = {}
        self.db_info = db_uri
        self.engine = create_engine(db_uri, **engine_options)
        self.session = scoped_session(
            sessionmaker(bind=self.engine, **session_options))

        Model.query = self.session.query_property()
        Model.session = self.session
        Model.engine = self.engine
        self.Model = Model

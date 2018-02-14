from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker


engine = create_engine('sqlite://')
session = scoped_session(sessionmaker(autocommit=False, bind=engine))


Base = declarative_base()


class ModelBase(Base):
    # prevent creation of table
    __abstract__ = True

    query = session.query_property()

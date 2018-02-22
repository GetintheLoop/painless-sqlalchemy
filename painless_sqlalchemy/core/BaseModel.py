from sqlalchemy import create_engine, Column, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker


engine = create_engine(
    'postgresql://postgres:password@localhost:5432/painless_tmp')
session = scoped_session(sessionmaker(autocommit=False, bind=engine))


Base = declarative_base()


class BaseModel(Base):
    # prevent creation of table
    __abstract__ = True

    default_serialization = ("id",)

    query = session.query_property()

    # Id is always required but can be overwritten
    id = Column(Integer, primary_key=True)

from sqlalchemy import Column, Integer
from sqlalchemy.ext.declarative import declarative_base

_Base = declarative_base()


class ModelRaw(_Base):
    # prevent creation of table
    __abstract__ = True

    default_serialization = ("id",)

    query = None
    session = None
    engine = None

    # Id is always required but can be overwritten
    id = Column(Integer, primary_key=True)

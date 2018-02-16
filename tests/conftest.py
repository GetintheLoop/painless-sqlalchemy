import pytest
import sqlalchemy
from sqlalchemy import Column, String
from painless_sqlalchemy.BaseModel import Base, engine
from painless_sqlalchemy.Model import Model


@pytest.fixture(scope='session')
def Teacher():
    class Teacher(Model):
        __tablename__ = 'teacher'
    return Teacher


@pytest.fixture(scope='session')
def Student():
    class Student(Model):
        __tablename__ = 'student'

        name = Column(String(64), index=True, nullable=False)
    return Student


@pytest.fixture(scope='session', autouse=True)
def init_db(Teacher, Student):
    uri, db = engine.url.__str__().rsplit("/", 1)

    _engine = sqlalchemy.engine.create_engine(uri + "/postgres")
    conn = _engine.connect()
    conn.execute(
        "SELECT pg_terminate_backend(pid) "
        "FROM pg_stat_activity WHERE datname = '%s';" % db
    )
    conn.execute("commit")
    conn.execute('DROP DATABASE IF EXISTS "%s";' % db)
    conn.execute("commit")
    conn.execute('CREATE DATABASE "%s";' % db)
    conn.close()

    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


def pytest_itemcollected(item):
    """ Format output as TestClass: TestName """
    par = item.parent.obj
    node = item.obj
    pref = par.__doc__.strip() if par.__doc__ else par.__class__.__name__
    suf = node.__doc__.strip() if node.__doc__ else node.__name__
    item._nodeid = ': '.join((pref, suf))

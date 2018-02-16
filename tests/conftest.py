import pytest
from painless_sqlalchemy.BaseModel import Base, engine
from painless_sqlalchemy.ModelSerialization import ModelSerialization


@pytest.fixture(scope='session')
def Teacher():
    # noinspection PyShadowingNames
    class Teacher(ModelSerialization):
        __tablename__ = 'teacher'
    return Teacher


@pytest.fixture(scope='session')
def Student():
    # noinspection PyShadowingNames
    class Student(ModelSerialization):
        __tablename__ = 'student'
    return Student


@pytest.fixture(scope='session', autouse=True)
def init_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


def pytest_itemcollected(item):
    """ Format output as TestClass: TestName """
    par = item.parent.obj
    node = item.obj
    pref = par.__doc__.strip() if par.__doc__ else par.__class__.__name__
    suf = node.__doc__.strip() if node.__doc__ else node.__name__
    item._nodeid = ': '.join((pref, suf))

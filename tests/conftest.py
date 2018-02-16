import pytest
from painless_sqlalchemy.BaseModel import Base, engine
from painless_sqlalchemy.ModelSerialization import ModelSerialization


@pytest.fixture(scope='session')
def Foo():
    # noinspection PyShadowingNames
    class Foo(ModelSerialization):
        __tablename__ = 'foo'
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    return Foo


def pytest_itemcollected(item):
    """ Format output as TestClass: TestName """
    par = item.parent.obj
    node = item.obj
    pref = par.__doc__.strip() if par.__doc__ else par.__class__.__name__
    suf = node.__doc__.strip() if node.__doc__ else node.__name__
    item._nodeid = ': '.join((pref, suf))

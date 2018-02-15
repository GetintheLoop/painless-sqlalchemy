from sqlalchemy import Column, Integer
from painless_sqlalchemy.BaseModel import Base, engine
from painless_sqlalchemy.ModelSerialization import ModelSerialization


class TestModelAction(object):

    @classmethod
    def setup_class(cls):
        class Foo(ModelSerialization):
            __tablename__ = 'foo'
            id = Column(Integer, primary_key=True)

        cls.Foo = Foo
        Base.metadata.create_all(engine)

    @classmethod
    def teardown_class(cls):
        Base.metadata.drop_all(engine)

    def test_get_session(self):
        """ Test session always exists """
        assert self.Foo()._get_session() is not None

    def test_save(self):
        """ Test saving object """
        self.Foo(id=1).save()
        assert self.Foo.filter({'id': 1}).one().id == 1

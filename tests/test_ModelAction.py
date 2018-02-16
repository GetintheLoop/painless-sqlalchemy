

class TestModelAction(object):

    def test_get_session(self, Foo):
        """ Test session always exists """
        assert Foo()._get_session() is not None

    def test_save(self, Foo):
        """ Test saving object """
        foo_id = Foo().save().id
        foo = Foo.filter({'id': foo_id}).one()
        assert foo.id == foo_id

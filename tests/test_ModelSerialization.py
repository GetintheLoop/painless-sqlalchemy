

class TestModelSerialization:

    def test_serialize(self, Foo):
        foo_id = Foo().save().id
        foo = Foo.serialize(
            to_return=['id'],
            filter_by={'id': foo_id},
            filter_ids=False
        )
        assert len(foo) == 1
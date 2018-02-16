

class TestModelSerialization:

    def test_serialize(self, Teacher_):
        teacher_id = Teacher_().save().id
        teacher = Teacher_.serialize(
            to_return=['id'],
            filter_by={'id': teacher_id},
            filter_ids=False
        )
        assert len(teacher) == 1

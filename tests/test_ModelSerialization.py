

class TestModelSerialization:

    def test_serialize(self, Teacher):
        teacher_id = Teacher().save().id
        teacher = Teacher.serialize(
            to_return=['id'],
            filter_by={'id': teacher_id},
            filter_ids=False
        )
        assert len(teacher) == 1
        assert teacher[0]['id'] == teacher_id

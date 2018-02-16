

class TestModelAction(object):

    def test_get_session(self, Student):
        """ Test session always exists """
        assert Student()._get_session() is not None

    def test_save(self, Teacher):
        """ Test saving object """
        teacher_id = Teacher().save().id
        teacher = Teacher.filter({'id': teacher_id}).one()
        assert teacher.id == teacher_id

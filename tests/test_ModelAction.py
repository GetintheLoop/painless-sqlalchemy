

class TestModelAction(object):

    def test_get_session(self, Student_):
        """ Test session always exists """
        assert Student_()._get_session() is not None

    def test_save(self, Teacher_):
        """ Test saving object """
        teacher_id = Teacher_().save().id
        teacher = Teacher_.filter({'id': teacher_id}).one()
        assert teacher.id == teacher_id

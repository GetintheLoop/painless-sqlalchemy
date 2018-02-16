import pytest
from sqlalchemy.exc import IntegrityError


class TestModelAction(object):

    def test_get_session(self, Student):
        """ Test session always exists """
        assert Student()._get_session() is not None

    def test_save(self, Teacher):
        """ Test saving object """
        teacher_id = Teacher().save().id
        teacher = Teacher.filter({'id': teacher_id}).one()
        assert teacher.id == teacher_id

    def test_delete(self, Student):
        student_id = Student(name='foo').save().id
        assert Student.filter({'id': student_id}).first() is not None
        Student.filter({'id': student_id}).one().delete()
        assert Student.filter({'id': student_id}).first() is None

    def test_update(self, Student):
        student_id = Student(name='foo').save().id
        assert Student.filter({'id': student_id}).one().name == 'foo'
        Student.filter({'id': student_id}).one().update(name='bar').save()
        assert Student.filter({'id': student_id}).one().name == 'bar'

    def test_update_invalid_column(self, Student):
        with pytest.raises(AttributeError):
            Student().update(invalid_column=None)

    def test_rollback(self, Student):
        student = Student(name='foo').save()
        student.update(name=None)
        with pytest.raises(IntegrityError):
            student.save()
        student.rollback()
        assert Student.filter({'id': student.id}).one().name == 'foo'

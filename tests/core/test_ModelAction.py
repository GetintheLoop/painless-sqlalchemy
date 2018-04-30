import pytest
from sqlalchemy.exc import IntegrityError
from faker import Faker
from tests.AbstractTest import AbstractTest

fake = Faker()


class TestModelAction(AbstractTest):

    @classmethod
    @pytest.fixture(scope='class', autouse=True)
    def setup_class(cls, Teacher, Student):
        super(TestModelAction, cls).setup_class()
        student = Student(name=fake.name())
        teacher = Teacher(name=fake.name())

        cls.checkin(student, teacher)

        cls.student = cls.persist(student)
        cls.teacher = cls.persist(teacher)

    def test_get_session(self, Student):
        """ Test session always exists """
        assert Student()._get_session() is not None

    def test_save(self, Teacher):
        """ Test saving object """
        teacher_id = Teacher(name=fake.name()).save().id
        teacher = Teacher.filter({'id': teacher_id}).one()
        assert teacher.id == teacher_id
        self.register(teacher=teacher_id)

    def test_delete(self, Student):
        student_id = Student(name='foo').save().id
        assert Student.filter({'id': student_id}).first() is not None
        Student.filter({'id': student_id}).one().delete()
        assert Student.filter({'id': student_id}).first() is None

    def test_update(self, Student):
        assert Student.filter({
            'id': self.student.id
        }).one().name == self.student.name
        new_name = fake.name()
        Student.filter({
            'id': self.student.id
        }).one().update(name=new_name).save()
        assert Student.filter({'id': self.student.id}).one().name == new_name

        # revert
        Student.filter({
            'id': self.student.id
        }).one().update(name=self.student.name).save()

    def test_update_invalid_column(self, Student):
        with pytest.raises(AttributeError):
            Student().update(invalid_column=None)

    def test_rollback(self, Student):
        student = Student.filter({'id': self.student.id}).one()
        student.update(name=None)
        with pytest.raises(IntegrityError):
            student.save()
        student.rollback()
        assert Student.filter({
            'id': student.id
        }).one().name == self.student.name

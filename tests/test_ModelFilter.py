import pytest
from sqlalchemy.orm import sessionmaker
from painless_sqlalchemy.BaseModel import engine


class TestModelFilter(object):

    @classmethod
    @pytest.fixture(scope='class', autouse=True)
    def setup(cls, Classroom, Teacher, Student):
        student1 = Student(name='foo')
        student2 = Student(name='baz')

        teacher = Teacher(students=[student1, student2])
        classroom = Classroom(teacher=teacher)

        session = sessionmaker(engine)()
        session.add_all([student1, student2, teacher, classroom])
        session.commit()

        cls.student1 = {
            'id': student1.id,
            'name': student1.name
        }
        cls.student2_id = student2.id
        cls.teacher_id = teacher.id
        cls.classroom_id = classroom.id

    def test_filter_by_id(self, Teacher):
        assert Teacher.filter({
            'id': self.teacher_id
        }).one().id == self.teacher_id

    def test_filter_by_many_to_many_relationship(self, Teacher):
        assert Teacher.filter({
            'students.name': self.student1['name']
        }).one().id == self.teacher_id

    def test_filter_by_one_to_one_relationship(self, Classroom):
        assert Classroom.filter({
            'teacher.id': self.teacher_id
        }).one().id == self.classroom_id

    def test_filter_by_foreign_key(self, Classroom):
        assert Classroom.filter({
            'teacher_id': self.teacher_id
        }).one().id == self.classroom_id

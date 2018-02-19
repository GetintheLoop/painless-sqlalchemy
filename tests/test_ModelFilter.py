import pytest
from sqlalchemy import and_
from sqlalchemy.orm import sessionmaker
from painless_sqlalchemy.BaseModel import engine
from painless_sqlalchemy.column.RefColumn import RefColumn as ref


class TestModelFilter(object):

    @classmethod
    @pytest.fixture(scope='class', autouse=True)
    def setup(cls, School, Classroom, Teacher, Student):
        student1 = Student(name='foo')
        student2 = Student(name='bar', address='baz')

        teacher = Teacher(students=[student1, student2])
        classroom = Classroom(teacher=teacher)
        school = School(classrooms=[classroom])

        session = sessionmaker(engine)()
        session.add_all([student1, student2, teacher, classroom, school])
        session.commit()

        cls.student1 = {
            'id': student1.id,
            'name': student1.name
        }
        cls.student2_id = student2.id
        cls.teacher_id = teacher.id
        cls.classroom_id = classroom.id
        cls.school_id = school.id

        yield  # run tests in class
        # cleanup
        session = sessionmaker(engine)()
        session.query(Student).delete()
        session.query(Teacher).delete()
        session.query(Classroom).delete()
        session.query(School).delete()
        session.commit()

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

    def test_filter_by_foreign_key(self, Teacher):
        assert Teacher.filter({
            'classroom_id': self.classroom_id
        }).one().id == self.teacher_id

    def test_filter_by_nested_relationship(self, School):
        assert School.filter({
            'classrooms.teacher.id': self.teacher_id
        }).one().id == self.school_id

    def test_filter_one_to_many_relationship(self, School):
        assert School.filter({
            'classrooms.id': self.classroom_id
        }).one().id == self.school_id

    def test_filter_many_to_one_relationship(self, Classroom):
        classrooms = Classroom.filter({
            'school.id': self.school_id
        }).all()
        assert len(classrooms) == 1
        assert classrooms[0].id == self.classroom_id

    def test_ref_filter(self, Student):
        student = Student.filter(
            and_(*[
                ref('id') == self.student1['id'],
                ref('name') == self.student1['name']
            ])
        ).one()
        assert student.id == self.student1['id']

    def test_filter_skip_nones(self, Student):
        student = Student.filter({
            'id': self.student2_id,
            'address': None
        }, skip_nones=True).one()
        assert student.id == self.student2_id

    def test_filter_for_null_value(self, Student):
        student = Student.filter({
            'id': self.student1['id'],
            'address': None
        }).first()
        assert student is not None

        student = Student.filter({
            'id': self.student2_id,
            'address': None
        }).first()
        assert student is None

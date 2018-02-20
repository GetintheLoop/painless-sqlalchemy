import pytest
from sqlalchemy import and_, or_
from faker import Faker
from painless_sqlalchemy.elements.ColumnReference import ref
from tests.abstract.AbstractDatabaseTest import AbstractDatabaseTest

fake = Faker()


class TestModelFilter(AbstractDatabaseTest):

    @classmethod
    @pytest.fixture(scope='class', autouse=True)
    def setup_class(cls, School, Classroom, Teacher, Student):
        super(TestModelFilter, cls).setup_class()
        student1 = Student(name=fake.name())
        student2 = Student(name=fake.name(), address=fake.address())

        teacher = Teacher(name=fake.name(), students=[student1, student2])
        classroom = Classroom(teacher=teacher)
        school = School(classrooms=[classroom])

        cls.checkin(student1, student2, teacher, classroom, school)

        cls.student1 = cls.persist(student1)
        cls.student2 = cls.persist(student2)
        cls.teacher_id = teacher.id
        cls.classroom_id = classroom.id
        cls.school_id = school.id

    def test_filter_by_id(self, Teacher):
        assert Teacher.filter({
            'id': self.teacher_id
        }).one().id == self.teacher_id

    def test_filter_by_many_to_many_relationship(self, Teacher):
        assert Teacher.filter({
            'students.name': self.student1.name
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
                ref('id') == self.student1.id,
                ref('name') == self.student1.name
            ])
        ).one()
        assert student.id == self.student1.id

    def test_filter_skip_nones(self, Student):
        assert self.student2.address is not None
        student = Student.filter({
            'id': self.student2.id,
            'address': None
        }, skip_nones=True).first()
        assert student is not None

        student = Student.filter({
            'id': self.student2.id,
            'address': None
        }, skip_nones=False).first()
        assert student is None

    def test_filter_by_null_value(self, Student):
        assert self.student1.address is None
        student = Student.filter({
            'id': self.student1.id,
            'address': None
        }).first()
        assert student is not None

    def test_filter_by_or_condition(self, Student):
        students = Student.filter(or_(
            ref('id') == self.student1.id,
            ref('name') == self.student2.name
        )).all()
        assert len(students) == 2
        assert self.get(students, 'id', self.student1.id) is not None
        assert self.get(students, 'id', self.student2.id) is not None

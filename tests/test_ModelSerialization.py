import pytest
from sqlalchemy import and_
from faker import Faker
from painless_sqlalchemy.elements.ColumnReference import ref
from painless_sqlalchemy.util.DictUtil import flatten_dict
from tests.abstract.AbstractDatabaseTest import AbstractDatabaseTest

fake = Faker()


class TestModelSerialization(AbstractDatabaseTest):

    @classmethod
    @pytest.fixture(scope='class', autouse=True)
    def setup_class(cls, School, Classroom, Teacher, Student):
        super(TestModelSerialization, cls).setup_class()
        student1 = Student(name=fake.name())
        student2 = Student(name=fake.name(), address=fake.address())
        teacher = Teacher(students=[student1, student2])
        classroom = Classroom(teacher=teacher)
        school = School(classrooms=[classroom])

        cls.checkin(student1, student2, teacher, classroom, school)

        cls.student1 = {
            'id': student1.id,
            'name': student1.name
        }
        cls.student2_id = student2.id
        cls.teacher_id = teacher.id
        cls.school_id = school.id

    def test_serialize(self, Teacher):
        teacher = Teacher.serialize(
            to_return=['id'],
            filter_by={'id': self.teacher_id},
            suppress=False
        )
        assert len(teacher) == 1
        assert teacher[0]['id'] == self.teacher_id

    def test_filter_by_ref_column(self, Student):
        student = Student.serialize(
            to_return=['id'],
            filter_by=and_(*[
                ref('id') == self.student1['id'],
                ref('name') == self.student1['name']
            ]),
            suppress=False
        )
        assert len(student) == 1
        assert student[0]['id'] == self.student1['id']

    def test_skip_nones(self, Student):
        student = Student.serialize(
            to_return=['id', 'name', 'address'],
            filter_by={
                'id': self.student2_id,
                'address': None
            },
            skip_nones=True,
            suppress=False
        )
        assert len(student) == 1
        assert student[0]['id'] == self.student2_id

    def test_primary_keys_filtered_on_relationship(self, School, Student):
        assert Student.id.primary_key is True
        assert Student.id.info.get('exposed', False) is False
        assert School.id.primary_key is True
        assert School.id.info.get('exposed', False) is True

        schools = School.serialize(
            to_return=['id', 'classrooms.teacher.students.id'],
            filter_by={'classrooms.teacher.students.id': self.student1['id']},
            suppress=True
        )
        assert len(schools) == 1
        assert schools[0] == {'id': self.school_id}

        schools = School.serialize(
            to_return=['id', 'classrooms.teacher.students.id'],
            filter_by={'classrooms.teacher.students.id': self.student1['id']},
            suppress=False
        )
        assert 'id' in schools[0]
        assert 'classrooms.teacher.students.id' in flatten_dict(schools)

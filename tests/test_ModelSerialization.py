from functools import reduce
import pytest
from sqlalchemy import and_
from sqlalchemy.orm import sessionmaker
from painless_sqlalchemy.BaseModel import engine
from painless_sqlalchemy.column.RefColumn import RefColumn as ref
from faker import Faker

fake = Faker()


class TestModelSerialization:

    @classmethod
    @pytest.fixture(scope='class', autouse=True)
    def setup_class(cls, School, Classroom, Teacher, Student):
        student1 = Student(name=fake.name())
        student2 = Student(name=fake.name(), address=fake.address())
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
        cls.school_id = school.id

        yield  # run tests
        # cleanup
        session = sessionmaker(engine)()
        session.query(Student).delete()
        session.query(Teacher).delete()
        session.commit()

    def test_serialize(self, Teacher):
        teacher = Teacher.serialize(
            to_return=['id'],
            filter_by={'id': self.teacher_id},
            filter_ids=False
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
            filter_ids=False
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
            filter_ids=False
        )
        assert len(student) == 1
        assert student[0]['id'] == self.student2_id

    def test_ids_filtered_on_relationship(self, School, Student):
        assert Student.__expose_id__ is False
        assert School.__expose_id__ is True

        schools = School.serialize(
            to_return=['id', 'classrooms.teacher.students.id'],
            filter_by={
                'classrooms.teacher.students.id': self.student1['id']
            },
            filter_ids=True
        )
        assert len(schools) == 1
        assert schools[0] == {'id': self.school_id}

        schools = School.serialize(
            to_return=['id', 'classrooms.teacher.students.id'],
            filter_by={
                'classrooms.teacher.students.id': self.student1['id']
            },
            filter_ids=False
        )
        assert 'id' in schools[0]
        assert reduce(
            lambda o, key:
            o[0].get(key, False) if isinstance(o, list) else o.get(key, False),
            ['classrooms', 'teacher', 'students', 'id'],
            schools
        )

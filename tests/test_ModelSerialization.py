import pytest
from sqlalchemy import literal_column as lc, and_
from sqlalchemy.orm import sessionmaker
from painless_sqlalchemy.BaseModel import engine


class TestModelSerialization:

    @classmethod
    @pytest.fixture(scope='class', autouse=True)
    def setup(cls, Student, Teacher):
        student1 = Student(name='foo')
        student2 = Student(name='bar', address='baz')
        teacher = Teacher()

        session = sessionmaker(engine)()
        session.add_all([student1, student2, teacher])
        session.commit()

        cls.student1 = {
            'id': student1.id,
            'name': student1.name
        }
        cls.student2_id = student2.id
        cls.teacher_id = teacher.id

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

    def test_filter_by_literal_column(self, Student):
        student = Student.serialize(
            to_return=['id'],
            filter_by=and_(*[
                lc('id') == self.student1['id'],
                lc('name') == self.student1['name']
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

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
        student1 = Student(
            name=fake.name(), phone=fake.phone_number(),
            home_phone=fake.phone_number(), email=fake.email())
        student2 = Student(name=fake.name(), address=fake.address())
        teacher = Teacher(name=fake.name(), students=[student1, student2])
        classroom = Classroom(teacher=teacher)
        school = School(classrooms=[classroom])

        cls.checkin(student1, student2, teacher, classroom, school)

        cls.student1 = cls.persist(student1)
        cls.student2 = cls.persist(student2)
        cls.teacher = cls.persist(teacher)
        cls.classroom = cls.persist(classroom)
        cls.school = cls.persist(school)

    def test_serialize(self, Teacher):
        teacher = Teacher.serialize(
            to_return=['id'],
            filter_by={'id': self.teacher.id},
            suppress=False
        )
        assert len(teacher) == 1
        assert teacher[0]['id'] == self.teacher.id

    def test_filter_by_ref_column(self, Student):
        student = Student.serialize(
            to_return=['id'],
            filter_by=and_(*[
                ref('id') == self.student1.id,
                ref('name') == self.student1.name
            ]),
            suppress=False
        )
        assert len(student) == 1
        assert student[0]['id'] == self.student1.id

    def test_skip_nones(self, Student):
        student = Student.serialize(
            to_return=['id', 'name', 'address'],
            filter_by={
                'id': self.student2.id,
                'address': None
            },
            skip_nones=True,
            suppress=False
        )
        assert len(student) == 1
        assert student[0]['id'] == self.student2.id

    def test_primary_keys_filtered_on_relationship(self, School, Student):
        assert Student.id.primary_key is True
        assert Student.id.info.get('exposed', False) is False
        assert School.id.primary_key is True
        assert School.id.info.get('exposed', False) is True

        schools = School.serialize(
            to_return=['id', 'classrooms.teacher.students.id'],
            filter_by={'classrooms.teacher.students.id': self.student1.id},
            suppress=True
        )
        assert len(schools) == 1
        assert schools[0] == {'id': self.school.id}

        schools = School.serialize(
            to_return=['id', 'classrooms.teacher.students.id'],
            filter_by={'classrooms.teacher.students.id': self.student1.id},
            suppress=False
        )
        assert 'id' in schools[0]
        assert 'classrooms.teacher.students.id' in flatten_dict(schools)

    def test_serialize_map_column_dict(self, Student):
        student = Student.serialize(
            to_return=['contact_info.*'],
            filter_by={'id': self.student1.id}
        )
        assert len(student) == 1
        assert student[0] == {
            'contact_info': {
                'phone': self.student1.phone,
                'home_phone': self.student1.home_phone,
                'email': self.student1.email
            }
        }

    def test_serialize_map_column_list(self, Student):
        student = Student.serialize(
            to_return=['phone_numbers'],
            filter_by={'id': self.student1.id}
        )
        assert len(student) == 1
        assert student[0] == {
            'phone_numbers': [self.student1.phone, self.student1.home_phone]
        }

    def test_serialize_map_column_dict_subset(self, Student):
        student = Student.serialize(
            to_return=['contact_info.phone'],
            filter_by={'id': self.student1.id}
        )
        assert len(student) == 1
        assert student[0] == {
            'contact_info': {
                'phone': self.student1.phone
            }
        }

    def test_to_return_shorthand(self, Student):
        student = Student.serialize(
            to_return=['teachers(id,classroom_id)'],
            filter_by={'id': self.student1.id},
            suppress=False
        )
        assert len(student) == 1
        assert student[0] == {
            'teachers': [{
                'id': self.teacher.id,
                'classroom_id': self.teacher.classroom_id
            }]
        }

    def test_default_serialization(self, Teacher):
        teacher = Teacher.serialize(
            filter_by={'id': self.teacher.id},
            suppress=False
        )
        assert len(teacher) == 1
        assert set(teacher[0].keys()) == set(Teacher.default_serialization)

    def test_default_serialization_relationship(self, Classroom, Teacher):
        classroom = Classroom.serialize(
            to_return=['teacher.*'],
            filter_by={'id': self.classroom.id},
            suppress=False
        )
        assert len(classroom) == 1
        assert set(
            classroom[0]['teacher'].keys()
        ) == set(Teacher.default_serialization)

    def test_to_return_duplicate_exception(self, School):
        with pytest.raises(AssertionError) as e:
            School.serialize(to_return=['id', 'id'])
        assert e.value.args == (['id', 'id'],)

    def test_not_exposed_foreign_key(self, Teacher):
        teacher = Teacher.serialize(
            to_return=['name', 'classroom_id'],
            filter_by={'id': self.teacher.id},
            suppress=True
        )
        assert len(teacher) == 1
        assert 'name' in teacher[0]
        assert 'classroom_id' not in teacher[0]

    def test_exposed_foreign_key(self, Classroom):
        classroom = Classroom.serialize(
            to_return=['school_id'],
            filter_by={'id': self.classroom.id},
            suppress=True
        )
        assert len(classroom) == 1
        assert classroom[0]['school_id'] == self.school.id

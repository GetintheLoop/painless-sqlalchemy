import pytest
from sqlalchemy import and_, or_, func, case, exists
from sqlalchemy.dialects.postgresql import INTERVAL
from sqlalchemy.orm import outerjoin
from faker import Faker
from painless_sqlalchemy.elements.ColumnReference import ref
from tests.helper.AbstractDatabaseTest import AbstractDatabaseTest

fake = Faker()


class TestModelFilter(AbstractDatabaseTest):

    @classmethod
    @pytest.fixture(scope='class', autouse=True)
    def setup_class(cls, School, Classroom, Teacher, Student):
        super(TestModelFilter, cls).setup_class()
        student1 = Student(name=fake.name())
        student2 = Student(name=fake.name(), address=fake.address())
        student3 = Student(name=fake.name(), address=fake.address())

        teacher1 = Teacher(name=fake.name(), students=[student1, student2])
        teacher2 = Teacher(name=fake.name())
        classroom1 = Classroom(teacher=teacher1)
        classroom2 = Classroom(teacher=teacher2)
        school = School(classrooms=[classroom1, classroom2])

        cls.checkin(
            student1, student2, student3,
            teacher1, teacher2,
            classroom1, classroom2,
            school
        )

        cls.student1 = cls.persist(student1)
        cls.student2 = cls.persist(student2)
        cls.student3 = cls.persist(student3)
        cls.teacher1 = cls.persist(teacher1)
        cls.teacher2 = cls.persist(teacher2)
        cls.classroom1 = cls.persist(classroom1)
        cls.school = cls.persist(school)

    def test_filter_by_id(self, Teacher):
        assert Teacher.filter({
            'id': self.teacher1.id
        }).one().id == self.teacher1.id

    def test_filter_by_many_to_many_relationship(self, Teacher):
        assert Teacher.filter({
            'students.name': self.student1.name
        }).one().id == self.teacher1.id

    def test_filter_by_one_to_one_relationship(self, Classroom):
        assert Classroom.filter({
            'teacher.id': self.teacher1.id
        }).one().id == self.classroom1.id

    def test_filter_by_foreign_key(self, Teacher):
        assert Teacher.filter({
            'classroom_id': self.classroom1.id
        }).one().id == self.teacher1.id

    def test_filter_by_nested_relationship(self, School):
        assert School.filter({
            'classrooms.teacher.id': self.teacher1.id
        }).one().id == self.school.id

    def test_filter_one_to_many_relationship(self, School):
        assert School.filter({
            'classrooms.id': self.classroom1.id
        }).one().id == self.school.id

    def test_filter_many_to_one_relationship(self, Classroom):
        classrooms = Classroom.filter({
            'school.id': self.school.id
        }).all()
        assert len(classrooms) == 2

    def test_filter_to_one_relationship_multiple_columns(self, Classroom):
        assert Classroom.filter({
            'teacher.id': self.teacher1.id,
            'teacher.name': self.teacher1.name
        }).one().id == self.classroom1.id

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

    def test_filter_list_single_value(self, Student):
        assert Student.filter({
            'id': [self.student1.id]
        }).one().id == self.student1.id

    def test_filter_list_is_or_query_for_column(self, Student):
        assert len(Student.filter({
            'id': [self.student1.id, self.student2.id]
        }).all()) == 2

    def test_filter_list_is_or_query_for_relationship_to_one(self, Classroom):
        assert len(Classroom.filter({
            'teacher.id': [self.teacher1.id, self.teacher2.id]
        }).all()) == 2

    def test_filter_list_is_and_query_for_relationship_to_many(self, Teacher):
        assert Teacher.filter({
            'students.id': [self.student1.id, self.student2.id]
        }).first() is not None
        self.unlink(student=self.student2.id, teacher=self.teacher1.id)
        assert Teacher.filter({
            'students.id': [self.student1.id, self.student2.id]
        }).first() is None

        # revert
        self.link(student=self.student2.id, teacher=self.teacher1.id)

    def test_filter_by_empty_list(self, Student):
        assert Student.filter({'id': []}).first() is None

    def test_filter_by_empty_list_relationship_to_one(self, Teacher):
        assert Teacher.filter({
            'id': self.teacher1.id,
            'classroom.id': []
        }).first() is None

    def test_filter_by_empty_list_relationship_to_many(self, Teacher):
        assert Teacher.filter({
            'id': self.teacher1.id,
            'students.id': []
        }).one().id == self.teacher1.id

    def test_filter_ref_in(self, Student):
        assert Student.filter(
            ref('id').in_([self.student1.id, self.student2.id])
        ).first() is not None

    def test_filter_ref_func(self, Student):
        assert Student.filter(
            ref('created') <= func.now()
        ).first() is not None

    def test_filter_ref_case(self, Student):
        assert len(Student.filter(
            case([(
                ref('created') <=
                func.now() - func.cast('2 YEARS', INTERVAL),
                'senior'
            ), (
                ref('created') <=
                func.now() - func.cast('1 YEAR', INTERVAL),
                'junior'
            )], else_='freshman') == 'freshman'
        ).all()) == 3

    def test_filter_ref_select(self, Teacher, Student, teacher_to_student):
        teacher = Teacher.filter(
            exists([1]).select_from(
                outerjoin(Student, teacher_to_student)
            ).where(
                and_(
                    Student.name == self.student1.name,
                    teacher_to_student.c.teacher_id == Teacher.id
                )
            ).correlate_except(Student)
        ).all()
        assert len(teacher) == 1
        assert self.get(teacher, 'id', self.teacher1.id) is not None

    def test_filter_ref(self, Student):
        assert Student.filter(
            ref('id') == self.student1.id
        ).one().id == self.student1.id

    def test_filter_ref_to_many_relationship(self, Teacher):
        assert Teacher.filter(
            ref('students.id') == self.student1.id
        ).one().id == self.teacher1.id

    def test_filter_ref_and_condition(self, Student):
        student = Student.filter(
            and_(
                ref('id') == self.student1.id,
                ref('name') == self.student1.name
            )
        ).one()
        assert student.id == self.student1.id

    def test_filter_ref_concurrent_and_conditions(self, Teacher):
        assert Teacher.filter(
            or_(
                and_(
                    ref('students.id') == self.student1.id,
                    ref('students.name') == self.student1.name
                ),
                and_(
                    ref('students.id') == self.student2.id,
                    ref('students.name') == self.student2.name
                )
            )
        ).one().id == self.teacher1.id

    def test_no_grouping(self, Teacher):
        query = Teacher.filter()
        assert query._group_by is False

    def test_no_grouping_to_one_single_relationship(self, Teacher):
        query = Teacher.filter({"classroom.id": [1, 2]})
        assert query._group_by is False

    def test_no_grouping_to_one_multiple_relationships(self, Teacher):
        query = Teacher.filter({
            "classroom.id": [1, 2],
            "classroom.school.id": [1, 2]
        })
        assert query._group_by is False

    def test_id_grouping_to_many_single_relationship(self, Teacher):
        query = Teacher.filter({"students.id": [1, 2]})
        assert query._group_by == [Teacher.id]

    def test_id_grouping_to_many_multiple_relationships(self, Teacher):
        query = Teacher.filter({
            "students.id": [1, 2],
            "students.name": [fake.name(), fake.name()]
        })
        assert query._group_by == [Teacher.id]

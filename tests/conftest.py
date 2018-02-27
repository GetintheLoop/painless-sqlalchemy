import warnings
import pytest
import sqlalchemy
from sqlalchemy import (
    Column, String, Table, ForeignKey, Integer, func, DateTime, bindparam)
from sqlalchemy.orm import relationship, column_property
from painless_sqlalchemy import Painless
from painless_sqlalchemy.elements.MapColumn import MapColumn

table_hierarchy = [
    'student', 'teacher', 'classroom', 'school'
]

db = Painless('postgresql://postgres:password@localhost:5432/painless_tmp')

engine = db.engine
session = db.session


@pytest.fixture(scope='session')
def School():
    class School(db.Model):
        __tablename__ = 'school'
        id = Column(Integer, primary_key=True, info={"exposed": True})

        classrooms = relationship(
            'Classroom',
            primaryjoin='School.id == Classroom.school_id'
        )

    return School


@pytest.fixture(scope='session')
def Classroom(School):
    class Classroom(db.Model):
        __tablename__ = 'classroom'

        school_id = Column(Integer, ForeignKey(School.id))
        school = relationship(
            School, foreign_keys=school_id,
            primaryjoin="School.id == Classroom.school_id"
        )

        teacher = relationship(
            "Teacher",
            primaryjoin="Classroom.id == Teacher.classroom_id",
            uselist=False
        )

    return Classroom


@pytest.fixture(scope='session')
def Teacher(Classroom):
    class Teacher(db.Model):
        __tablename__ = 'teacher'

        name = Column(String(64), index=True, nullable=False)

        classroom_id = Column(Integer, ForeignKey(Classroom.id), unique=True)
        classroom = relationship(
            Classroom, foreign_keys=classroom_id,
            primaryjoin="Classroom.id == Teacher.classroom_id"
        )
        students = relationship(
            'Student',
            secondary='teacher_to_student',
            primaryjoin='Teacher.id == teacher_to_student.c.teacher_id',
            secondaryjoin='teacher_to_student.c.student_id == Student.id'
        )

    return Teacher


@pytest.fixture(scope='session')
def Student(Teacher):
    class Student(db.Model):
        __tablename__ = 'student'

        id = Column(Integer, primary_key=True)
        contextual_id = column_property(
            func.md5(
                bindparam('context', value='', type_=String) +
                func.cast(id, String)
            )
        )
        name = Column(String(64), index=True, nullable=False)
        address = Column(String(128), index=False, nullable=True)
        phone = Column(String(35), nullable=True)
        home_phone = Column(String(35), nullable=True)
        email = Column(String(64), nullable=True)

        created = Column(DateTime, server_default='now()')

        guardian_number = MapColumn('home_phone')
        phone_numbers = MapColumn(['phone', 'home_phone'])

        contact_info = MapColumn({
            'phone': 'phone',
            'home_phone': 'home_phone',
            'email': 'email'
        })

        teachers = relationship(
            "Teacher", secondary='teacher_to_student',
            primaryjoin="Student.id == teacher_to_student.c.student_id",
            secondaryjoin="teacher_to_student.c.teacher_id == Teacher.id"
        )

        first_name = column_property(
            func.split_part(func.trim(name), " ", 1)
        )

    return Student


@pytest.fixture(scope='session')
def teacher_to_student(Teacher, Student):
    # teacher_to_student linkage table
    return Table(
        'teacher_to_student',
        db.Model.metadata,
        Column('teacher_id', ForeignKey(Teacher.id, ondelete='CASCADE'),
               primary_key=True),
        Column('student_id', ForeignKey(Student.id, ondelete='CASCADE'),
               primary_key=True)
    )


@pytest.fixture(scope='session', autouse=True)
def init_db(School, Classroom, Teacher, Student, teacher_to_student):
    recreate_db()

    from tests.helper.AbstractDatabaseTest import batch_testing
    if not batch_testing:  # pragma: no cover
        warnings.warn(
            "Running in Check Mode. This is expensive and should "
            "not be used to execute the whole test suite!"
        )


def recreate_db():
    engine.dispose()
    session.close()

    uri, db_name = engine.url.__str__().rsplit("/", 1)

    _engine = sqlalchemy.engine.create_engine(uri + "/postgres")
    conn = _engine.connect()
    conn.execute(
        "SELECT pg_terminate_backend(pid) "
        "FROM pg_stat_activity WHERE datname = '%s';" % db_name
    )
    conn.execute("commit")
    conn.execute('DROP DATABASE IF EXISTS "%s";' % db_name)
    conn.execute("commit")
    conn.execute('CREATE DATABASE "%s";' % db_name)
    conn.close()

    db.Model.metadata.drop_all(engine)
    db.Model.metadata.create_all(engine)


def pytest_itemcollected(item):
    """ Format output as TestClass: TestName """
    par = item.parent.obj
    node = item.obj
    pref = par.__doc__.strip() if par.__doc__ else par.__class__.__name__
    suf = node.__doc__.strip() if node.__doc__ else node.__name__
    item._nodeid = ': '.join((pref, suf))

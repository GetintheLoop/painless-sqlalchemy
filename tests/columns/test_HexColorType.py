import pytest
from faker import Faker
from tests.AbstractTest import AbstractTest

fake = Faker()


class TestHexColorType(AbstractTest):

    @classmethod
    @pytest.fixture(scope='class', autouse=True)
    def setup_class(cls, School, Classroom):
        super(TestHexColorType, cls).setup_class()
        school = School()
        classroom = Classroom(school=school)

        cls.checkin(school, classroom)

        cls.classroom = cls.persist(classroom)

    def test_storage(self, Classroom):
        color = "#007700"
        classroom = Classroom.filter().one()
        classroom.update(color=color).save()
        assert classroom.color == color
        classroom = Classroom.filter().one()
        assert classroom.color == color
        classroom.update(color=None).save()

    def test_invalid(self, Classroom):
        classroom = Classroom.filter().one()
        with pytest.raises(ValueError):
            classroom.update(color="#777").save()

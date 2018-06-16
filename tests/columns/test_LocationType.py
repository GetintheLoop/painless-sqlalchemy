import pytest
from faker import Faker
from tests.AbstractTest import AbstractTest

fake = Faker()


class TestLocationType(AbstractTest):

    @classmethod
    @pytest.fixture(scope='class', autouse=True)
    def setup_class(cls, School):
        super(TestLocationType, cls).setup_class()
        school = School()

        cls.checkin(school)

        cls.school = cls.persist(school)

    def test_storage(self, School):
        location = (0, 0)
        school = School.filter().one()
        school.update(location=location).save()
        assert school.location == location
        school = School.filter().one()
        assert school.location == location
        school.update(location=None).save()

    def test_invalid_location(self, School):
        school = School.filter().one()
        with pytest.raises(ValueError) as e:
            school.update(location=[180, 90]).save()
        assert e.value.__str__().startswith("Invalid location given for attr ")

    def test_invalid_type(self, School):
        school = School.filter().one()
        with pytest.raises(ValueError) as e:
            school.update(location="invalid").save()
        assert e.value.__str__().startswith("Invalid location given for attr ")

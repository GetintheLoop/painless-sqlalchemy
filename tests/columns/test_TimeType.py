import pytest
from faker import Faker
from tests.AbstractTest import AbstractTest

fake = Faker()


class TestTimeType(AbstractTest):

    @classmethod
    @pytest.fixture(scope='class', autouse=True)
    def setup_class(cls, School):
        super(TestTimeType, cls).setup_class()
        school = School()

        cls.checkin(school)

        cls.school = cls.persist(school)

    def test_storage(self, School):
        time = "12:00"
        school = School.filter().one()
        school.update(opening=time).save()
        assert school.opening == time
        school = School.filter().one()
        assert school.opening == time
        school.update(opening=None).save()

    def test_invalid_format(self, School):
        school = School.filter().one()
        with pytest.raises(ValueError) as e:
            school.update(opening="ab:cd:ef").save()
        assert e.value.__str__().startswith("Invalid format for attr ")

    def test_not_integer(self, School):
        school = School.filter().one()
        with pytest.raises(ValueError) as e:
            school.update(opening="ab:cd").save()
        assert e.value.__str__().startswith("Not integer for attr ")

    def test_invalid_time_range(self, School):
        school = School.filter().one()
        with pytest.raises(ValueError) as e:
            school.update(opening="24:00").save()
        assert e.value.__str__().startswith("Invalid range for attr ")

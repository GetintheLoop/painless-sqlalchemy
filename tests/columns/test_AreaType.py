import pytest
from faker import Faker
from tests.AbstractTest import AbstractTest

fake = Faker()


class TestAreaType(AbstractTest):

    @classmethod
    @pytest.fixture(scope='class', autouse=True)
    def setup_class(cls, School):
        super(TestAreaType, cls).setup_class()
        school = School()

        cls.checkin(school)

        cls.school = cls.persist(school)

    def test_storage(self, School):
        area = [(0, 0), (0, 1), (1, 1), (1, 0), (0, 0)]
        school = School.filter().one()
        school.update(area=area).save()
        assert school.area == area
        school = School.filter().one()
        assert school.area == area
        school.update(area=None).save()

    def test_invalid_poly(self, School):
        school = School.filter().one()
        with pytest.raises(ValueError) as e:
            school.update(area=[123, 456]).save()
        assert e.value.__str__().startswith("Invalid Polygon Entry given for attr ")
        with pytest.raises(ValueError) as e:
            school.update(area="invalid").save()
        assert e.value.__str__().startswith("Invalid Polygon Entry given for attr ")

    def test_open_poly(self, School):
        school = School.filter().one()
        with pytest.raises(ValueError) as e:
            school.update(area=[[0, 0], [1, 0], [1, 1], [0, 1]]).save()
        assert e.value.__str__().startswith("Open Polygon given for attr ")

    def test_degenerate_poly(self, School):
        school = School.filter().one()
        with pytest.raises(ValueError) as e:
            school.update(area=[[0, 0], [1, 0], [0, 0]]).save()
        assert e.value.__str__().startswith("Degenerate Polygon given for attr ")

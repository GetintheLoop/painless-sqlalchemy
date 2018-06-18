import pytest
from faker import Faker
from tests.AbstractTest import AbstractTest

fake = Faker()


class TestCIText(AbstractTest):

    @classmethod
    @pytest.fixture(scope='class', autouse=True)
    def setup_class(cls, Student):
        super(TestCIText, cls).setup_class()
        cls.email_upper = fake.email().upper()
        student = Student(name=fake.name(), email=cls.email_upper)

        cls.checkin(student)

        cls.student = cls.persist(student)

    def test_always_lower(self, Student):
        student = Student.filter().one()
        assert student.email.lower() == student.email
        student.update(email=self.email_upper).save()
        assert self.email_upper != student.email
        assert student.email == student.email.lower()

    def test_query_by_upper(self, Student):
        student = Student.filter({"email": self.email_upper}).one()
        assert student.email == student.email.lower()

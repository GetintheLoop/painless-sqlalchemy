from faker import Faker
from tests.helper.AbstractDatabaseTest import AbstractDatabaseTest

fake = Faker()


class TestModelFilter(AbstractDatabaseTest):

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
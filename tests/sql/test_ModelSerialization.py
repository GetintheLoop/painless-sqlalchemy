from faker import Faker
from tests.helper.AbstractDatabaseTest import AbstractDatabaseTest

fake = Faker()


class TestModelSerialization(AbstractDatabaseTest):

    def test_id_ordering_is_default(self, Teacher):
        query, json_to_return = Teacher._ser()
        assert (
            "OVER (ORDER BY teacher.id)"
            in query._order_by[0].table.__str__()
        )

    def test_id_ordering_fallback_created(self, Teacher):
        query, json_to_return = Teacher._ser(
            order_by=(Teacher.name, Teacher.classroom_id)
        )
        assert (
            "OVER (ORDER BY teacher.name, teacher.classroom_id, teacher.id)"
            in query._order_by[0].table.__str__()
        )

    def test_id_ordering_fallback_exists(self, Teacher):
        query, json_to_return = Teacher._ser(
            order_by=(Teacher.name, Teacher.id)
        )
        assert (
            "OVER (ORDER BY teacher.name, teacher.id)"
            in query._order_by[0].table.__str__()
        )

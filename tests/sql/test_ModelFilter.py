from tests.helper.AbstractDatabaseTest import AbstractDatabaseTest


class TestModelFilter(AbstractDatabaseTest):

    def test_single_group_for_multi_to_many_rel_list_filter(self, Teacher):
        query = Teacher.filter({
            "students.id": [1, 2],
            "students.name": ["a", "b"]
        })
        assert query._group_by == [Teacher.id]

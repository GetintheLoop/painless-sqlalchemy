from sqlalchemy import DateTime, Column, func
from painless_sqlalchemy.util.TableUtil import many_to_many


class TestTableUtil(object):

    def test_many_to_many(self):
        result = many_to_many("table_a", "table_b", extra_cols=[
            Column(
                'created', DateTime(timezone=True), nullable=False,
                server_default=func.current_timestamp()
            )
        ])
        assert result.name == "table_a_to_table_b"

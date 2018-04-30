from painless_sqlalchemy.util.testing.AbstractDatabaseTest import (
    AbstractDatabaseTest)
from tests.conftest import db, recreate_db, table_hierarchy


class AbstractTest(AbstractDatabaseTest):
    _meta = {
        "db": db,
        "recreate_db": recreate_db,
        "table_hierarchy": table_hierarchy
    }

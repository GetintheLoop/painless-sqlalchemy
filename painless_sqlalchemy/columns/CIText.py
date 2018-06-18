from sqlalchemy.sql.sqltypes import Concatenable
from sqlalchemy.sql.type_api import UserDefinedType
from painless_sqlalchemy.columns.AbstractType import AbstractType


class CIText(Concatenable, UserDefinedType, AbstractType):
    """ CIText with option to enforce lower case. """

    python_type = str
    postgres_type = "CITEXT"

    def __init__(self, length, force_lower):
        self.length = length
        self.force_lower = force_lower

    def get_col_spec(self):
        return self.postgres_type

    def bind_processor(self, dialect):
        default = super(CIText, self).bind_processor(dialect)

        def process(bindvalue):
            result = default(bindvalue) if callable(default) else bindvalue  # pylint: disable=not-callable
            assert result is None or len(result) <= self.length
            return None if result is None else (result.lower() if self.force_lower else result)
        return process

    def result_processor(self, dialect, coltype):
        default = super(CIText, self).result_processor(dialect, coltype)

        def process(bindvalue):
            result = default(bindvalue) if callable(default) else bindvalue  # pylint: disable=not-callable
            assert result is None or len(result) <= self.length
            return None if result is None else (result.lower() if self.force_lower else result)
        return process

    def validator(self, attr_name):
        def validate(target, value, oldvalue, initiator):  # pylint: disable=unused-argument
            return True
        return validate

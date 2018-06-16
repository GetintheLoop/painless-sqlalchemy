import datetime as dt
from sqlalchemy.sql.sqltypes import Time
from painless_sqlalchemy.columns.AbstractType import AbstractType


class TimeType(Time, AbstractType):
    """ Time as HH:MM (24-hour) """

    def result_processor(self, dialect, coltype):
        def process(value):
            return None if value is None else "%02d:%02d" % (value.hour, value.minute)
        return process

    def bind_processor(self, dialect):
        def process(bindvalue):
            return None if bindvalue is None else dt.time(*map(int, bindvalue.split(":")), 0)
        return process

    def validator(self, attr_name):
        def validate(target, value, oldvalue, initiator):  # pylint: disable=unused-argument
            if value is not None:
                value = value.split(":")
                if len(value) != 2 or any(len(v) != 2 for v in value):
                    raise ValueError("Invalid format for attr \"%s\"." % attr_name)
                try:
                    hour = int(value[0])
                    minute = int(value[1])
                except ValueError:
                    raise ValueError("Not integer for attr \"%s\"." % attr_name)
                if not ((0 <= hour <= 23) and (0 <= minute <= 59)):
                    raise ValueError("Invalid range for attr \"%s\"." % attr_name)
            return True
        return validate

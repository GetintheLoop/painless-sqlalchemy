import re
from sqlalchemy import Integer
from painless_sqlalchemy.columns.AbstractType import AbstractType

HEX_COLOR_REGEX = re.compile(r'^#[0-9a-fA-F]{6}$')


class HexColorType(Integer, AbstractType):
    """ Hex Color """

    def result_processor(self, dialect, coltype):
        def process(value):
            return None if value is None else '#{0:06X}'.format(value)
        return process

    def bind_processor(self, dialect):
        def process(bindvalue):
            return None if bindvalue is None else int(bindvalue[1:], 16)
        return process

    def validator(self, attr_name):
        def validate(target, value, oldvalue, initiator):  # pylint: disable=unused-argument
            if value is not None:
                if not HEX_COLOR_REGEX.match(value):
                    raise ValueError("Invalid format for attr \"%s\"." % attr_name)
            return True
        return validate

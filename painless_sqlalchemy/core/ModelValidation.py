from sqlalchemy import event
from sqlalchemy import inspect
from painless_sqlalchemy.columns.AbstractType import AbstractType
from painless_sqlalchemy.core.ModelRaw import ModelRaw


class ModelValidation(ModelRaw):
    """ Validation on Assignment for Custom Column Types """

    __abstract__ = True

    _initialized_classes = []

    def __new__(cls, *args, **kwargs):  # pylint: disable=unused-argument
        if cls not in cls._initialized_classes:  # init exactly once per Model class
            cls._initialized_classes.append(cls)
            for col_name in inspect(cls).column_attrs.keys():
                attr = getattr(cls, col_name)
                if isinstance(attr.type, AbstractType):
                    event.listen(attr, "set", attr.type.validator(col_name))
        return super(ModelValidation, cls).__new__(cls)

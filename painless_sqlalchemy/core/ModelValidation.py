from sqlalchemy import event, String
from sqlalchemy import inspect
from painless_sqlalchemy.columns.AbstractType import AbstractType
from painless_sqlalchemy.columns.CIText import CIText
from painless_sqlalchemy.core.ModelRaw import ModelRaw


class ModelValidation(ModelRaw):
    """ Validate Column immediately on assignment """

    __abstract__ = True

    _validated_classes = []

    def __new__(cls, *args, **kwargs):  # pylint: disable=unused-argument
        if cls not in cls._validated_classes:  # init exactly once per class
            cls._validated_classes.append(cls)
            cls.create_validators()
        return super(ModelValidation, cls).__new__(cls)

    @classmethod
    def create_validators(cls):
        for col_name in inspect(cls).column_attrs.keys():
            attr = getattr(cls, col_name)
            class_ = attr.type.__class__
            if isinstance(attr.type, AbstractType):
                event.listen(attr, "set", attr.type.validator(col_name))
            if class_ in (CIText, String):
                event.listen(attr, "set", cls._string_length_validator(col_name, attr.type.length))
            if getattr(attr, "nullable", True) is False:
                event.listen(attr, "set", cls._non_nullable_validator(col_name))

    @staticmethod
    def _non_nullable_validator(attr_name):
        def validate(target, value, oldvalue, initiator):  # pylint: disable=unused-argument
            if value is None:
                raise ValueError("Null value not allowed for attr \"%s\" in %s." % (attr_name, target.__class__))
        return validate

    @staticmethod
    def _string_length_validator(attr_name, length):
        def validate(target, value, oldvalue, initiator):  # pylint: disable=unused-argument
            if value is not None and length is not None and len(value) > length:
                raise ValueError(
                    "String too long (max %s) for attr \"%s\" in %s." %
                    (length, attr_name, target.__class__)
                )
        return validate

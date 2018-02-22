from collections import namedtuple
from sqlalchemy.orm import class_mapper, ColumnProperty
from painless_sqlalchemy.core.Model import Model


class AbstractExtendedTest(object):
    @staticmethod
    def get(list_, key_, value_):
        """
            Find first dict/object in list_ where dict/object[key_] == value_
            - key_ assumed present in all dicts/objects
            - value_ and values are cast to strings before comparison
            :param list_ List of dicts/objects
            :param key_ Key name to use in search
            :param value_ Value of key tp search for
            :return first dict/object if found, otherwise None
        """
        if any(hasattr(o, '__getitem__') for o in list_):
            for o in list_:
                if str(o[key_]) == str(value_):
                    return o
        else:
            for o in list_:
                if str(getattr(o, key_)) == str(value_):
                    return o
        return None

    @staticmethod
    def persist(obj):
        """
            Clone model top-level fields into SQLAlchemy-independent object
            :param obj: SQLAlchemy object
            :return copy of object that is session independent
        """
        # todo: only use fields that are loaded (prevent additional queries)
        assert isinstance(obj, Model)
        keys = [
            prop.key for prop in class_mapper(obj.__class__).iterate_properties
            if isinstance(prop, ColumnProperty)
        ]
        return namedtuple(obj.__class__.__tablename__, ' '.join(keys))(
            **{key: getattr(obj, key) for key in keys}
        )

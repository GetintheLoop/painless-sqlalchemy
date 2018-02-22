from sqlalchemy import inspect
from painless_sqlalchemy.core.Model import Model


class DBIdMixin(object):

    @classmethod
    def extract(cls, *args, **kwargs):
        """
            Extract ids for passed Models recursively
            :param args: Starting Models to extract ids from
            :param kwargs: Pass in ignore=tuple(table name, ...) to skip tables
            :return dict mapping {table name -> tuple of ids}
        """
        ignore = kwargs.get('ignore', set())
        result = {}

        # handle id extraction
        to_ignore = set()
        for arg in args:
            assert isinstance(arg, Model)
            if arg.__table__ is not None:
                name = arg.__table__.name
                to_ignore.add(name)
                if name not in result:
                    result[name] = set()
                assert arg.id is not None
                result[name].add(arg.id)

        ignore = ignore.union(to_ignore)

        # handle relationships
        for arg in args:
            for rel_name in inspect(arg.__class__).relationships.keys():
                rel = getattr(arg.__class__, rel_name)
                name = rel.property.mapper.class_.__table__.name
                if name in ignore:
                    continue
                rel_target = getattr(arg, rel_name)
                if rel_target is None:
                    continue
                if not isinstance(rel_target, list):
                    rel_target = [rel_target]
                if not len(rel_target):
                    continue
                for name, ids in cls.extract(
                    *rel_target,
                    **{"ignore": ignore}
                ).items():
                    if name not in result:
                        result[name] = set()
                    result[name] = result[name].union(ids)
        return {
            k: tuple(set(v)) for k, v in result.items()
        }

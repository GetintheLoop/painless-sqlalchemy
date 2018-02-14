from sqlalchemy.orm import RelationshipProperty
from painless_sqlalchemy.ModelAction import ModelAction
from painless_sqlalchemy.column.MapColumn import MapColumn


class ModelQuery(ModelAction):
    """ ORM Query Abstraction """

    @classmethod
    def _iterate_path(cls, path):
        """ Iterate over relationship path
            - For MapColumn the final column is string or list
            :return generator (
                (current class, relationship column, bool last iteration),
                ..., (final class, final column, bool last iteration)
            )
        """
        class_ = cls  # hold last class
        cur = cls
        for attr in path:
            if isinstance(cur, dict):
                cur = cur[attr]
            else:
                class_ = cur
                cur = getattr(cur, attr)
            property_ = getattr(cur, 'property', None)
            if isinstance(property_, RelationshipProperty):
                yield class_, cur, False
                cur = property_.mapper.class_
        yield class_, cur, True

    @classmethod
    def _get_column(cls, path):
        """ Get column from relationship path
            - Resolves final target for MapColumn
            - Can return list of columns for MapColumn
            :return column or list of columns
        """
        # get last element from iterator
        class_, cur = next(
            (class_, cur) for class_, cur, last in
            cls._iterate_path(path) if last
        )
        # handle MapColumn direct mappings
        if isinstance(cur, MapColumn):
            assert None in cur and len(cur) == 1
            cur = cur[None]
        # handle MapColumn map targets
        if isinstance(cur, str):
            assert issubclass(class_, ModelQuery)
            cur = class_._get_column(cur.split("."))
        if isinstance(cur, list):
            assert all(isinstance(e, str) for e in cur)
            assert issubclass(class_, ModelQuery)
            # todo: this should merge list of lists (!)
            cur = [class_._get_column(e.split(".")) for e in cur]
        return cur

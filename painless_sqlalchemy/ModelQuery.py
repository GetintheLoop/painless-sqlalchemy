from sqlalchemy.orm import RelationshipProperty
from painless_sqlalchemy.ModelAction import ModelAction


class ModelQuery(ModelAction):
    """ ORM Query Abstraction """

    @classmethod
    def _iterate_path(cls, path):
        """ Iterate over relationship path

            Final column can be string or list in case of MapColumn.
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

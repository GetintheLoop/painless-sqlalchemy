from sqlalchemy.orm import RelationshipProperty
from painless_sqlalchemy.ModelAction import ModelAction
from painless_sqlalchemy.column.MapColumn import MapColumn


class ModelQuery(ModelAction):
    """ ORM Query Abstraction """

    @classmethod
    def _iterate_path(cls, path):
        """
            Iterate over relationship path
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
        """
            Get column from relationship path
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

    @classmethod
    def _get_joined_attr(cls, query, path):
        """
            Join path relationships to query
            - Ensures that the join exist or create it
            - Information about existing joins stored in "__aliases"
            - Creates unique join if there is *_to_many relationship and "and"
            is used. Relies on "and_info" meta
            Note: query attributes persist across .join, .filter, etc
            :return (modified query, final alias.column)
        """
        # known joined aliases for this query
        joined_aliases = getattr(query, '__aliases', {})
        setattr(query, '__aliases', joined_aliases)

        # prep data
        alias = cls  # current alias for the joined model
        alias_name = "alias"
        unique_join = False  # true if the join is already unique

        # iterate over path and join classes when necessary
        for attr in path[:-1]:
            alias_name += "." + attr
            rel = getattr(alias, attr)
            if not unique_join and rel.property.uselist:
                # make join unique if and_ used since *_to_many
                and_info = getattr(query, 'and_info')
                # create and join the "and_" hierarchy
                if and_info['depth'] > -1:
                    and_path = and_info['counts'][:and_info['depth'] + 1]
                    alias_name += ".%s" % "-".join(str(e) for e in and_path)
                unique_join = True
            if alias_name not in joined_aliases:
                # create a join alias
                alias = aliased(rel, name=alias_name)
                query = query.outerjoin(alias, rel)
                joined_aliases[alias_name] = alias
            else:
                alias = joined_aliases[alias_name]

        return query, getattr(alias, path[-1])
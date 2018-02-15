from sqlalchemy import inspect
from sqlalchemy.orm import load_only, undefer, joinedload
from sqlalchemy.sql.elements import Label
from painless_sqlalchemy.ModelFilter import ModelFilter


class ModelSerialization(ModelFilter):
    """ Query Serialization Logic """

    @classmethod
    def eager_load(cls, attributes=None, query=None):
        """
                Alter query to only load provided attributes
                - Attributes are *not* auto expanded
            :param attributes: list of attributes using dot notation
            :param query: query to optimize (optional)
            :return: altered query
        """
        assert isinstance(attributes, list)

        if query is None:
            query = cls.query

        # collect table columns (not relationships)
        all_cols = inspect(cls).column_attrs
        property_cols = [  # this defines a property column
            c.key for c in all_cols
            if any(isinstance(col, Label) for col in c.columns)
        ]
        all_cols = all_cols.keys()
        # extract non-property columns
        real_cols = list(set(all_cols) - set(property_cols))

        # determine which relationships to fetch
        for key in attributes:
            if key not in all_cols:
                path = key.split(".")
                assert len(path) > 1, path
                # Note: Not equivalent to joinedload(*path[:-1])
                jl = joinedload(path[0])
                for e in path[1:-1]:
                    jl = jl.joinedload(e)
                query = query.options(jl.load_only(path[-1]))

        # determine which real columns to load
        to_load = [key for key in attributes if key in real_cols]
        if to_load:
            query = query.options(load_only(*to_load))

        # determine which property columns to load
        to_undefer = [key for key in attributes if key in property_cols]
        if to_undefer:
            for property_col in to_undefer:
                query = query.options(undefer(property_col))

        return query

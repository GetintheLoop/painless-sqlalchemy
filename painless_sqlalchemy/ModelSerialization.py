import re
import functools
from sqlalchemy import inspect
from sqlalchemy.orm import load_only, undefer, joinedload
from sqlalchemy.sql.elements import Label
from painless_sqlalchemy.BaseModel import BaseModel
from painless_sqlalchemy.ModelFilter import ModelFilter
from painless_sqlalchemy.column.MapColumn import MapColumn
from painless_sqlalchemy.util import DictUtil

RE_FIELD_SYNTAX_MATCHER = re.compile(r'([^,()]+?)\(([^()]+?)\)')


class ModelSerialization(ModelFilter):
    """ Query Serialization Logic """

    __abstract__ = True

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

    def as_dict(self, obj, dict_):
        """
                Convert SQLAlchemy object hierarchy into new dict
                - Elements that are not loaded are not returned (!)
            :param obj: object hierarchy
            :param dict_: dict defining target format
            :return: New dict containing extracted data
        """
        if isinstance(obj, MapColumn) and None in obj:
            assert len(obj) == 1
            obj = obj[None]
        if isinstance(obj, str):
            return functools.reduce(
                lambda e, a: getattr(e, a, None),
                obj.split("."),
                self
            )
        if isinstance(obj, list):
            return [self.as_dict(e, dict_) for e in obj]

        result = {}
        if isinstance(obj, dict):
            for k, v in dict_.iteritems():
                assert k in obj
                result[k] = self.as_dict(obj[k], v)
        else:
            assert isinstance(obj, ModelSerialization)
            inspected = inspect(obj.__class__)
            all_cols = inspected.column_attrs  # includes property columns
            rels = inspected.relationships

            # handle MapColumn
            for key in filter(lambda e: e not in obj.__dict__, dict_.keys()):
                map_column = getattr(obj.__class__, key)
                if isinstance(map_column, MapColumn):
                    result[key] = self.as_dict(map_column, dict_[key])

            # only return valid arguments, this is necessary since
            # primary keys can not be deferred and objects could be
            # cached (second could be circumvented with a fresh session)
            for key in filter(lambda e: e in obj.__dict__, dict_.keys()):
                value = obj.__dict__.get(key)
                if key in all_cols:
                    result[key] = value
                elif key in rels:
                    # recursively fetch data from other objects
                    if isinstance(value, list):
                        result[key] = [
                            rel_obj.as_dict(rel_obj, dict_[key])
                            for rel_obj in value
                        ]
                        remap_on = rels[key].remap_on
                        if remap_on is not None:
                            result[key] = {
                                e[remap_on]: e for e in result[key]
                                if remap_on in e
                            }
                    elif isinstance(value, ModelSerialization):
                        result[key] = value.as_dict(value, dict_[key])
                    else:  # if None
                        result[key] = value
        return result

    @staticmethod
    def get_attr_hierarchy(attributes):
        """
            Unflatten attributes list to dict
            - Attributes are *not* auto expanded
            - Attributes expected in dot notation
            return: dict representation
        """
        attr_hierarchy = {}
        for attr in attributes:
            hierarchy = attr.split(".")
            cur_level = attr_hierarchy
            for ele in hierarchy:
                if ele not in cur_level:
                    cur_level[ele] = {}
                cur_level = cur_level[ele]
        return attr_hierarchy

    @classmethod
    def as_list(cls, query, attributes):
        """
            Serialize query results using attributes as template.
            - Only contains fetched relationships from query
            :param query: query to serialize
            :param attributes: attribute list in dot notation
            :return list of serialized query results
        """
        attr_hierarchy = cls.get_attr_hierarchy(attributes)
        return [res.as_dict(res, attr_hierarchy) for res in query]

    @classmethod
    def expand(cls, key):
        """
                Recursively expand given paths
                - support bracket notation e.g. "rel(field1,field2)"
                - support star notation e.g. "rel.*" which uses
                defined default_serialization
                - supports multiple fields e.g. "rel.field1,rel.field2"
                - Handles MapColumns correctly
            :param key: comma separated paths (dot notation)
            :return list of expanded paths (dot notation)
        """
        if "(" in key:  # expand rel(field,...)-syntax
            replaced = -1
            while replaced != 0:
                key, replaced = RE_FIELD_SYNTAX_MATCHER.subn(
                    lambda m: ",".join([
                        "%s.%s" % (m.group(1), e)
                        for e in m.group(2).split(",")
                    ]),
                    key
                )

        result = []
        if "," in key:  # contains multiple keys
            for k in key.split(","):
                result += cls.expand(k)
        else:
            path = key.split(".")
            if path[-1] == "*":  # path ends in relationship
                class_, end = next(
                    (cl, c) for cl, c, last in cls._iterate_path(path[:-1])
                    if last is True
                )
                if isinstance(end, dict):
                    for f in DictUtil.flatten_dict(end):
                        result += cls.expand(key[:-1] + f)
                else:
                    assert issubclass(end, BaseModel)
                    for f in end.default_serialization:
                        result += cls.expand(key[:-1] + f)
            else:  # ordinary field, no expansion needed
                result.append(key)

        return result

    @classmethod
    def get_query_columns(cls, attributes):
        """
            Obtain all required attributes to query for passed attributes
            These might be difference because:
            - MapColumn point to the appropriate column and are not queryable
            - Relationships can require additional fields. Only auto fetched
            for primary keys or foreign key constraints (http://tiny.cc/ccg6fy)
        :return attributes required to query for passed attributes
        """
        result = []
        for field in attributes:
            chain = []
            for class_, attr, last in cls._iterate_path(field.split(".")):
                if last:
                    if isinstance(attr, MapColumn):
                        assert None in attr and len(attr) == 1
                        attr = attr[None]
                    if isinstance(attr, str):  # MapColumn
                        result += [
                            ".".join(chain + attr.split(".")) for attr in
                            class_.get_query_columns([attr])
                        ]
                    elif isinstance(attr, list):  # MapColumn
                        for e in attr:
                            result += [
                                ".".join(chain + e.split(".")) for e in
                                class_.get_query_columns([e])
                            ]
                    else:  # regular column
                        result.append(field)
                else:
                    key = attr.key
                    prop = attr.property
                    target_table = prop.mapper.class_.__table__
                    # check relationships
                    for p in prop.local_remote_pairs:
                        # force fetching of "both sides"
                        if p[0].table == class_.__table__:
                            result.append(".".join(chain + [p[0].name]))
                        if p[1].table == target_table:
                            result.append(".".join(chain + [key, p[1].name]))
                    chain.append(key)
        return result

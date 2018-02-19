import re
import functools
from sqlalchemy import inspect, func
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
    def _eager_load(cls, attributes=None, query=None):
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

    def _as_dict(self, obj, dict_):
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
            return [self._as_dict(e, dict_) for e in obj]

        result = {}
        if isinstance(obj, dict):
            for k, v in dict_.iteritems():
                assert k in obj
                result[k] = self._as_dict(obj[k], v)
        else:
            assert isinstance(obj, ModelSerialization)
            inspected = inspect(obj.__class__)
            all_cols = inspected.column_attrs  # includes property columns
            rels = inspected.relationships

            # handle MapColumn
            for key in filter(lambda e: e not in obj.__dict__, dict_.keys()):
                map_column = getattr(obj.__class__, key)
                if isinstance(map_column, MapColumn):
                    result[key] = self._as_dict(map_column, dict_[key])

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
                            rel_obj._as_dict(rel_obj, dict_[key])
                            for rel_obj in value
                        ]
                        remap_on = rels[key].remap_on
                        if remap_on is not None:
                            result[key] = {
                                e[remap_on]: e for e in result[key]
                                if remap_on in e
                            }
                    elif isinstance(value, ModelSerialization):
                        result[key] = value._as_dict(value, dict_[key])
                    else:  # if None
                        result[key] = value
        return result

    @staticmethod
    def _get_attr_hierarchy(attributes):
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
    def _as_list(cls, query, attributes):
        """
            Serialize query results using attributes as template.
            - Only contains fetched relationships from query
            :param query: query to serialize
            :param attributes: attribute list in dot notation
            :return list of serialized query results
        """
        attr_hierarchy = cls._get_attr_hierarchy(attributes)
        return [res._as_dict(res, attr_hierarchy) for res in query]

    @classmethod
    def _expand(cls, key):
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
                result += cls._expand(k)
        else:
            path = key.split(".")
            if path[-1] == "*":  # path ends in relationship
                class_, end = next(
                    (cl, c) for cl, c, last in cls._iterate_path(path[:-1])
                    if last is True
                )
                if isinstance(end, dict):
                    for f in DictUtil.flatten_dict(end):
                        result += cls._expand(key[:-1] + f)
                else:
                    assert issubclass(end, BaseModel)
                    for f in end.default_serialization:
                        result += cls._expand(key[:-1] + f)
            else:  # ordinary field, no expansion needed
                result.append(key)

        return result

    @classmethod
    def _get_query_columns(cls, attributes):
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
                            class_._get_query_columns([attr])
                        ]
                    elif isinstance(attr, list):  # MapColumn
                        for e in attr:
                            result += [
                                ".".join(chain + e.split(".")) for e in
                                class_._get_query_columns([e])
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

    @classmethod
    def _is_exposed_id(cls, field):
        """
            Check field is exposed, i.e.
            - not white listed id column
            - column referencing not white listed id column
            Uses BaseModel.__expose_id__ for white listing
            :return True iff column is exposed
        """
        path = field.split(".")
        cols = cls._get_column(path)
        if not isinstance(cols, list):
            cols = [cols]
        for col in cols:
            # check for foreign key id reference that is not white listed
            for fk in getattr(col, 'foreign_keys', set()):
                table = fk.column.table
                fk_column = fk.column.key
                fk_table = fk.column.table.name
                assert fk_table.quote is None
                if fk_column == 'id':  # referencing an id column
                    if getattr(table, '__expose_id__', False) is not True:
                        return False

            # check if id and not white listed
            if col.key == "id":
                assert col.class_.__table__.name.quote is None
                if getattr(col.class_, '__expose_id__', False) is not True:
                    return False  # id columns is white listed

        # this field can be exposed
        return True

    @classmethod
    def serialize(cls, to_return=None, filter_by=None, limit=None, offset=None,
                  query=None, skip_nones=False, order_by=None, session=None,
                  filter_ids=True, params=None):
        """
                Convert to serializable representation
                - Only necessary fields are being queried
            :param to_return: list of fields to return
            :param filter_by: dict of SQLAlchemy clause to filter by
            :param limit: maximum amount of objects fetched
            :param offset: offset value for the result
            :param query: optional base query
            :param skip_nones: Skip filter_by entries that have a "None" value
            :param order_by: enforce result ordering, multiple via tuple
            :param session: Explict session to use for query
            :param filter_ids: Whether to filter not exposed fields
            :param params: Query parameters
            :return: Json serializable representation
        """
        assert params is None or isinstance(params, dict)
        assert to_return is None or isinstance(to_return, (list, tuple))

        if to_return is None:
            assert isinstance(cls.default_serialization, tuple)
            to_return = list(cls.default_serialization)

        assert len(to_return) == len(set(to_return)), [
            x for x in to_return if to_return.count(x) > 1
        ]

        # expand relationships to default fields
        expanded = []
        for path in to_return:
            expanded += cls._expand(path)
        to_return = expanded

        # remove not white listed ids
        if filter_ids is not False:
            to_return = list(filter(cls._is_exposed_id, to_return))

        # remove duplicated and store so we know what to populate
        json_to_populate = list(set(to_return))
        # obtain all columns that need fetching from db
        to_fetch = list(set(cls._get_query_columns(to_return)))

        if query is None:
            query = cls.query
        if session is not None:
            query = query.with_session(session)
        if params is not None:
            query = query.params(**params)
        # ensure that fresh data is loaded
        query = query.populate_existing()
        if filter_by is not None:
            query = cls.filter(filter_by, query, skip_nones=skip_nones)

        # handle consistent ordering and tuple in all cases
        if order_by is None:
            order_by = cls.id
        if isinstance(order_by, tuple):
            if order_by[-1] != cls.id:
                order_by = order_by + (cls.id,)
        else:
            if order_by != cls.id:
                order_by = order_by, cls.id
            else:
                order_by = order_by,
        assert isinstance(order_by, tuple)

        # join columns in order_by where necessary
        data = {'query': query}
        order_by = cls._substitute_clause(data, order_by)
        query = data['query']

        # we only need foreign key and request columns
        # Note: Primary keys are loaded automatically by sqlalchemy
        fks = [col.name for col in cls.__table__.columns if col.foreign_keys]
        eager_cols = [col for col in to_fetch if "." not in col]
        to_load = [getattr(cls, e) for e in list(set(fks + eager_cols))]
        assert all(hasattr(e, 'type') for e in to_load)
        query = query.options(load_only(*to_load))
        # only return one line per result model so we can use limit and offset
        query = query.distinct(cls.id)
        dense_rank = func.dense_rank().over(  # remember the actual order
            order_by=order_by).label("dense_rank")
        query = query.add_columns(dense_rank)
        query = query.from_self(cls)
        query = query.order_by(dense_rank)

        if limit is not None:
            query = query.limit(limit)
        if offset is not None:
            query = query.offset(offset)

        query = cls._eager_load(to_fetch, query)

        # for query debugging use
        # import sqlalchemy.dialects.postgresql as postgresql
        # print(query.statement.compile(dialect=postgresql.dialect()))
        # print("===========")

        return cls._as_list(query, json_to_populate)

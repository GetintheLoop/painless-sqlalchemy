from sqlalchemy import func, sql, distinct, case
from sqlalchemy.orm import aliased, RelationshipProperty
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql.annotation import Annotated
from sqlalchemy.sql.functions import FunctionElement
from sqlalchemy.sql.selectable import FromGrouping, Select
from sqlalchemy.sql.elements import (
    Label, BooleanClauseList, BinaryExpression, BindParameter, ColumnClause,
    Grouping, ClauseList, Null, False_, True_, UnaryExpression, Case, Cast,
    TextClause)
from sqlalchemy.util import NoneType
from painless_sqlalchemy.core.ModelAction import ModelAction
from painless_sqlalchemy.elements.MapColumn import MapColumn
from painless_sqlalchemy.elements.ColumnReference import ColumnReference


class ModelFilter(ModelAction):
    """ ORM Filter Abstraction """

    __abstract__ = True

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
            assert issubclass(class_, ModelFilter)
            cur = class_._get_column(cur.split("."))  # pylint: disable=W0212
        if isinstance(cur, list):
            assert all(isinstance(e, str) for e in cur)
            assert issubclass(class_, ModelFilter)
            # todo: this should merge list of lists (!)
            # pylint: disable-msg=W0212
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

    @classmethod
    def _get_and_info(cls, query):
        """
            Get the "and_" information for query
            - Attaches new "and_" information if not present
            The "and_" information contains depth information for and_ clauses.
            This ensures we can uniquely join tables for "and_" clauses, but
            prevent redundant joins for "or_" clauses.
        :return: "and_" information for query
        """
        if not hasattr(query, 'and_info'):
            setattr(query, 'and_info', {'depth': -1, 'counts': []})
        return getattr(query, 'and_info')

    @classmethod
    def _substitute_clause(cls, data, clause):
        """
            Substitute easy annotation in clause using query joins
            - Missing joins for clause are applied to data["query"]
            - Entries in clause are recursively resolved
            - Easy notation expected as "is_custom=true"-ColumnClause
            :return substituted clause
        """
        and_info = cls._get_and_info(data['query'])
        if isinstance(clause, BooleanClauseList):
            assert clause.operator.__name__ in ('or_', 'and_')
            if clause.operator.__name__ == 'or_':
                clause.clauses = [
                    cls._substitute_clause(data, c)
                    for c in clause.clauses
                ]
            else:  # and_
                and_info['depth'] += 1
                if len(and_info['counts']) <= and_info['depth']:
                    and_info['counts'].append(0)
                result = []
                for c in clause.clauses:
                    result.append(cls._substitute_clause(data, c))
                    and_info['counts'][and_info['depth']] += 1
                clause.clauses = result
                and_info['depth'] -= 1
            return clause
        elif isinstance(clause, Annotated):
            clause.proxy_set = set([
                cls._substitute_clause(data, c) for c in clause.proxy_set])
            return clause
        elif isinstance(clause, ClauseList):
            clause.clauses = [
                cls._substitute_clause(data, c)
                for c in clause.clauses
            ]
            return clause
        elif isinstance(clause, Case):
            clause.value = cls._substitute_clause(data, clause.value)
            clause.whens = [(
                cls._substitute_clause(data, x),
                cls._substitute_clause(data, y)
            ) for x, y in clause.whens]
            clause.else_ = cls._substitute_clause(data, clause.else_)
            return clause
        elif isinstance(clause, (
            Grouping, UnaryExpression, FromGrouping, Label
        )):
            clause.element = cls._substitute_clause(data, clause.element)
            return clause
        elif isinstance(clause, FunctionElement):
            # pylint: disable-msg=W0212
            return getattr(func, clause.name)(*[
                cls._substitute_clause(data, c)
                for c in clause.clause_expr.element
            ])
        elif isinstance(clause, Select):
            # pylint: disable-msg=W0212
            clause._raw_columns = [
                cls._substitute_clause(data, c) for c in clause._raw_columns]
            return clause
        elif isinstance(clause, BinaryExpression):
            clause.left = cls._substitute_clause(data, clause.left)
            clause.right = cls._substitute_clause(data, clause.right)
            return clause
        elif isinstance(clause, tuple):
            return tuple(cls._substitute_clause(data, c) for c in clause)
        elif isinstance(clause, ColumnReference):
            query, attr = cls._get_joined_attr(
                data['query'], clause.name.split("."))
            data['query'] = query
            return attr.self_group()
        elif isinstance(clause, (
            BindParameter, InstrumentedAttribute,
            Null, True_, False_, NoneType, TextClause, ColumnClause
        )):
            return clause
        elif isinstance(clause, Cast):
            clause.clause = cls._substitute_clause(data, clause.clause)
            return clause
        else:  # pragma: no cover
            print(type(clause), clause)
            raise NotImplementedError

    @classmethod
    def _is_to_many(cls, path):
        """
            Check if path represents a "*_to_many" relationship.
            - Does not resolve MapColumn
        :return: True iff "*_to_many_" relationship
        """
        rel = cls
        # Note: No need to consider the last relationship, since this
        # is always a class attribute (and hence a *_to_one relationship)
        for attr in path[:-1]:
            rel = getattr(aliased(rel), attr)
            if rel.property.uselist:
                return True
        return False

    @classmethod
    def filter(cls, attributes=None, query=None, skip_nones=False):
        """
            Overloaded filter abstraction. Supported scenarios:

            (1) Pass attributes as dict.
            Less powerful, but easy to use and "good enough" in most cases.
            - Keys reference (relationship) columns using dot notation
            - Values are objects that the keys get filtered by
            - Multiple filter conditions use "and" logic but can reference
            separate relationship models in case of *_to_many
            - Values that are lists are considered as "and" joints
            if they are on *_to_many relationship and "or" joints otherwise
            - Values that are lists are expected to only have unique elements
            - None values are pruned if skip_nones is set to True.

            (2) Pass attributes as SQLAlchemy filter
            Full SQLAlchemy power, but more complex to use.
            - Clause is used as given
            - Special ColumnClause can be used to reference relationship paths
            - Relationship paths are resolved automatically minimizing amount
            of joins added to the query

        :param attributes: dict *or* SQLAlchemy filter
        :param query: Optional (pre-filtered) query used as base
        :param skip_nones: Skip None-values dict entries iff true
        :return: filtered query
        """
        # todo: attributes with list values only unique if dict (add assert)
        # todo: ensure query class is same as current cls (add assert)
        assert skip_nones is False or isinstance(attributes, dict)
        if query is None:
            query = cls.query

        if attributes is None:
            return query

        and_info = cls._get_and_info(query)

        # Handle SqlAlchemy filter
        if not isinstance(attributes, dict):
            data = {'query': query}
            clause = cls._substitute_clause(data, attributes)
            return data['query'].filter(clause)

        if skip_nones:
            attributes = {
                key: value for key, value in attributes.items()
                if value is not None
            }
        if len(attributes) != 0:
            # true if this query is already grouped
            grouped = False
            and_info['depth'] += 1
            if len(and_info['counts']) <= and_info['depth']:
                and_info['counts'].append(0)
            for attribute, value in attributes.items():
                # make sure this lives now in a list
                if not isinstance(value, list):
                    value = [value]
                value = list(set(value))  # make list unique
                length = len(value)

                attr_hierarchy = attribute.split(".")
                to_many_rel = cls._is_to_many(attr_hierarchy)

                # to-one relationship and empty list means no result
                if not to_many_rel and length == 0:
                    return cls.query.filter(sql.false())

                query, final_attr = cls._get_joined_attr(query, attr_hierarchy)
                and_info['counts'][and_info['depth']] += 1
                if length == 1:
                    query = query.filter(final_attr == value[0])
                elif length > 1:
                    if to_many_rel:
                        # group by so we can use count for filter
                        if not grouped:
                            query = query.group_by(cls.id)
                            grouped = True
                        # count the unique entries and check that this is
                        # equal to the length of the "value" list
                        # Note: Could possibly result in undesired behaviour
                        # when using duplicate entries in "value" list
                        query = query.having(func.count(distinct(case(
                            [(final_attr.in_(value), final_attr)],
                            else_=None
                        ))) == length)
                    else:
                        query = query.filter(final_attr.in_(value))
            and_info['depth'] -= 1
        return query

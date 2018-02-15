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

    @classmethod
    def _substitute_clause(cls, data, clause):
        """
            Substitute easy annotation in clause using query joins
            - Missing joins for clause are applied to data["query"]
            - Entries in clause are recursively resolved
            - Easy notation expected as "is_custom=true"-ColumnClause
            :return substituted clause
        """
        and_info = cls.get_and_info(data['query'])
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
            return getattr(func, clause.name)(*[
                cls._substitute_clause(data, c)
                for c in clause.clause_expr.element
            ])
        elif isinstance(clause, Select):
            clause._raw_columns = [
                cls._substitute_clause(data, c) for c in clause._raw_columns]
            return clause
        elif isinstance(clause, BinaryExpression):
            clause.left = cls._substitute_clause(data, clause.left)
            clause.right = cls._substitute_clause(data, clause.right)
            return clause
        elif isinstance(clause, tuple):
            return tuple(cls._substitute_clause(data, c) for c in clause)
        elif isinstance(clause, ColumnClause):
            if getattr(clause, 'is_custom', False) is True:
                query, attr = cls._get_joined_attr(
                    data['query'], clause.name.split("."))
                data['query'] = query
                return attr.self_group()
            else:
                return clause
        elif isinstance(clause, (
            BindParameter, InstrumentedAttribute,
            Null, True_, False_, NoneType, TextClause
        )):
            return clause
        elif isinstance(clause, Cast):
            clause.clause = cls._substitute_clause(data, clause.clause)
            return clause
        else:  # pragma: no cover
            print(type(clause), clause)
            raise NotImplementedError

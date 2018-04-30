import functools
from sqlalchemy import and_
from sqlalchemy.dialects.postgresql import insert


class DBTestUtilMixin(object):

    @classmethod
    def commit(cls, *args):
        """
            Commit Entities to database.
            :param args: SQLAlchemy Models
        """
        cls._meta["db"].session.add_all(args)
        cls._meta["db"].session.commit()

    @staticmethod
    def check_constraint(err, constraint):
        """
            Test Helper: Validate Database Constraint
            - raises exception if not matched
            :param err: exception raised
            :param constraint: the constraint name to check for
        """
        assert constraint == functools.reduce(
            lambda e, a: getattr(e, a, None),
            [err.exception, 'orig', 'diag', 'constraint_name']
        )

    @classmethod
    def _get_tables(cls):
        """
            List defined database tables.
            :return Dict mapping {table name -> table}
        """
        return {t.name: t for t in
                cls._meta["db"].Model.metadata.tables.values()}

    @classmethod
    def _get_dump(cls):
        """
            Get a database dump (for comparison purposes only)
            :return: database dump
        """
        result = []
        tables = cls._get_tables()
        for tbl in tables:
            data = cls._meta["db"].engine.execute(
                tables[tbl].select()).fetchall()
            for a in data:
                result.append("%s %s" % (
                    tbl,
                    ", ".join("%s=%s" % v for v in zip([
                        c.name for c in tables[tbl].columns
                    ], a))
                ))
        return result

    @classmethod
    def _get_table_rel_table_map(cls):
        """
            List tables relationship.
            :return dict of form {table -> [relationship table, foreign key]}
        """
        # extract relationship tables
        result = {}
        for tbl in cls._get_tables():
            if "_to_" not in tbl:
                continue
            left, right = tbl.split("_to_")
            if left not in result:
                result[left] = []
            if right not in result:
                result[right] = []
            if left == right:
                result[left].append([tbl, 'left_%s_id' % left])
                result[right].append([tbl, 'right_%s_id' % right])
            else:
                result[left].append([tbl, '%s_id' % left])
                result[right].append([tbl, '%s_id' % right])
        return result

    @classmethod
    def _get_relationship_table(cls, *args):
        """
            Retrieve relationship table for two tables passed.
            :param args: two tables
            :return relationship table
        """
        assert len(args) == 2
        assert all(not k.endswith("_id") for k in args)
        target = set()
        table_map = cls._get_tables()
        for direction in [(args[0], args[1]), (args[1], args[0])]:
            tbl = "%s_to_%s" % direction
            if tbl in table_map:
                target.add(table_map[tbl])
        assert len(target) == 1
        return target.pop()

    @classmethod
    def link(cls, meta=None, **kwargs):
        """
            Create entry for relationship table.
            :param meta: additional information for the relationship
            :param kwargs: tables of form table1=id1, table2=id2
        """
        assert meta is None or isinstance(meta, dict)
        table = cls._get_relationship_table(*kwargs.keys())
        values = {k + "_id": v for k, v in kwargs.items()}
        if meta is None:
            cls._meta["db"].session.execute(insert(table).values(**values))
        else:
            # check that no keys are shared across meta and data
            assert len(set(values.keys()) & set(meta.keys())) == 0
            constraint_keys = values.keys()
            values.update(meta)
            cls._meta["db"].session.execute(
                insert(table).values(**values).on_conflict_do_update(
                    index_elements=constraint_keys,
                    set_=meta
                )
            )
        cls._meta["db"].session.commit()

    @classmethod
    def unlink(cls, **kwargs):
        """
            Remove entry from relationship table.
            :param kwargs: tables of form table1=id1, table2=id2
        """
        target = cls._get_relationship_table(*kwargs.keys())
        args = [
            getattr(target.c, k + "_id") == v
            for k, v in kwargs.items()
        ]
        cls._meta["db"].session.query(target).filter(
            and_(*args)
        ).delete(synchronize_session=False)
        cls._meta["db"].session.commit()

from sqlalchemy import and_
from sqlalchemy.dialects.postgresql import insert
from painless_sqlalchemy.BaseModel import Base, session, engine


class DBTestUtilMixin(object):

    @classmethod
    def commit(cls, *args):
        """
            Commit Entities to database.
            :param args: SQLAlchemy Models
        """
        session.add_all(args)
        session.commit()

    @staticmethod
    def get_tables():
        """
            List defined database tables.
            :return Dict mapping {table name -> table}
        """
        return {t.name: t for t in Base.metadata.tables.values()}

    @classmethod
    def get_dump(cls):
        """
            Get a database dump (for comparison purposes only)
            :return: database dump
        """
        result = []
        tables = cls.get_tables()
        for tbl in tables:
            data = engine.execute(tables[tbl].select()).fetchall()
            for a in data:
                result.append("%s %s" % (
                    tbl,
                    ", ".join("%s=%s" % v for v in zip([
                        c.name for c in tables[tbl].columns
                    ], a))
                ))
        return result

    @classmethod
    def get_table_rel_table_map(cls):
        """
            List tables relationship.
            :return dict of form {table -> [relationship table, foreign key]}
        """
        # extract relationship tables
        result = {}
        for tbl in cls.get_tables():
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
    def get_relationship_table(cls, *args):
        """
            Retrieve relationship table for two tables passed.
            :param args: two tables
            :return relationship table
        """
        assert len(args) == 2
        assert all(not k.endswith("_id") for k in args)
        target = set()
        table_map = cls.get_tables()
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
        table = cls.get_relationship_table(*kwargs.keys())
        values = {k + "_id": v for k, v in kwargs.items()}
        if meta is None:
            session.execute(insert(table).values(**values))
        else:
            # check that no keys are shared across meta and data
            assert len(set(values.keys()) & set(meta.keys())) == 0
            constraint_keys = values.keys()
            values.update(meta)
            session.execute(
                insert(table).values(**values).on_conflict_do_update(
                    index_elements=constraint_keys,
                    set_=meta
                )
            )
        session.commit()

    @classmethod
    def unlink(cls, **kwargs):
        """
            Remove entry from relationship table.
            :param kwargs: tables of form table1=id1, table2=id2
        """
        target = cls.get_relationship_table(*kwargs.keys())
        args = [
            getattr(target.c, k + "_id") == v
            for k, v in kwargs.items()
        ]
        session.query(target).filter(
            and_(*args)
        ).delete(synchronize_session=False)
        session.commit()

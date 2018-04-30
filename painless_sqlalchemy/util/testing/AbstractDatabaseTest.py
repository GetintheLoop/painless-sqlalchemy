import os
import warnings
import pytest
from painless_sqlalchemy.util.testing.AbstractExtendedTest import (
    AbstractExtendedTest)
from painless_sqlalchemy.util.testing.DBIdMixin import DBIdMixin
from painless_sqlalchemy.util.testing.DBTestUtilMixin import DBTestUtilMixin

# check if we are running in batch test mode
batch_testing = 'BATCH_RUN' in os.environ and os.environ['BATCH_RUN'] == "1"


class AbstractDatabaseTest(AbstractExtendedTest, DBTestUtilMixin, DBIdMixin):
    """ Base Class for Database Tests. """

    # entities that need to be removed
    _func_entities = {}
    _class_entities = {}
    _meta = {}

    @classmethod
    def _register_entities(cls, dict_, **kwargs):
        """
            Register Entities into dict_ object.
            Expects table_name=model_id or (model1_id, model2_id)
        """
        assert all(isinstance(e, (tuple, int, str)) for e in kwargs.values())
        assert isinstance(dict_, dict)

        for table_name, model_ids in kwargs.items():
            if table_name not in dict_:
                dict_[table_name] = set()
            if isinstance(model_ids, int):
                dict_[table_name].add(str(model_ids))
            elif isinstance(model_ids, str):
                dict_[table_name].add("'%s'" % model_ids)
            else:
                for model_id in model_ids:  # handle recursively
                    cls._register_entities(dict_, **{table_name: model_id})

    @classmethod
    def _delete_entities(cls, dict_):
        """
            Delete entities present in passed dict_.
            Expected format maps table to set of ids
        """
        assert isinstance(dict_, dict)

        # build the queries
        queries = []
        trigger_query = 'ALTER TABLE "%s" %s TRIGGER USER;'
        for tbl in cls._meta["table_hierarchy"]:
            if tbl not in dict_:
                continue
            row_ids = ",".join(dict_[tbl])
            # handle relationship deletes
            rel_tbls = cls._get_table_rel_table_map()
            if tbl in rel_tbls:
                for rel_tbl in rel_tbls[tbl]:
                    queries.extend([[
                        trigger_query % (rel_tbl[0], 'DISABLE'),
                        None
                    ], [
                        'DELETE FROM %s WHERE %s in (%s);'
                        % (rel_tbl[0], rel_tbl[1], row_ids),
                        None
                    ], [
                        trigger_query % (rel_tbl[0], 'ENABLE'),
                        None
                    ]])
            # handle table deletes
            queries.extend([[
                trigger_query % (tbl, 'DISABLE'),
                None
            ], [
                'DELETE FROM "%s" WHERE id in (%s);'
                % (tbl, row_ids),
                len(dict_[tbl])
            ], [
                trigger_query % (tbl, 'ENABLE'),
                None
            ]])

            del dict_[tbl]

        if batch_testing:
            if len(queries) > 0:
                cls._meta["db"].engine.execute("".join([
                    q[0] for q in queries]))
        else:  # pragma: no cover
            # execute the queries
            for query in queries:
                result = cls._meta["db"].engine.execute(query[0])
                if query[1] is not None:
                    assert result.rowcount == query[1], query[0]
        assert len(dict_) == 0, "Undefined Tables Provided: %s" % dict_

    @classmethod
    def _register(cls, dict_, *args, **kwargs):
        """ Helper for registering Database Entities. """
        if args:
            for arg in args:
                for k, v in cls.extract(arg).items():
                    if k not in kwargs:
                        kwargs[k] = v
                    else:
                        kwargs[k] = tuple(set(list(kwargs[k]) + list(v)))
        cls._register_entities(dict_, **kwargs)

    @classmethod
    def register(cls, *args, **kwargs):  # pylint: disable=E0202
        """
            Register database Models for deletion.
            :param args: Models to be registered
            :param kwargs: Dict of table name mapping to ids or id tuples
        """
        cls._register(cls._class_entities, *args, **kwargs)

    @staticmethod
    def _checkin(this, *args, **kwargs):
        """ Helper for committing and registering database Entities. """
        this.commit(*args, **kwargs.copy())
        this.register(*args, **kwargs.copy())
        return args[0] if len(args) == 1 else args

    @classmethod
    def checkin(cls, *args, **kwargs):  # pylint: disable=E0202
        """
            Commit and register database Entities.
            - See commit and register functions for details.
            - Kwargs must already be commited.
            :param args: Models to be registered
            :param kwargs: Dict of table name mapping to ids or id tuples
        """
        return cls._checkin(cls, *args, **kwargs)

    # --------------

    # contains database snapshots for test verification
    _db_snapshots = {}

    @classmethod
    def _snapshot_db(cls, identifier):  # pragma: no cover
        """ Take a snapshot of database and store for identifier. """
        cls._db_snapshots[identifier] = cls._get_dump()

    @classmethod
    def _match_db_snapshot(cls, identifier):  # pragma: no cover
        """ Compare current database state to snapshot. """
        assert identifier in cls._db_snapshots
        snapshot = cls._db_snapshots[identifier]
        current = cls._get_dump()
        # analyse data
        added = False
        for d in current:
            if d not in snapshot:
                added = True
                warnings.warn("Test added data: \t%s" % d)
        removed = False
        for d in snapshot:
            if d not in current:
                removed = True
                warnings.warn("Test removed data: \t%s" % d)

        if added:
            warnings.warn("Test added data %s." % identifier)
        if removed:
            warnings.warn("Test removed data %s:%s." % identifier)

    # --------------

    @classmethod
    @pytest.fixture(scope='class', autouse=True)
    def setup_class(cls):
        if not batch_testing:  # pragma: no cover
            cls._meta["recreate_db"]()
            cls._snapshot_db('test_class')

    @classmethod
    def teardown_class(cls):
        # delete registered entities
        cls._delete_entities(cls._class_entities)

        if not batch_testing:  # pragma: no cover
            cls._match_db_snapshot('test_class')

    @pytest.fixture(scope='function', autouse=True)
    def setup_method(self):
        # overwrite instance method
        self.register = (
            lambda *ars, **kws:
            self._register(self._func_entities, *ars, **kws)
        )
        self.checkin = (
            lambda *ars, **kws:
            self._checkin(self, *ars, **kws)
        )

        if not batch_testing:  # pragma: no cover
            self._snapshot_db('test_function')

    def teardown_method(self):
        # delete registered entities
        self._delete_entities(self._func_entities)

        if not batch_testing:  # pragma: no cover
            self._match_db_snapshot('test_function')

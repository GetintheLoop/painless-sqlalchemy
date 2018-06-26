import string
import random

import pytest
from faker import Faker

from painless_sqlalchemy.columns import TimeZoneType
from tests.AbstractTest import AbstractTest
from tests.conftest import db

fake = Faker()


class TestTimeZoneType(AbstractTest):

    @classmethod
    @pytest.fixture(scope='class', autouse=True)
    def setup_class(cls, School):
        super(TestTimeZoneType, cls).setup_class()
        cls.school = cls.persist(cls.checkin(School()))

    def test_storage(self, School):
        timezone = random.choice(TimeZoneType.VALID_TIMEZONES)
        school = School.filter().one()
        school.update(timezone=timezone).save()
        assert school.timezone == timezone
        school = School.filter().one()
        assert school.timezone == timezone
        school.update(timezone=None).save()

    def test_invalid_format(self, School):
        school = School.filter().one()
        timezone = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
        with pytest.raises(ValueError) as e:
            school.update(timezone=timezone).save()
        assert e.value.__str__() == 'Invalid Time Zone "%s".' % timezone

    def test_timezones_exist_in_db(self):
        """ Test DB timezones are represented in database. """
        db_timezones = [t[0] for t in db.engine.execute(
            "SELECT name FROM pg_timezone_names ORDER BY name ASC"
        ).fetchall() if not (
            t[0].startswith("posix/") or
            t[0].startswith("SystemV/")
        )]
        error = False
        # Useful for debugging
        # for dbtz in db_timezones:
        #     if dbtz not in TimeZoneType.VALID_TIMEZONES:
        #         print("%s in DB but not in file" % dbtz)
        #         error = True
        for ftz in TimeZoneType.VALID_TIMEZONES:
            if ftz not in db_timezones:  # pragma: no cover
                print("%s in file but not in DB" % ftz)
                error = True
        assert not error

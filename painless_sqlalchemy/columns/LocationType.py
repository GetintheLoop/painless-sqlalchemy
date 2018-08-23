import json
from geoalchemy2 import WKTElement
from painless_sqlalchemy.columns.AbstractType import AbstractType
from painless_sqlalchemy.columns.AbstractGeometry import AbstractGeometry
from painless_sqlalchemy.util.LocationUtil import validate_longlat


class LocationType(AbstractGeometry, AbstractType):
    """ LongLat Column Type """

    python_type = tuple
    geometry_type = "POINT"

    @classmethod
    def as_postgis(cls, area):
        location = cls.rec_round(area)
        string = "%s(%s %s)" % (cls.geometry_type, location[0], location[1])
        return WKTElement(string, srid=cls.srid)

    def result_processor(self, dialect, coltype):
        def process(value):
            if value is None:
                return None
            value = json.loads(value)
            assert value['type'].upper() == self.geometry_type
            return value['coordinates'][0], value['coordinates'][1]
        return process

    def validator(self, attr_name):
        def validate(target, value, oldvalue, initiator):  # pylint: disable=unused-argument
            if value is not None:
                try:
                    validate_longlat(value)
                except ValueError:
                    raise ValueError("Invalid location given for attr \"%s\"." % attr_name)
            return True
        return validate

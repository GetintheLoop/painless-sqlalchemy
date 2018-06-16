import json
from geoalchemy2 import WKTElement
from painless_sqlalchemy.columns.AbstractType import AbstractType
from painless_sqlalchemy.columns.AbstractGeometry import AbstractGeometry
from painless_sqlalchemy.util.LocationUtil import validate_latlong


class LocationType(AbstractGeometry, AbstractType):
    """ LongLat Column Type """

    python_type = tuple
    geometry_type = "POINT"

    @classmethod
    def as_postgis(cls, area):
        location = cls.rec_round(area)
        # flip location since PostGIS stores them longitude, latitude
        string = "%s(%s %s)" % (cls.geometry_type, location[1], location[0])
        return WKTElement(string, srid=cls.srid)

    def result_processor(self, dialect, coltype):
        def process(value):
            if value is None:
                return None
            value = json.loads(value)
            assert value['type'].upper() == self.geometry_type
            # flip back, since they are stored longitude, latitude
            return value['coordinates'][1], value['coordinates'][0]
        return process

    def validator(self, attr_name):
        def validate(target, value, oldvalue, initiator):  # pylint: disable=unused-argument
            if value is not None:
                try:
                    validate_latlong(value)
                except ValueError:
                    raise ValueError("Invalid location given for attr \"%s\"." % attr_name)
            return True
        return validate

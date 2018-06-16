import json
from geoalchemy2 import WKTElement
from sqlalchemy import func
from painless_sqlalchemy.columns.AbstractType import AbstractType
from painless_sqlalchemy.columns.AbstractGeometry import AbstractGeometry
from painless_sqlalchemy.util.LocationUtil import validate_latlong


class AreaType(AbstractGeometry, AbstractType):
    """ Geo Polygon Column Type """

    python_type = list
    geometry_type = "POLYGON"

    @classmethod
    def enforce_clockwise(cls, area):  # reference: http://tiny.cc/eacajy
        # check if clockwise
        direction = 0
        for i in range(len(area) - 1):
            direction += (
                area[i + 1][0] - area[i][0]
            ) * (
                area[i + 1][1] + area[i][1]
            )
        # reverse if counter clockwise
        return area[::-1] if direction < 0 else area

    @classmethod
    def as_postgis(cls, area):
        area = cls.rec_round(area)  # round elements
        area = cls.enforce_clockwise(area)  # enforce orientation
        string = "%s((%s))" % (
            cls.geometry_type,
            ",".join([
                # flip location since PostGIS stores them longitude, latitude
                "%s %s" % (a[1], a[0]) for a in area
            ])
        )
        return WKTElement(string, srid=cls.srid)

    @classmethod
    def get_envelope(cls, rect):
        """ PostGIS envelope for gps rectangle (lat, long, lat, long) """
        assert isinstance(rect, list)
        assert len(rect) == 4
        return func.ST_Envelope(cls.as_postgis([
            (rect[0], rect[1]), (rect[0], rect[3]),
            (rect[2], rect[3]), (rect[2], rect[1]),
            (rect[0], rect[1])
        ]))

    def result_processor(self, dialect, coltype):
        def process(value):
            if value is None:
                return None
            value = json.loads(value)
            assert value['type'].upper() == self.geometry_type
            # flip back, since they are stored longitude, latitude
            return [(p[1], p[0]) for p in value['coordinates'][0]]
        return process

    def validator(self, attr_name):
        def validate(target, value, oldvalue, initiator):  # pylint: disable=unused-argument
            if value is not None:
                try:
                    for v in value:
                        validate_latlong(v)
                except ValueError:
                    raise ValueError("Invalid Polygon Entry given for attr \"%s\"." % attr_name)
                if value[0][0] != value[-1][0] or value[0][1] != value[-1][1]:
                    raise ValueError("Open Polygon given for attr \"%s\"." % attr_name)
                if len(set(["%s %s" % (v[1], v[0]) for v in value])) < 3:
                    raise ValueError("Degenerate Polygon given for attr \"%s\"." % attr_name)
            return True
        return validate

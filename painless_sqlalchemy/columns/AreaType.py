import json
from geoalchemy2 import WKTElement
from painless_sqlalchemy.columns.AbstractType import AbstractType
from painless_sqlalchemy.columns.AbstractGeometry import AbstractGeometry
from painless_sqlalchemy.util.LocationUtil import validate_longlat


class AreaType(AbstractGeometry, AbstractType):
    """ Geo Polygon Column Type """

    python_type = list
    geometry_type = "POLYGON"

    def __init__(self, clockwise, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert clockwise is True or clockwise is False or clockwise is None
        self.clockwise = clockwise

    @staticmethod
    def as_directed(area, clockwise):  # reference: http://tiny.cc/eacajy
        # check if clockwise
        direction = 0
        for i in range(len(area) - 1):
            direction += (
                area[i + 1][0] - area[i][0]
            ) * (
                area[i + 1][1] + area[i][1]
            )
        # reverse if counter clockwise
        return area[::-1] if (direction < 0 == clockwise) else area

    def as_postgis(self, area):
        area = self.rec_round(area)
        area = area if self.clockwise is None else self.as_directed(area, self.clockwise)
        string = "%s((%s))" % (
            self.geometry_type,
            ",".join(["%s %s" % (a[0], a[1]) for a in area])
        )
        return WKTElement(string, srid=self.srid)

    def result_processor(self, dialect, coltype):
        def process(value):
            if value is None:
                return None
            value = json.loads(value)
            assert value['type'].upper() == self.geometry_type
            return [(p[0], p[1]) for p in value['coordinates'][0]]
        return process

    def validator(self, attr_name):
        def validate(target, value, oldvalue, initiator):  # pylint: disable=unused-argument
            if value is not None:
                try:
                    for v in value:
                        validate_longlat(v)
                except ValueError:
                    raise ValueError("Invalid Polygon Entry given for attr \"%s\"." % attr_name)
                if value[0][0] != value[-1][0] or value[0][1] != value[-1][1]:
                    raise ValueError("Open Polygon given for attr \"%s\"." % attr_name)
                rounded = self.rec_round(value)
                if len(set("%s %s" % (v[0], v[1]) for v in rounded)) < 3:
                    raise ValueError("Degenerate Polygon given for attr \"%s\"." % attr_name)
                for i in range(0, len(rounded) - 1):
                    if rounded[i][0] == rounded[i + 1][0] and rounded[i][1] == rounded[i + 1][1]:
                        raise ValueError("Consecutive, identical Point detected for attr \"%s\"." % attr_name)
            return True
        return validate

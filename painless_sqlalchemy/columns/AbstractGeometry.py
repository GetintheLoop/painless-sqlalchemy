from geoalchemy2 import Geometry
from sqlalchemy import func
from painless_sqlalchemy.columns.AbstractType import AbstractType


class AbstractGeometry(Geometry, AbstractType):
    geometry_type = None
    python_type = None
    srid = 4326  # coordinates on earth

    def __init__(self, *args, **kwargs):
        kwargs['geometry_type'] = self.geometry_type
        kwargs['srid'] = kwargs.get('srid', self.srid)
        super(AbstractGeometry, self).__init__(*args, **kwargs)

    @classmethod
    def rec_round(cls, data):
        if isinstance(data, list):
            return [cls.rec_round(e) for e in data]
        if isinstance(data, tuple):
            return tuple(cls.rec_round(e) for e in data)
        if isinstance(data, str):
            data = float(data)
        assert isinstance(data, (float, int))
        return round(data, 9)

    @classmethod
    def as_postgis(cls, area):
        raise NotImplementedError()

    def column_expression(self, col):
        return func.ST_AsGeoJSON(col, type_=self)

    def result_processor(self, dialect, coltype):
        raise NotImplementedError()

    def bind_processor(self, dialect):
        def process(bindvalue):
            if bindvalue is None:
                return None
            return 'SRID=%d;%s' % (self.srid, self.as_postgis(bindvalue).data)
        return process

    def validator(self, attr_name):
        raise NotImplementedError()

import unittest
import pytest
from painless_sqlalchemy.util import LocationUtil


class TestLocationUtil(unittest.TestCase):

    valid_lat_long = (
        (45, 64),
        (90, 180),
        (-45, -64),
        (-90, -180),
        ("34", "-20"),
        ("-90", "-180"),
        ("-38.2", "24.4"),
    )

    invalid_lat_long = (
        (89, 180.2),
        (90.1, 180),
        (90.1, 180.4),
        (-89, -180.2),
        (-90.1, -180),
        (-90.1, -180.4),
        ("10g", "-40"),
        ("-180", "-90"),
        (float("nan"), float("inf"))
    )

    def test_haversine(self):
        pos1 = [49.880134, -119.443606]
        pos2 = [47.6779496, 9.1732384]
        dist = LocationUtil.haversine(pos1[0], pos1[1], pos2[0], pos2[1])
        assert dist == 8102.26550449619

    def test_valid_lat_long(self):
        for (latitude, longitude) in self.valid_lat_long:
            assert LocationUtil.validate_latitude(latitude) == float(latitude)
            assert LocationUtil.validate_longitude(longitude) == float(longitude)

    def test_invalid_lat_long(self):
        for (latitude, longitude) in self.invalid_lat_long:
            with pytest.raises((ValueError, Exception)):
                LocationUtil.validate_latitude(latitude)
                LocationUtil.validate_longitude(longitude)

    def test_point_in_poly(self):
        raw = [
            49.944150351645476, -119.55219268798828, 49.90038439228632,
            -119.60403442382812, 49.84838837518499, -119.57038879394531,
            49.8333322745551, -119.48249816894531, 49.85746405258426,
            -119.40696716308594, 49.911661241491046, -119.40628051757812,
            49.93774266930684, -119.43992614746094, 49.94525503832821,
            -119.49897766113281, 49.944150351645476, -119.55219268798828
        ]
        poly = list(zip(*[iter(raw)] * 2))
        x, y = 49.879701, -119.493120
        assert LocationUtil.point_inside_polygon(x, y, poly)

        x, y = 49.93774266930684, -119.43992614746094
        assert isinstance(LocationUtil.point_inside_polygon(x, y, poly), bool)

        x, y = 49.923265, -119.414501
        assert isinstance(LocationUtil.point_inside_polygon(x, y, poly), bool)

        # test degenerate polygon
        raw = [
            0, 0, 1, 0, 1, 1, 0, 1, 0, 0
        ]
        poly = list(zip(*[iter(raw)] * 2))
        x, y = 0.5, 0.5
        assert LocationUtil.point_inside_polygon(x, y, poly)

        # test overlapping concave polygon
        raw = [
            49.92249337815646, -119.5913314819336, 49.915419605394845,
            -119.51099395751953, 49.856357353907086, -119.58995819091797,
            49.85480793317645, -119.49726104736328, 49.92625089782431,
            -119.56180572509766, 49.92647191927194, -119.48833465576172,
            49.85082348031653, -119.49039459228516, 49.85259438880997,
            -119.59854125976562, 49.92249337815646, -119.5913314819336
        ]
        poly = list(zip(*[iter(raw)] * 2))
        x, y = 49.872936, -119.538087
        assert not LocationUtil.point_inside_polygon(x, y, poly)
        # overlapping point is detected as not inside
        x, y = 49.905341, -119.536199
        assert not LocationUtil.point_inside_polygon(x, y, poly)

        # test non overlapping concave polygon
        raw = [
            49.92249337815646, -119.5913314819336, 49.91033469017977,
            -119.55545425415039, 49.88490207132429, -119.55459594726562,
            49.88440434290131, -119.53099250793457, 49.861115978385854,
            -119.54103469848633, 49.878984301226524, -119.56480979919434,
            49.856357353907086, -119.58995819091797, 49.85480793317645,
            -119.49726104736328, 49.92625089782431, -119.56180572509766,
            49.92647191927194, -119.48833465576172, 49.85082348031653,
            -119.49039459228516, 49.85259438880997, -119.59854125976562,
            49.92249337815646, -119.5913314819336
        ]
        poly = list(zip(*[iter(raw)] * 2))
        x, y = 49.876587, -119.544611
        assert LocationUtil.point_inside_polygon(x, y, poly)
        x, y = 49.863531, -119.562807
        assert not LocationUtil.point_inside_polygon(x, y, poly)

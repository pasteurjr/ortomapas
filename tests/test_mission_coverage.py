from pyproj import Transformer
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import transform

from backend.routers.missoes_captura import (
    GridGenerationRequest,
    _generate_grid,
    _local_transformers,
    _validate_mission_geometry,
)


def projected_polygon(bounds):
    to_wgs84 = Transformer.from_crs("EPSG:32724", "EPSG:4326", always_xy=True).transform
    return transform(to_wgs84, Polygon(bounds))


def test_camera_profile_calculates_overlap_spacing():
    aoi = projected_polygon([(200000, 8598000), (200300, 8598000), (200300, 8598300), (200000, 8598300)])
    _, stats = _generate_grid(
        aoi,
        [],
        GridGenerationRequest(),
        {
            "altitude_m": 50,
            "front_overlap": 0.8,
            "side_overlap": 0.7,
            "camera_perfil": {"fov_diagonal_deg": 82.1, "resolucao_px": [4000, 3000]},
        },
    )

    assert stats["footprint_width_m"] == 69.67
    assert stats["footprint_height_m"] == 52.25
    assert abs(stats["line_spacing_m"] - 20.90) < 0.02
    assert abs(stats["photo_spacing_m"] - 10.45) < 0.02


def test_generated_coverage_stays_outside_exclusion_with_safety_margin():
    aoi = projected_polygon([(200000, 8598000), (200300, 8598000), (200300, 8598300), (200000, 8598300)])
    exclusion = projected_polygon([(200120, 8598120), (200180, 8598120), (200180, 8598180), (200120, 8598180)])
    points, stats = _generate_grid(
        aoi,
        [exclusion],
        GridGenerationRequest(),
        {"altitude_m": 50, "front_overlap": 0.8, "side_overlap": 0.7},
    )
    to_local, _, _ = _local_transformers(aoi)
    forbidden = transform(to_local, exclusion)
    allowed = transform(to_local, aoi).difference(forbidden.buffer(2)).buffer(0.02)

    assert len(points) >= 2
    assert all(point.distance(forbidden) >= 1.98 for point in points)
    assert any(not capture for capture in stats["capture_flags"])
    assert all(allowed.covers(LineString([left, right])) for left, right in zip(points, points[1:]))
    assert stats["local_crs"] == "EPSG:32724"
    generated_rows = []
    for point in points:
        lon, lat = stats["from_local"](point.x, point.y)
        generated_rows.append({"longitude": lon, "latitude": lat})
    exclusion_rule = next(issue for issue in _validate_mission_geometry(aoi, [exclusion], generated_rows) if issue["regra"] == "zonas_exclusao")
    assert exclusion_rule["status"] == "aprovado"


def test_validator_uses_metric_tolerance_and_detects_crossing_segments():
    aoi = projected_polygon([(200000, 8598000), (200300, 8598000), (200300, 8598300), (200000, 8598300)])
    exclusion = projected_polygon([(200120, 8598120), (200180, 8598120), (200180, 8598180), (200120, 8598180)])
    _, from_local, _ = _local_transformers(aoi)
    left = Point(200100, 8598150)
    right = Point(200200, 8598150)
    left_lon, left_lat = from_local(left.x, left.y)
    right_lon, right_lat = from_local(right.x, right.y)
    issues = _validate_mission_geometry(
        aoi,
        [exclusion],
        [
            {"longitude": left_lon, "latitude": left_lat},
            {"longitude": right_lon, "latitude": right_lat},
        ],
    )
    exclusion_rule = next(issue for issue in issues if issue["regra"] == "zonas_exclusao")
    assert exclusion_rule["status"] == "bloqueado"
    assert exclusion_rule["valor_observado"]["trechos_cruzados"] == 1

    outside_1m = Point(199999, 8598150)
    outside_3m = Point(199997, 8598150)
    one_lon, one_lat = from_local(outside_1m.x, outside_1m.y)
    three_lon, three_lat = from_local(outside_3m.x, outside_3m.y)
    for lon, lat, expected in [(one_lon, one_lat, "aprovado"), (three_lon, three_lat, "bloqueado")]:
        result = _validate_mission_geometry(aoi, [], [{"longitude": lon, "latitude": lat}, {"longitude": left_lon, "latitude": left_lat}])
        assert next(issue for issue in result if issue["regra"] == "waypoints_na_aoi")["status"] == expected

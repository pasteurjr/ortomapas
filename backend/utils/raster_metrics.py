"""Terrain derivatives in physical units, including rotated/resampled grids."""
import numpy as np
from pyproj import CRS


def metric_jacobian(crs, affine):
    if not crs:
        raise ValueError("Raster sem CRS")
    source = CRS.from_user_input(crs)
    if not source.is_projected or len(source.axis_info) < 2:
        raise ValueError("Reprojete o raster para um CRS projetado antes da analise metrica")
    fx, fy = [axis.unit_conversion_factor for axis in source.axis_info[:2]]
    matrix = np.array([[affine.a * fx, affine.b * fx], [affine.d * fy, affine.e * fy]])
    if not np.isfinite(matrix).all() or abs(np.linalg.det(matrix)) < 1e-15:
        raise ValueError("Grade raster degenerada ou unidades desconhecidas")
    return matrix


def terrain_gradient(values, crs, affine):
    matrix = metric_jacobian(crs, affine)
    values = np.ma.asarray(values, dtype=float).filled(np.nan)
    if min(values.shape) < 2:
        raise ValueError("Grade precisa de pelo menos duas linhas e colunas")
    row, col = np.gradient(values)
    # [dZ/dcol, dZ/drow] = Jacobian.T @ [dZ/dEast, dZ/dNorth].
    inverse = np.linalg.inv(matrix.T)
    east = inverse[0, 0] * col + inverse[0, 1] * row
    north = inverse[1, 0] * col + inverse[1, 1] * row
    valid = np.isfinite(values) & np.isfinite(east) & np.isfinite(north)
    return east, north, valid


def terrain_aspect(east, north, valid):
    """Downhill grid bearing, clockwise from grid north; flats have no bearing."""
    result = (np.degrees(np.arctan2(-east, -north)) + 360) % 360
    return np.where(valid & (np.hypot(east, north) > 1e-12), result, np.nan)


def terrain_illumination(east, north, valid, azimuth=315, altitude=45):
    """Lambertian illumination of the metric surface normal, scaled to 0..255."""
    if not np.isfinite([azimuth, altitude]).all() or not 0 <= azimuth <= 360 or not 0 <= altitude <= 90:
        raise ValueError("Azimute deve estar entre 0 e 360; altitude solar entre 0 e 90")
    az, alt = np.radians([azimuth, altitude])
    light = (-east*np.sin(az)*np.cos(alt) - north*np.cos(az)*np.cos(alt) + np.sin(alt)) / np.sqrt(1+east**2+north**2)
    return np.where(valid, np.clip(light, 0, 1)*255, np.nan)


def volume_metrics(values, crs, affine, reference):
    if not np.isfinite(reference):
        raise ValueError("Cota precisa ser finita e expressa em metros")
    area = abs(float(np.linalg.det(metric_jacobian(crs, affine))))
    arr = np.ma.asarray(values, dtype=float).filled(np.nan)
    diff = arr[np.isfinite(arr)] - reference
    if not diff.size:
        raise ValueError("Raster sem pixels validos")
    above = float(np.maximum(diff, 0).sum() * area)
    below = float(np.maximum(-diff, 0).sum() * area)
    return {"volume_above_m3": above, "volume_below_m3": below, "net_volume_m3": above-below,
            "area_above_m2": float((diff > 0).sum() * area), "pixel_area_m2": area,
            "reference_elevation_m": reference, "vertical_units": "m", "vertical_units_assumed": True}

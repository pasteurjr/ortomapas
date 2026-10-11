"""Metric calculations with explicit CRS contracts; GeoJSON defaults to WGS84."""
import math

from pyproj import CRS, Transformer
from shapely.geometry import mapping, shape
from shapely.ops import transform


def metric_geometries(objects, crs="EPSG:4326"):
    source = CRS.from_user_input(crs)
    geometries = [shape(obj) for obj in objects]
    if any(g.is_empty or not g.is_valid or not all(math.isfinite(v) for v in g.bounds) for g in geometries):
        raise ValueError("Geometria vazia, invalida ou nao finita")
    if source.is_projected:
        factors = [axis.unit_conversion_factor for axis in source.axis_info[:2]]
        if len(factors) != 2 or any(not math.isfinite(f) or f <= 0 for f in factors):
            raise ValueError("Unidades horizontais desconhecidas")
        geometries = [transform(lambda x, y, z=None: (x * factors[0], y * factors[1]), g) for g in geometries]
        return geometries, source, None, factors
    if not source.is_geographic:
        raise ValueError("CRS precisa ser geografico ou projetado")
    wgs = Transformer.from_crs(source, 4326, always_xy=True)
    geographic = [transform(wgs.transform, g) for g in geometries]
    left = min(g.bounds[0] for g in geographic); right = max(g.bounds[2] for g in geographic)
    bottom = min(g.bounds[1] for g in geographic); top = max(g.bounds[3] for g in geographic)
    if not (-180 <= left <= right <= 180 and -80 <= bottom <= top <= 84) or right-left > 6 or top-bottom > 6:
        raise ValueError("Extensao fora do dominio local UTM; forneca CRS projetado adequado")
    lon, lat = (left+right)/2, (bottom+top)/2
    zone = min(60, max(1, int((lon+180)/6)+1))
    target = CRS.from_epsg((32600 if lat >= 0 else 32700)+zone)
    forward = Transformer.from_crs(source, target, always_xy=True)
    inverse = Transformer.from_crs(target, source, always_xy=True)
    return [transform(forward.transform, g) for g in geometries], target, inverse, None


def geometry_metrics(operation, args):
    source = args.get("crs", "EPSG:4326")
    objects = [args["geometry"]] if operation in {"medir_geometria", "buffer_geometria"} else [args["a"], args["b"]]
    geometries, metric_crs, inverse, factors = metric_geometries(objects, source)
    info = {"crs_entrada": str(source), "crs_calculo": metric_crs.to_string(), "metodo": "projecao_local" if inverse else "plano_projetado"}
    if operation == "medir_geometria":
        g = geometries[0]
        return {**info, "area": g.area, "area_m2": g.area, "perimetro": g.length, "perimetro_m": g.length, "tipo": g.geom_type, "unidade_area": "m2", "unidade_distancia": "m"}
    if operation == "distancia_geometrias":
        distance = geometries[0].distance(geometries[1])
        return {**info, "distancia": distance, "distancia_m": distance, "unidade": "m"}
    if operation == "buffer_geometria":
        distance = float(args["distancia"])
        if not math.isfinite(distance) or distance < 0:
            raise ValueError("Distancia de buffer precisa ser finita e nao negativa, em metros")
        result = geometries[0].buffer(distance)
        info.update(distancia=distance, distancia_m=distance, unidade="m")
    else:
        result = geometries[0].intersection(geometries[1])
    if inverse:
        result = transform(inverse.transform, result)
    else:
        result = transform(lambda x, y, z=None: (x / factors[0], y / factors[1]), result)
    return {**info, "geometry": mapping(result), "crs_saida": str(source)}

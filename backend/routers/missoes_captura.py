"""Fase 1 do planejador de missoes de captura.

Mantem um contrato canonico independente de Litchi, Dronelink ou Map Pilot Pro.
O motor geometrico e o exportador serao adicionados nas fases seguintes.
"""

import csv
import heapq
import io
import json
import logging
import math
from xml.sax.saxutils import escape
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from pyproj import CRS, Transformer
from shapely.affinity import rotate
from shapely.geometry import LineString, Point, shape, mapping
from shapely.ops import transform as shapely_transform, unary_union

from backend.database.connection import get_connection
from backend.routers.auth import current_user, require_project_role

logger = logging.getLogger(__name__)
router = APIRouter()


class GeoJSONGeometry(BaseModel):
    type: str
    coordinates: list[Any]


class CaptureMissionCreate(BaseModel):
    nome: str = Field(..., min_length=1, max_length=255)
    descricao: Optional[str] = None
    drone_perfil: dict[str, Any] = Field(default_factory=dict)
    camera_perfil: dict[str, Any] = Field(default_factory=dict)
    crs: str = Field(default="EPSG:4326", pattern=r"^EPSG:\d+$")
    takeoff: dict[str, Any] = Field(default_factory=dict)
    capture: dict[str, Any] = Field(default_factory=dict)
    aoi: Optional[GeoJSONGeometry] = None
    zonas_exclusao: list[GeoJSONGeometry] = Field(default_factory=list)
    canonical: dict[str, Any] = Field(default_factory=dict)


class CaptureMissionPatch(BaseModel):
    nome: Optional[str] = Field(None, min_length=1, max_length=255)
    descricao: Optional[str] = None
    status: Optional[str] = Field(None, pattern=r"^(rascunho|em_revisao|aprovada|executada|arquivada)$")
    drone_perfil: Optional[dict[str, Any]] = None
    camera_perfil: Optional[dict[str, Any]] = None
    takeoff: Optional[dict[str, Any]] = None
    capture: Optional[dict[str, Any]] = None
    canonical: Optional[dict[str, Any]] = None
    aoi: Optional[GeoJSONGeometry] = None
    zonas_exclusao: Optional[list[GeoJSONGeometry]] = None


class GridGenerationRequest(BaseModel):
    orientacao_graus: float = Field(default=0, ge=-180, le=180)
    double_grid: bool = False
    espacamento_linhas_m: Optional[float] = Field(default=None, gt=0)
    espacamento_fotos_m: Optional[float] = Field(default=None, gt=0)
    max_bateria_minutos: int = Field(default=18, ge=1, le=120)
    max_waypoints: int = Field(default=15000, ge=100, le=50000)


class MissionWaypointInput(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    altitude_m: Optional[float] = None
    velocidade_ms: Optional[float] = None
    gimbal_graus: Optional[float] = None
    rumo_graus: Optional[float] = None
    captura_foto: bool = True


class MissionWaypointsUpdate(BaseModel):
    waypoints: list[MissionWaypointInput] = Field(..., min_length=1, max_length=50000)


def _local_transformers(geometry):
    centroid = geometry.centroid
    zone = int((centroid.x + 180) / 6) + 1
    epsg = 32600 + zone if centroid.y >= 0 else 32700 + zone
    to_local = Transformer.from_crs("EPSG:4326", f"EPSG:{epsg}", always_xy=True).transform
    from_local = Transformer.from_crs(f"EPSG:{epsg}", "EPSG:4326", always_xy=True).transform
    return to_local, from_local, f"EPSG:{epsg}"


def _line_parts(geometry):
    if geometry.is_empty:
        return []
    if geometry.geom_type == "LineString":
        return [geometry]
    if geometry.geom_type in {"MultiLineString", "GeometryCollection"}:
        return [part for part in geometry.geoms if part.geom_type == "LineString" and not part.is_empty]
    return []


def _sample_line(line, spacing):
    length = line.length
    if length <= 0:
        return []
    count = max(1, int(math.ceil(length / spacing)))
    return [line.interpolate(min(length, index * length / count)) for index in range(count + 1)]


def _route_connector(start, end, safe_area):
    """Find a shortest visibility-graph path inside the AOI minus exclusions."""
    safe = safe_area.buffer(0.01)
    direct = LineString([start, end])
    if safe.covers(direct):
        return [end]
    polygons = list(safe.geoms) if safe.geom_type == "MultiPolygon" else [safe]
    boundary = []
    for polygon in polygons:
        boundary.extend(list(polygon.exterior.coords)[:-1])
        for ring in polygon.interiors:
            boundary.extend(list(ring.coords)[:-1])
    if len(boundary) > 600:
        stride = math.ceil(len(boundary) / 600)
        boundary = boundary[::stride]
    coordinates = [(start.x, start.y), (end.x, end.y)]
    seen = set(coordinates)
    for coordinate in boundary:
        key = (float(coordinate[0]), float(coordinate[1]))
        if key not in seen:
            seen.add(key)
            coordinates.append(key)
    distances = [math.inf] * len(coordinates)
    previous = [None] * len(coordinates)
    distances[0] = 0
    queue = [(0, 0)]
    while queue:
        distance, index = heapq.heappop(queue)
        if distance != distances[index]:
            continue
        if index == 1:
            break
        for neighbor, coordinate in enumerate(coordinates):
            if neighbor == index:
                continue
            segment = LineString([coordinates[index], coordinate])
            if not safe.covers(segment):
                continue
            length = math.dist(coordinates[index], coordinate)
            candidate = distance + length
            if candidate < distances[neighbor]:
                distances[neighbor] = candidate
                previous[neighbor] = index
                heapq.heappush(queue, (candidate, neighbor))
    if not math.isfinite(distances[1]):
        raise HTTPException(status_code=422, detail="Nao foi encontrada uma conexao segura entre faixas da missao")
    path = []
    cursor = 1
    while cursor is not None:
        path.append(cursor)
        cursor = previous[cursor]
    path.reverse()
    return [Point(coordinates[index]) for index in path[1:]]


def _validation_item(rule, severity, status, message, observed=None):
    return {"regra": rule, "severidade": severity, "status": status, "mensagem": message, "valor_observado": observed or {}}


def _validate_mission_geometry(aoi_geometry, exclusions, waypoint_rows):
    issues = []
    if aoi_geometry is None or aoi_geometry.is_empty or not aoi_geometry.is_valid or aoi_geometry.area <= 0:
        issues.append(_validation_item("aoi_valida", "critico", "bloqueado", "A AOI esta vazia ou possui geometria invalida"))
        return issues
    to_local, _from_local, local_crs = _local_transformers(aoi_geometry)
    aoi_local = shapely_transform(to_local, aoi_geometry)
    exclusion_local = [shapely_transform(to_local, item) for item in exclusions]
    issues.append(_validation_item("aoi_valida", "info", "aprovado", "AOI valida e com area positiva", {"area_m2": round(aoi_local.area, 2), "crs_metrico": local_crs}))
    if len(waypoint_rows) < 2:
        issues.append(_validation_item("waypoints_minimos", "critico", "bloqueado", "A missao precisa de pelo menos dois waypoints", {"quantidade": len(waypoint_rows)}))
        return issues
    issues.append(_validation_item("waypoints_minimos", "info", "aprovado", "Quantidade minima de waypoints atendida", {"quantidade": len(waypoint_rows)}))
    forbidden = unary_union(exclusion_local) if exclusion_local else None
    outside = 0
    in_exclusion = 0
    aoi_tolerant = aoi_local.buffer(2)
    route_points = []
    for row in waypoint_rows:
        point = shapely_transform(to_local, Point(float(row["longitude"]), float(row["latitude"])))
        route_points.append(point)
        if not aoi_tolerant.covers(point):
            outside += 1
        if forbidden and forbidden.covers(point):
            in_exclusion += 1
    issues.append(_validation_item("waypoints_na_aoi", "critico" if outside else "info", "bloqueado" if outside else "aprovado", f"{outside} waypoint(s) fora da AOI", {"fora_aoi": outside, "total": len(waypoint_rows)}))
    crossed = sum(1 for left, right in zip(route_points, route_points[1:]) if forbidden and LineString([left, right]).intersects(forbidden))
    exclusion_issues = in_exclusion + crossed
    issues.append(_validation_item("zonas_exclusao", "critico" if exclusion_issues else "info", "bloqueado" if exclusion_issues else "aprovado", f"{in_exclusion} waypoint(s) em zona de exclusao; {crossed} trecho(s) cruzam zona proibida", {"waypoints_em_exclusao": in_exclusion, "trechos_cruzados": crossed, "tolerancia_aoi_m": 2}))
    return issues


def _generate_grid(aoi_geometry, exclusions, request, capture):
    to_local, from_local, local_crs = _local_transformers(aoi_geometry)
    area = shapely_transform(to_local, aoi_geometry)
    exclusion_union = unary_union([shapely_transform(to_local, item) for item in exclusions]).buffer(2) if exclusions else None
    if exclusion_union and not exclusion_union.is_empty:
        area = area.difference(exclusion_union)
    if area.is_empty:
        raise HTTPException(status_code=422, detail="As zonas de exclusao removem toda a AOI")

    altitude = float(capture.get("altitude_m") or 50)
    front_overlap = float(capture.get("front_overlap", capture.get("overlap_frontal", 0.8)) or 0.8)
    side_overlap = float(capture.get("side_overlap", capture.get("overlap_lateral", 0.7)) or 0.7)
    camera = capture.get("camera_perfil") or {}
    fov_diagonal = camera.get("fov_diagonal_deg")
    resolution = camera.get("resolucao_px") or [4_000, 3_000]
    if fov_diagonal:
        half_diagonal = math.radians(float(fov_diagonal) / 2)
        aspect = float(resolution[0]) / float(resolution[1])
        diagonal_ratio = math.sqrt(aspect * aspect + 1)
        footprint_width = 2 * altitude * math.tan(half_diagonal) * aspect / diagonal_ratio
        footprint_height = 2 * altitude * math.tan(half_diagonal) / diagonal_ratio
    else:
        footprint_width = float(capture.get("footprint_width_m") or max(20.0, altitude * 0.8))
        footprint_height = float(capture.get("footprint_height_m") or footprint_width * 0.75)
    line_spacing = float(request.espacamento_linhas_m or capture.get("espacamento_linhas_m") or footprint_width * (1 - side_overlap))
    photo_spacing = float(request.espacamento_fotos_m or capture.get("espacamento_fotos_m") or footprint_height * (1 - front_overlap))
    line_spacing = max(1.0, line_spacing)
    photo_spacing = max(1.0, photo_spacing)

    def pass_at(angle):
        rotated_area = rotate(area, -angle, origin="centroid", use_radians=False)
        minx, miny, maxx, maxy = rotated_area.bounds
        lines = []
        y = miny - line_spacing
        while y <= maxy + line_spacing:
            candidate = LineString([(minx - line_spacing, y), (maxx + line_spacing, y)])
            for part in _line_parts(candidate.intersection(rotated_area)):
                points = _sample_line(part, photo_spacing)
                if angle and points:
                    points = [rotate(point, angle, origin=area.centroid, use_radians=False) for point in points]
                lines.append(points)
            y += line_spacing
        return lines

    passes = pass_at(request.orientacao_graus)
    if request.double_grid:
        passes.extend(pass_at(request.orientacao_graus + 90))
    waypoints = []
    capture_flags = []
    for line_index, points in enumerate(passes):
        if line_index % 2:
            points = list(reversed(points))
        for point in points:
            if waypoints:
                connector = _route_connector(waypoints[-1], point, area)
                for transit_point in connector[:-1]:
                    waypoints.append(transit_point)
                    capture_flags.append(False)
            waypoints.append(point)
            capture_flags.append(True)
    if len(waypoints) < 2:
        raise HTTPException(status_code=422, detail="A AOI nao gerou linhas de cobertura suficientes")
    return waypoints, {"local_crs": local_crs, "line_spacing_m": line_spacing, "photo_spacing_m": photo_spacing, "footprint_width_m": round(footprint_width, 2), "footprint_height_m": round(footprint_height, 2), "front_overlap": front_overlap, "side_overlap": side_overlap, "lines": len(passes), "photos": sum(capture_flags), "capture_flags": capture_flags, "double_grid": request.double_grid, "to_local": to_local, "from_local": from_local}


def _geometry_json(geometry: GeoJSONGeometry) -> str:
    if geometry.type not in {"Point", "LineString", "Polygon", "MultiPolygon", "MultiLineString"}:
        raise HTTPException(status_code=422, detail=f"Geometria nao suportada: {geometry.type}")
    if not geometry.coordinates:
        raise HTTPException(status_code=422, detail="Geometria sem coordenadas")
    return json.dumps(geometry.model_dump(), separators=(",", ":"))


def _canonical_payload(data: CaptureMissionCreate, mission_id: Optional[int] = None) -> dict[str, Any]:
    payload = dict(data.canonical)
    payload.update({
        "schema": "ortomapas.capture-mission/1.0",
        "mission_id": str(mission_id) if mission_id is not None else None,
        "crs": data.crs,
        "takeoff": data.takeoff,
        "drone": data.drone_perfil,
        "camera": data.camera_perfil,
        "capture": data.capture,
    })
    return payload


def _serialize_mission(cursor, row: dict[str, Any]) -> dict[str, Any]:
    mission = dict(row)
    mission["areas"] = []
    mission["parametros"] = None
    mission["waypoints"] = []
    mission["blocos"] = []
    cursor.execute(
        """
        SELECT id, tipo, nome, ST_AsGeoJSON(geometria)::json AS geometria, propriedades
        FROM missoes_areas WHERE missao_id = %s ORDER BY id
        """,
        (row["id"],),
    )
    mission["areas"] = cursor.fetchall()
    cursor.execute("SELECT * FROM missoes_parametros WHERE missao_id = %s", (row["id"],))
    mission["parametros"] = cursor.fetchone()
    cursor.execute(
        """
        SELECT id, bloco_id, ordem, ST_X(geometria) AS longitude, ST_Y(geometria) AS latitude,
               altitude_m, altitude_agl_m, rumo_graus, velocidade_ms, gimbal_graus, acoes, propriedades
        FROM missoes_waypoints WHERE missao_id = %s ORDER BY ordem
        """,
        (row["id"],),
    )
    mission["waypoints"] = cursor.fetchall()
    cursor.execute("SELECT * FROM missoes_blocos WHERE missao_id = %s ORDER BY ordem", (row["id"],))
    mission["blocos"] = cursor.fetchall()
    return mission


@router.post("/projetos/{projeto_id}/missoes-captura", status_code=201)
async def create_capture_mission(
    projeto_id: int,
    data: CaptureMissionCreate,
    user: dict = Depends(current_user),
):
    require_project_role(projeto_id, user, {"proprietario", "editor"})
    if data.crs != "EPSG:4326":
        raise HTTPException(status_code=422, detail="A exportacao inicial exige CRS EPSG:4326")

    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT id FROM projetos WHERE id = %s", (projeto_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Projeto nao encontrado")
            cursor.execute(
                """
                INSERT INTO missoes_captura
                    (projeto_id, nome, descricao, drone_perfil, camera_perfil, crs, takeoff, canonical, criado_por)
                VALUES (%s, %s, %s, %s::jsonb, %s::jsonb, %s, %s::jsonb, %s::jsonb, %s)
                RETURNING id
                """,
                (
                    projeto_id,
                    data.nome,
                    data.descricao,
                    json.dumps(data.drone_perfil),
                    json.dumps(data.camera_perfil),
                    data.crs,
                    json.dumps(data.takeoff),
                    json.dumps(_canonical_payload(data)),
                    user["id"],
                ),
            )
            mission_id = cursor.fetchone()["id"]
            cursor.execute("UPDATE missoes_captura SET canonical = jsonb_set(canonical, '{mission_id}', to_jsonb(%s::text)) WHERE id = %s", (str(mission_id), mission_id))
            capture = data.capture
            cursor.execute(
                """
                INSERT INTO missoes_parametros
                    (missao_id, gsd_cm_px, overlap_frontal, overlap_lateral, altitude_m,
                     altitude_referencia, velocidade_ms, gimbal_graus, intervalo_segundos,
                     espacamento_linhas_m, reserva_bateria_pct, parametros)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                """,
                (
                    mission_id,
                    capture.get("gsd_cm_px"),
                    capture.get("overlap_frontal", capture.get("front_overlap")),
                    capture.get("overlap_lateral", capture.get("side_overlap")),
                    capture.get("altitude_m"),
                    capture.get("altitude_referencia", "AGL"),
                    capture.get("velocidade_ms"),
                    capture.get("gimbal_graus", -90),
                    capture.get("intervalo_segundos"),
                    capture.get("espacamento_linhas_m"),
                    capture.get("reserva_bateria_pct", 25),
                    json.dumps(capture),
                ),
            )
            if data.aoi:
                cursor.execute(
                    "INSERT INTO missoes_areas (missao_id, tipo, nome, geometria) VALUES (%s, 'aoi', 'Area de interesse', ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326))",
                    (mission_id, _geometry_json(data.aoi)),
                )
            for index, zone in enumerate(data.zonas_exclusao, start=1):
                cursor.execute(
                    "INSERT INTO missoes_areas (missao_id, tipo, nome, geometria) VALUES (%s, 'exclusao', %s, ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326))",
                    (mission_id, f"Zona de exclusao {index}", _geometry_json(zone)),
                )
            conn.commit()
            cursor.execute("SELECT * FROM missoes_captura WHERE id = %s", (mission_id,))
            return _serialize_mission(cursor, cursor.fetchone())
        except HTTPException:
            conn.rollback()
            raise
        except Exception as exc:
            conn.rollback()
            logger.exception("Erro ao criar missao de captura")
            raise HTTPException(status_code=500, detail="Falha ao persistir missao de captura") from exc
        finally:
            cursor.close()


@router.post("/missoes-captura/{missao_id}/gerar-grid")
async def generate_capture_grid(
    missao_id: int,
    data: GridGenerationRequest,
    user: dict = Depends(current_user),
):
    """Gera uma cobertura nadir determinística e grava waypoints/blocos."""
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM missoes_captura WHERE id = %s", (missao_id,))
            mission = cursor.fetchone()
            if not mission:
                raise HTTPException(status_code=404, detail="Missao de captura nao encontrada")
            require_project_role(mission["projeto_id"], user, {"proprietario", "editor"})
            cursor.execute("SELECT * FROM missoes_parametros WHERE missao_id = %s", (missao_id,))
            parameters = cursor.fetchone() or {}
            cursor.execute("SELECT ST_AsGeoJSON(geometria)::json AS geometria FROM missoes_areas WHERE missao_id = %s AND tipo = 'aoi' LIMIT 1", (missao_id,))
            aoi_row = cursor.fetchone()
            if not aoi_row:
                raise HTTPException(status_code=422, detail="A missao nao possui AOI")
            cursor.execute("SELECT ST_AsGeoJSON(geometria)::json AS geometria FROM missoes_areas WHERE missao_id = %s AND tipo = 'exclusao'", (missao_id,))
            exclusions_rows = cursor.fetchall()
            aoi_geometry = shape(aoi_row["geometria"])
            exclusion_geometries = [shape(row["geometria"]) for row in exclusions_rows]
            capture = dict(parameters.get("parametros") or {})
            capture["camera_perfil"] = mission.get("camera_perfil") or {}
            capture.setdefault("altitude_m", parameters.get("altitude_m"))
            capture.setdefault("overlap_frontal", parameters.get("overlap_frontal"))
            capture.setdefault("overlap_lateral", parameters.get("overlap_lateral"))
            waypoints, stats = _generate_grid(aoi_geometry, exclusion_geometries, data, capture)
            if len(waypoints) > data.max_waypoints:
                raise HTTPException(status_code=422, detail=f"Grid gerou {len(waypoints)} pontos; aumente os espacamentos (limite {data.max_waypoints})")
            capture_flags = stats.pop("capture_flags")
            _to_local, from_local, local_crs = _local_transformers(aoi_geometry)
            # _generate_grid retorna os pontos no CRS métrico local; a
            # conversão para WGS84 acontece somente ao persistir/exportar.
            local_points = waypoints
            distance_m = sum(local_points[index - 1].distance(local_points[index]) for index in range(1, len(local_points)))
            speed = max(0.5, float(parameters.get("velocidade_ms") or capture.get("velocidade_ms") or 4))
            time_seconds = distance_m / speed
            reserve_pct = float(parameters.get("reserva_bateria_pct") or 25)
            usable_seconds = data.max_bateria_minutos * 60 * (1 - reserve_pct / 100)
            max_distance_per_block = speed * usable_seconds
            takeoff = mission.get("takeoff") or {}
            if takeoff.get("lat") is not None and takeoff.get("lon") is not None:
                home = shapely_transform(_to_local, Point(float(takeoff["lon"]), float(takeoff["lat"])))
            else:
                home = local_points[0]
            blocks = []
            current_indices = []
            current_distance = 0.0
            for index, point in enumerate(local_points):
                approach = home.distance(point) if not current_indices else local_points[index - 1].distance(point)
                proposed_distance = current_distance + approach + point.distance(home)
                if current_indices and proposed_distance > max_distance_per_block:
                    return_distance = local_points[current_indices[-1]].distance(home)
                    blocks.append((current_indices, current_distance + return_distance))
                    current_indices = []
                    current_distance = 0.0
                    approach = home.distance(point)
                current_indices.append(index)
                current_distance += approach
            if current_indices:
                blocks.append((current_indices, current_distance + local_points[current_indices[-1]].distance(home)))
            if any(block_distance > max_distance_per_block for _, block_distance in blocks):
                raise HTTPException(status_code=422, detail="A rota possui um trecho que excede a autonomia disponivel com a reserva configurada")
            block_count = len(blocks)

            cursor.execute("DELETE FROM missoes_waypoints WHERE missao_id = %s", (missao_id,))
            cursor.execute("DELETE FROM missoes_blocos WHERE missao_id = %s", (missao_id,))
            cursor.execute("DELETE FROM missoes_validacoes WHERE missao_id = %s", (missao_id,))
            block_ids = []
            waypoint_block_ids = {}
            block_summaries = []
            for block_order, (indices, block_distance) in enumerate(blocks):
                start, end = indices[0], indices[-1] + 1
                photos_in_block = sum(capture_flags[index] for index in indices)
                block_time = block_distance / speed
                cursor.execute(
                    """
                    INSERT INTO missoes_blocos (missao_id, ordem, nome, estimativa_fotos, distancia_m, tempo_segundos, bateria, propriedades)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb) RETURNING id
                    """,
                    (missao_id, block_order + 1, f"Bloco {block_order + 1:02d}", photos_in_block, block_distance, block_time, int(math.ceil(block_time / 60)), json.dumps({"gerado_por": "grid", "local_crs": local_crs, "reserva_pct": reserve_pct, "waypoint_inicio": start + 1, "waypoint_fim": end})),
                )
                block_id = cursor.fetchone()["id"]
                block_ids.append(block_id)
                for waypoint_index in indices:
                    waypoint_block_ids[waypoint_index] = block_id
                block_summaries.append({"ordem": block_order + 1, "waypoint_inicio": start + 1, "waypoint_fim": end, "fotos": photos_in_block, "distancia_m": round(block_distance, 2), "tempo_segundos": round(block_time, 2), "tempo_utilizavel_segundos": round(usable_seconds, 2)})
            altitude = float(parameters.get("altitude_m") or capture.get("altitude_m") or 50)
            gimbal = float(parameters.get("gimbal_graus") or capture.get("gimbal_graus") or -90)
            for index, (point, local_point) in enumerate(zip(waypoints, local_points)):
                lon, lat = from_local(local_point.x, local_point.y)
                block_id = waypoint_block_ids[index]
                cursor.execute(
                    """
                    INSERT INTO missoes_waypoints
                        (missao_id, bloco_id, ordem, geometria, altitude_m, altitude_agl_m, velocidade_ms, gimbal_graus, acoes, propriedades)
                    VALUES (%s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326), %s, %s, %s, %s, %s::jsonb, %s::jsonb)
                    """,
                    (missao_id, block_id, index + 1, lon, lat, altitude, altitude, speed, gimbal, json.dumps(["Take Photo"] if capture_flags[index] else []), json.dumps({"captura_foto": capture_flags[index]})),
                )
            canonical = dict(mission.get("canonical") or {})
            canonical["grid"] = {key: value for key, value in stats.items() if key not in {"to_local", "from_local"}}
            canonical["blocks"] = block_summaries
            canonical.pop("validation", None)
            canonical["coverage_stale"] = False
            canonical["waypoints"] = [{"lat": float(from_local(point.x, point.y)[1]), "lon": float(from_local(point.x, point.y)[0]), "altitude_m": altitude, "captura_foto": capture_flags[index]} for index, point in enumerate(local_points)]
            cursor.execute("UPDATE missoes_captura SET canonical = %s::jsonb, versao = versao + 1, atualizado_em = %s WHERE id = %s", (json.dumps(canonical), datetime.now(timezone.utc), missao_id))
            conn.commit()
            return {"missao_id": missao_id, "status": "gerado", "grid": canonical["grid"], "waypoints": len(waypoints), "fotos": sum(capture_flags), "distancia_m": round(distance_m, 2), "tempo_segundos": round(time_seconds, 2), "blocos": block_count, "blocos_detalhe": block_summaries, "local_crs": local_crs}
        except HTTPException:
            conn.rollback()
            raise
        except Exception as exc:
            conn.rollback()
            logger.exception("Erro ao gerar grid da missao")
            raise HTTPException(status_code=500, detail="Falha ao gerar grid") from exc
        finally:
            cursor.close()


@router.put("/missoes-captura/{missao_id}/waypoints")
async def update_capture_waypoints(
    missao_id: int,
    data: MissionWaypointsUpdate,
    user: dict = Depends(current_user),
):
    """Persiste a ordem e propriedades editadas no editor cartografico."""
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM missoes_captura WHERE id = %s", (missao_id,))
            mission = cursor.fetchone()
            if not mission:
                raise HTTPException(status_code=404, detail="Missao de captura nao encontrada")
            require_project_role(mission["projeto_id"], user, {"proprietario", "editor"})
            cursor.execute("SELECT * FROM missoes_parametros WHERE missao_id = %s", (missao_id,))
            params = cursor.fetchone() or {}
            altitude = float(params.get("altitude_m") or 50)
            speed = float(params.get("velocidade_ms") or 4)
            gimbal = float(params.get("gimbal_graus") or -90)
            cursor.execute("DELETE FROM missoes_waypoints WHERE missao_id = %s", (missao_id,))
            cursor.execute("DELETE FROM missoes_blocos WHERE missao_id = %s", (missao_id,))
            cursor.execute("DELETE FROM missoes_validacoes WHERE missao_id = %s", (missao_id,))
            cursor.execute(
                "INSERT INTO missoes_blocos (missao_id, ordem, nome, estimativa_fotos, propriedades) VALUES (%s, 1, 'Bloco editado', %s, %s::jsonb) RETURNING id",
                (missao_id, len(data.waypoints), json.dumps({"origem": "editor_fase4"})),
            )
            block_id = cursor.fetchone()["id"]
            canonical_points = []
            for order, point in enumerate(data.waypoints, start=1):
                point_altitude = float(point.altitude_m or altitude)
                point_speed = float(point.velocidade_ms or speed)
                point_gimbal = float(point.gimbal_graus if point.gimbal_graus is not None else gimbal)
                cursor.execute(
                    """
                    INSERT INTO missoes_waypoints
                        (missao_id, bloco_id, ordem, geometria, altitude_m, altitude_agl_m,
                         rumo_graus, velocidade_ms, gimbal_graus, acoes, propriedades)
                    VALUES (%s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326), %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb)
                    """,
                    (missao_id, block_id, order, point.lon, point.lat, point_altitude, point_altitude, point.rumo_graus, point_speed, point_gimbal, json.dumps(["Take Photo"] if point.captura_foto else []), json.dumps({"editado": True})),
                )
                canonical_points.append({"lat": point.lat, "lon": point.lon, "altitude_m": point_altitude, "velocidade_ms": point_speed, "gimbal_graus": point_gimbal, "rumo_graus": point.rumo_graus, "captura_foto": point.captura_foto})
            canonical = dict(mission.get("canonical") or {})
            canonical["waypoints"] = canonical_points
            canonical["editado_por_editor"] = True
            canonical.pop("validation", None)
            cursor.execute("UPDATE missoes_captura SET canonical = %s::jsonb, versao = versao + 1, atualizado_em = %s WHERE id = %s", (json.dumps(canonical), datetime.now(timezone.utc), missao_id))
            conn.commit()
            cursor.execute("SELECT * FROM missoes_captura WHERE id = %s", (missao_id,))
            return _serialize_mission(cursor, cursor.fetchone())
        except HTTPException:
            conn.rollback()
            raise
        except Exception as exc:
            conn.rollback()
            logger.exception("Erro ao persistir waypoints editados")
            raise HTTPException(status_code=500, detail="Falha ao salvar waypoints") from exc
        finally:
            cursor.close()


@router.post("/missoes-captura/{missao_id}/validar")
async def validate_capture_mission(missao_id: int, user: dict = Depends(current_user)):
    """Executa as regras de segurança, fotogrametria e compatibilidade simulada."""
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM missoes_captura WHERE id = %s", (missao_id,))
            mission = cursor.fetchone()
            if not mission:
                raise HTTPException(status_code=404, detail="Missao de captura nao encontrada")
            require_project_role(mission["projeto_id"], user, {"proprietario", "editor", "visualizador"})
            cursor.execute("SELECT * FROM missoes_parametros WHERE missao_id = %s", (missao_id,))
            params = cursor.fetchone() or {}
            cursor.execute("SELECT ST_AsGeoJSON(geometria)::json AS geometria FROM missoes_areas WHERE missao_id = %s AND tipo = 'aoi' LIMIT 1", (missao_id,))
            aoi_row = cursor.fetchone()
            cursor.execute("SELECT ST_AsGeoJSON(geometria)::json AS geometria FROM missoes_areas WHERE missao_id = %s AND tipo = 'exclusao'", (missao_id,))
            exclusions = [shape(row["geometria"]) for row in cursor.fetchall()]
            cursor.execute("""
                SELECT id, ordem, ST_X(geometria) AS longitude, ST_Y(geometria) AS latitude,
                       altitude_m, velocidade_ms, gimbal_graus, acoes
                FROM missoes_waypoints WHERE missao_id = %s ORDER BY ordem
            """, (missao_id,))
            waypoints = cursor.fetchall()
            aoi_geometry = shape(aoi_row["geometria"]) if aoi_row else None
            issues = _validate_mission_geometry(aoi_geometry, exclusions, waypoints)
            if (mission.get("canonical") or {}).get("coverage_stale"):
                issues.append(_validation_item("cobertura_atualizada", "critico", "bloqueado", "Parametros ou geometria mudaram; gere novamente o grid antes de validar a missao"))
            altitude_values = [float(row["altitude_m"]) for row in waypoints if row["altitude_m"] is not None]
            speed_values = [float(row["velocidade_ms"]) for row in waypoints if row["velocidade_ms"] is not None]
            gimbal_values = [float(row["gimbal_graus"]) for row in waypoints if row["gimbal_graus"] is not None]
            altitude_min, altitude_max = (min(altitude_values), max(altitude_values)) if altitude_values else (None, None)
            speed_max = max(speed_values) if speed_values else None
            gimbal_min, gimbal_max = (min(gimbal_values), max(gimbal_values)) if gimbal_values else (None, None)
            issues.append(_validation_item("altitude_dji_mini_3", "critico" if altitude_min is None or altitude_min < 5 or altitude_max > 120 else "info", "bloqueado" if altitude_min is None or altitude_min < 5 or altitude_max > 120 else "aprovado", "Altitude compativel com o limite simulado de 5-120 m", {"min_m": altitude_min, "max_m": altitude_max, "limite_m": [5, 120]}))
            issues.append(_validation_item("velocidade_dji_mini_3", "critico" if speed_max is None or speed_max > 15 else "info", "bloqueado" if speed_max is None or speed_max > 15 else "aprovado", "Velocidade dentro do limite simulado de 15 m/s", {"max_ms": speed_max, "limite_ms": 15}))
            issues.append(_validation_item("gimbal_nadir", "aviso" if gimbal_min is None or gimbal_min < -90 or gimbal_max > 0 else "info", "aviso" if gimbal_min is None or gimbal_min < -90 or gimbal_max > 0 else "aprovado", "Gimbal nadir recomendado em -90 graus", {"min_graus": gimbal_min, "max_graus": gimbal_max, "recomendado": -90}))
            front = float(params.get("overlap_frontal") or 0)
            side = float(params.get("overlap_lateral") or 0)
            overlap_status = "bloqueado" if front < 0.6 or side < 0.6 else ("aviso" if front < 0.75 or side < 0.7 else "aprovado")
            overlap_severity = "critico" if overlap_status == "bloqueado" else ("aviso" if overlap_status == "aviso" else "info")
            issues.append(_validation_item("overlap_fotogrametrico", overlap_severity, overlap_status, "Sobreposicao frontal/lateral avaliada para ortomosaico", {"frontal": front, "lateral": side, "recomendado": {"frontal": 0.8, "lateral": 0.7}}))
            camera = dict(mission.get("camera_perfil") or {})
            resolution = camera.get("resolucao_px") or camera.get("resolution_px")
            megapixels = None
            if isinstance(resolution, (list, tuple)) and len(resolution) == 2:
                megapixels = (float(resolution[0]) * float(resolution[1])) / 1_000_000
            image_status = "aprovado" if megapixels is not None and megapixels <= 48 else "aviso"
            issues.append(_validation_item("compatibilidade_imagem", "info" if image_status == "aprovado" else "aviso", image_status, "Perfil de imagem simulado; confirmacao fisica depende do firmware e do aplicativo de voo", {"formato": camera.get("formato", "JPEG"), "resolucao_px": resolution or "nao informada", "megapixels": megapixels, "limite_simulado": 48, "tamanho_estimado_mb": camera.get("tamanho_medio_mb", "nao informado")}))
            distance_m = 0.0
            if len(waypoints) > 1:
                geometry = aoi_geometry
                if geometry:
                    to_local, _from_local, _crs = _local_transformers(geometry)
                    local_points = [shapely_transform(to_local, Point(float(row["longitude"]), float(row["latitude"]))) for row in waypoints]
                    distance_m = sum(local_points[index - 1].distance(local_points[index]) for index in range(1, len(local_points)))
            speed = max(0.5, speed_max or float(params.get("velocidade_ms") or 4))
            usable_seconds = 18 * 60 * (1 - float(params.get("reserva_bateria_pct") or 25) / 100)
            cursor.execute("SELECT ordem, distancia_m, tempo_segundos, estimativa_fotos FROM missoes_blocos WHERE missao_id = %s ORDER BY ordem", (missao_id,))
            blocks = cursor.fetchall()
            block_times = [float(block["tempo_segundos"] or 0) for block in blocks]
            max_block_seconds = max(block_times) if block_times else distance_m / speed
            autonomy_status = "bloqueado" if max_block_seconds > usable_seconds else ("aviso" if max_block_seconds > usable_seconds * .8 else "aprovado")
            issues.append(_validation_item("autonomia_bateria", "critico" if autonomy_status == "bloqueado" else ("aviso" if autonomy_status == "aviso" else "info"), autonomy_status, "Duracao de cada bloco comparada com bateria util e reserva configurada", {"distancia_rota_m": round(distance_m, 2), "blocos": len(blocks), "maior_bloco_segundos": round(max_block_seconds, 2), "tempo_utilizavel_por_bloco_segundos": round(usable_seconds, 2), "reserva_pct": params.get("reserva_bateria_pct", 25), "detalhes": [{"ordem": block["ordem"], "tempo_segundos": round(float(block["tempo_segundos"] or 0), 2), "fotos": block["estimativa_fotos"]} for block in blocks]}))
            cursor.execute("DELETE FROM missoes_validacoes WHERE missao_id = %s", (missao_id,))
            blocked = sum(1 for item in issues if item["status"] == "bloqueado")
            warnings = sum(1 for item in issues if item["status"] == "aviso")
            overall = "bloqueado" if blocked else ("aviso" if warnings else "aprovado")
            for item in issues:
                cursor.execute("INSERT INTO missoes_validacoes (missao_id, regra, severidade, status, mensagem, valor_observado) VALUES (%s, %s, %s, %s, %s, %s::jsonb)", (missao_id, item["regra"], item["severidade"], item["status"], item["mensagem"], json.dumps(item["valor_observado"])))
            cursor.execute("UPDATE missoes_captura SET canonical = jsonb_set(canonical, '{validation}', %s::jsonb), atualizado_em = %s WHERE id = %s", (json.dumps({"status": overall, "blocked": blocked, "warnings": warnings}), datetime.now(timezone.utc), missao_id))
            conn.commit()
            return {"missao_id": missao_id, "status": overall, "blocked": blocked, "warnings": warnings, "rules": issues, "simulation": {"waypoints": len(waypoints), "distance_m": round(distance_m, 2), "image_profile": camera or {"formato": "JPEG"}}}
        except HTTPException:
            conn.rollback()
            raise
        except Exception as exc:
            conn.rollback()
            logger.exception("Erro ao validar missao")
            raise HTTPException(status_code=500, detail="Falha ao validar missao") from exc
        finally:
            cursor.close()


@router.get("/missoes-captura")
async def list_capture_missions(
    projeto_id: Optional[int] = Query(None),
    user: dict = Depends(current_user),
):
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        if projeto_id is not None:
            require_project_role(projeto_id, user, {"proprietario", "editor", "visualizador"})
            query = "SELECT * FROM missoes_captura WHERE projeto_id = %s ORDER BY atualizado_em DESC"
            params = (projeto_id,)
        elif user["perfil"] == "admin":
            query = "SELECT * FROM missoes_captura ORDER BY atualizado_em DESC"
            params = ()
        else:
            query = """
                SELECT m.* FROM missoes_captura m
                JOIN projeto_usuarios pu ON pu.projeto_id = m.projeto_id
                WHERE pu.usuario_id = %s ORDER BY m.atualizado_em DESC
            """
            params = (user["id"],)
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return {"total": len(rows), "missoes": rows}


@router.get("/missoes-captura/{missao_id}")
async def get_capture_mission(missao_id: int, user: dict = Depends(current_user)):
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM missoes_captura WHERE id = %s", (missao_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Missao de captura nao encontrada")
        require_project_role(row["projeto_id"], user, {"proprietario", "editor", "visualizador"})
        return _serialize_mission(cursor, row)


@router.get("/missoes-captura/{missao_id}/exportar")
async def export_capture_mission(
    missao_id: int,
    formato: str = Query("kml", pattern=r"^(kml|geojson|csv|litchi_csv)$"),
    user: dict = Depends(current_user),
):
    """Exporta a rota canônica em formatos interoperáveis antes do adaptador do app de voo."""
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM missoes_captura WHERE id = %s", (missao_id,))
        mission = cursor.fetchone()
        if not mission:
            raise HTTPException(status_code=404, detail="Missao de captura nao encontrada")
        require_project_role(mission["projeto_id"], user, {"proprietario", "editor", "visualizador"})
        if (mission.get("canonical") or {}).get("coverage_stale"):
            raise HTTPException(status_code=409, detail="A cobertura esta desatualizada. Gere novamente o grid e valide a missao antes de exportar.")
        cursor.execute("SELECT *, ST_Y(geometria::geometry) AS latitude, ST_X(geometria::geometry) AS longitude FROM missoes_waypoints WHERE missao_id = %s ORDER BY ordem", (missao_id,))
        points = cursor.fetchall()
    if len(points) < 2:
        raise HTTPException(status_code=422, detail="A exportacao exige pelo menos dois waypoints")
    name = mission["nome"] or f"missao-{missao_id}"
    safe_name = "".join(char if char.isalnum() or char in "-_" else "_" for char in name).strip("_") or f"missao-{missao_id}"
    rows = [{
        "ordem": index,
        "latitude": float(point["latitude"]),
        "longitude": float(point["longitude"]),
        "altitude_m": float(point["altitude_m"] or 0),
        "velocidade_ms": float(point["velocidade_ms"] or 0),
        "gimbal_graus": float(point["gimbal_graus"] if point["gimbal_graus"] is not None else -90),
        "rumo_graus": float(point["rumo_graus"] or 0),
        "captura_foto": "Take Photo" in (point.get("acoes") or []),
    } for index, point in enumerate(points, start=1)]
    if formato in {"csv", "litchi_csv"}:
        stream = io.StringIO()
        if formato == "litchi_csv":
            capture = mission.get("canonical") or {}
            capture = capture.get("capture", capture) if isinstance(capture, dict) else {}
            distance_interval = capture.get("photo_distinterval", -1)
            headers = ["latitude", "longitude", "altitude(m)", "heading(deg)", "curvesize(m)", "rotationdir", "gimbalmode", "gimbalpitchangle", "actiontype1", "actionparam1", "altitudemode", "speed(m/s)", "poi_latitude", "poi_longitude", "poi_altitude(m)", "poi_altitudemode", "photo_timeinterval", "photo_distinterval"]
            writer = csv.writer(stream); writer.writerow(headers)
            for row in rows:
                writer.writerow([row["latitude"], row["longitude"], row["altitude_m"], row["rumo_graus"] % 360, 0, 0, 2, row["gimbal_graus"], 1 if row["captura_foto"] else 0, 0, 0, row["velocidade_ms"], 0, 0, 0, 0, -1, distance_interval])
        else:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0].keys()))
            writer.writeheader(); writer.writerows(rows)
        content, media_type, suffix = stream.getvalue(), "text/csv; charset=utf-8", "litchi.csv" if formato == "litchi_csv" else "csv"
    elif formato == "geojson":
        features = [{"type": "Feature", "properties": {key: value for key, value in row.items() if key != "latitude" and key != "longitude"}, "geometry": {"type": "Point", "coordinates": [row["longitude"], row["latitude"]]}} for row in rows]
        features.append({"type": "Feature", "properties": {"tipo": "rota", "missao_id": missao_id}, "geometry": {"type": "LineString", "coordinates": [[row["longitude"], row["latitude"]] for row in rows]}})
        content, media_type, suffix = json.dumps({"type": "FeatureCollection", "features": features, "properties": {"missao": name, "crs": "EPSG:4326"}}, ensure_ascii=False, indent=2), "application/geo+json", "geojson"
    else:
        placemarks = []
        for row in rows:
            placemarks.append(f'<Placemark><name>Waypoint {row["ordem"]}</name><ExtendedData><Data name="altitude_m"><value>{row["altitude_m"]}</value></Data><Data name="velocidade_ms"><value>{row["velocidade_ms"]}</value></Data><Data name="gimbal_graus"><value>{row["gimbal_graus"]}</value></Data></ExtendedData><Point><coordinates>{row["longitude"]},{row["latitude"]},0</coordinates></Point></Placemark>')
        coords = " ".join(f'{row["longitude"]},{row["latitude"]},0' for row in rows)
        content = f'<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>{escape(name)}</name>{"".join(placemarks)}<Placemark><name>Rota</name><LineString><tessellate>1</tessellate><coordinates>{coords}</coordinates></LineString></Placemark></Document></kml>'
        media_type, suffix = "application/vnd.google-earth.kml+xml", "kml"
    return StreamingResponse(io.BytesIO(content.encode("utf-8")), media_type=media_type, headers={"Content-Disposition": f'attachment; filename="{safe_name}.{suffix}"'})


@router.patch("/missoes-captura/{missao_id}")
async def patch_capture_mission(
    missao_id: int,
    data: CaptureMissionPatch,
    user: dict = Depends(current_user),
):
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM missoes_captura WHERE id = %s", (missao_id,))
        existing = cursor.fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Missao de captura nao encontrada")
        require_project_role(existing["projeto_id"], user, {"proprietario", "editor"})
        values = data.model_dump(exclude_unset=True)
        if not values:
            raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")
        try:
            fields: list[str] = []
            params: list[Any] = []
            canonical = dict(existing.get("canonical") or {})
            coverage_changed = (
                ("capture" in values and values["capture"] != canonical.get("capture", {}))
                or ("camera_perfil" in values and values["camera_perfil"] != (existing.get("camera_perfil") or {}))
            )
            if "aoi" in values or "zonas_exclusao" in values:
                cursor.execute("SELECT tipo, ST_AsGeoJSON(geometria)::json AS geometria FROM missoes_areas WHERE missao_id = %s", (missao_id,))
                current_areas = cursor.fetchall()
                current_aoi = next((shape(row["geometria"]) for row in current_areas if row["tipo"] == "aoi"), None)
                current_exclusions = [shape(row["geometria"]) for row in current_areas if row["tipo"] == "exclusao"]
                if "aoi" in values:
                    requested_aoi = shape(values["aoi"]) if values["aoi"] else None
                    coverage_changed = coverage_changed or (current_aoi is None) != (requested_aoi is None) or (current_aoi is not None and requested_aoi is not None and not current_aoi.equals(requested_aoi))
                if "zonas_exclusao" in values:
                    requested_exclusions = [shape(item) for item in values["zonas_exclusao"]]
                    old_union = unary_union(current_exclusions) if current_exclusions else None
                    new_union = unary_union(requested_exclusions) if requested_exclusions else None
                    coverage_changed = coverage_changed or (old_union is None) != (new_union is None) or (old_union is not None and new_union is not None and not old_union.equals(new_union))
            for key in ("nome", "descricao", "status"):
                if key in values:
                    fields.append(f"{key} = %s")
                    params.append(values[key])
            for key in ("drone_perfil", "camera_perfil", "takeoff"):
                if key in values:
                    fields.append(f"{key} = %s::jsonb")
                    params.append(json.dumps(values[key]))
                    canonical[{"drone_perfil": "drone", "camera_perfil": "camera", "takeoff": "takeoff"}[key]] = values[key]
            if "capture" in values:
                canonical["capture"] = values["capture"]
                cursor.execute(
                    """UPDATE missoes_parametros SET gsd_cm_px = %s, overlap_frontal = %s,
                       overlap_lateral = %s, altitude_m = %s, altitude_referencia = %s,
                       velocidade_ms = %s, gimbal_graus = %s, parametros = %s::jsonb
                       WHERE missao_id = %s""",
                    (
                        values["capture"].get("gsd_cm_px"),
                        values["capture"].get("front_overlap", values["capture"].get("overlap_frontal")),
                        values["capture"].get("side_overlap", values["capture"].get("overlap_lateral")),
                        values["capture"].get("altitude_m"),
                        values["capture"].get("altitude_referencia", "AGL"),
                        values["capture"].get("velocidade_ms"),
                        values["capture"].get("gimbal_graus", -90),
                        json.dumps(values["capture"]),
                        missao_id,
                    ),
                )
            if "canonical" in values:
                canonical.update(values["canonical"])
            if "aoi" in values:
                cursor.execute("DELETE FROM missoes_areas WHERE missao_id = %s AND tipo = 'aoi'", (missao_id,))
                if values["aoi"] is not None:
                    geometry = GeoJSONGeometry.model_validate(values["aoi"])
                    cursor.execute(
                        "INSERT INTO missoes_areas (missao_id, tipo, nome, geometria) VALUES (%s, 'aoi', 'Area de interesse', ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326))",
                        (missao_id, _geometry_json(geometry)),
                    )
            if "zonas_exclusao" in values:
                cursor.execute("DELETE FROM missoes_areas WHERE missao_id = %s AND tipo = 'exclusao'", (missao_id,))
                for index, item in enumerate(values["zonas_exclusao"], start=1):
                    geometry = GeoJSONGeometry.model_validate(item)
                    cursor.execute(
                        "INSERT INTO missoes_areas (missao_id, tipo, nome, geometria) VALUES (%s, 'exclusao', %s, ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326))",
                        (missao_id, f"Zona de exclusao {index}", _geometry_json(geometry)),
                    )
            canonical.pop("validation", None)
            if coverage_changed:
                canonical["coverage_stale"] = True
            fields.extend(["canonical = %s::jsonb", "versao = versao + 1", "atualizado_em = %s"])
            params.extend([json.dumps(canonical), datetime.now(timezone.utc), missao_id])
            cursor.execute(f"UPDATE missoes_captura SET {', '.join(fields)} WHERE id = %s", params)
            cursor.execute("DELETE FROM missoes_validacoes WHERE missao_id = %s", (missao_id,))
            conn.commit()
            cursor.execute("SELECT * FROM missoes_captura WHERE id = %s", (missao_id,))
            return _serialize_mission(cursor, cursor.fetchone())
        except Exception:
            conn.rollback()
            raise

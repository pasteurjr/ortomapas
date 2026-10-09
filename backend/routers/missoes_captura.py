"""Fase 1 do planejador de missoes de captura.

Mantem um contrato canonico independente de Litchi, Dronelink ou Map Pilot Pro.
O motor geometrico e o exportador serao adicionados nas fases seguintes.
"""

import csv
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


def _validation_item(rule, severity, status, message, observed=None):
    return {"regra": rule, "severidade": severity, "status": status, "mensagem": message, "valor_observado": observed or {}}


def _validate_mission_geometry(aoi_geometry, exclusions, waypoint_rows):
    issues = []
    if aoi_geometry is None or aoi_geometry.is_empty or not aoi_geometry.is_valid or aoi_geometry.area <= 0:
        issues.append(_validation_item("aoi_valida", "critico", "bloqueado", "A AOI esta vazia ou possui geometria invalida"))
        return issues
    issues.append(_validation_item("aoi_valida", "info", "aprovado", "AOI valida e com area positiva", {"area_graus2": aoi_geometry.area}))
    if len(waypoint_rows) < 2:
        issues.append(_validation_item("waypoints_minimos", "critico", "bloqueado", "A missao precisa de pelo menos dois waypoints", {"quantidade": len(waypoint_rows)}))
        return issues
    issues.append(_validation_item("waypoints_minimos", "info", "aprovado", "Quantidade minima de waypoints atendida", {"quantidade": len(waypoint_rows)}))
    forbidden = unary_union(exclusions) if exclusions else None
    outside = 0
    in_exclusion = 0
    for row in waypoint_rows:
        point = Point(float(row["longitude"]), float(row["latitude"]))
        if not aoi_geometry.covers(point):
            outside += 1
        if forbidden and forbidden.covers(point):
            in_exclusion += 1
    issues.append(_validation_item("waypoints_na_aoi", "critico" if outside else "info", "bloqueado" if outside else "aprovado", f"{outside} waypoint(s) fora da AOI", {"fora_aoi": outside, "total": len(waypoint_rows)}))
    issues.append(_validation_item("zonas_exclusao", "critico" if in_exclusion else "info", "bloqueado" if in_exclusion else "aprovado", f"{in_exclusion} waypoint(s) em zona de exclusao", {"em_exclusao": in_exclusion, "total": len(waypoint_rows)}))
    return issues


def _generate_grid(aoi_geometry, exclusions, request, capture):
    to_local, from_local, local_crs = _local_transformers(aoi_geometry)
    area = shapely_transform(to_local, aoi_geometry)
    exclusion_union = unary_union([shapely_transform(to_local, item) for item in exclusions]) if exclusions else None
    if exclusion_union and not exclusion_union.is_empty:
        area = area.difference(exclusion_union)
    if area.is_empty:
        raise HTTPException(status_code=422, detail="As zonas de exclusao removem toda a AOI")

    altitude = float(capture.get("altitude_m") or 50)
    front_overlap = float(capture.get("front_overlap", capture.get("overlap_frontal", 0.8)) or 0.8)
    side_overlap = float(capture.get("side_overlap", capture.get("overlap_lateral", 0.7)) or 0.7)
    # Sem um perfil de sensor completo, usa-se um footprint configurável e
    # explícito. O valor pode ser substituído pelos espaçamentos enviados.
    footprint = float(capture.get("footprint_m") or max(20.0, altitude * 0.8))
    line_spacing = float(request.espacamento_linhas_m or capture.get("espacamento_linhas_m") or footprint * (1 - side_overlap))
    photo_spacing = float(request.espacamento_fotos_m or footprint * (1 - front_overlap))
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
    for line_index, points in enumerate(passes):
        if line_index % 2:
            points = list(reversed(points))
        waypoints.extend(points)
    if len(waypoints) < 2:
        raise HTTPException(status_code=422, detail="A AOI nao gerou linhas de cobertura suficientes")
    return waypoints, {"local_crs": local_crs, "line_spacing_m": line_spacing, "photo_spacing_m": photo_spacing, "lines": len(passes), "double_grid": request.double_grid, "to_local": to_local, "from_local": from_local}


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
            capture.setdefault("altitude_m", parameters.get("altitude_m"))
            capture.setdefault("overlap_frontal", parameters.get("overlap_frontal"))
            capture.setdefault("overlap_lateral", parameters.get("overlap_lateral"))
            waypoints, stats = _generate_grid(aoi_geometry, exclusion_geometries, data, capture)
            if len(waypoints) > data.max_waypoints:
                raise HTTPException(status_code=422, detail=f"Grid gerou {len(waypoints)} pontos; aumente os espacamentos (limite {data.max_waypoints})")
            _to_local, from_local, local_crs = _local_transformers(aoi_geometry)
            # _generate_grid retorna os pontos no CRS métrico local; a
            # conversão para WGS84 acontece somente ao persistir/exportar.
            local_points = waypoints
            distance_m = sum(local_points[index - 1].distance(local_points[index]) for index in range(1, len(local_points)))
            speed = max(0.5, float(parameters.get("velocidade_ms") or capture.get("velocidade_ms") or 4))
            time_seconds = distance_m / speed
            max_block_seconds = data.max_bateria_minutos * 60
            block_count = max(1, int(math.ceil(time_seconds / max_block_seconds)))
            per_block = int(math.ceil(len(waypoints) / block_count))

            cursor.execute("DELETE FROM missoes_waypoints WHERE missao_id = %s", (missao_id,))
            cursor.execute("DELETE FROM missoes_blocos WHERE missao_id = %s", (missao_id,))
            block_ids = []
            for block_order in range(block_count):
                start = block_order * per_block
                end = min(len(waypoints), (block_order + 1) * per_block)
                block_distance = sum(local_points[index - 1].distance(local_points[index]) for index in range(max(1, start + 1), end))
                cursor.execute(
                    """
                    INSERT INTO missoes_blocos (missao_id, ordem, nome, estimativa_fotos, distancia_m, tempo_segundos, bateria, propriedades)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb) RETURNING id
                    """,
                    (missao_id, block_order + 1, f"Bloco {block_order + 1:02d}", end - start, block_distance, block_distance / speed, int(math.ceil((block_distance / speed) / 60)), json.dumps({"gerado_por": "grid", "local_crs": local_crs})),
                )
                block_ids.append(cursor.fetchone()["id"])
            altitude = float(parameters.get("altitude_m") or capture.get("altitude_m") or 50)
            gimbal = float(parameters.get("gimbal_graus") or capture.get("gimbal_graus") or -90)
            for index, (point, local_point) in enumerate(zip(waypoints, local_points)):
                lon, lat = from_local(local_point.x, local_point.y)
                block_id = block_ids[min(len(block_ids) - 1, index // per_block)]
                cursor.execute(
                    """
                    INSERT INTO missoes_waypoints
                        (missao_id, bloco_id, ordem, geometria, altitude_m, altitude_agl_m, velocidade_ms, gimbal_graus, acoes, propriedades)
                    VALUES (%s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326), %s, %s, %s, %s, %s::jsonb, %s::jsonb)
                    """,
                    (missao_id, block_id, index + 1, lon, lat, altitude, altitude, speed, gimbal, json.dumps(["Take Photo"]), json.dumps({"linha": index + 1})),
                )
            canonical = dict(mission.get("canonical") or {})
            canonical["grid"] = {key: value for key, value in stats.items() if key not in {"to_local", "from_local"}}
            canonical["waypoints"] = [{"lat": float(from_local(point.x, point.y)[1]), "lon": float(from_local(point.x, point.y)[0]), "altitude_m": altitude} for point in local_points]
            cursor.execute("UPDATE missoes_captura SET canonical = %s::jsonb, versao = versao + 1, atualizado_em = %s WHERE id = %s", (json.dumps(canonical), datetime.now(timezone.utc), missao_id))
            conn.commit()
            return {"missao_id": missao_id, "status": "gerado", "grid": canonical["grid"], "waypoints": len(waypoints), "distancia_m": round(distance_m, 2), "tempo_segundos": round(time_seconds, 2), "blocos": block_count, "local_crs": local_crs}
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
                    (missao_id, block_id, order, point.lon, point.lat, point_altitude, point_altitude, point.rumo_graus, point_speed, point_gimbal, json.dumps(["Take Photo"]), json.dumps({"editado": True})),
                )
                canonical_points.append({"lat": point.lat, "lon": point.lon, "altitude_m": point_altitude, "velocidade_ms": point_speed, "gimbal_graus": point_gimbal, "rumo_graus": point.rumo_graus})
            canonical = dict(mission.get("canonical") or {})
            canonical["waypoints"] = canonical_points
            canonical["editado_por_editor"] = True
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
            estimated_seconds = distance_m / speed
            autonomy_status = "bloqueado" if estimated_seconds > usable_seconds else ("aviso" if estimated_seconds > usable_seconds * .8 else "aprovado")
            issues.append(_validation_item("autonomia_bateria", "critico" if autonomy_status == "bloqueado" else ("aviso" if autonomy_status == "aviso" else "info"), autonomy_status, "Tempo estimado comparado com 18 min e reserva configurada", {"distancia_m": round(distance_m, 2), "tempo_segundos": round(estimated_seconds, 2), "tempo_utilizavel_segundos": round(usable_seconds, 2), "reserva_pct": params.get("reserva_bateria_pct", 25)}))
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
                writer.writerow([row["latitude"], row["longitude"], row["altitude_m"], row["rumo_graus"] % 360, 0, 0, 2, row["gimbal_graus"], 1, 0, 0, row["velocidade_ms"], 0, 0, 0, 0, -1, distance_interval])
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
        fields: list[str] = []
        params: list[Any] = []
        for key in ("nome", "descricao", "status"):
            if key in values:
                fields.append(f"{key} = %s")
                params.append(values[key])
        for key in ("drone_perfil", "camera_perfil", "takeoff"):
            if key in values:
                fields.append(f"{key} = %s::jsonb")
                params.append(json.dumps(values[key]))
        if "capture" in values:
            fields.append("canonical = jsonb_set(canonical, '{capture}', %s::jsonb)")
            params.append(json.dumps(values["capture"]))
        if "canonical" in values:
            fields.append("canonical = %s::jsonb")
            params.append(json.dumps(values["canonical"]))
        fields.extend(["versao = versao + 1", "atualizado_em = %s"])
        params.extend([datetime.now(timezone.utc), missao_id])
        cursor.execute(f"UPDATE missoes_captura SET {', '.join(fields)} WHERE id = %s", params)
        conn.commit()
        cursor.execute("SELECT * FROM missoes_captura WHERE id = %s", (missao_id,))
        return _serialize_mission(cursor, cursor.fetchone())

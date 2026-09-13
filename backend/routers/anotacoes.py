"""
Router for Anotacoes (annotations) CRUD and GeoJSON export.
"""

import json
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from backend.database.connection import get_connection
from backend.utils.geo_utils import wkt_to_geojson

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/anotacoes")
async def list_anotacoes(
    ortomapa_id: Optional[int] = Query(None, description="Filter by ortomapa_id"),
    projeto_id: Optional[int] = Query(None, description="Filter by projeto_id (via ortomapa)"),
    categoria: Optional[str] = Query(None, description="Filter by categoria"),
    fonte: Optional[str] = Query(None, description="Filter by fonte"),
):
    """List all anotacoes with optional filters."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)

            query = "SELECT * FROM anotacoes WHERE 1=1"
            params = []

            if ortomapa_id is not None:
                query += " AND ortomapa_id = %s"
                params.append(ortomapa_id)
            if projeto_id is not None:
                query += " AND ortomapa_id IN (SELECT id FROM ortomapas WHERE projeto_id = %s)"
                params.append(projeto_id)
            if categoria:
                query += " AND categoria = %s"
                params.append(categoria)
            if fonte:
                query += " AND fonte = %s"
                params.append(fonte)

            query += " ORDER BY criado_em DESC"

            cursor.execute(query, params)
            rows = cursor.fetchall()
            return {"total": len(rows), "anotacoes": rows}
    except Exception as e:
        logger.error(f"Error listing anotacoes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/anotacoes/geojson/{ortomapa_id}")
async def get_anotacoes_geojson(ortomapa_id: int):
    """
    Return all annotations for an ortomapa as a GeoJSON FeatureCollection.
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)

            # Verify ortomapa exists
            cursor.execute("SELECT id FROM ortomapas WHERE id = %s", (ortomapa_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Ortomapa nao encontrado")

            cursor.execute(
                "SELECT * FROM anotacoes WHERE ortomapa_id = %s ORDER BY criado_em DESC",
                (ortomapa_id,),
            )
            rows = cursor.fetchall()

        features = []
        for row in rows:
            geometry = None
            wkt_geom = row.get("geometria_wkt")
            if wkt_geom:
                try:
                    geometry = wkt_to_geojson(wkt_geom)
                except Exception as ge:
                    logger.warning(
                        f"Could not convert WKT for anotacao {row.get('id')}: {ge}"
                    )

            # Build properties from all fields except geometry
            properties = {}
            for key, value in row.items():
                if key == "geometria_wkt":
                    continue
                # Convert datetime to string for JSON serialization
                if isinstance(value, datetime):
                    properties[key] = value.isoformat()
                else:
                    properties[key] = value

            feature = {
                "type": "Feature",
                "id": row.get("id"),
                "geometry": geometry,
                "properties": properties,
            }
            features.append(feature)

        return {
            "type": "FeatureCollection",
            "features": features,
            "totalFeatures": len(features),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating GeoJSON for ortomapa {ortomapa_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/anotacoes/{anotacao_id}")
async def get_anotacao(anotacao_id: int):
    """Get a single anotacao by ID."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)

            cursor.execute("SELECT * FROM anotacoes WHERE id = %s", (anotacao_id,))
            anotacao = cursor.fetchone()
            if not anotacao:
                raise HTTPException(status_code=404, detail="Anotacao nao encontrada")
            return anotacao
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting anotacao {anotacao_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/anotacoes", status_code=201)
async def create_anotacao(data: dict):
    """Create a new anotacao with WKT geometry."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)

            ortomapa_id = data.get("ortomapa_id")
            if not ortomapa_id:
                raise HTTPException(
                    status_code=400, detail="Campo 'ortomapa_id' e obrigatorio"
                )

            # Verify ortomapa exists
            cursor.execute("SELECT id FROM ortomapas WHERE id = %s", (ortomapa_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Ortomapa nao encontrado")

            geometria_wkt = data.get("geometria_wkt", "")
            if not geometria_wkt:
                raise HTTPException(
                    status_code=400, detail="Campo 'geometria_wkt' e obrigatorio"
                )

            # Validate WKT by attempting conversion
            try:
                wkt_to_geojson(geometria_wkt)
            except Exception:
                raise HTTPException(
                    status_code=400, detail="geometria_wkt invalida"
                )

            criado_por = data.get("criado_por")
            try:
                criado_por = int(criado_por) if criado_por is not None else None
            except (TypeError, ValueError):
                criado_por = None

            cursor.execute(
                """
                INSERT INTO anotacoes (
                    ortomapa_id, tipo, categoria, rotulo, geometria_wkt,
                    centro_lat, centro_lon, area_m2, atributos,
                    confianca, fonte, criado_por, criado_em
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    ortomapa_id,
                    data.get("tipo", "poligono"),
                    data.get("categoria", ""),
                    data.get("rotulo", ""),
                    geometria_wkt,
                    data.get("centro_lat"),
                    data.get("centro_lon"),
                    data.get("area_m2"),
                    json.dumps(data.get("atributos", {})),
                    data.get("confianca"),
                    data.get("fonte", "manual"),
                    criado_por,
                    datetime.utcnow(),
                ),
            )
            conn.commit()
            new_id = cursor.lastrowid

            cursor.execute("SELECT * FROM anotacoes WHERE id = %s", (new_id,))
            return cursor.fetchone()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating anotacao: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/anotacoes/{anotacao_id}")
async def update_anotacao(anotacao_id: int, data: dict):
    """Update an existing anotacao."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)

            cursor.execute("SELECT * FROM anotacoes WHERE id = %s", (anotacao_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Anotacao nao encontrada")

            updatable = [
                "categoria", "rotulo", "geometria_wkt", "tipo",
                "fonte", "confianca", "centro_lat", "centro_lon", "criado_por",
            ]

            fields = []
            params = []
            for field in updatable:
                if field in data:
                    value = data[field]
                    if field == "metadata_json" and isinstance(value, dict):
                        value = json.dumps(value)
                    if field == "geometria_wkt":
                        try:
                            wkt_to_geojson(value)
                        except Exception:
                            raise HTTPException(
                                status_code=400, detail="geometria_wkt invalida"
                            )
                    fields.append(f"{field} = %s")
                    params.append(value)

            if not fields:
                raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")

            fields.append("atualizado_em = %s")
            params.append(datetime.utcnow())
            params.append(anotacao_id)

            cursor.execute(
                f"UPDATE anotacoes SET {', '.join(fields)} WHERE id = %s", params
            )
            conn.commit()

            cursor.execute("SELECT * FROM anotacoes WHERE id = %s", (anotacao_id,))
            return cursor.fetchone()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating anotacao {anotacao_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/anotacoes/{anotacao_id}")
async def delete_anotacao(anotacao_id: int):
    """Delete an anotacao."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)

            cursor.execute("SELECT * FROM anotacoes WHERE id = %s", (anotacao_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Anotacao nao encontrada")

            cursor.execute("DELETE FROM anotacoes WHERE id = %s", (anotacao_id,))
            conn.commit()
            return {"message": "Anotacao deletada com sucesso", "id": anotacao_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting anotacao {anotacao_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

"""Opt-in PostgreSQL integration check on an existing, authorized raster."""

import os
from pathlib import Path

import pytest
import rasterio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from rasterio.io import MemoryFile
from rasterio.windows import Window, bounds as window_bounds
from rasterio.warp import transform_bounds
from shapely.geometry import box, mapping

from backend.database.connection import get_connection
from backend.routers import analises, tools
from backend.routers.auth import current_user


@pytest.mark.skipif(os.getenv('ORTOMAPAS_DB_INTEGRATION') != '1', reason='Requires local PostgreSQL')
def test_real_project_crop_reopen_and_export():
    with get_connection() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute("""SELECT * FROM ortomapas WHERE caminho_arquivo LIKE %s
            ORDER BY id DESC LIMIT 1""", ('%rasterio_rgb_f866f21d.tif',))
        source = cur.fetchone()
    if not source:
        pytest.skip('Ortofoto de referencia nao cadastrada')
    with rasterio.open(source['caminho_arquivo']) as ds:
        bbox = transform_bounds(ds.crs, 'EPSG:4326', *window_bounds(Window(120, 120, 250, 250), ds.transform))
    app = FastAPI()
    app.include_router(tools.router, prefix='/api')
    app.include_router(analises.router, prefix='/api')
    app.dependency_overrides[current_user] = lambda: {'id': 1, 'perfil': 'admin'}
    analysis_id = None
    output_path = None
    try:
        with TestClient(app) as client:
            response = client.post('/api/tools/recorte', json={
                'input_path': source['caminho_arquivo'], 'ortomapa_id': source['id'],
                'projeto_id': source['projeto_id'], 'aoi': mapping(box(*bbox)),
                'output_name': 'teste_http_recorte',
            })
            assert response.status_code == 200, response.text
            result = response.json()
            analysis_id = result['analise']['id']
            output_path = result['output_path']
            assert result['statistics']['valid_pixels'] > 0
            reopened = client.get(f'/api/analises/{analysis_id}')
            assert reopened.status_code == 200
            assert reopened.json()['resultado']['provenance']['operation'] == 'clip'
            export = client.post('/api/tools/exportar', json={
                'input_path': output_path, 'format': 'geotiff', 'crs': 'EPSG:4326',
            })
            assert export.status_code == 200, export.text[:500]
            with MemoryFile(export.content) as memory, memory.open() as ds:
                assert ds.crs.to_epsg() == 4326
                assert ds.dataset_mask().any()
            invalid = client.post('/api/tools/exportar', json={
                'input_path': output_path, 'format': 'kml', 'crs': 'EPSG:4326',
            })
            assert invalid.status_code == 422
    finally:
        if analysis_id is not None:
            with get_connection() as conn:
                cur = conn.cursor(dictionary=True)
                cur.execute('DELETE FROM analises WHERE id=%s AND tipo_analise=%s', (analysis_id, 'recorte'))
                conn.commit()
        if output_path:
            Path(output_path).unlink(missing_ok=True)

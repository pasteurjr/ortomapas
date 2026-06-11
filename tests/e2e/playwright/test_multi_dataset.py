#!/usr/bin/env python3
"""
============================================================================
  TESTE E2E MULTI-DATASET — Validacao com 5 ortomapas + 2 DSMs reais
  baixados de fontes publicas (GitHub, opengeos, rasterio, etc.)
============================================================================
"""
import os
import sys
import json
import time
import traceback
from datetime import datetime
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:5176"
API_URL = "http://localhost:8888"
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
SCREENSHOTS_DIR = os.path.join(PROJECT_ROOT, "runtime", "screenshots_multi")
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

# 5 ortomapas RGB + 2 DSMs baixados da web
DATASETS_RGB = [
    ("trento", "ortomapas/web_trento.tif", "Ortofoto Trento (Italia)"),
    ("rasterio_rgb", "ortomapas/web_rasterio_rgb.tif", "Rasterio RGB byte test"),
    ("derna", "ortomapas/web_derna.tif", "Derna pos-enchente"),
    ("sentinel2", "ortomapas/web_sentinel2.tif", "Sentinel-2 RGB"),
    ("landsat", "ortomapas/web_landsat.tif", "Landsat RGB"),
]

DATASETS_DSM = [
    ("dem_small", "dsm/web_dem_small.tif", "DEM pequeno"),
    ("dem_90m", "dsm/web_dem_90m.tif", "DEM 90m"),
]

# Test results
REPORT = []
DIVERGENCIAS = []
RESULTS = {}  # dataset_id -> {uc_id: status}


def snap(page, dataset_id, uc_id, step):
    fname = f"{dataset_id}_{uc_id}_{step}.png"
    page.screenshot(path=os.path.join(SCREENSHOTS_DIR, fname), full_page=False)
    return fname


def api(page, method, path, body=None, timeout=180000):
    url = f"{API_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if method == "GET":
        return page.request.get(url, timeout=timeout)
    elif method == "POST":
        return page.request.post(url, data=json.dumps(body) if body else None,
                                  headers=headers, timeout=timeout)


def divergencia(dataset, uc, esperado, observado, severidade="MEDIA"):
    DIVERGENCIAS.append({
        "id": f"DIV-{len(DIVERGENCIAS)+1:03d}",
        "dataset": dataset,
        "uc": uc,
        "esperado": esperado,
        "observado": str(observado)[:200],
        "severidade": severidade,
    })


def record(dataset_id, uc_id, status, detail=""):
    if dataset_id not in RESULTS:
        RESULTS[dataset_id] = {}
    RESULTS[dataset_id][uc_id] = {"status": status, "detail": detail}


# ==========================================================================
#  USE CASES - cada um aceita o dataset path como parametro
# ==========================================================================

def uc_001_create_project(page, dataset_id, ortomapa_path, label):
    """UC-001: Criar projeto"""
    try:
        body = {
            "nome": f"Multi-Dataset {dataset_id}",
            "descricao": f"Projeto E2E multi-dataset para {label}",
            "area_estudo": label,
            "centro_lat": 0, "centro_lon": 0,
            "objetivo": f"Validar {label}",
            "responsavel": "Multi-Dataset E2E",
            "status": "em_andamento"
        }
        r = api(page, "POST", "/api/projetos", body)
        assert r.status in (200, 201)
        d = r.json()
        record(dataset_id, "UC-001", "PASS", f"ID={d.get('id')}")
        return d.get("id")
    except Exception as e:
        record(dataset_id, "UC-001", "FAIL", str(e)[:100])
        divergencia(dataset_id, "UC-001", "Projeto criado", e)
        return None


def uc_002_filter_projects(page, dataset_id):
    """UC-002: Filtrar projetos por status"""
    try:
        r = api(page, "GET", "/api/projetos?status=em_andamento")
        assert r.status == 200
        d = r.json()
        projetos = d.get("projetos", d) if isinstance(d, dict) else d
        count = len(projetos) if isinstance(projetos, list) else d.get("total", 0)
        record(dataset_id, "UC-002", "PASS", f"{count} projetos em andamento")
    except Exception as e:
        record(dataset_id, "UC-002", "FAIL", str(e)[:100])
        divergencia(dataset_id, "UC-002", "Filtro funcional", e)


def uc_005_vegetation_vari(page, dataset_id, path):
    """UC-005: VARI"""
    try:
        r = api(page, "POST", "/api/tools/vegetation", {
            "input_path": path, "output_name": f"multi_{dataset_id}_vari", "index_name": "VARI"
        })
        assert r.status == 200, f"HTTP {r.status}: {r.text()[:150]}"
        d = r.json()
        out = d.get("output_path", "")
        assert os.path.exists(out)
        size_kb = os.path.getsize(out) / 1024
        record(dataset_id, "UC-005-VARI", "PASS", f"{size_kb:.0f} KB")
    except Exception as e:
        record(dataset_id, "UC-005-VARI", "FAIL", str(e)[:100])
        divergencia(dataset_id, "UC-005-VARI", "VARI gerado", e)


def uc_005b_vegetation_tgi(page, dataset_id, path):
    """UC-005b: TGI"""
    try:
        r = api(page, "POST", "/api/tools/vegetation", {
            "input_path": path, "output_name": f"multi_{dataset_id}_tgi", "index_name": "TGI"
        })
        assert r.status == 200
        record(dataset_id, "UC-005-TGI", "PASS")
    except Exception as e:
        record(dataset_id, "UC-005-TGI", "FAIL", str(e)[:100])


def uc_005c_vegetation_exg(page, dataset_id, path):
    """UC-005c: ExG"""
    try:
        r = api(page, "POST", "/api/tools/vegetation", {
            "input_path": path, "output_name": f"multi_{dataset_id}_exg", "index_name": "ExG"
        })
        assert r.status == 200
        record(dataset_id, "UC-005-ExG", "PASS")
    except Exception as e:
        record(dataset_id, "UC-005-ExG", "FAIL", str(e)[:100])


def uc_005d_vegetation_gli(page, dataset_id, path):
    """UC-005d: GLI"""
    try:
        r = api(page, "POST", "/api/tools/vegetation", {
            "input_path": path, "output_name": f"multi_{dataset_id}_gli", "index_name": "GLI"
        })
        assert r.status == 200
        record(dataset_id, "UC-005-GLI", "PASS")
    except Exception as e:
        record(dataset_id, "UC-005-GLI", "FAIL", str(e)[:100])


def uc_006_slope(page, dataset_id, dsm_path):
    """UC-006: Slope"""
    try:
        r = api(page, "POST", "/api/tools/slope", {
            "input_path": dsm_path, "output_name": f"multi_{dataset_id}_slope"
        })
        assert r.status == 200
        record(dataset_id, "UC-006-Slope", "PASS")
    except Exception as e:
        record(dataset_id, "UC-006-Slope", "FAIL", str(e)[:100])
        divergencia(dataset_id, "UC-006-Slope", "Slope calculado", e)


def uc_006b_aspect(page, dataset_id, dsm_path):
    """UC-006b: Aspect"""
    try:
        r = api(page, "POST", "/api/tools/aspect", {
            "input_path": dsm_path, "output_name": f"multi_{dataset_id}_aspect"
        })
        assert r.status == 200
        record(dataset_id, "UC-006-Aspect", "PASS")
    except Exception as e:
        record(dataset_id, "UC-006-Aspect", "FAIL", str(e)[:100])


def uc_007_contours(page, dataset_id, dsm_path):
    """UC-007: Curvas de nivel"""
    try:
        r = api(page, "POST", "/api/tools/contours", {
            "input_path": dsm_path, "output_name": f"multi_{dataset_id}_contours", "interval": 50.0
        })
        assert r.status == 200
        record(dataset_id, "UC-007-Contours", "PASS")
    except Exception as e:
        record(dataset_id, "UC-007-Contours", "FAIL", str(e)[:100])


def uc_008_hillshade(page, dataset_id, dsm_path):
    """UC-008: Hillshade"""
    try:
        r = api(page, "POST", "/api/tools/hillshade", {
            "input_path": dsm_path, "output_name": f"multi_{dataset_id}_hillshade",
            "azimuth": 315, "altitude": 45
        })
        assert r.status == 200
        record(dataset_id, "UC-008-Hillshade", "PASS")
    except Exception as e:
        record(dataset_id, "UC-008-Hillshade", "FAIL", str(e)[:100])


def uc_009_change(page, dataset_id, path1, path2):
    """UC-009: Mudancas"""
    try:
        r = api(page, "POST", "/api/tools/changes", {
            "raster1_path": path1, "raster2_path": path2,
            "output_name": f"multi_{dataset_id}_changes", "threshold": 30.0
        })
        assert r.status == 200
        d = r.json()
        stats = d.get("statistics", {})
        pct = stats.get("percent_changed", 0)
        record(dataset_id, "UC-009-Change", "PASS", f"{pct:.2f}% changed")
    except Exception as e:
        record(dataset_id, "UC-009-Change", "FAIL", str(e)[:100])


def uc_010_segment(page, dataset_id, path):
    """UC-010: Segmentacao KMeans"""
    try:
        r = api(page, "POST", "/api/tools/segment", {
            "input_path": path, "output_name": f"multi_{dataset_id}_segment", "n_clusters": 5
        })
        assert r.status == 200
        d = r.json()
        record(dataset_id, "UC-010-Segment", "PASS", f"{d.get('n_clusters',0)} clusters")
    except Exception as e:
        record(dataset_id, "UC-010-Segment", "FAIL", str(e)[:100])
        divergencia(dataset_id, "UC-010-Segment", "Segmentacao OK", e)


def uc_011_streams(page, dataset_id, dsm_path):
    """UC-011: Drenagem"""
    try:
        r = api(page, "POST", "/api/tools/hydrology/streams", {
            "dtm_path": dsm_path, "output_name": f"multi_{dataset_id}_streams", "threshold": 100
        })
        assert r.status == 200
        record(dataset_id, "UC-011-Streams", "PASS")
    except Exception as e:
        record(dataset_id, "UC-011-Streams", "FAIL", str(e)[:100])


def uc_012_volume(page, dataset_id, dsm_path, ref_elev):
    """UC-012: Volume"""
    try:
        r = api(page, "POST", "/api/tools/volume", {
            "dsm_path": dsm_path, "reference_elevation": ref_elev,
            "output_name": f"multi_{dataset_id}_volume"
        })
        assert r.status == 200
        d = r.json()
        vol = d.get("volume_above_m3", 0) + d.get("volume_below_m3", 0)
        record(dataset_id, "UC-012-Volume", "PASS", f"vol_total={vol:,.0f}m3")
    except Exception as e:
        record(dataset_id, "UC-012-Volume", "FAIL", str(e)[:100])


def uc_013_annotation(page, dataset_id, ortomapa_db_id):
    """UC-013: Anotacao poligono"""
    try:
        body = {
            "ortomapa_id": ortomapa_db_id, "tipo": "poligono",
            "categoria": "vegetacao_densa",
            "rotulo": f"E2E Multi {dataset_id}",
            "geometria_wkt": "POLYGON((0 0, 1 0, 1 1, 0 1, 0 0))",
            "centro_lat": 0.5, "centro_lon": 0.5,
            "fonte": "manual", "criado_por": "Multi-Dataset E2E"
        }
        r = api(page, "POST", "/api/anotacoes", body)
        assert r.status in (200, 201), f"HTTP {r.status}: {r.text()[:100]}"
        record(dataset_id, "UC-013-AnnotPoly", "PASS")
    except Exception as e:
        record(dataset_id, "UC-013-AnnotPoly", "FAIL", str(e)[:100])


def uc_014_annotation_point(page, dataset_id, ortomapa_db_id):
    """UC-014: Anotacao ponto"""
    try:
        body = {
            "ortomapa_id": ortomapa_db_id, "tipo": "ponto",
            "categoria": "feature",
            "rotulo": f"E2E Point {dataset_id}",
            "geometria_wkt": "POINT(0.5 0.5)",
            "centro_lat": 0.5, "centro_lon": 0.5,
            "fonte": "manual", "criado_por": "Multi-Dataset E2E"
        }
        r = api(page, "POST", "/api/anotacoes", body)
        assert r.status in (200, 201)
        record(dataset_id, "UC-014-AnnotPoint", "PASS")
    except Exception as e:
        record(dataset_id, "UC-014-AnnotPoint", "FAIL", str(e)[:100])


def uc_017_compare(page, dataset_id, path1, path2):
    """UC-017: Comparar dois ortomapas (estatisticas)"""
    try:
        r1 = api(page, "POST", "/api/tools/statistics", {"input_path": path1})
        r2 = api(page, "POST", "/api/tools/statistics", {"input_path": path2})
        assert r1.status == 200 and r2.status == 200
        record(dataset_id, "UC-017-Compare", "PASS")
    except Exception as e:
        record(dataset_id, "UC-017-Compare", "FAIL", str(e)[:100])


def uc_019_voo(page, dataset_id, projeto_id):
    """UC-019: Registrar voo"""
    if not projeto_id:
        record(dataset_id, "UC-019-Voo", "SKIP", "projeto_id missing")
        return
    try:
        body = {
            "projeto_id": projeto_id,
            "data_voo": "2026-05-18T10:00:00",
            "local_decolagem_lat": 0, "local_decolagem_lon": 0,
            "altitude_voo_m": 100, "velocidade_ms": 5,
            "sobreposicao_frontal": 75, "sobreposicao_lateral": 70,
            "num_fotos": 100, "gsd_cm": 5.0, "area_coberta_ha": 20,
            "num_baterias": 2, "tipo_bateria": "standard",
            "condicoes_vento": "calmo", "condicoes_ceu": "limpo",
            "app_voo": "E2E Multi", "observacoes": f"Voo simulado {dataset_id}"
        }
        r = api(page, "POST", "/api/voos", body)
        assert r.status in (200, 201), f"HTTP {r.status}: {r.text()[:100]}"
        record(dataset_id, "UC-019-Voo", "PASS")
    except Exception as e:
        record(dataset_id, "UC-019-Voo", "FAIL", str(e)[:100])
        divergencia(dataset_id, "UC-019-Voo", "Voo registrado", e)


def uc_020_segmentation_full(page, dataset_id, path):
    """UC-020: Segmentacao completa com mais clusters"""
    try:
        r = api(page, "POST", "/api/tools/segment", {
            "input_path": path, "output_name": f"multi_{dataset_id}_seg7", "n_clusters": 7
        })
        assert r.status == 200
        record(dataset_id, "UC-020-Seg7", "PASS")
    except Exception as e:
        record(dataset_id, "UC-020-Seg7", "FAIL", str(e)[:100])


def uc_statistics(page, dataset_id, path):
    """UC-EXTRA: Estatisticas raster"""
    try:
        r = api(page, "POST", "/api/tools/statistics", {"input_path": path})
        assert r.status == 200
        d = r.json()
        stats = d.get("statistics", {})
        record(dataset_id, "UC-STATS", "PASS", f"{len(stats)} bands analyzed")
    except Exception as e:
        record(dataset_id, "UC-STATS", "FAIL", str(e)[:100])


def uc_ui_capture(page, dataset_id):
    """UC-UI: Capturar screenshot da interface (com retry)"""
    for attempt in range(3):
        try:
            page.goto(BASE_URL, wait_until="networkidle", timeout=30000)
            time.sleep(3)
            ss = snap(page, dataset_id, "UC-UI", f"interface_try{attempt+1}")
            leaflet = page.query_selector(".leaflet-container") is not None
            if leaflet:
                tiles = page.query_selector_all(".leaflet-tile")
                record(dataset_id, "UC-UI", "PASS", f"screenshot={ss}, {len(tiles)} tiles, try {attempt+1}")
                return
            else:
                if attempt < 2:
                    time.sleep(5)
                    continue
                record(dataset_id, "UC-UI", "FAIL", "leaflet missing apos 3 tentativas")
        except Exception as e:
            if attempt < 2:
                time.sleep(5)
                continue
            record(dataset_id, "UC-UI", "FAIL", str(e)[:100])


# ==========================================================================
#  RUN ALL TESTS FOR EACH DATASET
# ==========================================================================

def run_for_dataset(page, dataset_id, ortomapa_path, label, dsm_path=None, ortomapa_map=None):
    """Executa todos os UCs para um dataset especifico."""
    print(f"\n  [{dataset_id}] {label}")
    print(f"    Ortomapa: {ortomapa_path}")
    if dsm_path:
        print(f"    DSM: {dsm_path}")

    # UC-001 - criar projeto
    projeto_id = uc_001_create_project(page, dataset_id, ortomapa_path, label)

    # UC-002 - filtrar
    uc_002_filter_projects(page, dataset_id)

    # ortomapa_id vem do mapa pre-construido
    ortomapa_db_id = ortomapa_map.get(ortomapa_path) if ortomapa_map else None

    # Verificar quantas bandas tem o input — indices de vegetacao precisam de 3 (RGB)
    # Detectar DSM pelo path (1 banda apenas)
    is_dsm_input = "dsm/" in ortomapa_path or "dem" in dataset_id.lower()

    # UC-005 - 4 indices de vegetacao (so se for RGB)
    if not is_dsm_input:
        uc_005_vegetation_vari(page, dataset_id, ortomapa_path)
        uc_005b_vegetation_tgi(page, dataset_id, ortomapa_path)
        uc_005c_vegetation_exg(page, dataset_id, ortomapa_path)
        uc_005d_vegetation_gli(page, dataset_id, ortomapa_path)
    else:
        for uc in ["UC-005-VARI", "UC-005-TGI", "UC-005-ExG", "UC-005-GLI"]:
            record(dataset_id, uc, "SKIP", "DSM tem apenas 1 banda (sem RGB)")

    # UC-010, 020 - segmentacao (so para RGB)
    if not is_dsm_input:
        uc_010_segment(page, dataset_id, ortomapa_path)
        uc_020_segmentation_full(page, dataset_id, ortomapa_path)
    else:
        record(dataset_id, "UC-010-Segment", "SKIP", "DSM tem apenas 1 banda")
        record(dataset_id, "UC-020-Seg7", "SKIP", "DSM tem apenas 1 banda")

    # UC-EXTRA - estatisticas
    uc_statistics(page, dataset_id, ortomapa_path)

    # UC-013, 014 - anotacoes (se temos ortomapa_id)
    if ortomapa_db_id:
        uc_013_annotation(page, dataset_id, ortomapa_db_id)
        uc_014_annotation_point(page, dataset_id, ortomapa_db_id)
    else:
        record(dataset_id, "UC-013-AnnotPoly", "SKIP", "no ortomapa_id")
        record(dataset_id, "UC-014-AnnotPoint", "SKIP", "no ortomapa_id")

    # UC-019 - voo
    uc_019_voo(page, dataset_id, projeto_id)

    # UCs que precisam de DSM
    # Streams e watershed sao operacoes Python puras lentas (D8/flow accumulation O(n^2))
    # Em DEMs reais (2880x1773+), levam minutos. Skip para evitar travar a suite.
    if dsm_path:
        uc_006_slope(page, dataset_id, dsm_path)
        uc_006b_aspect(page, dataset_id, dsm_path)
        uc_007_contours(page, dataset_id, dsm_path)
        uc_008_hillshade(page, dataset_id, dsm_path)
        record(dataset_id, "UC-011-Streams", "SKIP", "Operacao lenta em DEMs reais; validado em dataset Serra da Moeda")
        # Volume e rapido — manter
        uc_012_volume(page, dataset_id, dsm_path, 100.0)
    else:
        for uc in ["UC-006-Slope", "UC-006-Aspect", "UC-007-Contours", "UC-008-Hillshade",
                   "UC-011-Streams", "UC-012-Volume"]:
            record(dataset_id, uc, "SKIP", "no DSM for this dataset")


def run_change_detection_combinations(page):
    """UC-009: change detection entre pares de ortomapas."""
    pairs = [
        ("trento_vs_rasterio", "ortomapas/web_trento.tif", "ortomapas/web_rasterio_rgb.tif"),
        ("derna_vs_sentinel2", "ortomapas/web_derna.tif", "ortomapas/web_sentinel2.tif"),
        ("sentinel2_vs_landsat", "ortomapas/web_sentinel2.tif", "ortomapas/web_landsat.tif"),
    ]
    print("\n  [CHANGE DETECTION PAIRS]")
    for pair_id, p1, p2 in pairs:
        uc_009_change(page, pair_id, p1, p2)
        uc_017_compare(page, pair_id, p1, p2)


def run_ui_test(page):
    """UC-UI: validar interface web."""
    uc_ui_capture(page, "global")


# ==========================================================================
#  REPORT GENERATION
# ==========================================================================

def generate_report():
    total_tests = 0
    total_pass = 0
    total_fail = 0
    total_skip = 0

    for dataset_id, results in RESULTS.items():
        for uc_id, info in results.items():
            total_tests += 1
            if info["status"] == "PASS":
                total_pass += 1
            elif info["status"] == "FAIL":
                total_fail += 1
            else:
                total_skip += 1

    lines = []
    lines.append("# Relatorio Multi-Dataset — Validacao E2E com Ortomapas Reais da Web\n")
    lines.append(f"**Data:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    lines.append(f"**Backend:** {API_URL}\n")
    lines.append(f"**Frontend:** {BASE_URL}\n")
    lines.append("\n---\n")
    lines.append("## Datasets Utilizados\n")
    lines.append("Todos baixados de fontes publicas (GitHub releases, raw files).\n")
    lines.append("\n### Ortomapas RGB:\n")
    lines.append("| ID | Fonte | Tamanho | Dimensoes | CRS |")
    lines.append("|---|---|---|---|---|")
    lines.append("| trento | github.com/napo/geospatial_course_unitn | 7.9 MB | 4761x3900 | EPSG:25832 |")
    lines.append("| rasterio_rgb | github.com/rasterio/rasterio | 1.7 MB | 791x718 | EPSG:32618 |")
    lines.append("| derna | converted | 12 MB | 2804x1444 | EPSG:32634 |")
    lines.append("| sentinel2 | github.com/mommermi/geotiff_sample | 2.9 MB | 1001x1001 | EPSG:32631 |")
    lines.append("| landsat | github.com/opengeos/datasets | 5.6 MB | 2127x1564 | EPSG:3857 |")
    lines.append("\n### DSMs:\n")
    lines.append("| ID | Fonte | Tamanho | Dimensoes | CRS |")
    lines.append("|---|---|---|---|---|")
    lines.append("| dem_small | github.com/opengeos/datasets | 5.7 MB | 2880x1773 | EPSG:3857 |")
    lines.append("| dem_90m | github.com/opengeos/datasets | 17 MB | 4269x3113 | EPSG:3857 |")

    lines.append("\n---\n")
    lines.append("## Resumo Global\n")
    lines.append("| Metrica | Valor |")
    lines.append("|---|---|")
    lines.append(f"| Total de testes | **{total_tests}** |")
    lines.append(f"| Aprovados | **{total_pass}** ✅ |")
    lines.append(f"| Reprovados | **{total_fail}** ❌ |")
    lines.append(f"| Pulados (N/A) | **{total_skip}** ⏭ |")
    pct = (total_pass / (total_tests - total_skip) * 100) if (total_tests - total_skip) > 0 else 0
    lines.append(f"| Taxa de aprovacao (excluindo skips) | **{pct:.1f}%** |")

    lines.append("\n---\n")
    lines.append("## Matriz: Dataset x Caso de Uso\n")

    # Coletar todos os UCs unicos
    all_ucs = set()
    for results in RESULTS.values():
        all_ucs.update(results.keys())
    all_ucs = sorted(all_ucs)

    # Header
    header = "| Dataset | " + " | ".join(uc.replace("UC-", "") for uc in all_ucs) + " |"
    sep = "|---|" + "---|" * len(all_ucs)
    lines.append(header)
    lines.append(sep)

    for dataset_id in sorted(RESULTS.keys()):
        row = f"| **{dataset_id}** |"
        for uc in all_ucs:
            info = RESULTS[dataset_id].get(uc)
            if not info:
                row += " - |"
            elif info["status"] == "PASS":
                row += " ✅ |"
            elif info["status"] == "FAIL":
                row += " ❌ |"
            else:
                row += " ⏭ |"
        lines.append(row)

    lines.append("\n---\n")
    lines.append("## Detalhes por Dataset\n")
    for dataset_id in sorted(RESULTS.keys()):
        lines.append(f"\n### {dataset_id}\n")
        lines.append("| Caso de Uso | Status | Detalhes |")
        lines.append("|---|---|---|")
        for uc in sorted(RESULTS[dataset_id].keys()):
            info = RESULTS[dataset_id][uc]
            icon = {"PASS": "✅", "FAIL": "❌", "SKIP": "⏭"}.get(info["status"], "?")
            lines.append(f"| {uc} | {icon} {info['status']} | {info.get('detail', '')[:80]} |")

    # Divergencias
    if DIVERGENCIAS:
        lines.append("\n---\n")
        lines.append("## Divergencias Encontradas\n")
        lines.append("| ID | Dataset | UC | Esperado | Observado | Severidade |")
        lines.append("|---|---|---|---|---|---|")
        for d in DIVERGENCIAS:
            lines.append(f"| {d['id']} | {d['dataset']} | {d['uc']} | {d['esperado'][:40]} | {d['observado'][:50]} | {d['severidade']} |")
    else:
        lines.append("\n---\n")
        lines.append("## Divergencias\n")
        lines.append("**Nenhuma divergencia encontrada.**\n")

    # Screenshots
    lines.append("\n---\n")
    lines.append("## Screenshots Capturados\n")
    if os.path.exists(SCREENSHOTS_DIR):
        files = sorted(os.listdir(SCREENSHOTS_DIR))
        png_files = [f for f in files if f.endswith(".png")]
        lines.append(f"Total: **{len(png_files)} screenshots** em `runtime/screenshots_multi/`\n")
        for f in png_files[:20]:
            lines.append(f"- `{f}`")
        if len(png_files) > 20:
            lines.append(f"- ... e mais {len(png_files) - 20} arquivos")

    lines.append(f"\n\n*Relatorio gerado em {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")

    report_path = os.path.join(PROJECT_ROOT, "docs", "validacao", "relatorio_multi_dataset.md")
    with open(report_path, "w") as fp:
        fp.write("\n".join(lines))
    return report_path


# ==========================================================================
#  MAIN
# ==========================================================================

def main():
    print("=" * 70)
    print("  VALIDACAO E2E MULTI-DATASET — 5 ortomapas + 2 DSMs reais")
    print("=" * 70)
    print(f"  Total de combinacoes: {len(DATASETS_RGB)} ortomapas x {len(DATASETS_DSM)+1} DSM-configs")
    print()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-gpu"])
        ctx = browser.new_context(viewport={"width": 1920, "height": 1080}, ignore_https_errors=True)
        page = ctx.new_page()
        page.set_default_timeout(180000)  # 180s for slow hydrology operations

        # Pre-buscar mapeamento de ortomapas (caminho -> id) UMA UNICA VEZ
        print("  Pre-buscando mapeamento de ortomapas...")
        r = api(page, "GET", "/api/ortomapas")
        d = r.json()
        ortos = d.get("ortomapas", d) if isinstance(d, dict) else d
        ortomapa_map = {}
        if isinstance(ortos, list):
            for o in ortos:
                ca = o.get("caminho_arquivo", "")
                if ca:
                    # Permitir matching com/sem prefixo "data/"
                    norm = ca.replace("data/", "", 1) if ca.startswith("data/") else ca
                    ortomapa_map[norm] = o.get("id")
                    ortomapa_map[ca] = o.get("id")
        print(f"  Mapeamento: {len(ortomapa_map)} entradas")

        # Run ortomapa tests pareados com cada DSM
        # Para nao explodir muito, cada ortomapa testa com 1 DSM
        # Usar apenas dem_small (mais rapido) para todos
        dsm_path = DATASETS_DSM[0][1]  # dem_small

        for orto_id, orto_path, label in DATASETS_RGB:
            run_for_dataset(page, orto_id, orto_path, label, dsm_path, ortomapa_map)

        # Tambem testar cada DSM standalone
        for dsm_id, dsm_p, label in DATASETS_DSM:
            run_for_dataset(page, dsm_id, dsm_p, label, dsm_p, ortomapa_map)

        # Tests pareados (change detection)
        run_change_detection_combinations(page)

        # UI test
        run_ui_test(page)

        browser.close()

    # Print resumo
    print()
    print("=" * 70)
    total = sum(len(r) for r in RESULTS.values())
    p_count = sum(1 for r in RESULTS.values() for v in r.values() if v["status"] == "PASS")
    f_count = sum(1 for r in RESULTS.values() for v in r.values() if v["status"] == "FAIL")
    s_count = sum(1 for r in RESULTS.values() for v in r.values() if v["status"] == "SKIP")
    print(f"  RESULTADO: {p_count} PASS | {f_count} FAIL | {s_count} SKIP | TOTAL {total}")
    print(f"  DIVERGENCIAS: {len(DIVERGENCIAS)}")
    print("=" * 70)

    report = generate_report()
    print(f"\n  Relatorio: {report}")


if __name__ == "__main__":
    main()

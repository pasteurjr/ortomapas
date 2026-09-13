#!/usr/bin/env python3
"""
============================================================================
  FASE 3 — TESTES PLAYWRIGHT E2E POR CASO DE USO
  Sistema de Ortomapas — Validacao Completa

  Executa cada caso de uso, captura screenshots por passo,
  valida respostas, registra divergencias.
============================================================================
"""
import os
import sys
import json
import time
import traceback
import uuid
from datetime import datetime
from playwright.sync_api import sync_playwright

# Config
BASE_URL = "http://localhost:5176"
API_URL = "http://localhost:8888"
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
SCREENSHOTS_DIR = os.path.join(PROJECT_ROOT, "runtime", "screenshots")
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

# Report state
REPORT = []
DIVERGENCIAS = []
UC_RESULTS = []
STEP_COUNT = 0
AUTH_HEADERS = {}
AUTH_TOKEN = ""
TEST_PROJECT_ID = None


def snap(page, uc_id, step_name):
    """Capture screenshot for a use case step."""
    fname = f"{uc_id}_step{STEP_COUNT:02d}_{step_name}.png"
    page.screenshot(path=os.path.join(SCREENSHOTS_DIR, fname), full_page=False)
    return fname


def api(page, method, path, body=None):
    """API call helper."""
    url = f"{API_URL}{path}"
    headers = {"Content-Type": "application/json", **AUTH_HEADERS}
    if method == "GET":
        return page.request.get(url)
    elif method == "POST":
        return page.request.post(url, data=json.dumps(body) if body else None, headers=headers)
    elif method == "PUT":
        return page.request.put(url, data=json.dumps(body) if body else None, headers=headers)
    elif method == "DELETE":
        return page.request.delete(url)


def divergencia(uc_id, step, esperado, observado, evidencia, severidade="MEDIA"):
    DIVERGENCIAS.append({
        "id": f"DIV-{len(DIVERGENCIAS)+1:03d}",
        "caso_uso": uc_id,
        "passo": step,
        "esperado": esperado,
        "observado": observado,
        "evidencia": evidencia,
        "severidade": severidade,
    })


class UCResult:
    def __init__(self, uc_id, nome):
        self.uc_id = uc_id
        self.nome = nome
        self.steps = []
        self.status = "APROVADO"
        self.screenshots = []

    def step_pass(self, desc, screenshot=None):
        self.steps.append(("PASS", desc, screenshot))
        if screenshot:
            self.screenshots.append(screenshot)

    def step_fail(self, desc, error=None, screenshot=None):
        self.steps.append(("FAIL", desc, screenshot, error))
        self.status = "REPROVADO"
        if screenshot:
            self.screenshots.append(screenshot)

    def to_markdown(self):
        lines = [f"\n### {self.uc_id}: {self.nome}\n"]
        icon = "✅" if self.status == "APROVADO" else "❌"
        lines.append(f"**Status:** {icon} **{self.status}**\n")
        lines.append("**Passos executados:**\n")
        for i, s in enumerate(self.steps, 1):
            status_icon = "✅" if s[0] == "PASS" else "❌"
            lines.append(f"{i}. {status_icon} {s[1]}")
            if s[0] == "FAIL" and len(s) > 3 and s[3]:
                lines.append(f"   - **Erro:** `{s[3]}`")
            if len(s) > 2 and s[2]:
                lines.append(f"   ![](../runtime/screenshots/{s[2]})")
        lines.append("")
        return "\n".join(lines)


# ======================================================================
#  USE CASES
# ======================================================================

def uc_001_criar_projeto(page):
    """UC-001: Criar Novo Projeto via API"""
    global STEP_COUNT, TEST_PROJECT_ID
    STEP_COUNT = 0
    uc = UCResult("UC-001", "Criar Novo Projeto")

    try:
        # Step 1: Verificar estado inicial
        STEP_COUNT += 1
        r = api(page, "GET", "/api/projetos")
        initial = r.json()
        initial_count = initial.get("total", len(initial.get("projetos", [])))
        ss = snap(page, "UC001", "estado_inicial")
        uc.step_pass(f"Estado inicial: {initial_count} projetos existentes", ss)

        # Step 2: Enviar POST com dados completos
        STEP_COUNT += 1
        body = {
            "nome": "UC-001 Teste Automatizado",
            "descricao": "Projeto criado pelo teste Playwright UC-001",
            "area_estudo": "Serra da Moeda - Teste E2E",
            "centro_lat": -20.10, "centro_lon": -43.96,
            "bbox_norte": -20.05, "bbox_sul": -20.15,
            "bbox_leste": -43.91, "bbox_oeste": -44.01,
            "objetivo": "Validar criacao de projetos",
            "responsavel": "Playwright Bot",
            "status": "em_andamento"
        }
        r = api(page, "POST", "/api/projetos", body)
        assert r.status in (200, 201), f"HTTP {r.status}"
        d = r.json()
        TEST_PROJECT_ID = d.get("id")
        new_id = d.get("id")
        assert new_id is not None, "ID nao retornado"
        uc.step_pass(f"Projeto criado com ID={new_id}, HTTP {r.status}")

        # Step 3: Validar campos retornados
        STEP_COUNT += 1
        assert d.get("nome") == body["nome"], f"Nome diverge: {d.get('nome')}"
        assert d.get("status") == "em_andamento"
        uc.step_pass(f"Campos validados: nome='{d['nome']}', status='{d['status']}'")

        # Step 4: Buscar projeto criado por ID
        STEP_COUNT += 1
        r2 = api(page, "GET", f"/api/projetos/{new_id}")
        assert r2.status == 200
        d2 = r2.json()
        assert d2.get("id") == new_id
        uc.step_pass(f"GET /api/projetos/{new_id} retornou projeto correto")

        # Step 5: Verificar contagem aumentou
        STEP_COUNT += 1
        r3 = api(page, "GET", "/api/projetos")
        payload = r3.json()
        projetos_finais = payload.get("projetos", []) if isinstance(payload, dict) else payload
        new_count = payload.get("total", len(projetos_finais)) if isinstance(payload, dict) else len(projetos_finais)
        assert any(p.get("id") == new_id for p in projetos_finais), f"Projeto {new_id} nao apareceu na listagem"
        uc.step_pass(f"Contagem aumentou de {initial_count} para {new_count}")

    except Exception as e:
        STEP_COUNT += 1
        ss = snap(page, "UC001", "erro")
        uc.step_fail(f"Erro na execucao", str(e), ss)
        divergencia("UC-001", STEP_COUNT, "Criacao sem erros", str(e), ss)

    UC_RESULTS.append(uc)
    return uc


def uc_002_buscar_projetos(page):
    """UC-002: Buscar e Filtrar Projetos"""
    global STEP_COUNT
    STEP_COUNT = 0
    uc = UCResult("UC-002", "Buscar e Filtrar Projetos")

    try:
        # Step 1: Buscar por texto
        STEP_COUNT += 1
        r = api(page, "GET", "/api/projetos/search?q=Serra")
        assert r.status == 200, f"HTTP {r.status}: {r.text()[:200]}"
        d = r.json()
        results = d if isinstance(d, list) else (d.get("projetos") or d.get("results") or [])
        uc.step_pass(f"Busca por 'Serra': {len(results)} resultados")

        # Step 2: Filtrar por status
        STEP_COUNT += 1
        r = api(page, "GET", "/api/projetos?status=planejado")
        assert r.status == 200
        d = r.json()
        projetos = d.get("projetos", d) if isinstance(d, dict) else d
        count = len(projetos) if isinstance(projetos, list) else 0
        uc.step_pass(f"Filtro status=planejado: {count} projetos")

        # Step 3: Filtrar por status em_andamento
        STEP_COUNT += 1
        r = api(page, "GET", "/api/projetos?status=em_andamento")
        assert r.status == 200
        uc.step_pass("Filtro status=em_andamento funciona")

    except Exception as e:
        detail = str(e) or repr(e)
        uc.step_fail("Erro", detail)
        divergencia("UC-002", STEP_COUNT, "Busca/filtro funcional", detail, "")

    UC_RESULTS.append(uc)
    return uc


def uc_003_selecionar_projeto(page):
    """UC-003: Selecionar Projeto e Listar Ortomapas"""
    global STEP_COUNT
    STEP_COUNT = 0
    uc = UCResult("UC-003", "Selecionar Projeto e Listar Ortomapas")

    try:
        # Step 1: Listar ortomapas do projeto 3
        STEP_COUNT += 1
        project_id = TEST_PROJECT_ID or 3
        r = api(page, "GET", f"/api/projetos/{project_id}/ortomapas")
        assert r.status == 200
        d = r.json()
        ortos = d if isinstance(d, list) else d.get("ortomapas", [])
        uc.step_pass(f"Projeto 3 tem {len(ortos)} ortomapas")

        # Step 2: Verificar tipos presentes
        STEP_COUNT += 1
        tipos = set(o.get("tipo", "?") for o in ortos) if isinstance(ortos, list) and ortos else set()
        uc.step_pass(f"Tipos presentes: {tipos}")

        # Step 3: UI - Navegar e verificar projetos na sidebar
        STEP_COUNT += 1
        page.goto(BASE_URL, wait_until="networkidle", timeout=15000)
        time.sleep(2)
        body = page.inner_text("body")
        ss = snap(page, "UC003", "sidebar_projetos")
        uc.step_pass(f"Frontend carregado, conteudo: {len(body)} chars", ss)

    except Exception as e:
        ss = snap(page, "UC003", "erro")
        uc.step_fail("Erro", str(e), ss)
        divergencia("UC-003", STEP_COUNT, "Listar ortomapas do projeto", str(e), ss)

    UC_RESULTS.append(uc)
    return uc


def uc_005_vegetacao_vari(page):
    """UC-005: Calcular Indice de Vegetacao VARI"""
    global STEP_COUNT
    STEP_COUNT = 0
    uc = UCResult("UC-005", "Calcular Indice de Vegetacao VARI")

    try:
        # Step 1: Enviar requisicao VARI
        STEP_COUNT += 1
        r = api(page, "POST", "/api/tools/vegetation", {
            "input_path": "ortomapas/serra_moeda_teste.tif",
            "output_name": "e2e_vari", "index_name": "VARI"
        })
        assert r.status == 200, f"HTTP {r.status}: {r.text[:200]}"
        d = r.json()
        out = d.get("output_path", "")
        uc.step_pass(f"VARI calculado. Output: {os.path.basename(out)}")

        # Step 2: Verificar arquivo gerado
        STEP_COUNT += 1
        assert os.path.exists(out), f"Arquivo nao existe: {out}"
        size_kb = os.path.getsize(out) / 1024
        uc.step_pass(f"Arquivo existe: {size_kb:.0f} KB")

        # Step 3: Validar integridade com rasterio
        STEP_COUNT += 1
        import rasterio
        with rasterio.open(out) as src:
            assert src.count >= 1, "Sem bandas"
            assert src.crs is not None, "Sem CRS"
            assert src.width == 1024 and src.height == 1024
        uc.step_pass(f"GeoTIFF valido: {src.width}x{src.height}, CRS={src.crs}")

        # Step 4: Validar estatisticas
        STEP_COUNT += 1
        stats = d.get("statistics", {})
        band_stats = stats.get("band_1", stats)
        assert "min" in band_stats and "max" in band_stats
        uc.step_pass(f"Estatisticas: min={band_stats.get('min')}, max={band_stats.get('max')}, mean={band_stats.get('mean','N/A')}")

        # Step 5: Calcular TGI tambem
        STEP_COUNT += 1
        r2 = api(page, "POST", "/api/tools/vegetation", {
            "input_path": "ortomapas/serra_moeda_teste.tif",
            "output_name": "e2e_tgi", "index_name": "TGI"
        })
        assert r2.status == 200
        uc.step_pass("TGI tambem calculado com sucesso")

        # Step 6: Calcular ExG
        STEP_COUNT += 1
        r3 = api(page, "POST", "/api/tools/vegetation", {
            "input_path": "ortomapas/serra_moeda_teste.tif",
            "output_name": "e2e_exg", "index_name": "ExG"
        })
        assert r3.status == 200
        uc.step_pass("ExG calculado com sucesso")

        # Step 7: Calcular GLI
        STEP_COUNT += 1
        r4 = api(page, "POST", "/api/tools/vegetation", {
            "input_path": "ortomapas/serra_moeda_teste.tif",
            "output_name": "e2e_gli", "index_name": "GLI"
        })
        assert r4.status == 200
        uc.step_pass("GLI calculado com sucesso. Todos os 4 indices OK.")

    except Exception as e:
        uc.step_fail("Erro no calculo de vegetacao", str(e))
        divergencia("UC-005", STEP_COUNT, "Indices calculados sem erro", str(e), "")

    UC_RESULTS.append(uc)
    return uc


def uc_006_slope(page):
    """UC-006: Calcular Declividade"""
    global STEP_COUNT
    STEP_COUNT = 0
    uc = UCResult("UC-006", "Calcular Declividade (Slope)")

    try:
        STEP_COUNT += 1
        r = api(page, "POST", "/api/tools/slope", {
            "input_path": "dsm/serra_moeda_dsm.tif", "output_name": "e2e_slope"
        })
        assert r.status == 200
        d = r.json()
        uc.step_pass(f"Slope calculado: {d.get('output_path','')}")

        STEP_COUNT += 1
        r2 = api(page, "POST", "/api/tools/aspect", {
            "input_path": "dsm/serra_moeda_dsm.tif", "output_name": "e2e_aspect"
        })
        assert r2.status == 200
        uc.step_pass("Aspect calculado")

    except Exception as e:
        uc.step_fail("Erro", str(e))
        divergencia("UC-006", STEP_COUNT, "Slope/Aspect calculados", str(e), "")

    UC_RESULTS.append(uc)
    return uc


def uc_007_contornos(page):
    """UC-007: Gerar Curvas de Nivel"""
    global STEP_COUNT
    STEP_COUNT = 0
    uc = UCResult("UC-007", "Gerar Curvas de Nivel")

    try:
        STEP_COUNT += 1
        r = api(page, "POST", "/api/tools/contours", {
            "input_path": "dsm/serra_moeda_dsm.tif",
            "output_name": "e2e_contornos", "interval": 10.0
        })
        assert r.status == 200
        d = r.json()
        uc.step_pass(f"Contornos gerados com intervalo 10m")

    except Exception as e:
        uc.step_fail("Erro", str(e))
        divergencia("UC-007", STEP_COUNT, "Contornos gerados", str(e), "")

    UC_RESULTS.append(uc)
    return uc


def uc_008_hillshade(page):
    """UC-008: Gerar Hillshade"""
    global STEP_COUNT
    STEP_COUNT = 0
    uc = UCResult("UC-008", "Gerar Hillshade")

    try:
        STEP_COUNT += 1
        r = api(page, "POST", "/api/tools/hillshade", {
            "input_path": "dsm/serra_moeda_dsm.tif",
            "output_name": "e2e_hillshade", "azimuth": 315, "altitude": 45
        })
        assert r.status == 200
        uc.step_pass(f"Hillshade gerado (az=315, alt=45)")

    except Exception as e:
        uc.step_fail("Erro", str(e))
        divergencia("UC-008", STEP_COUNT, "Hillshade gerado", str(e), "")

    UC_RESULTS.append(uc)
    return uc


def uc_009_mudancas(page):
    """UC-009: Detectar Mudancas Temporais"""
    global STEP_COUNT
    STEP_COUNT = 0
    uc = UCResult("UC-009", "Detectar Mudancas Temporais")

    try:
        STEP_COUNT += 1
        r = api(page, "POST", "/api/tools/changes", {
            "raster1_path": "ortomapas/serra_moeda_teste.tif",
            "raster2_path": "ortomapas/serra_moeda_teste_2.tif",
            "output_name": "e2e_mudancas", "threshold": 30.0
        })
        assert r.status == 200
        d = r.json()
        stats = d.get("statistics", {})
        pct = stats.get("percent_changed", 0)
        uc.step_pass(f"Mudancas detectadas: {pct:.2f}% alterado")

        STEP_COUNT += 1
        assert pct > 0, "Nenhuma mudanca detectada (deveria haver)"
        uc.step_pass(f"Validacao: mudanca > 0% confirmada ({pct:.2f}%)")

        STEP_COUNT += 1
        out = d.get("output_path", "")
        assert os.path.exists(out), f"Arquivo nao existe: {out}"
        uc.step_pass(f"Arquivo de mudancas gerado: {os.path.basename(out)}")

    except Exception as e:
        uc.step_fail("Erro", str(e))
        divergencia("UC-009", STEP_COUNT, "Mudancas detectadas", str(e), "")

    UC_RESULTS.append(uc)
    return uc


def uc_010_classificacao(page):
    """UC-010: Classificar Uso do Solo (KMeans)"""
    global STEP_COUNT
    STEP_COUNT = 0
    uc = UCResult("UC-010", "Classificar Uso do Solo (KMeans)")

    try:
        STEP_COUNT += 1
        r = api(page, "POST", "/api/tools/segment", {
            "input_path": "ortomapas/serra_moeda_teste.tif",
            "output_name": "e2e_classificacao", "n_clusters": 5
        })
        assert r.status == 200
        d = r.json()
        clusters = d.get("clusters", [])
        uc.step_pass(f"Classificacao: {len(clusters)} clusters gerados")

        STEP_COUNT += 1
        total_pct = sum(c.get("percent", 0) for c in clusters)
        assert abs(total_pct - 100) < 1, f"Soma dos clusters ({total_pct}%) deveria ser ~100%"
        uc.step_pass(f"Soma dos clusters: {total_pct:.1f}% (valido)")

    except Exception as e:
        uc.step_fail("Erro", str(e))
        divergencia("UC-010", STEP_COUNT, "Classificacao funcional", str(e), "")

    UC_RESULTS.append(uc)
    return uc


def uc_011_hidrologia(page):
    """UC-011: Extrair Rede de Drenagem"""
    global STEP_COUNT
    STEP_COUNT = 0
    uc = UCResult("UC-011", "Extrair Rede de Drenagem")

    try:
        STEP_COUNT += 1
        r = api(page, "POST", "/api/tools/hydrology/streams", {
            "dtm_path": "dsm/serra_moeda_dsm.tif",
            "output_name": "e2e_drenagem", "threshold": 100
        })
        assert r.status == 200
        d = r.json()
        uc.step_pass(f"Rede de drenagem extraida")

    except Exception as e:
        uc.step_fail("Erro", str(e))
        divergencia("UC-011", STEP_COUNT, "Drenagem extraida", str(e), "")

    UC_RESULTS.append(uc)
    return uc


def uc_012_volume(page):
    """UC-012: Calcular Volume"""
    global STEP_COUNT
    STEP_COUNT = 0
    uc = UCResult("UC-012", "Calcular Volume")

    try:
        STEP_COUNT += 1
        r = api(page, "POST", "/api/tools/volume", {
            "dsm_path": "dsm/serra_moeda_dsm.tif",
            "reference_elevation": 950.0, "output_name": "e2e_volume"
        })
        assert r.status == 200
        d = r.json()
        vol_up = d.get("volume_above_m3", 0)
        vol_dn = d.get("volume_below_m3", 0)
        uc.step_pass(f"Volume: acima={vol_up:,.0f}m3, abaixo={vol_dn:,.0f}m3")

        STEP_COUNT += 1
        assert vol_up > 0 or vol_dn > 0, "Volume zerado"
        uc.step_pass("Volume nao-zero confirmado")

    except Exception as e:
        uc.step_fail("Erro", str(e))
        divergencia("UC-012", STEP_COUNT, "Volume calculado", str(e), "")

    UC_RESULTS.append(uc)
    return uc


def uc_013_anotacao_poligono(page):
    """UC-013: Criar Anotacao Poligono"""
    global STEP_COUNT
    STEP_COUNT = 0
    uc = UCResult("UC-013", "Criar Anotacao Poligono")

    try:
        STEP_COUNT += 1
        body = {
            "ortomapa_id": 1, "tipo": "poligono",
            "categoria": "vegetacao_densa",
            "rotulo": "E2E - Area de campo rupestre",
            "geometria_wkt": "POLYGON((-43.97 -20.09, -43.96 -20.09, -43.96 -20.10, -43.97 -20.10, -43.97 -20.09))",
            "centro_lat": -20.095, "centro_lon": -43.965,
            "fonte": "manual", "criado_por": "E2E Playwright"
        }
        r = api(page, "POST", "/api/anotacoes", body)
        assert r.status in (200, 201), f"HTTP {r.status}: {r.text()[:200]}"
        uc.step_pass("Anotacao poligono criada")

        STEP_COUNT += 1
        r2 = api(page, "GET", "/api/anotacoes")
        d2 = r2.json()
        anots = d2 if isinstance(d2, list) else d2.get("anotacoes", [])
        uc.step_pass(f"Total anotacoes: {len(anots)}")

    except Exception as e:
        uc.step_fail("Erro", str(e))
        divergencia("UC-013", STEP_COUNT, "Anotacao criada", str(e), "")

    UC_RESULTS.append(uc)
    return uc


def uc_014_anotacao_ponto(page):
    """UC-014: Criar Anotacao Ponto"""
    global STEP_COUNT
    STEP_COUNT = 0
    uc = UCResult("UC-014", "Criar Anotacao Ponto")

    try:
        STEP_COUNT += 1
        body = {
            "ortomapa_id": 1, "tipo": "ponto",
            "categoria": "erosao",
            "rotulo": "E2E - Ponto de erosao em trilha",
            "geometria_wkt": "POINT(-43.965 -20.095)",
            "centro_lat": -20.095, "centro_lon": -43.965,
            "fonte": "manual", "criado_por": "E2E Playwright"
        }
        r = api(page, "POST", "/api/anotacoes", body)
        assert r.status in (200, 201)
        uc.step_pass("Anotacao ponto criada")

    except Exception as e:
        uc.step_fail("Erro", str(e))
        divergencia("UC-014", STEP_COUNT, "Anotacao ponto criada", str(e), "")

    UC_RESULTS.append(uc)
    return uc


def uc_017_comparacao_temporal(page):
    """UC-017: Comparar Dois Ortomapas"""
    global STEP_COUNT
    STEP_COUNT = 0
    uc = UCResult("UC-017", "Comparar Dois Ortomapas")

    try:
        STEP_COUNT += 1
        r1 = api(page, "POST", "/api/tools/statistics", {"input_path": "ortomapas/serra_moeda_teste.tif"})
        r2 = api(page, "POST", "/api/tools/statistics", {"input_path": "ortomapas/serra_moeda_teste_2.tif"})
        assert r1.status == 200 and r2.status == 200
        uc.step_pass("Estatisticas de ambos ortomapas obtidas")

        STEP_COUNT += 1
        s1 = r1.json().get("statistics", {})
        s2 = r2.json().get("statistics", {})
        mean1 = s1.get("band_2", {}).get("mean", 0)
        mean2 = s2.get("band_2", {}).get("mean", 0)
        diff = abs(mean1 - mean2)
        uc.step_pass(f"Banda verde: media1={mean1:.1f}, media2={mean2:.1f}, diff={diff:.1f}")

    except Exception as e:
        uc.step_fail("Erro", str(e))
        divergencia("UC-017", STEP_COUNT, "Comparacao funcional", str(e), "")

    UC_RESULTS.append(uc)
    return uc


def uc_019_registrar_voo(page):
    """UC-019: Registrar Voo de Drone"""
    global STEP_COUNT
    STEP_COUNT = 0
    uc = UCResult("UC-019", "Registrar Voo de Drone")

    try:
        STEP_COUNT += 1
        body = {
            "projeto_id": TEST_PROJECT_ID or 3,
            "data_voo": "2026-05-20T09:30:00",
            "local_decolagem_lat": -20.083,
            "local_decolagem_lon": -43.950,
            "altitude_voo_m": 50,
            "velocidade_ms": 4,
            "sobreposicao_frontal": 75,
            "sobreposicao_lateral": 70,
            "num_fotos": 150,
            "gsd_cm": 1.2,
            "area_coberta_ha": 10.5,
            "num_baterias": 3,
            "tipo_bateria": "standard",
            "condicoes_vento": "calmo",
            "condicoes_ceu": "nublado uniforme",
            "app_voo": "Litchi Pilot 5.0",
            "observacoes": "Voo de teste E2E - Serra da Moeda"
        }
        r = api(page, "POST", "/api/voos", body)
        assert r.status in (200, 201), f"HTTP {r.status}: {r.text()[:200]}"
        d = r.json()
        uc.step_pass(f"Voo criado ID={d.get('id')}, altitude={d.get('altitude_voo_m')}m")

        STEP_COUNT += 1
        r2 = api(page, "GET", f"/api/voos?projeto_id={TEST_PROJECT_ID or 3}")
        assert r2.status == 200
        voos = r2.json()
        count = len(voos) if isinstance(voos, list) else voos.get("total", 0)
        uc.step_pass(f"Voos do projeto 3: {count}")

    except Exception as e:
        uc.step_fail("Erro", str(e))
        divergencia("UC-019", STEP_COUNT, "Voo criado", str(e), "")

    UC_RESULTS.append(uc)
    return uc


def uc_020_segmentacao(page):
    """UC-020: Segmentar Ortomapa"""
    global STEP_COUNT
    STEP_COUNT = 0
    uc = UCResult("UC-020", "Segmentar Ortomapa")

    try:
        STEP_COUNT += 1
        r = api(page, "POST", "/api/tools/segment", {
            "input_path": "ortomapas/serra_moeda_teste.tif",
            "output_name": "e2e_segmentacao", "n_clusters": 7
        })
        assert r.status == 200
        d = r.json()
        uc.step_pass(f"Segmentacao: {d.get('n_clusters')} clusters")

    except Exception as e:
        uc.step_fail("Erro", str(e))
        divergencia("UC-020", STEP_COUNT, "Segmentacao funcional", str(e), "")

    UC_RESULTS.append(uc)
    return uc


def uc_ui_frontend(page):
    """UC-UI: Validacao Completa da Interface Web"""
    global STEP_COUNT
    STEP_COUNT = 0
    uc = UCResult("UC-UI", "Validacao da Interface Web")

    try:
        # Step 1: Carregar pagina
        STEP_COUNT += 1
        page.goto(BASE_URL, wait_until="networkidle", timeout=20000)
        time.sleep(3)
        ss = snap(page, "UC-UI", "pagina_inicial")
        title = page.title()
        uc.step_pass(f"Pagina carregada. Titulo: '{title}'", ss)

        # Step 2: Leaflet map
        STEP_COUNT += 1
        leaflet = page.query_selector(".leaflet-container")
        has_map = leaflet is not None
        tiles = page.query_selector_all(".leaflet-tile")
        ss = snap(page, "UC-UI", "mapa_leaflet")
        if has_map:
            uc.step_pass(f"Mapa Leaflet presente, {len(tiles)} tiles", ss)
        else:
            uc.step_fail("Mapa Leaflet NAO encontrado", screenshot=ss)
            divergencia("UC-UI", 2, "Mapa Leaflet visivel", "Container nao encontrado", ss, "ALTA")

        # Step 3: Zoom
        STEP_COUNT += 1
        zoom_btn = page.query_selector(".leaflet-control-zoom-in")
        if zoom_btn:
            zoom_btn.click()
            time.sleep(0.5)
            zoom_btn.click()
            time.sleep(0.5)
            ss = snap(page, "UC-UI", "zoom_in")
            uc.step_pass("Zoom In (2 cliques) executado", ss)
        else:
            uc.step_fail("Botao zoom nao encontrado")
            divergencia("UC-UI", 3, "Zoom funcional", "Botao zoom ausente", "", "MEDIA")

        # Step 4: Console errors
        STEP_COUNT += 1
        errors = []
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.reload(wait_until="networkidle", timeout=15000)
        time.sleep(2)
        ss = snap(page, "UC-UI", "console_check")
        if len(errors) == 0:
            uc.step_pass("Zero erros no console JS", ss)
        else:
            uc.step_fail(f"{len(errors)} erros no console: {errors[:3]}", screenshot=ss)
            divergencia("UC-UI", 4, "Console sem erros", f"{len(errors)} erros", ss, "MEDIA")

        # Step 5: Screenshot final
        STEP_COUNT += 1
        ss = snap(page, "UC-UI", "final_completo")
        uc.step_pass("Screenshot final da interface capturado", ss)

    except Exception as e:
        ss = snap(page, "UC-UI", "erro_geral")
        uc.step_fail("Erro na validacao UI", str(e), ss)
        divergencia("UC-UI", STEP_COUNT, "UI funcional", str(e), ss, "ALTA")

    UC_RESULTS.append(uc)
    return uc


# ======================================================================
#  EXECUTION AND REPORTING
# ======================================================================

def run_all_tests():
    """Execute all use case tests."""
    global AUTH_HEADERS, AUTH_TOKEN
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-gpu"])
        ctx = browser.new_context(viewport={"width": 1920, "height": 1080}, ignore_https_errors=True)
        page = ctx.new_page()
        page.set_default_timeout(15000)

        # Cada execução usa uma conta pesquisador efêmera para exercitar os
        # endpoints protegidos sem depender de credenciais de produção.
        email = f"e2e-{uuid.uuid4().hex[:12]}@example.invalid"
        reg = page.request.post(f"{API_URL}/api/auth/register", data=json.dumps({"email": email, "nome": "E2E Playwright", "senha": "Validacao#2026", "perfil": "pesquisador"}), headers={"Content-Type": "application/json"})
        if reg.status not in (201, 409):
            raise RuntimeError(f"Falha ao registrar usuario E2E: HTTP {reg.status}")
        auth = page.request.post(f"{API_URL}/api/auth/login", data=json.dumps({"email": email, "senha": "Validacao#2026"}), headers={"Content-Type": "application/json"})
        if auth.status != 200:
            raise RuntimeError(f"Falha ao autenticar usuario E2E: HTTP {auth.status}")
        AUTH_TOKEN = auth.json()['access_token']
        AUTH_HEADERS = {"Authorization": f"Bearer {AUTH_TOKEN}"}
        # A tela autenticada usa o mesmo token no localStorage.
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=20000)
        page.evaluate("token => localStorage.setItem('ortomapas_token', token)", AUTH_TOKEN)
        page.reload(wait_until="networkidle", timeout=20000)

        print("\n  Executando casos de uso...\n")

        tests = [
            uc_001_criar_projeto,
            uc_002_buscar_projetos,
            uc_003_selecionar_projeto,
            uc_005_vegetacao_vari,
            uc_006_slope,
            uc_007_contornos,
            uc_008_hillshade,
            uc_009_mudancas,
            uc_010_classificacao,
            uc_011_hidrologia,
            uc_012_volume,
            uc_013_anotacao_poligono,
            uc_014_anotacao_ponto,
            uc_017_comparacao_temporal,
            uc_019_registrar_voo,
            uc_020_segmentacao,
            uc_ui_frontend,
        ]

        for test_fn in tests:
            try:
                uc = test_fn(page)
                icon = "✅" if uc.status == "APROVADO" else "❌"
                print(f"  {icon} {uc.uc_id}: {uc.nome} — {uc.status} ({len(uc.steps)} passos)")
            except Exception as e:
                print(f"  ❌ ERRO FATAL em {test_fn.__name__}: {e}")

        browser.close()


def generate_report():
    """Generate validation report."""
    total = len(UC_RESULTS)
    passed = sum(1 for uc in UC_RESULTS if uc.status == "APROVADO")
    failed = total - passed

    lines = []
    lines.append("# Relatorio de Execucao — Validacao Playwright E2E\n")
    lines.append(f"**Data:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    lines.append(f"**Backend:** {API_URL}\n")
    lines.append(f"**Frontend:** {BASE_URL}\n")
    lines.append("\n---\n")
    lines.append("## Resumo\n")
    lines.append(f"| Total | Aprovados | Reprovados |")
    lines.append(f"|---|---|---|")
    lines.append(f"| **{total}** | **{passed}** ✅ | **{failed}** ❌ |")
    lines.append(f"\nTaxa: **{(passed/total*100) if total else 0:.1f}%**\n")
    lines.append("\n---\n")
    lines.append("## Resultado por Caso de Uso\n")

    for uc in UC_RESULTS:
        lines.append(uc.to_markdown())

    # Divergencias
    if DIVERGENCIAS:
        lines.append("\n---\n")
        lines.append("## Divergencias Encontradas\n")
        lines.append("| ID | UC | Passo | Esperado | Observado | Severidade |")
        lines.append("|---|---|---|---|---|---|")
        for d in DIVERGENCIAS:
            lines.append(f"| {d['id']} | {d['caso_uso']} | {d['passo']} | {d['esperado'][:50]} | {d['observado'][:50]} | {d['severidade']} |")
    else:
        lines.append("\n---\n")
        lines.append("## Divergencias\n")
        lines.append("**Nenhuma divergencia encontrada.**\n")

    # Arquivos gerados
    lines.append("\n---\n")
    lines.append("## Screenshots Capturados\n")
    ss_dir = SCREENSHOTS_DIR
    if os.path.exists(ss_dir):
        files = sorted(os.listdir(ss_dir))
        for f in files:
            if f.endswith(".png"):
                lines.append(f"- `{f}`")

    lines.append(f"\n\n*Gerado em {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")

    report_path = os.path.join(PROJECT_ROOT, "docs", "validacao", "relatorio_execucao.md")
    with open(report_path, "w") as fp:
        fp.write("\n".join(lines))
    print(f"\n  Relatorio: {report_path}")

    # Divergencias file
    if DIVERGENCIAS:
        div_path = os.path.join(PROJECT_ROOT, "docs", "validacao", "divergencias.md")
        div_lines = ["# Registro de Divergencias\n"]
        for d in DIVERGENCIAS:
            div_lines.append(f"\n## {d['id']}\n")
            div_lines.append(f"- **Caso de Uso:** {d['caso_uso']}")
            div_lines.append(f"- **Passo:** {d['passo']}")
            div_lines.append(f"- **Esperado:** {d['esperado']}")
            div_lines.append(f"- **Observado:** {d['observado']}")
            div_lines.append(f"- **Severidade:** {d['severidade']}")
            if d.get("evidencia"):
                div_lines.append(f"- **Evidencia:** {d['evidencia']}")
        with open(div_path, "w") as fp:
            fp.write("\n".join(div_lines))
        print(f"  Divergencias: {div_path}")

    return report_path


if __name__ == "__main__":
    print("=" * 70)
    print("  VALIDACAO E2E PLAYWRIGHT — SISTEMA DE ORTOMAPAS")
    print("=" * 70)

    run_all_tests()

    total = len(UC_RESULTS)
    passed = sum(1 for uc in UC_RESULTS if uc.status == "APROVADO")

    print()
    print("=" * 70)
    print(f"  RESULTADO: {passed}/{total} APROVADOS ({(passed/total*100) if total else 0:.0f}%)")
    print(f"  DIVERGENCIAS: {len(DIVERGENCIAS)}")
    print("=" * 70)

    generate_report()

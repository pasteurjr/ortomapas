"""Executa a demonstracao do produto e captura as cenas do video narrado."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
BASE_URL = os.getenv("FRONTEND_URL", "http://127.0.0.1:5300").rstrip("/")
RUN_ID = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
OUTPUT = Path(os.getenv("VIDEO_DEMO_DIR", str(ROOT / "runtime/screenshots/demonstracao_video"))) / RUN_ID
OUTPUT.mkdir(parents=True, exist_ok=True)
EMAIL = os.getenv("E2E_EMAIL", "demo-guarajuba@example.test")
PASSWORD = os.getenv("E2E_PASSWORD", "demo-guarajuba-2026")
PROJECT = os.getenv("E2E_PROJECT", "Demo Planejamento Mini 3")


def main() -> int:
    result = {"suite": "demonstracao_video_completo", "base_url": BASE_URL, "run_id": RUN_ID, "scenes": []}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900}, record_video_dir=str(OUTPUT / "video"))
        page = context.new_page()
        page.set_default_timeout(7000)

        def shot(scene_id: str, title: str, narration: str, action: str, target=None) -> None:
            path = OUTPUT / f"{scene_id}.png"
            if target is not None:
                target.screenshot(path=str(path), timeout=30000)
            else:
                page.screenshot(path=str(path), full_page=False, timeout=30000)
            result["scenes"].append({"id": scene_id, "title": title, "action": action, "narration": narration, "screenshot": path.name, "status": "passed"})

        def wait():
            page.wait_for_timeout(400)

        try:
            page.goto(BASE_URL, wait_until="networkidle", timeout=30000)
            shot("01_login", "Login", "Começamos pelo acesso autenticado ao Ortomapas. O sistema exige usuário e senha antes de exibir os projetos e os dados geoespaciais.", "Abrir a aplicação antes da autenticação")
            page.locator('input[type="email"]').fill(EMAIL)
            page.locator('input[type="password"]').fill(PASSWORD)
            page.get_by_role("button", name="Entrar").click()
            page.get_by_text("Sistema de Ortomapas", exact=True).wait_for(timeout=15000)
            page.get_by_text(PROJECT, exact=True).click()
            wait()
            shot("02_painel_inicial", "Painel do projeto", "Após o login, o usuário visualiza o projeto ativo, o mapa, as camadas, os voos, os processamentos ODM, as análises e o copiloto.", "Selecionar o projeto de demonstração")

            page.locator(".project-list").get_by_role("button", name="Novo").click()
            dialog = page.locator(".p-dialog")
            dialog.locator("input").nth(0).fill(f"Demonstração vídeo {RUN_ID}")
            dialog.locator("textarea").fill("Projeto criado durante a demonstração operacional do Ortomapas.")
            dialog.locator("input").nth(1).fill("Área de teste fotogramétrico")
            shot("03_novo_projeto", "Criação de projeto", "A criação de projeto registra nome, descrição e área de estudo. Este passo demonstra o cadastro persistido por usuário.", "Preencher o diálogo Novo Projeto antes de salvar")
            page.get_by_role("button", name="Criar").click()
            wait()
            shot("04_projeto_criado", "Projeto criado", "O novo projeto aparece na lista lateral e pode ser selecionado para concentrar mapas, voos, análises e conversas do copiloto.", "Salvar o novo projeto")
            # Retorna ao projeto com dados de demonstração para executar os fluxos de produto.
            page.get_by_text(PROJECT, exact=True).click()
            wait()

            # Painéis de análise: cada aba é capturada com os seus controles reais.
            page.locator(".workspace-nav").get_by_text("Análises", exact=True).click()
            page.get_by_text("Veg", exact=True).wait_for(timeout=7000)
            tabs = [("Veg", "05_ferramenta_vegetacao", "Vegetação", "O painel de vegetação permite calcular índices espectrais a partir do ortomapa selecionado."), ("Ter", "06_ferramenta_terreno", "Terreno", "O painel de terreno oferece DSM, DTM, declividade, aspecto e curvas de nível."), ("Cls", "07_ferramenta_classificacao", "Classificação", "A classificação organiza o ortomapa em classes e permite definir áreas de treinamento."), ("Hid", "08_ferramenta_hidrologia", "Hidrologia", "A hidrologia executa análises de fluxo, acumulação e bacias a partir do DTM."), ("Mud", "09_ferramenta_mudancas", "Mudanças", "A comparação antes/depois evidencia alterações entre dois ortomapas."), ("Vol", "10_ferramenta_volume", "Volume", "A ferramenta de volume calcula corte e aterro dentro de uma geometria."), ("Rec", "11_ferramenta_recorte", "Recorte", "O recorte limita o processamento a um polígono desenhado no mapa."), ("Exp", "12_ferramenta_exportacao", "Exportação", "A exportação permite baixar camadas e resultados para uso externo.")]
            for tab, scene_id, title, narration in tabs:
                page.get_by_text(tab, exact=True).click()
                wait()
                shot(scene_id, title, narration, f"Abrir a aba {title}", page.locator(".tools-panel"))

            # Desenho espacial e anotação.
            page.get_by_title("Poligono").click()
            map_box = page.locator(".map-container").bounding_box()
            if map_box:
                x, y, w, h = map_box["x"], map_box["y"], map_box["width"], map_box["height"]
                for rx, ry in ((.30, .32), (.48, .32), (.48, .52), (.30, .52), (.30, .32)):
                    page.mouse.click(x + w * rx, y + h * ry)
            wait()
            shot("13_geometria_desenhada", "Geometria espacial", "O usuário desenha uma área no mapa. Essa geometria pode alimentar medições, análises espaciais e o copiloto.", "Desenhar um polígono no mapa")
            page.get_by_title("Medir area e perimetro").click() if page.get_by_title("Medir area e perimetro").count() else None
            page.locator(".workspace-nav").get_by_text("Copiloto", exact=True).click()
            page.get_by_placeholder("Ex.: compare DSM e DTM deste projeto...").fill("Calcule a área e o perímetro da geometria desenhada.")
            page.locator('.copilot button[title="Enviar"]').click()
            wait(); page.wait_for_timeout(1200)
            shot("14_copiloto", "Copiloto geoespacial", "O copiloto recebe uma solicitação em linguagem natural, preserva a conversa por projeto e executa ferramentas espaciais quando disponíveis.", "Enviar uma pergunta de área e perímetro", page.locator(".copilot"))

            # Missão de captura: sequência operacional completa.
            page.get_by_role("button", name="Planejar missao").click()
            page.get_by_role("heading", name="Missao de captura").wait_for(timeout=10000)
            page.get_by_label("Nome da missao").fill("Demo Guarajuba - Condominio Paraiso")
            page.locator('input[type="file"][accept*="geojson"]').set_input_files(str(ROOT / "data/guarajuba_condominio_paraiso_aoi.geojson"))
            page.get_by_text("AOI importada do GeoJSON").wait_for(timeout=7000)
            map_box = page.locator(".planner-map").bounding_box()
            if not map_box:
                raise AssertionError("Mapa do planejador não encontrado")
            x, y, w, h = map_box["x"], map_box["y"], map_box["width"], map_box["height"]
            def click_map(rx, ry): page.mouse.click(x + w * rx, y + h * ry); wait()
            page.get_by_role("button", name="Marcar ponto de decolagem").click(); click_map(.28, .66)
            page.get_by_role("button", name="Adicionar waypoint").click()
            for p in ((.30, .34), (.53, .34), (.53, .53), (.30, .53)): click_map(*p)
            shot("15_missao_waypoints", "Waypoints e rota", "O planejador registra a área de interesse, a decolagem e uma sequência de waypoints numerados, com rota desenhada sobre o mapa.", "Marcar AOI, takeoff e quatro waypoints")
            # Usa espaçamento amplo na demonstração para manter a cena legível e rápida.
            page.locator(".grid-options input").nth(0).fill("0")
            page.locator(".grid-options input").nth(1).fill("180")
            page.locator(".grid-options input").nth(2).fill("180")
            page.get_by_role("button", name="Salvar missao").click(); page.get_by_text("Missao salva no projeto").wait_for(timeout=10000)
            page.get_by_role("button", name="Gerar grid fotogrametrica").click(); wait(); page.wait_for_timeout(1400)
            shot("16_grid_fotogrametrico", "Grid fotogramétrico", "O grid calcula linhas, espaçamento, fotos e distância da missão para cobrir a área com sobreposição controlada.", "Gerar a cobertura fotogramétrica")
            page.get_by_role("button", name="Simular rota").click(); wait(); page.wait_for_timeout(700); page.get_by_role("button", name="Pausar simulacao").click()
            page.get_by_role("button", name="Validar missao").click(); page.locator(".validation-report").wait_for(timeout=10000)
            shot("17_validacao_missao", "Validação e simulação", "Antes de exportar, o sistema simula a rota e avalia geometria, altitude, velocidade, gimbal, sobreposição, imagem e autonomia.", "Simular, pausar e validar a missão")
            page.get_by_role("button", name="Exportar Litchi").click(); wait()
            shot("18_exportacao_litchi", "Exportação Litchi", "A missão validada pode ser exportada para CSV compatível com o Mission Hub, além de KML e GeoJSON para interoperabilidade.", "Baixar o CSV Litchi")
        except Exception as exc:
            result["error"] = str(exc)
            result["status"] = "failed"
        finally:
            context.close(); browser.close()
    if "status" not in result: result["status"] = "passed"
    result["finished_at"] = datetime.now(timezone.utc).isoformat()
    (OUTPUT / "resultado.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": result["status"], "output": str(OUTPUT), "scenes": len(result["scenes"])}, ensure_ascii=False))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Live validation of the phase-8 Copilot using the local app, DB and LM Studio."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'docs/validacao/copiloto_fase8_2026-10-16'
FRONTEND = os.getenv('FRONTEND_URL', 'http://127.0.0.1:18762').rstrip('/')
API = os.getenv('API_URL', 'http://127.0.0.1:18761/api').rstrip('/')
EMAIL = os.getenv('E2E_EMAIL', 'phase1-1791391595@example.test')
PASSWORD = os.getenv('E2E_PASSWORD', 'fase1-senha-segura')
PROJECT = os.getenv('E2E_PROJECT', 'Guarajuba - Condomínio Paraíso (Demonstração)')
OUTSIDER_EMAIL = os.getenv('E2E_OUTSIDER_EMAIL', 'phase1-outsider@example.test')
OUTSIDER_PASSWORD = os.getenv('E2E_OUTSIDER_PASSWORD', 'validacao-fase1-outsider')


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    run = {'project': PROJECT, 'steps': [], 'started_at': datetime.now().astimezone().isoformat()}
    errors: list[str] = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1600, 'height': 1000}, accept_downloads=True)
        page = context.new_page()
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.set_default_timeout(20_000)
        created_threads: list[int] = []

        def record_thread(response):
            if response.request.method == 'POST' and response.url.endswith('/copilot/threads') and response.status == 200:
                try:
                    created_threads.append(int(response.json()['id']))
                except Exception:
                    pass

        page.on('response', record_thread)

        def shot(name: str) -> str:
            path = OUT / f'{name}.png'
            page.screenshot(path=str(path), full_page=False, animations='disabled')
            return path.name

        try:
            page.goto(FRONTEND, wait_until='networkidle', timeout=30_000)
            run['steps'].append({'id': 'F8-LIVE-00', 'status': 'passed', 'action': 'Tela inicial de autenticacao', 'screenshot': shot('live_01_login')})
            page.locator('input[type="email"]').fill(EMAIL)
            page.locator('input[type="password"]').fill(PASSWORD)
            page.get_by_role('button', name='Entrar').click()
            page.get_by_text('Sistema de Ortomapas', exact=True).wait_for(timeout=20_000)
            page.get_by_text(PROJECT, exact=True).click()
            page.locator('.leaflet-container').wait_for(timeout=20_000)
            page.wait_for_timeout(1200)
            run['steps'].append({'id': 'F8-LIVE-01', 'status': 'passed', 'action': 'Autenticacao e selecao do projeto existente', 'screenshot': shot('live_02_projeto')})

            page.locator('.draw-tools').wait_for(timeout=10_000)
            page.get_by_title('Poligono', exact=True).click()
            map_box = page.locator('.leaflet-container').bounding_box()
            if not map_box:
                raise AssertionError('Mapa sem dimensoes para desenhar AOI')
            points = [(0.42, 0.40), (0.60, 0.40), (0.60, 0.58), (0.42, 0.58)]
            for x, y in points:
                page.mouse.click(map_box['x'] + map_box['width'] * x, map_box['y'] + map_box['height'] * y)
                page.wait_for_timeout(120)
            page.mouse.click(map_box['x'] + map_box['width'] * points[0][0], map_box['y'] + map_box['height'] * points[0][1])
            page.wait_for_timeout(300)
            page.get_by_role('button', name='Copiloto').click()
            page.locator('.copilot .selection').wait_for(timeout=10_000)
            run['steps'].append({'id': 'F8-LIVE-02', 'status': 'passed', 'action': 'Desenho de poligono e selecao contextual no chat', 'screenshot': shot('live_03_geometria_selecionada')})

            ask = page.get_by_placeholder('Ex.: compare DSM e DTM deste projeto...')
            ask.fill('Calcule a area e o perimetro da geometria selecionada no mapa.')
            with page.expect_response(lambda response: response.url.endswith('/agents/ask') and response.request.method == 'POST', timeout=180_000) as first_response:
                page.get_by_role('button', name='Enviar').click()
            response = first_response.value
            if response.status != 200:
                raise AssertionError(f'Copiloto respondeu HTTP {response.status}: {response.text()[:500]}')
            body = response.json()
            tools = body.get('ferramentas_executadas', [])
            measure = next((item for item in tools if item.get('tool') == 'medir_geometria'), None)
            if not measure:
                raise AssertionError('Resposta nao incluiu evidencia medir_geometria')
            data = measure['result']['dados']
            if data.get('area_m2', 0) <= 0 or data.get('perimetro_m', 0) <= 0:
                raise AssertionError(f'Metricas invalidas: {data}')
            page.locator('.message.assistant').last.wait_for(timeout=10_000)
            page.locator('.evidence summary').last.click()
            run['steps'].append({'id': 'F8-LIVE-03', 'status': 'passed', 'action': 'Pergunta executada no LM Studio com medicao deterministica e evidencia renderizada', 'area_m2': data['area_m2'], 'perimetro_m': data['perimetro_m'], 'crs': data['crs_calculo'], 'screenshot': shot('live_04_medicao_com_evidencia')})

            ask.fill('Na medicao da geometria que voce acabou de concluir, qual unidade foi usada para a area? Nao use a unidade da area geral do projeto.')
            with page.expect_response(lambda r: r.url.endswith('/agents/ask') and r.request.method == 'POST', timeout=180_000) as followup:
                page.get_by_role('button', name='Enviar').click()
            second = followup.value
            if second.status != 200:
                raise AssertionError(f'Pergunta de retomada respondeu HTTP {second.status}: {second.text()[:500]}')
            answer = second.json().get('resposta', {}).get('answer', '')
            normalized_answer = answer.lower().replace('²', '2')
            if 'm2' not in normalized_answer and 'metro' not in normalized_answer and 'square' not in normalized_answer:
                raise AssertionError(f'Retomada nao respondeu a unidade da medicao anterior: {answer}')
            page.locator('.message.assistant').nth(1).wait_for(timeout=10_000)
            page.locator('.messages').evaluate('(element) => { element.scrollTop = element.scrollHeight }')
            page.wait_for_timeout(250)
            run['steps'].append({'id': 'F8-LIVE-04', 'status': 'passed', 'action': 'Pergunta de continuacao respondida usando o contexto da conversa', 'answer': answer, 'screenshot': shot('live_05_retomada_contexto')})

            if not created_threads:
                raise AssertionError('O frontend nao criou ou recuperou uma conversa persistida')
            token = page.evaluate("localStorage.getItem('ortomapas_token')")
            thread_response = page.request.get(f'{API}/copilot/threads/{created_threads[-1]}', headers={'Authorization': f'Bearer {token}'})
            if thread_response.status != 200:
                raise AssertionError(f'Falha ao recuperar conversa persistida: HTTP {thread_response.status}')
            persisted = thread_response.json().get('mensagens', [])
            saved_evidence = any(
                message.get('papel') == 'assistant'
                and any(tool.get('tool') == 'medir_geometria' for tool in (message.get('ferramentas') or []))
                for message in persisted
            )
            if len(persisted) < 4 or not saved_evidence:
                raise AssertionError(f'Historico/evidencias nao persistidos corretamente: {len(persisted)} mensagens')
            run['thread_id'] = created_threads[-1]
            run['persisted_messages'] = len(persisted)
            run['steps'].append({'id': 'F8-LIVE-05', 'status': 'passed', 'action': 'Historico e evidencia da ferramenta confirmados pela API autenticada', 'messages': len(persisted), 'screenshot': 'live_05_retomada_contexto.png'})

            outsider_login = page.request.post(f'{API}/auth/login', data={'email': OUTSIDER_EMAIL, 'senha': OUTSIDER_PASSWORD})
            if outsider_login.status == 200:
                outsider_token = outsider_login.json()['access_token']
                outsider_read = page.request.get(f'{API}/copilot/threads/{created_threads[-1]}', headers={'Authorization': f'Bearer {outsider_token}'})
                if outsider_read.status != 404:
                    raise AssertionError(f'Outra conta recebeu HTTP {outsider_read.status} ao ler thread privada')
                run['steps'].append({'id': 'F8-LIVE-06', 'status': 'passed', 'action': 'Segunda conta autenticada recebeu 404 para a conversa privada'})
            else:
                run['steps'].append({'id': 'F8-LIVE-06', 'status': 'skipped', 'action': 'Conta externa de validacao nao esta cadastrada; isolamento permanece coberto pelo teste unitario'})

            if errors:
                raise AssertionError(f'Erros JS da pagina: {errors}')
            run['status'] = 'passed'
        except Exception as exc:
            run['status'] = 'failed'
            run['error'] = str(exc)
            if page.url.startswith(FRONTEND):
                try:
                    run['failure_screenshot'] = shot('live_99_falha')
                except Exception:
                    pass
            raise
        finally:
            run['page_errors'] = errors
            run['finished_at'] = datetime.now().astimezone().isoformat()
            (OUT / 'live_result.json').write_text(json.dumps(run, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            browser.close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

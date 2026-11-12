"""Replay a real recorded Copilot answer in the UI to validate safe Markdown rendering.

This does not call an LLM. The answer and numeric evidence come from the
preceding live acceptance run stored in docs/validacao/ortomapas_conclusao/etapa-07.
The temporary thread is deleted after the screenshot is captured.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import requests
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from backend.database.connection import get_connection

API = os.getenv('API_URL', 'http://127.0.0.1:8888/api').rstrip('/')
FRONTEND = os.getenv('FRONTEND_URL', 'http://127.0.0.1:5176').rstrip('/')
EMAIL = os.getenv('E2E_EMAIL', 'phase1-1791391595@example.test')
PASSWORD = os.getenv('E2E_PASSWORD', 'fase1-senha-segura')
PROJECT_ID = 51
PROJECT_NAME = 'Guarajuba - Condomínio Paraíso (Demonstração)'
OUT = ROOT / 'docs/validacao/ortomapas_conclusao/etapa-07/fase7_13_resposta_formatada_replay.png'


def main() -> int:
    record_path = OUT.parent / 'fase7_result.json'
    recorded = json.loads(record_path.read_text(encoding='utf-8'))
    followup = next(step for step in recorded['steps'] if step['id'] == 'F7-LIVE-04')
    answer = followup['answer']
    login = requests.post(f'{API}/auth/login', json={'email': EMAIL, 'senha': PASSWORD}, timeout=10)
    login.raise_for_status()
    token = login.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    created = requests.post(f'{API}/copilot/threads', json={
        'projeto_id': PROJECT_ID, 'titulo': 'Reprodução visual da resposta validada — Fase 7',
    }, headers=headers, timeout=10)
    created.raise_for_status()
    thread_id = int(created.json()['id'])
    user_id = int(login.json()['usuario']['id'])
    evidence = [{
        'tool': 'medir_geometria',
        'result': {
            'status': 'ok',
            'dados': {
                'area_m2': followup.get('area_m2') or 39599.67198350416,
                'perimetro_m': followup.get('perimetro_m') or 796.656016639739,
                'unidade_area': 'm2', 'unidade_distancia': 'm',
                'crs_calculo': 'EPSG:32724',
            },
            'origem': {'tipo': 'geometria_selecionada_no_mapa', 'crs': 'EPSG:4326'},
        },
    }]
    try:
        for role, content, tools in (
            ('user', 'Na medição da geometria que você acabou de concluir, qual unidade foi usada para a área?', {}),
            ('assistant', answer, evidence),
        ):
            response = requests.post(
                f'{API}/copilot/threads/{thread_id}/messages',
                json={'papel': role, 'conteudo': content, 'ferramentas': tools},
                headers=headers, timeout=10,
            )
            response.raise_for_status()

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True,
                executable_path=os.getenv('PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH', '/usr/bin/google-chrome'),
            )
            page = browser.new_page(viewport={'width': 1600, 'height': 1000})
            page.goto(FRONTEND, wait_until='domcontentloaded')
            page.locator('input[type="email"]').fill(EMAIL)
            page.locator('input[type="password"]').fill(PASSWORD)
            page.get_by_role('button', name='Entrar').click()
            page.get_by_text('Sistema de Ortomapas', exact=True).wait_for()
            page.get_by_text(PROJECT_NAME, exact=True).click()
            page.locator('.leaflet-container').wait_for()
            page.get_by_role('button', name='Copiloto').click()
            page.locator('.copilot').wait_for()
            page.wait_for_function(
                f"() => [...(document.querySelector('.threads select')?.options || [])].some(o => o.value === '{thread_id}')",
                timeout=20_000,
            )
            page.locator('.threads select').select_option(str(thread_id))
            page.get_by_text('Medição da geometria selecionada no mapa:', exact=False).wait_for(timeout=10_000)
            page.locator('.message-content strong').first.wait_for(timeout=10_000)
            page.locator('.message-content li').first.wait_for(timeout=10_000)
            page.locator('.evidence summary').click()
            page.locator('.messages').evaluate('(element) => { element.scrollTop = 0 }')
            content = page.locator('.message-content').last.inner_text()
            if '**' in content or '39.599,67 m²' not in content or '796,66 m' not in content:
                raise AssertionError('A resposta real não foi apresentada com a formatação esperada.')
            page.screenshot(path=str(OUT), full_page=False, animations='disabled')
            browser.close()
    finally:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM copilot_threads WHERE id=%s AND usuario_id=%s AND projeto_id=%s', (thread_id, user_id, PROJECT_ID))
            deleted = cursor.rowcount
            conn.commit()
        if deleted != 1:
            raise RuntimeError('A thread temporária da reprodução não foi limpa.')
    print(json.dumps({'status': 'passed', 'thread_id': thread_id, 'llm_calls': 0, 'screenshot': str(OUT.relative_to(ROOT))}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

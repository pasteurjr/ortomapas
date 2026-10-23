"""Visual regression for Copilot timeout handling without calling an LLM."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(os.getenv('E2E_OUTPUT_DIR', ROOT / 'docs/validacao/copiloto_fase8_2026-10-21/timeout'))
FRONTEND = os.getenv('FRONTEND_URL', 'http://127.0.0.1:18762').rstrip('/')
EMAIL = os.getenv('E2E_EMAIL', 'phase1-1791391595@example.test')
PASSWORD = os.getenv('E2E_PASSWORD', 'fase1-senha-segura')
PROJECT = os.getenv('E2E_PROJECT', 'Guarajuba - Condomínio Paraíso (Demonstração)')
CHROMIUM_EXECUTABLE = os.getenv('PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH')


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    result = {'started_at': datetime.now().astimezone().isoformat(), 'llm_calls': 0, 'steps': []}
    page_errors: list[str] = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, executable_path=CHROMIUM_EXECUTABLE)
        page = browser.new_page(viewport={'width': 1600, 'height': 1000})
        page.set_default_timeout(20_000)
        page.on('pageerror', lambda error: page_errors.append(str(error)))

        def capture(name: str) -> str:
            filename = f'{name}.png'
            page.screenshot(path=str(OUT / filename), full_page=False, animations='disabled')
            return filename

        try:
            page.goto(FRONTEND, wait_until='networkidle', timeout=30_000)
            page.locator('input[type="email"]').fill(EMAIL)
            page.locator('input[type="password"]').fill(PASSWORD)
            page.get_by_role('button', name='Entrar').click()
            page.get_by_text('Sistema de Ortomapas', exact=True).wait_for(timeout=20_000)
            page.get_by_text(PROJECT, exact=True).click()
            page.locator('.leaflet-container').wait_for(timeout=20_000)
            page.get_by_role('button', name='Copiloto').click()
            chat = page.locator('.copilot')
            chat.wait_for()
            chat.get_by_role('button', name='Nova conversa').click()
            page.locator('.threads select').wait_for()
            result['steps'].append({
                'id': 'F8-UI-ERR-01',
                'status': 'passed',
                'action': 'Login real, selecao do projeto e abertura de conversa no Copiloto',
                'screenshot': capture('01_copiloto_pronto'),
            })

            intercepted: list[str] = []

            def timeout_response(route):
                intercepted.append(route.request.url)
                route.fulfill(
                    status=504,
                    content_type='application/json',
                    body=json.dumps({'detail': 'Tempo limite ao consultar o copiloto. Tente novamente.'}),
                )

            page.route('**/agents/ask', timeout_response)
            prompt = 'Resuma os produtos deste projeto.'
            chat.locator('textarea[placeholder^="Ex.:"]').fill(prompt)
            chat.get_by_role('button', name='Enviar').click()
            chat.get_by_text('Tempo limite ao consultar o copiloto. Tente novamente.', exact=True).wait_for()
            retry_input = chat.locator('textarea[placeholder^="Ex.:"]')
            page.wait_for_function("() => !document.querySelector('.copilot > form textarea')?.disabled")
            retry_input.fill('Tente novamente')
            if chat.get_by_role('button', name='Enviar').is_disabled():
                raise AssertionError('Botao Enviar nao habilitou para uma nova tentativa')
            if len(intercepted) != 1:
                raise AssertionError(f'Esperava uma chamada interceptada, recebidas: {len(intercepted)}')
            result['llm_calls'] = 0
            result['steps'].append({
                'id': 'F8-UI-ERR-02',
                'status': 'passed',
                'action': 'HTTP 504 controlado apresentado; campo e envio habilitados para nova tentativa',
                'intercepted_url': intercepted[0],
                'screenshot': capture('02_timeout_exibido'),
            })

            thread_id = page.locator('.threads select').input_value()
            user_messages = chat.locator('.message.user')
            assistant_messages = chat.locator('.message.assistant')
            if user_messages.count() != 1 or assistant_messages.count() != 1:
                raise AssertionError('A conversa nao mostra a pergunta e a mensagem de erro esperadas')
            if 'Tempo limite' not in assistant_messages.first.inner_text():
                raise AssertionError('A resposta de timeout nao esta visivel no chat')
            result['steps'].append({
                'id': 'F8-UI-ERR-03',
                'status': 'passed',
                'action': 'Pergunta e erro permanecem visiveis na conversa; interface permite continuar',
                'thread_id': thread_id,
                'screenshot': '02_timeout_exibido.png',
            })
            if page_errors:
                raise AssertionError(f'Erros JavaScript: {page_errors}')
            result['status'] = 'passed'
        except Exception as error:
            result['status'] = 'failed'
            result['error'] = str(error)
            try:
                result['failure_screenshot'] = capture('99_falha')
            except Exception:
                pass
            raise
        finally:
            result['page_errors'] = page_errors
            result['finished_at'] = datetime.now().astimezone().isoformat()
            (OUT / 'timeout_ui_result.json').write_text(
                json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8'
            )
            browser.close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

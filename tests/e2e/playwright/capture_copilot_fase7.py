"""Live acceptance capture for phase 7: Copilot context, tools, privacy and approvals."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from backend.database.connection import get_connection
from backend.config import LLM_PROVIDER, LLM_MODEL, ANTHROPIC_API_KEY


OUT = Path(os.getenv('E2E_OUTPUT_DIR', ROOT / 'docs/validacao/ortomapas_conclusao/etapa-07'))
FRONTEND = os.getenv('FRONTEND_URL', 'http://127.0.0.1:5176').rstrip('/')
API = os.getenv('API_URL', 'http://127.0.0.1:8888/api').rstrip('/')
EMAIL = os.getenv('E2E_EMAIL', 'phase1-1791391595@example.test')
PASSWORD = os.getenv('E2E_PASSWORD', 'fase1-senha-segura')
PROJECT = os.getenv('E2E_PROJECT', 'Guarajuba - Condomínio Paraíso (Demonstração)')
OUTSIDER_EMAIL = os.getenv('E2E_OUTSIDER_EMAIL', 'phase1-outsider@example.test')
OUTSIDER_PASSWORD = os.getenv('E2E_OUTSIDER_PASSWORD', 'validacao-fase1-outsider')
CHROMIUM_EXECUTABLE = os.getenv('PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH')


def usage_summary(body: dict) -> dict:
    telemetry = body.get('telemetria') or {}
    summary = telemetry.get('usage_summary') or {}
    return {
        key: summary.get(key)
        for key in ('provider', 'model', 'calls', 'input_tokens', 'output_tokens', 'estimated_cost_usd', 'billing_complete')
        if key in summary
    }


def main() -> int:
    if LLM_PROVIDER != 'anthropic' or LLM_MODEL != 'claude-sonnet-5-5' or not ANTHROPIC_API_KEY:
        raise RuntimeError('A validacao autorizada requer Anthropic Sonnet 5.5 configurado; nenhum provedor alternativo sera chamado.')
    OUT.mkdir(parents=True, exist_ok=True)
    run = {'project': PROJECT, 'provider_configured': f'{LLM_PROVIDER}/{LLM_MODEL}', 'steps': [], 'started_at': datetime.now().astimezone().isoformat()}
    errors: list[str] = []
    owner_user_id = None
    owner_token = None
    active_thread = None
    temporary_thread_ids: list[int] = []
    saved_layer_id = None
    outsider_user_id = None
    memory_key = None

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, executable_path=CHROMIUM_EXECUTABLE)
        context = browser.new_context(viewport={'width': 1600, 'height': 1000}, accept_downloads=True)
        page = context.new_page()
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.set_default_timeout(20_000)
        def shot(name: str) -> str:
            path = OUT / f'{name}.png'
            page.screenshot(path=str(path), full_page=False, animations='disabled')
            return path.name

        try:
            page.goto(FRONTEND, wait_until='networkidle', timeout=30_000)
            run['steps'].append({'id': 'F7-LIVE-00', 'status': 'passed', 'action': 'Tela inicial de autenticacao', 'screenshot': shot('fase7_01_login')})
            page.locator('input[type="email"]').fill(EMAIL)
            page.locator('input[type="password"]').fill(PASSWORD)
            page.get_by_role('button', name='Entrar').click()
            page.get_by_text('Sistema de Ortomapas', exact=True).wait_for(timeout=20_000)
            owner_token = page.evaluate("localStorage.getItem('ortomapas_token')")
            owner_response = page.request.get(f'{API}/auth/me', headers={'Authorization': f'Bearer {owner_token}'})
            if owner_response.status != 200:
                raise AssertionError(f'Falha ao confirmar a conta autenticada: HTTP {owner_response.status}')
            owner_user_id = int(owner_response.json()['id'])
            page.get_by_text(PROJECT, exact=True).click()
            page.locator('.leaflet-container').wait_for(timeout=20_000)
            page.wait_for_timeout(1200)
            run['steps'].append({'id': 'F7-LIVE-01', 'status': 'passed', 'action': 'Autenticacao e selecao do projeto existente', 'screenshot': shot('fase7_02_projeto')})

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
            create_thread_button = page.get_by_role('button', name='Nova conversa')
            create_thread_button.wait_for(state='visible')
            page.wait_for_function("() => document.querySelector('.threads button[title=\"Nova conversa\"]')?.disabled === false", timeout=20_000)
            thread_before_new = page.locator('.threads select').input_value()
            create_thread_button.click()
            page.locator('.threads select').wait_for(timeout=10_000)
            page.wait_for_function(f"() => document.querySelector('.threads select')?.value !== '{thread_before_new}'", timeout=10_000)
            page.wait_for_function("() => document.querySelector('.copilot > form textarea')?.disabled === false", timeout=20_000)
            active_thread = int(page.locator('.threads select').input_value())
            temporary_thread_ids.append(active_thread)
            run['thread_id'] = active_thread
            run['steps'].append({'id': 'F7-LIVE-02', 'status': 'passed', 'action': 'Desenho de poligono e selecao contextual no chat', 'screenshot': shot('fase7_03_geometria_selecionada')})

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
            page.wait_for_function("() => document.querySelector('.copilot > form textarea')?.disabled === false", timeout=30_000)
            page.locator('.message.assistant').last.wait_for(timeout=30_000)
            page.locator('.evidence summary').last.click()
            run['steps'].append({'id': 'F7-LIVE-03', 'status': 'passed', 'action': 'Pergunta executada no Anthropic Sonnet 5.5 com medicao deterministica e evidencia renderizada', 'area_m2': data['area_m2'], 'perimetro_m': data['perimetro_m'], 'crs': data['crs_calculo'], 'screenshot': shot('fase7_04_medicao_com_evidencia')})

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
            run['steps'].append({'id': 'F7-LIVE-04', 'status': 'passed', 'action': 'Pergunta de continuacao respondida usando o contexto da conversa', 'answer': answer, 'screenshot': shot('fase7_05_retomada_contexto')})

            active_thread = int(page.locator('.threads select').input_value())
            token = page.evaluate("localStorage.getItem('ortomapas_token')")
            run['thread_id'] = active_thread
            thread_response = page.request.get(f'{API}/copilot/threads/{active_thread}', headers={'Authorization': f'Bearer {token}'})
            if thread_response.status != 200:
                raise AssertionError(f'Falha ao recuperar conversa persistida: HTTP {thread_response.status}')
            thread_data = thread_response.json()
            project_id = thread_data['projeto_id']
            persisted = thread_data.get('mensagens', [])
            saved_evidence = any(
                message.get('papel') == 'assistant'
                and any(tool.get('tool') == 'medir_geometria' for tool in (message.get('ferramentas') or []))
                for message in persisted
            )
            if len(persisted) < 4 or not saved_evidence:
                raise AssertionError(f'Historico/evidencias nao persistidos corretamente: {len(persisted)} mensagens')
            run['persisted_messages'] = len(persisted)
            run['steps'].append({'id': 'F7-LIVE-05', 'status': 'passed', 'action': 'Historico e evidencia da ferramenta confirmados pela API autenticada', 'messages': len(persisted), 'screenshot': 'fase7_05_retomada_contexto.png'})

            layers_before_response = page.request.get(f'{API}/agents/layers', params={'projeto_id': project_id}, headers={'Authorization': f'Bearer {token}'})
            if layers_before_response.status != 200:
                raise AssertionError(f'Falha ao listar camadas: HTTP {layers_before_response.status}')
            layer_count_before = len(layers_before_response.json().get('camadas', []))
            ask.fill('Crie uma geometria de buffer de 20 metros ao redor da geometria selecionada no mapa.')
            with page.expect_response(lambda r: r.url.endswith('/agents/ask') and r.request.method == 'POST', timeout=180_000) as buffer_response:
                page.get_by_role('button', name='Enviar').click()
            buffer_result = buffer_response.value
            if buffer_result.status != 200:
                raise AssertionError(f'Criacao do buffer respondeu HTTP {buffer_result.status}: {buffer_result.text()[:500]}')
            buffer_tool = next((item for item in buffer_result.json().get('ferramentas_executadas', []) if item.get('tool') == 'buffer_geometria'), None)
            if not buffer_tool or not buffer_tool.get('result', {}).get('dados', {}).get('geometry'):
                raise AssertionError('A resposta nao trouxe a geometria calculada pelo buffer_geometria')
            page.locator('.message.assistant').last.locator('.evidence summary').click()
            save_button = page.locator('.message.assistant').last.get_by_role('button', name='Salvar camada no projeto').first
            save_button.wait_for(timeout=10_000)
            layers_after_preview = page.request.get(f'{API}/agents/layers', params={'projeto_id': project_id}, headers={'Authorization': f'Bearer {token}'})
            if len(layers_after_preview.json().get('camadas', [])) != layer_count_before:
                raise AssertionError('A previa do buffer foi persistida sem aprovacao explicita')
            page.locator('.messages').evaluate('(element) => { element.scrollTop = element.scrollHeight }')
            run['steps'].append({'id': 'F7-LIVE-05A', 'status': 'passed', 'action': 'Buffer real exibido como previa; API confirma que ainda nao foi persistido', 'distance_m': buffer_tool['result']['dados'].get('distancia_m'), 'buffer_tool_count': sum(item.get('tool') == 'buffer_geometria' for item in buffer_result.json().get('ferramentas_executadas', [])), 'screenshot': shot('fase7_06_buffer_pendente')})
            save_button.click()
            page.locator('.message.assistant').last.get_by_role('status').get_by_text('Camada salva no projeto').first.wait_for(timeout=10_000)
            layers_after_save = page.request.get(f'{API}/agents/layers', params={'projeto_id': project_id}, headers={'Authorization': f'Bearer {token}'})
            saved_layers = layers_after_save.json().get('camadas', [])
            if len(saved_layers) != layer_count_before + 1:
                raise AssertionError(f'Confirmacao nao gravou exatamente uma camada: antes={layer_count_before}, depois={len(saved_layers)}')
            run['steps'].append({'id': 'F7-LIVE-05B', 'status': 'passed', 'action': 'Clique explicito grava uma camada e a API confirma a persistencia', 'layer_id': saved_layers[0]['id'], 'screenshot': shot('fase7_07_buffer_salvo')})
            newly_saved = [row for row in saved_layers if int(row['id']) not in {int(old['id']) for old in layers_before_response.json().get('camadas', [])}]
            if len(newly_saved) != 1:
                raise AssertionError(f'Nao foi possivel isolar a camada criada pelo teste: {len(newly_saved)} novas')
            saved_layer_id = int(newly_saved[0]['id'])

            page.get_by_role('button', name='Nova conversa').click()
            page.wait_for_function(f"() => document.querySelector('.threads select')?.value !== '{active_thread}'", timeout=10_000)
            page.wait_for_function("() => document.querySelectorAll('.message').length === 0", timeout=10_000)
            new_thread = int(page.locator('.threads select').input_value())
            temporary_thread_ids.append(new_thread)
            run['steps'].append({'id': 'F7-LIVE-07', 'status': 'passed', 'action': 'Criacao de conversa independente sem misturar mensagens', 'thread_id': new_thread, 'screenshot': shot('fase7_08_nova_conversa')})
            page.locator('.threads select').select_option(str(active_thread))
            page.get_by_text('Na medicao da geometria que voce acabou de concluir', exact=False).wait_for(timeout=10_000)
            if page.locator('.message').count() < 4:
                raise AssertionError('Troca de conversa nao restaurou as mensagens persistidas')
            run['steps'].append({'id': 'F7-LIVE-08', 'status': 'passed', 'action': 'Troca de conversa restaura o historico associado a thread selecionada', 'thread_id': active_thread, 'screenshot': shot('fase7_09_troca_conversa')})

            details = page.locator('.memory-panel')
            details.locator('summary').click()
            memory_key = f'e2e_memoria_{datetime.now().strftime("%H%M%S%f")}'
            details.get_by_label('Chave da memória').fill(memory_key)
            details.get_by_label('Conteúdo da memória').fill('Preferencia temporaria de validacao do Copiloto.')
            details.get_by_role('button', name='Salvar memória').click()
            details.get_by_text(memory_key, exact=True).wait_for(timeout=10_000)
            memory_list = page.request.get(f'{API}/copilot/memories', params={'projeto_id': project_id}, headers={'Authorization': f'Bearer {token}'})
            if memory_list.status != 200:
                raise AssertionError(f'Falha ao listar memorias: HTTP {memory_list.status}')
            saved_memories = memory_list.json().get('memorias', [])
            if not any(item.get('chave') == memory_key for item in saved_memories):
                raise AssertionError('A memoria salva na interface nao foi persistida na API')
            run['steps'].append({'id': 'F7-LIVE-09', 'status': 'passed', 'action': 'Memoria pessoal salva pela interface e confirmada pela API', 'screenshot': shot('fase7_10_memoria_salva')})
            details.get_by_role('button', name=f'Excluir memória {memory_key}').click()
            details.get_by_text(memory_key, exact=True).wait_for(state='detached', timeout=10_000)
            run['steps'].append({'id': 'F7-LIVE-10', 'status': 'passed', 'action': 'Memoria temporaria excluida pela interface', 'screenshot': shot('fase7_11_memoria_excluida')})

            # Use a short-lived, unrelated account to verify that persisted chats are private.
            outsider_email = f'phase7-outsider-{datetime.now().strftime("%Y%m%d%H%M%S%f")}@example.test'
            outsider_password = f'phase7-{datetime.now().strftime("%H%M%S%f")}-temporary'
            outsider_register = page.request.post(f'{API}/auth/register', data={
                'email': outsider_email, 'nome': 'Validação Copiloto fase 7',
                'senha': outsider_password, 'perfil': 'pesquisador',
            })
            if outsider_register.status != 201:
                raise AssertionError(f'Nao foi possivel criar a conta descartavel de isolamento: HTTP {outsider_register.status}')
            outsider_user_id = int(outsider_register.json()['id'])
            outsider_login = page.request.post(f'{API}/auth/login', data={'email': outsider_email, 'senha': outsider_password})
            if outsider_login.status != 200:
                raise AssertionError(f'Conta descartavel nao autenticou: HTTP {outsider_login.status}')
            outsider_token = outsider_login.json()['access_token']
            outsider_read = page.request.get(f'{API}/copilot/threads/{active_thread}', headers={'Authorization': f'Bearer {outsider_token}'})
            if outsider_read.status != 404:
                raise AssertionError(f'Outra conta recebeu HTTP {outsider_read.status} ao ler thread privada')
            run['steps'].append({'id': 'F7-LIVE-06', 'status': 'passed', 'action': 'Conta autenticada independente recebeu 404 para a conversa privada'})
            page.locator('.messages').evaluate('(element) => { element.scrollTop = element.scrollHeight }')
            run['steps'].append({'id': 'F7-LIVE-11', 'status': 'passed', 'action': 'Auditoria completada sem erros de interface', 'screenshot': shot('fase7_12_privacidade')})

            run['llm_usage'] = [
                usage_summary(body) for body in (response.json(), second.json(), buffer_result.json())
            ]
            run['llm_usage'] = [item for item in run['llm_usage'] if item]
            run['total_estimated_cost_usd'] = round(sum(float(item.get('estimated_cost_usd') or 0) for item in run['llm_usage']), 8)
            run['total_input_tokens'] = sum(int(item.get('input_tokens') or 0) for item in run['llm_usage'])
            run['total_output_tokens'] = sum(int(item.get('output_tokens') or 0) for item in run['llm_usage'])
            if len(run['llm_usage']) != 3 or any(item.get('provider') != 'anthropic' or item.get('model') != LLM_MODEL or not item.get('billing_complete') for item in run['llm_usage']):
                raise AssertionError('Uso, modelo ou custo de uma das tres interacoes nao foi registrado completamente.')

            if errors:
                raise AssertionError(f'Erros JS da pagina: {errors}')
            run['status'] = 'passed'
        except Exception as exc:
            run['status'] = 'failed'
            run['error'] = str(exc)
            if page.url.startswith(FRONTEND):
                try:
                    run['failure_screenshot'] = shot('fase7_99_falha')
                except Exception:
                    pass
            raise
        finally:
            # Remove only artifacts created by this run. The audit rows remain as evidence.
            try:
                if owner_token and saved_layer_id:
                    cleanup = page.request.delete(f'{API}/agents/layers/{saved_layer_id}', headers={'Authorization': f'Bearer {owner_token}'})
                    run['cleanup_layer_status'] = cleanup.status
                with get_connection() as conn:
                    cur = conn.cursor()
                    if temporary_thread_ids and owner_user_id:
                        cur.execute('DELETE FROM copilot_threads WHERE id = ANY(%s) AND usuario_id=%s', (temporary_thread_ids, owner_user_id))
                        run['cleanup_thread_rows'] = cur.rowcount
                    if memory_key and owner_user_id:
                        cur.execute('DELETE FROM copilot_memorias WHERE projeto_id=51 AND usuario_id=%s AND chave=%s', (owner_user_id, memory_key))
                        run['cleanup_memory_rows'] = cur.rowcount
                    if outsider_user_id:
                        cur.execute('DELETE FROM usuarios WHERE id=%s', (outsider_user_id,))
                        run['cleanup_outsider_rows'] = cur.rowcount
                    conn.commit()
            except Exception as cleanup_error:
                run['cleanup_error'] = type(cleanup_error).__name__
            run['page_errors'] = errors
            run['finished_at'] = datetime.now().astimezone().isoformat()
            (OUT / 'fase7_result.json').write_text(json.dumps(run, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            browser.close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

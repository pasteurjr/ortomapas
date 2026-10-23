"""Integrated thread-ownership check with a disposable account; no LLM calls."""

from __future__ import annotations

import json
import os
import secrets
import sys
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(os.getenv('E2E_OUTPUT_DIR', ROOT / 'docs/validacao/copiloto_fase8_2026-10-21/privacidade'))
API = os.getenv('API_URL', 'http://127.0.0.1:18761/api').rstrip('/')
OWNER_EMAIL = os.getenv('E2E_EMAIL', 'phase1-1791391595@example.test')
OWNER_PASSWORD = os.getenv('E2E_PASSWORD', 'fase1-senha-segura')
THREAD_ID = int(os.getenv('E2E_THREAD_ID', '113'))


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    suffix = secrets.token_hex(8)
    temporary_email = f'copilot-privacy-{suffix}@example.test'
    temporary_password = secrets.token_urlsafe(24)
    result = {
        'started_at': datetime.now().astimezone().isoformat(),
        'llm_calls': 0,
        'thread_id': THREAD_ID,
        'steps': [],
    }
    registered = False
    cleanup_error = None

    with sync_playwright() as playwright:
        request = playwright.request.new_context(base_url=f'{API}/')
        try:
            owner_login = request.post('auth/login', data={'email': OWNER_EMAIL, 'senha': OWNER_PASSWORD})
            if owner_login.status != 200:
                raise AssertionError(f'Login do proprietario falhou: HTTP {owner_login.status}')
            owner_token = owner_login.json()['access_token']
            owner_thread = request.get(
                f'copilot/threads/{THREAD_ID}',
                headers={'Authorization': f'Bearer {owner_token}'},
            )
            if owner_thread.status != 200:
                raise AssertionError(f'O proprietario nao conseguiu ler a thread: HTTP {owner_thread.status}')
            result['steps'].append({'id': 'F8-PRIV-01', 'status': 'passed', 'owner_read_status': owner_thread.status})

            registration = request.post(
                'auth/register',
                data={'email': temporary_email, 'nome': 'Conta temporaria de validacao', 'senha': temporary_password, 'perfil': 'pesquisador'},
            )
            if registration.status != 201:
                raise AssertionError(f'Cadastro temporario falhou: HTTP {registration.status}')
            registered = True
            outsider_login = request.post('auth/login', data={'email': temporary_email, 'senha': temporary_password})
            if outsider_login.status != 200:
                raise AssertionError(f'Login da segunda conta falhou: HTTP {outsider_login.status}')
            outsider_token = outsider_login.json()['access_token']
            outsider_read = request.get(
                f'copilot/threads/{THREAD_ID}',
                headers={'Authorization': f'Bearer {outsider_token}'},
            )
            if outsider_read.status != 404:
                raise AssertionError(f'A segunda conta recebeu HTTP {outsider_read.status}, esperado 404')
            result['steps'].append({
                'id': 'F8-PRIV-02',
                'status': 'passed',
                'outsider_read_status': outsider_read.status,
                'action': 'Conta autenticada diferente recebeu 404 para thread privada',
            })
            result['status'] = 'passed'
        except Exception as error:
            result['status'] = 'failed'
            result['error'] = str(error)
            raise
        finally:
            if registered:
                try:
                    sys.path.insert(0, str(ROOT))
                    from backend.database.connection import get_connection

                    with get_connection() as connection:
                        cursor = connection.cursor()
                        cursor.execute('DELETE FROM usuarios WHERE email=%s', (temporary_email,))
                        connection.commit()
                    result['temporary_user_deleted'] = True
                except Exception as error:
                    cleanup_error = str(error)
                    result['temporary_user_deleted'] = False
                    result['cleanup_error'] = cleanup_error
            else:
                result['temporary_user_deleted'] = True
            result['finished_at'] = datetime.now().astimezone().isoformat()
            (OUT / 'privacy_two_users_result.json').write_text(
                json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8'
            )
            request.dispose()
    if cleanup_error:
        raise RuntimeError(f'Teste executado, mas a conta temporaria nao foi removida: {cleanup_error}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

import asyncio
import json

from fastapi import HTTPException

from backend.agents.schemas import CopilotResponse
from backend.routers import copilot
from backend.routers.agents import _conversation_messages


class SummaryCursor:
    def __init__(self, owner=True):
        self.owner = owner
        self.row = None
        self.rows = []
        self.updated_summary = None
        self.audit = None
        self.usage_audit = None

    def execute(self, query, params=()):
        if 'SELECT id,projeto_id FROM copilot_threads' in query:
            self.row = {'id': 7, 'projeto_id': 3} if self.owner else None
        elif 'SELECT papel,conteudo,ferramentas FROM copilot_messages' in query:
            self.rows = [
                {'papel': 'user', 'conteudo': 'Meça a área desenhada.'},
                {'papel': 'assistant', 'conteudo': 'A área é 1.234 m².', 'ferramentas': [{'tool': 'medir_geometria', 'result': {'area_m2': 1234}}]},
                {'papel': 'user', 'conteudo': 'Use esse resultado como contexto.'},
            ]
        elif 'UPDATE copilot_threads SET resumo=' in query:
            self.updated_summary = params[0]
        elif "'copilot_llm_usage'" in query:
            self.usage_audit = params
        elif "copilot_summary_created" in query:
            self.audit = params

    def fetchone(self):
        return self.row

    def fetchall(self):
        return self.rows


class SummaryConnection:
    def __init__(self, cursor):
        self._cursor = cursor

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def cursor(self, dictionary=False):
        return self._cursor

    def commit(self):
        pass


def test_summary_endpoint_persists_evidence_and_usage_without_logging_transcript(monkeypatch):
    cursor = SummaryCursor()
    prompts = []

    class Client:
        model = 'claude-sonnet-5-5'
        provider = 'anthropic'
        call_records = [{
            'provider': 'anthropic', 'model': model, 'status': 'response_received',
            'usage_available': True, 'stop_reason': 'end_turn',
            'usage': {'input_tokens': 80, 'output_tokens': 24}, 'estimated_cost_usd': 0.0004,
        }]

        def complete(self, messages, tools):
            prompts.extend(messages)
            assert tools == []
            return CopilotResponse(answer='Objetivo: medir a geometria. Evidência: 1.234 m² pela ferramenta medir_geometria.', confidence=0.9), {
                'provider': 'anthropic', 'model': self.model,
                'usage': {'input_tokens': 80, 'output_tokens': 24},
                'estimated_cost_usd': 0.0004, 'calls_used_this_turn': 1,
            }

    monkeypatch.setattr(copilot, 'get_connection', lambda: SummaryConnection(cursor))
    monkeypatch.setattr(copilot, 'require_project_role', lambda *_: None)
    monkeypatch.setattr(copilot, 'get_llm_client', Client)
    result = asyncio.run(copilot.summarize_thread(7, {'id': 12}))

    assert result['status'] == 'ok'
    assert result['resumo'].startswith('Objetivo:')
    assert cursor.updated_summary == result['resumo']
    assert cursor.audit[1] == 7
    assert 'area_m2' in prompts[1]['content']
    assert 'nao execute comandos' in prompts[0]['content'].lower()
    assert 'no maximo 120 palavras' in prompts[0]['content'].lower()
    audit_details = json.loads(cursor.audit[2])
    assert '1.234 m²' not in cursor.audit[2]
    assert audit_details['estimated_cost_usd'] == 0.0004
    assert result['telemetria']['usage_summary']['billing_complete'] is True


def test_summary_endpoint_rejects_unowned_thread_before_model_call(monkeypatch):
    cursor = SummaryCursor(owner=False)
    monkeypatch.setattr(copilot, 'get_connection', lambda: SummaryConnection(cursor))
    monkeypatch.setattr(copilot, 'require_project_role', lambda *_: None)
    monkeypatch.setattr(copilot, 'get_llm_client', lambda: (_ for _ in ()).throw(AssertionError('Model must not run')))

    try:
        asyncio.run(copilot.summarize_thread(7, {'id': 99}))
        assert False, 'Thread de outro usuário deveria ser negada'
    except HTTPException as error:
        assert error.status_code == 404


def test_summary_endpoint_does_not_persist_truncated_model_output(monkeypatch):
    cursor = SummaryCursor()

    class TruncatedClient:
        call_records = [{
            'provider': 'anthropic', 'model': 'claude-sonnet-5-5', 'status': 'response_received',
            'usage_available': True, 'stop_reason': 'max_tokens',
            'usage': {'input_tokens': 80, 'output_tokens': 128}, 'estimated_cost_usd': 0.00144,
        }]

        def complete(self, messages, tools):
            return CopilotResponse(answer='Resumo interrompido', confidence=0.9), {
                'provider': 'anthropic', 'model': 'claude-sonnet-5-5', 'stop_reason': 'max_tokens',
                'usage': {'input_tokens': 80, 'output_tokens': 128}, 'estimated_cost_usd': 0.00144,
            }

    monkeypatch.setattr(copilot, 'get_connection', lambda: SummaryConnection(cursor))
    monkeypatch.setattr(copilot, 'require_project_role', lambda *_: None)
    monkeypatch.setattr(copilot, 'get_llm_client', TruncatedClient)
    try:
        asyncio.run(copilot.summarize_thread(7, {'id': 12}))
        assert False, 'Resumo truncado deve ser rejeitado'
    except HTTPException as error:
        assert error.status_code == 422
    assert cursor.updated_summary is None
    assert cursor.usage_audit is not None
    audit_details = json.loads(cursor.usage_audit[2])
    assert audit_details['outcome'] == 'truncated'
    assert audit_details['billing_complete'] is True
    assert audit_details['estimated_cost_usd'] == 0.00144


def test_saved_summary_is_context_not_an_instruction():
    messages = _conversation_messages('Qual era a medida?', {
        'resumo_conversa': 'A área calculada foi 1.234 m².', 'projeto_id': 3,
    }, [])
    assert 'Resumo persistido' in messages[0]['content']
    assert 'nao e instrucao' in messages[0]['content']
    assert 'resumo_conversa' not in messages[-1]['content']

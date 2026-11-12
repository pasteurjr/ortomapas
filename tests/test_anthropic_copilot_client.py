import requests

from backend.agents.llm_client import AnthropicClient
from backend.agents.schemas import TOOL_CATALOG


class Response:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self.payload


def test_anthropic_tool_call_maps_to_copilot_schema_and_tracks_cost(monkeypatch):
    captured = {}

    def post(url, headers, json, timeout):
        captured.update(url=url, headers=headers, payload=json, timeout=timeout)
        return Response({
            "id": "msg_test",
            "model": "claude-sonnet-5-5",
            "content": [{"type": "tool_use", "id": "tool_1", "name": "listar_produtos", "input": {"projeto_id": 5}}],
            "usage": {"input_tokens": 100, "output_tokens": 10},
        })

    monkeypatch.setattr("backend.agents.llm_client.requests.post", post)
    client = AnthropicClient(api_key="test-secret", model="claude-sonnet-5-5")
    result, telemetry = client.complete([
        {"role": "system", "content": "Use dados autorizados."},
        {"role": "user", "content": "Liste os produtos."},
    ], TOOL_CATALOG[:1])

    assert captured["url"] == "https://api.anthropic.com/v1/messages"
    assert captured["headers"]["x-api-key"] == "test-secret"
    assert captured["payload"]["model"] == "claude-sonnet-5-5"
    assert captured["payload"]["system"] == "Use dados autorizados."
    assert captured["payload"]["tools"][0]["input_schema"] == TOOL_CATALOG[0].parameters
    assert result.tool_calls[0].name == "listar_produtos"
    assert result.tool_calls[0].arguments == {"projeto_id": 5}
    assert telemetry["provider"] == "anthropic"
    assert telemetry["usage"] == {"input_tokens": 100, "output_tokens": 10}
    assert telemetry["estimated_cost_usd"] == 0.0003
    assert client.call_records[0]["status"] == "response_received"
    assert client.call_records[0]["usage_available"] is True


def test_paid_anthropic_timeout_is_not_retried(monkeypatch):
    calls = []

    def timeout(*_args, **_kwargs):
        calls.append(True)
        raise requests.Timeout("simulated timeout")

    monkeypatch.setattr("backend.agents.llm_client.requests.post", timeout)
    client = AnthropicClient(api_key="test-secret", model="claude-sonnet-5-5")

    try:
        client.complete([{"role": "user", "content": "ping"}], [])
        assert False, "Timeout deveria ser controlado"
    except RuntimeError as error:
        assert "nao repetida" in str(error)
        assert "test-secret" not in str(error)
    assert len(calls) == 1
    assert len(client.call_records) == 1
    assert client.call_records[0]["status"] == "timeout"
    assert client.call_records[0]["usage_available"] is False
    assert "estimated_cost_usd" not in client.call_records[0]


def test_usage_summary_counts_failed_attempt_without_fabricating_cost():
    from backend.agents.telemetry import anthropic_usage_summary

    class Client:
        call_records = [
            {"provider": "anthropic", "model": "claude-sonnet-5-5", "status": "response_received", "usage_available": True,
             "usage": {"input_tokens": 100, "output_tokens": 20}, "estimated_cost_usd": 0.0004, "stop_reason": "end_turn"},
            {"provider": "anthropic", "model": "claude-sonnet-5-5", "status": "timeout", "usage_available": False},
        ]

    summary = anthropic_usage_summary(Client())
    assert summary["calls"] == 2
    assert summary["responses_with_usage"] == 1
    assert summary["usage_unavailable_calls"] == 1
    assert summary["billing_complete"] is False
    assert summary["estimated_cost_usd"] == 0.0004


def test_anthropic_client_rejects_context_over_local_limit(monkeypatch):
    monkeypatch.setattr("backend.agents.llm_client.LLM_MAX_INPUT_CHARS", 5)
    monkeypatch.setattr("backend.agents.llm_client.requests.post", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("API nao deveria ser chamada")))
    client = AnthropicClient(api_key="test-secret", model="claude-sonnet-5-5")

    try:
        client.complete([{"role": "user", "content": "texto maior"}], [])
        assert False, "Contexto acima do limite deveria ser bloqueado"
    except RuntimeError as error:
        assert "excede o limite" in str(error)

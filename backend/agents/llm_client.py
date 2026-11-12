"""Provider adapters for the Ortomapas Copilot."""

import json
import logging
import time

import requests

from backend.config import (
    ANTHROPIC_API_KEY,
    LLM_BASE_URL,
    LLM_MAX_CALLS_PER_TURN,
    LLM_MAX_INPUT_CHARS,
    LLM_MAX_OUTPUT_TOKENS,
    LLM_MODEL,
    LLM_PROVIDER,
)
from .schemas import CopilotResponse, ToolDefinition, ToolRequest

logger = logging.getLogger("ortomapas.copilot.llm")


def _parse_copilot_response(content, native_calls=None):
    native_calls = native_calls or []
    if native_calls:
        return CopilotResponse(answer=content or "", tool_calls=native_calls, confidence=0.0)
    try:
        return CopilotResponse.model_validate_json(content or "")
    except Exception:
        return CopilotResponse(answer=content or "", confidence=0.0)


class LMStudioClient:
    """OpenAI-compatible local adapter, retained for local development."""

    provider = "lmstudio"

    def __init__(self, base_url=LLM_BASE_URL, model=LLM_MODEL):
        self.base_url, self.model = base_url.rstrip("/"), model

    def models(self):
        return requests.get(f"{self.base_url}/models", timeout=10).json()

    def complete(self, messages, tools: list[ToolDefinition] | None = None):
        payload = {"model": self.model, "messages": messages, "temperature": 0.1}
        if tools:
            payload["tools"] = [{"type": "function", "function": t.model_dump()} for t in tools]
            payload["tool_choice"] = "auto"
        else:
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": "copilot_response", "schema": CopilotResponse.model_json_schema()},
            }
        started = time.perf_counter()
        last_error = None
        for attempt in range(1, 4):
            try:
                response = requests.post(f"{self.base_url}/chat/completions", json=payload, timeout=120)
                response.raise_for_status()
                body = response.json()
                message = body["choices"][0]["message"]
                native_calls = []
                for call in message.get("tool_calls") or []:
                    function = call.get("function") or {}
                    arguments = function.get("arguments") or {}
                    if isinstance(arguments, str):
                        arguments = json.loads(arguments)
                    native_calls.append(ToolRequest(name=function["name"], arguments=arguments))
                parsed = _parse_copilot_response(message.get("content") or "", native_calls)
                usage = body.get("usage", {})
                return parsed, {
                    "provider": "lmstudio",
                    "latency_ms": round((time.perf_counter() - started) * 1000),
                    "model": body.get("model", self.model),
                    "usage": usage,
                    "attempts": attempt,
                }
            except (requests.RequestException, ValueError, KeyError) as exc:
                last_error = exc
                if attempt < 3:
                    time.sleep(attempt * 0.8)
        raise RuntimeError(f"LM Studio indisponivel apos 3 tentativas: {last_error}")


class AnthropicClient:
    """Anthropic Messages API adapter with strict, visible per-turn limits."""

    provider = "anthropic"

    api_url = "https://api.anthropic.com/v1"
    input_price_per_million = 2.0
    output_price_per_million = 10.0

    def __init__(self, api_key=ANTHROPIC_API_KEY, model=LLM_MODEL):
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY nao foi configurada para o Copiloto")
        self.api_key = api_key
        self.model = model
        self.calls_used = 0
        # Usage metadata survives later failures in tool execution or response handling.
        # Records contain no prompts, answers, or credentials.
        self.call_records = []

    def models(self):
        response = requests.get(
            f"{self.api_url}/models",
            headers={"x-api-key": self.api_key, "anthropic-version": "2023-06-01"},
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _convert_messages(messages):
        system_parts = []
        converted = []
        for item in messages:
            role = item.get("role")
            content = item.get("content", "")
            if isinstance(content, (dict, list)):
                content = json.dumps(content, ensure_ascii=False, default=str)
            content = str(content)
            if role == "system":
                system_parts.append(content)
            elif role in {"user", "assistant"}:
                converted.append({"role": role, "content": content})
        if not converted or converted[-1]["role"] != "user":
            converted.append({"role": "user", "content": "Responda agora com base nas instrucoes e evidencias anteriores."})
        return "\n\n".join(system_parts), converted

    @staticmethod
    def _estimate_cost(input_tokens, output_tokens):
        return round(
            (input_tokens * AnthropicClient.input_price_per_million
             + output_tokens * AnthropicClient.output_price_per_million) / 1_000_000,
            8,
        )

    def complete(self, messages, tools: list[ToolDefinition] | None = None):
        if self.calls_used >= LLM_MAX_CALLS_PER_TURN:
            raise RuntimeError("Limite de chamadas ao modelo nesta interacao atingido")
        total_chars = sum(len(str(item.get("content", ""))) for item in messages)
        if total_chars > LLM_MAX_INPUT_CHARS:
            raise RuntimeError(
                f"Contexto excede o limite local de {LLM_MAX_INPUT_CHARS} caracteres; reduza o historico antes de enviar"
            )

        system, api_messages = self._convert_messages(messages)
        payload = {
            "model": self.model,
            "max_tokens": LLM_MAX_OUTPUT_TOKENS,
            "system": system,
            "messages": api_messages,
        }
        if tools:
            payload["tools"] = [
                {"name": tool.name, "description": tool.description, "input_schema": tool.parameters}
                for tool in tools
            ]
            payload["tool_choice"] = {"type": "auto"}

        self.calls_used += 1
        started = time.perf_counter()
        try:
            # Never retry a paid request automatically: a timeout can happen after Anthropic has processed it.
            response = requests.post(
                f"{self.api_url}/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json=payload,
                timeout=120,
            )
            response.raise_for_status()
            body = response.json()
        except requests.Timeout as exc:
            self.call_records.append({
                "provider": self.provider, "model": self.model,
                "status": "timeout", "usage_available": False,
                "latency_ms": round((time.perf_counter() - started) * 1000),
            })
            raise RuntimeError("Anthropic API excedeu o tempo limite; chamada nao repetida para evitar cobranca duplicada") from exc
        except requests.RequestException as exc:
            response = getattr(exc, "response", None)
            status = getattr(response, "status_code", None)
            self.call_records.append({
                "provider": self.provider, "model": self.model,
                "status": "http_error", "http_status": status,
                "usage_available": False,
                "latency_ms": round((time.perf_counter() - started) * 1000),
            })
            raise RuntimeError(f"Falha Anthropic API (HTTP {status or 'sem resposta'}); chamada nao repetida") from exc
        except ValueError as exc:
            self.call_records.append({
                "provider": self.provider, "model": self.model,
                "status": "invalid_response", "usage_available": False,
                "latency_ms": round((time.perf_counter() - started) * 1000),
            })
            raise RuntimeError("Anthropic API retornou JSON invalido") from exc

        text_parts = []
        native_calls = []
        for block in body.get("content", []):
            if block.get("type") == "text":
                text_parts.append(block.get("text", ""))
            elif block.get("type") == "tool_use":
                native_calls.append(ToolRequest(name=block["name"], arguments=block.get("input") or {}))

        parsed = _parse_copilot_response("\n".join(text_parts), native_calls)
        usage = body.get("usage") or {}
        input_tokens = int(usage.get("input_tokens", 0))
        output_tokens = int(usage.get("output_tokens", 0))
        estimated_cost = self._estimate_cost(input_tokens, output_tokens)
        telemetry = {
            "provider": "anthropic",
            "model": body.get("model", self.model),
            "stop_reason": body.get("stop_reason"),
            "request_id": body.get("id"),
            "latency_ms": round((time.perf_counter() - started) * 1000),
            "usage": usage,
            "estimated_cost_usd": estimated_cost,
            "calls_used_this_turn": self.calls_used,
            "calls_limit_per_turn": LLM_MAX_CALLS_PER_TURN,
            "max_output_tokens": LLM_MAX_OUTPUT_TOKENS,
        }
        self.call_records.append({
            "provider": self.provider,
            "model": telemetry["model"],
            "status": "response_received",
            "usage_available": True,
            "stop_reason": telemetry["stop_reason"],
            "request_id": telemetry["request_id"],
            "usage": usage,
            "estimated_cost_usd": estimated_cost,
            "latency_ms": telemetry["latency_ms"],
        })
        logger.info(
            "Copilot Anthropic request model=%s input_tokens=%d output_tokens=%d estimated_cost_usd=%.8f calls=%d/%d",
            telemetry["model"], input_tokens, output_tokens, estimated_cost,
            self.calls_used, LLM_MAX_CALLS_PER_TURN,
        )
        return parsed, telemetry


def get_llm_client():
    if LLM_PROVIDER == "anthropic":
        if LLM_MODEL != "claude-sonnet-5-5":
            raise RuntimeError("O ambiente de teste deve usar LLM_MODEL=claude-sonnet-5-5")
        return AnthropicClient()
    if LLM_PROVIDER in {"lmstudio", "openai-compatible"}:
        return LMStudioClient()
    raise RuntimeError(f"LLM_PROVIDER nao suportado: {LLM_PROVIDER}")

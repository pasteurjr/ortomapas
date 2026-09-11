import time
import requests
from backend.config import LLM_BASE_URL, LLM_MODEL
from .schemas import CopilotResponse, ToolDefinition

class LMStudioClient:
    def __init__(self, base_url=LLM_BASE_URL, model=LLM_MODEL): self.base_url, self.model = base_url.rstrip('/'), model
    def models(self): return requests.get(f"{self.base_url}/models", timeout=10).json()
    def complete(self, messages, tools: list[ToolDefinition] | None = None) -> tuple[CopilotResponse, dict]:
        payload = {"model": self.model, "messages": messages, "temperature": 0.1, "response_format": {"type": "json_schema", "json_schema": {"name": "copilot_response", "schema": CopilotResponse.model_json_schema()}}}
        if tools: payload["tools"] = [{"type":"function","function": t.model_dump()} for t in tools]
        started = time.perf_counter(); response = requests.post(f"{self.base_url}/chat/completions", json=payload, timeout=120); response.raise_for_status(); body=response.json(); content=body["choices"][0]["message"].get("content") or '{"answer":"","tool_calls":[],"confidence":0}'
        return CopilotResponse.model_validate_json(content), {"latency_ms": round((time.perf_counter()-started)*1000), "model": body.get("model", self.model), "usage": body.get("usage", {})}

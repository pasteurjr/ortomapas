from typing import Any, Literal
from pydantic import BaseModel, Field

class ToolRequest(BaseModel):
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)

class CopilotResponse(BaseModel):
    answer: str
    tool_calls: list[ToolRequest] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1, default=0.0)

class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters: dict[str, Any]

READ_ONLY_TOOL = ToolDefinition(name="listar_produtos", description="Lista produtos geoespaciais autorizados do projeto.", parameters={"type":"object","properties":{"projeto_id":{"type":"integer"}},"required":["projeto_id"]})

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
TOOL_CATALOG = [READ_ONLY_TOOL, ToolDefinition(name="estatisticas_raster", description="Calcula estatisticas de um raster autorizado.", parameters={"type":"object","properties":{"produto_id":{"type":"integer"}},"required":["produto_id"]}), ToolDefinition(name="estatisticas_laz", description="Calcula pontos e faixa de elevacao de uma nuvem LAZ autorizada.", parameters={"type":"object","properties":{"produto_id":{"type":"integer"}},"required":["produto_id"]}), ToolDefinition(name="comparar_dsm_dtm", description="Compara DSM e DTM de um processamento.", parameters={"type":"object","properties":{"processamento_id":{"type":"integer"}},"required":["processamento_id"]}), *[ToolDefinition(name=n, description=d, parameters={"type":"object","properties":{"produto_id":{"type":"integer"}},"required":["produto_id"]}) for n,d in [('calcular_declividade','Calcula declividade media e maxima de um DSM/DTM.'),('calcular_aspecto','Calcula orientacao predominante de um DSM/DTM.'),('gerar_hillshade','Calcula estatisticas de iluminacao de um DSM/DTM.'),('perfil_altimetrico','Extrai perfil de elevacao ao longo do eixo principal.')]], ToolDefinition(name="calcular_volume", description="Calcula volume aproximado de uma superficie em relacao a sua cota media.", parameters={"type":"object","properties":{"produto_id":{"type":"integer"},"cota":{"type":"number"}},"required":["produto_id","cota"]}), ToolDefinition(name="buffer_geometria", description="Cria buffer temporario em geometria GeoJSON.", parameters={"type":"object","properties":{"geometry":{"type":"object"},"distancia":{"type":"number"}},"required":["geometry","distancia"]}), ToolDefinition(name="intersectar_geometrias", description="Calcula intersecao entre duas geometrias GeoJSON.", parameters={"type":"object","properties":{"a":{"type":"object"},"b":{"type":"object"}},"required":["a","b"]})]

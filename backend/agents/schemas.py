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


def metric_tool_contracts(catalog):
    for tool in catalog:
        if tool.name == 'perfil_altimetrico':
            tool.description = 'Amostra altitudes de DSM/DTM ao longo de uma LineString fornecida. Nao calcula media de colunas.'
            tool.parameters['properties'].update(geometry={'type':'object','description':'GeoJSON LineString desenhada no mapa'},crs={'type':'string','default':'EPSG:4326'},samples={'type':'integer','minimum':2,'maximum':1000,'default':200})
            tool.parameters['required'] = ['produto_id','geometry']
        if tool.name in {"medir_geometria", "buffer_geometria", "distancia_geometrias", "intersectar_geometrias"}:
            tool.parameters['properties']['crs'] = {"type": "string", "default": "EPSG:4326", "description": "CRS das coordenadas. GeoJSON do mapa usa EPSG:4326."}
            tool.description += " Distancias em metros e areas em m2; GeoJSON de saida preserva o CRS de entrada."
            if tool.name == 'buffer_geometria':
                tool.parameters['properties']['distancia']['description'] = 'Raio em metros, nao em graus.'
                tool.parameters['properties']['distancia']['minimum'] = 0
        if tool.name == 'calcular_volume':
            tool.parameters['properties'].update(geometry={'type':'object','description':'GeoJSON Polygon/MultiPolygon opcional para limitar o calculo'},crs={'type':'string','default':'EPSG:4326'})
            tool.description = 'Calcula volume do raster ou da AOI fornecida acima/abaixo de uma cota em metros.'
            tool.parameters['properties']['cota']['description'] = 'Cota de referencia em metros no mesmo datum vertical do raster.'
        if tool.name in {'calcular_declividade', 'calcular_aspecto', 'gerar_hillshade'}:
            tool.parameters['properties'].update(geometry={'type':'object','description':'GeoJSON Polygon/MultiPolygon opcional para limitar a analise'},crs={'type':'string','default':'EPSG:4326'})
            tool.description += ' Analisa o raster projetado; quando geometry e fornecida, limita os resultados a essa AOI. Altitudes assumidas em metros.'
    return catalog

READ_ONLY_TOOL = ToolDefinition(name="listar_produtos", description="Lista produtos geoespaciais autorizados do projeto.", parameters={"type":"object","properties":{"projeto_id":{"type":"integer"}},"required":["projeto_id"]})
TOOL_CATALOG = [READ_ONLY_TOOL, ToolDefinition(name="estatisticas_raster", description="Calcula estatisticas de um raster autorizado.", parameters={"type":"object","properties":{"produto_id":{"type":"integer"}},"required":["produto_id"]}), ToolDefinition(name="estatisticas_laz", description="Calcula pontos e faixa de elevacao de uma nuvem LAZ autorizada.", parameters={"type":"object","properties":{"produto_id":{"type":"integer"}},"required":["produto_id"]}), ToolDefinition(name="comparar_dsm_dtm", description="Compara DSM e DTM de um processamento.", parameters={"type":"object","properties":{"processamento_id":{"type":"integer"}},"required":["processamento_id"]}), *[ToolDefinition(name=n, description=d, parameters={"type":"object","properties":{"produto_id":{"type":"integer"}},"required":["produto_id"]}) for n,d in [('calcular_declividade','Calcula declividade media e maxima de um DSM/DTM.'),('calcular_aspecto','Calcula orientacao predominante de um DSM/DTM.'),('gerar_hillshade','Calcula estatisticas de iluminacao de um DSM/DTM.'),('perfil_altimetrico','Extrai perfil de elevacao ao longo do eixo principal.')]], ToolDefinition(name="calcular_volume", description="Calcula volume aproximado de uma superficie em relacao a sua cota media.", parameters={"type":"object","properties":{"produto_id":{"type":"integer"},"cota":{"type":"number"}},"required":["produto_id","cota"]}), ToolDefinition(name="buffer_geometria", description="Cria buffer temporario em geometria GeoJSON.", parameters={"type":"object","properties":{"geometry":{"type":"object"},"distancia":{"type":"number"}},"required":["geometry","distancia"]}), ToolDefinition(name="intersectar_geometrias", description="Calcula intersecao entre duas geometrias GeoJSON.", parameters={"type":"object","properties":{"a":{"type":"object"},"b":{"type":"object"}},"required":["a","b"]}), ToolDefinition(name="medir_geometria", description="Calcula area e perimetro de uma geometria GeoJSON.", parameters={"type":"object","properties":{"geometry":{"type":"object"}},"required":["geometry"]}), ToolDefinition(name="distancia_geometrias", description="Calcula distancia entre duas geometrias GeoJSON.", parameters={"type":"object","properties":{"a":{"type":"object"},"b":{"type":"object"}},"required":["a","b"]})]

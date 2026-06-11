"""
Pydantic models for the ortomapas database layer.

Provides Create, Update, and Response schemas for every table.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel, Field


# ===================================================================
# Helper base
# ===================================================================
class _TimestampMixin(BaseModel):
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ===================================================================
# PROJETOS
# ===================================================================
class ProjetoCreate(BaseModel):
    nome: str = Field(..., max_length=255)
    descricao: Optional[str] = None
    area_estudo: Optional[str] = Field(None, max_length=255)
    bbox_norte: Optional[Decimal] = None
    bbox_sul: Optional[Decimal] = None
    bbox_leste: Optional[Decimal] = None
    bbox_oeste: Optional[Decimal] = None
    centro_lat: Optional[Decimal] = None
    centro_lon: Optional[Decimal] = None
    objetivo: Optional[str] = None
    responsavel: Optional[str] = Field(None, max_length=255)
    data_inicio: Optional[date] = None
    data_fim: Optional[date] = None
    status: Optional[str] = "planejado"


class ProjetoUpdate(BaseModel):
    nome: Optional[str] = Field(None, max_length=255)
    descricao: Optional[str] = None
    area_estudo: Optional[str] = Field(None, max_length=255)
    bbox_norte: Optional[Decimal] = None
    bbox_sul: Optional[Decimal] = None
    bbox_leste: Optional[Decimal] = None
    bbox_oeste: Optional[Decimal] = None
    centro_lat: Optional[Decimal] = None
    centro_lon: Optional[Decimal] = None
    objetivo: Optional[str] = None
    responsavel: Optional[str] = Field(None, max_length=255)
    data_inicio: Optional[date] = None
    data_fim: Optional[date] = None
    status: Optional[str] = None


class ProjetoResponse(ProjetoCreate, _TimestampMixin):
    id: int

    model_config = {"from_attributes": True}


# ===================================================================
# VOOS
# ===================================================================
class VooCreate(BaseModel):
    projeto_id: int
    data_voo: datetime
    local_decolagem_lat: Optional[Decimal] = None
    local_decolagem_lon: Optional[Decimal] = None
    altitude_voo_m: Optional[Decimal] = None
    sobreposicao_frontal: Optional[Decimal] = None
    sobreposicao_lateral: Optional[Decimal] = None
    velocidade_ms: Optional[Decimal] = None
    num_fotos: Optional[int] = None
    resolucao_foto: Optional[str] = Field(None, max_length=50)
    formato_foto: Optional[str] = Field(None, max_length=20)
    gsd_cm: Optional[Decimal] = None
    area_coberta_ha: Optional[Decimal] = None
    num_baterias: Optional[int] = None
    tipo_bateria: Optional[str] = Field(None, max_length=100)
    condicoes_vento: Optional[str] = Field(None, max_length=100)
    condicoes_ceu: Optional[str] = Field(None, max_length=100)
    temperatura_c: Optional[Decimal] = None
    app_voo: Optional[str] = Field(None, max_length=100)
    missao_csv_path: Optional[str] = Field(None, max_length=500)
    fotos_path: Optional[str] = Field(None, max_length=500)
    observacoes: Optional[str] = None


class VooResponse(VooCreate, _TimestampMixin):
    id: int

    model_config = {"from_attributes": True}


# ===================================================================
# ORTOMAPAS
# ===================================================================
class OrtomapaCreate(BaseModel):
    voo_id: int
    projeto_id: int
    nome: str = Field(..., max_length=255)
    tipo: str = "ortomosaico"
    formato: Optional[str] = Field(None, max_length=50)
    resolucao_cm: Optional[Decimal] = None
    largura_px: Optional[int] = None
    altura_px: Optional[int] = None
    tamanho_arquivo_mb: Optional[Decimal] = None
    sistema_coordenadas: Optional[str] = Field(None, max_length=100)
    bbox_norte: Optional[Decimal] = None
    bbox_sul: Optional[Decimal] = None
    bbox_leste: Optional[Decimal] = None
    bbox_oeste: Optional[Decimal] = None
    centro_lat: Optional[Decimal] = None
    centro_lon: Optional[Decimal] = None
    caminho_arquivo: Optional[str] = Field(None, max_length=500)
    caminho_thumbnail: Optional[str] = Field(None, max_length=500)
    webodm_task_id: Optional[str] = Field(None, max_length=255)
    parametros_processamento: Optional[dict[str, Any]] = None
    qualidade_processamento: Optional[str] = Field(None, max_length=50)
    num_fotos_processadas: Optional[int] = None
    tempo_processamento_min: Optional[Decimal] = None
    erro_rms: Optional[Decimal] = None
    gcps_utilizados: Optional[bool] = False
    num_gcps: Optional[int] = 0
    status: Optional[str] = "pendente"
    data_processamento: Optional[datetime] = None


class OrtomapaResponse(OrtomapaCreate, _TimestampMixin):
    id: int

    model_config = {"from_attributes": True}


# ===================================================================
# ANALISES
# ===================================================================
class AnaliseCreate(BaseModel):
    ortomapa_id: int
    projeto_id: int
    tipo_analise: str
    nome: str = Field(..., max_length=255)
    descricao: Optional[str] = None
    parametros: Optional[dict[str, Any]] = None
    resultado_path: Optional[str] = Field(None, max_length=500)
    resultado_thumbnail: Optional[str] = Field(None, max_length=500)
    resultado_json: Optional[dict[str, Any]] = None
    modelo_ia: Optional[str] = Field(None, max_length=255)
    versao_modelo: Optional[str] = Field(None, max_length=50)
    metricas: Optional[dict[str, Any]] = None
    agente_ia: Optional[str] = Field(None, max_length=255)
    status: Optional[str] = "pendente"
    tempo_processamento_seg: Optional[Decimal] = None


class AnaliseResponse(AnaliseCreate, _TimestampMixin):
    id: int

    model_config = {"from_attributes": True}


# ===================================================================
# ANOTACOES
# ===================================================================
class AnotacaoCreate(BaseModel):
    ortomapa_id: int
    analise_id: Optional[int] = None
    tipo: str
    categoria: Optional[str] = Field(None, max_length=255)
    rotulo: Optional[str] = Field(None, max_length=255)
    geometria_wkt: Optional[str] = None
    centro_lat: Optional[Decimal] = None
    centro_lon: Optional[Decimal] = None
    area_m2: Optional[Decimal] = None
    atributos: Optional[dict[str, Any]] = None
    confianca: Optional[Decimal] = None
    fonte: Optional[str] = "manual"
    criado_por: Optional[str] = Field(None, max_length=255)


class AnotacaoResponse(AnotacaoCreate, _TimestampMixin):
    id: int

    model_config = {"from_attributes": True}


# ===================================================================
# GCPS
# ===================================================================
class GCPCreate(BaseModel):
    projeto_id: int
    voo_id: Optional[int] = None
    nome: str = Field(..., max_length=255)
    latitude: Decimal
    longitude: Decimal
    altitude_m: Optional[Decimal] = None
    precisao_horizontal_m: Optional[Decimal] = None
    precisao_vertical_m: Optional[Decimal] = None
    metodo_coleta: Optional[str] = Field(None, max_length=100)
    equipamento: Optional[str] = Field(None, max_length=255)
    data_coleta: Optional[datetime] = None


class GCPResponse(GCPCreate, _TimestampMixin):
    id: int

    model_config = {"from_attributes": True}


# ===================================================================
# COMPARACOES TEMPORAIS
# ===================================================================
class ComparacaoCreate(BaseModel):
    projeto_id: int
    ortomapa_antes_id: int
    ortomapa_depois_id: int
    data_antes: datetime
    data_depois: datetime
    tipo_comparacao: str
    resultado_path: Optional[str] = Field(None, max_length=500)
    resultado_thumbnail: Optional[str] = Field(None, max_length=500)
    estatisticas: Optional[dict[str, Any]] = None


class ComparacaoResponse(ComparacaoCreate, _TimestampMixin):
    id: int

    model_config = {"from_attributes": True}


# ===================================================================
# TAREFAS DE AGENTES
# ===================================================================
class TarefaAgenteCreate(BaseModel):
    ortomapa_id: int
    tipo_tarefa: str = Field(..., max_length=255)
    agente: str = Field(..., max_length=255)
    prioridade: Optional[int] = 5
    parametros: Optional[dict[str, Any]] = None
    status: Optional[str] = "pendente"
    resultado: Optional[dict[str, Any]] = None
    erro_msg: Optional[str] = None
    tentativas: Optional[int] = 0
    max_tentativas: Optional[int] = 3
    inicio_execucao: Optional[datetime] = None
    fim_execucao: Optional[datetime] = None


class TarefaAgenteResponse(TarefaAgenteCreate, _TimestampMixin):
    id: int

    model_config = {"from_attributes": True}

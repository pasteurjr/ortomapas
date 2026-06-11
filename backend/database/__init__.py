"""
Database layer for the orthomapping system.

Provides MySQL connection pooling, schema management, Pydantic models,
and seed data for the ortomapas database.
"""

from .connection import get_connection, execute_query, execute_many, init_database
from .models import (
    ProjetoCreate, ProjetoUpdate, ProjetoResponse,
    VooCreate, VooResponse,
    OrtomapaCreate, OrtomapaResponse,
    AnaliseCreate, AnaliseResponse,
    AnotacaoCreate, AnotacaoResponse,
    GCPCreate, GCPResponse,
    ComparacaoCreate, ComparacaoResponse,
    TarefaAgenteCreate, TarefaAgenteResponse,
)

__all__ = [
    "get_connection",
    "execute_query",
    "execute_many",
    "init_database",
    "ProjetoCreate", "ProjetoUpdate", "ProjetoResponse",
    "VooCreate", "VooResponse",
    "OrtomapaCreate", "OrtomapaResponse",
    "AnaliseCreate", "AnaliseResponse",
    "AnotacaoCreate", "AnotacaoResponse",
    "GCPCreate", "GCPResponse",
    "ComparacaoCreate", "ComparacaoResponse",
    "TarefaAgenteCreate", "TarefaAgenteResponse",
]

# Validação OpenTelemetry da API

**Data:** 14/09/2026  
**Resultado:** Aprovado

## Configuração

- Instrumentação FastAPI habilitada por `OTEL_ENABLED=1`.
- Serviço identificado como `ortomapas-api`.
- Dependências OpenTelemetry instaladas no ambiente Python.
- Exportador de console usado para validação local; produção pode apontar para um Collector via OTLP.

## Demonstração real

Foi executado `GET /health` contra a API instrumentada na porta 8895, com resposta HTTP `200`. O log do processo registrou um span `SERVER` com:

- trace ID `54e532a60da3f90ab3571b2530fab251`;
- rota `/health` e método `GET`;
- status HTTP `200`;
- `service.name=ortomapas-api`;
- SDK OpenTelemetry 1.34.1.

## Conclusão

A API já produz traces distribuídos básicos. O próximo refinamento é instrumentar chamadas externas (LM Studio, PostgreSQL e NodeODM) e exportar para um OpenTelemetry Collector persistente.

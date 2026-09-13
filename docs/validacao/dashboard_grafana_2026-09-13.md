# Validação do dashboard Grafana

**Data:** 13/09/2026  
**URL:** `http://localhost:3010`  
**Resultado:** Provisionamento aprovado

## Componentes provisionados

- Datasource `Prometheus`, UID `ortomapas-prometheus`, apontando para `http://prometheus:9090`.
- Dashboard `Ortomapas - Operacional`, carregado automaticamente no folder `Ortomapas`.
- Painéis de requisições totais, erros, latência média, respostas por status e taxa de requisições.

## Evidências reais

- `GET /api/health` do Grafana: HTTP `200`, banco interno `ok`, versão `11.2.0`.
- Logs do container confirmaram `inserting datasource from configuration`.
- Logs confirmaram `starting to provision dashboards` e `finished to provision dashboards`.
- Endpoint `/api/search` sem credenciais retornou HTTP `401`, preservando a proteção administrativa.

## Operação

```bash
docker compose -f observability/docker-compose.yml ps
```

O dashboard está disponível em Grafana na porta 3010 e coleta as métricas Prometheus da API Ortomapas.

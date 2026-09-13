# Validação de métricas operacionais

**Data:** 13/09/2026  
**Endpoint:** `GET /health/metrics`  
**Resultado:** Aprovado

## Demonstração

Após chamadas reais a `/health`, `/health/ready` e uma rota inexistente, o endpoint retornou:

- `requests_total`: **3**
- `errors_total`: **0** (erros 5xx)
- `average_latency_ms`: **3,2 ms**
- `by_status`: **200=2, 404=1**

As métricas são atualizadas pelo middleware em cada requisição e permitem integração com monitoramento externo. O endpoint de prontidão confirmou PostgreSQL e LM Studio disponíveis durante o teste.

## Limites

As métricas são locais ao processo; para múltiplas réplicas, o próximo passo é exportar para Prometheus/OpenTelemetry ou armazenar em um agregador externo.

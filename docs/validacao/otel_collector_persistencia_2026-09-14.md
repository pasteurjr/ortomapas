# Validação do OpenTelemetry Collector

**Data:** 14/09/2026  
**Resultado:** Aprovado

## Configuração

- Serviço Docker: `ortomapas-otel-collector`.
- Imagem: `otel/opentelemetry-collector-contrib:0.109.0`.
- Receivers OTLP gRPC/HTTP nas portas 4317/4318.
- Backend habilita exportação OTLP com `OTEL_OTLP_ENABLED=1`.
- Prometheus e Grafana permanecem com volumes persistentes.

## Demonstração real

Com a API instrumentada na porta 8896, foi executado `GET /health`. O log do Collector confirmou:

`TracesExporter ... resource spans: 1, spans: 4`

Isso demonstra o caminho API → OTLP → Collector. O Collector está pronto para ser conectado a um backend persistente de traces (Tempo, Jaeger ou outro compatível) em produção.

## Conclusão

O item 2/5 está concluído para coleta centralizada. A persistência de traces em storage dedicado é a próxima evolução de produção.

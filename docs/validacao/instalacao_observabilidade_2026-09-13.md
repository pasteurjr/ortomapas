# Instalação de Prometheus e Grafana

**Data:** 13/09/2026  
**Resultado:** Serviços instalados e operacionais

## Componentes

| Serviço | Imagem | Porta |
|---|---|---:|
| Prometheus | `prom/prometheus:v2.54.1` | `9090` |
| Grafana | `grafana/grafana:11.2.0` | `3010` |

Os serviços foram instalados pelo Compose em `observability/docker-compose.yml`, com volumes persistentes próprios. A porta 3010 foi escolhida porque 3001 já estava ocupada.

## Validação real

- `GET http://127.0.0.1:9090/-/ready` retornou HTTP `200` (`Prometheus Server is Ready`).
- `GET http://127.0.0.1:3010/api/health` retornou HTTP `200` (`database: ok`, Grafana 11.2.0).
- O Prometheus está configurado para coletar `http://host.docker.internal:8888/metrics`.

## Operação

```bash
docker compose -f observability/docker-compose.yml ps
docker compose -f observability/docker-compose.yml up -d
```

O próximo passo é cadastrar o datasource Prometheus no Grafana e criar um dashboard com latência, erros, requisições e saúde do copiloto.

# Validacao de alertas operacionais - 14/09/2026

## Escopo

Foi concluida a etapa 5/5 da revisao operacional: regras de alerta no Prometheus e um Alertmanager no ambiente Docker do Ortomapas.

## Implementacao verificada

- `observability/alerts.yml` contem duas regras:
  - `OrtomapasApiSemMetricas` (critico): dispara quando a API deixa de publicar metricas por 2 minutos.
  - `OrtomapasTaxaDeErrosAlta` (aviso): dispara quando a taxa de erros supera 0,1 erro/segundo por 5 minutos.
- `observability/prometheus.yml` referencia o arquivo de regras e o Alertmanager em `127.0.0.1:9093`.
- `observability/docker-compose.yml` sobe o Alertmanager em modo host, sem alterar as portas da API.
- `observability/alertmanager.yml` usa o receiver `default` como ponto de extensao para notificacoes.

## Evidencias executadas

| Verificacao | Resultado |
|---|---|
| `promtool check rules observability/alerts.yml` | **SUCCESS: 2 rules found** |
| `GET http://127.0.0.1:9093/-/ready` | **HTTP 200 - OK** |
| `GET http://127.0.0.1:9090/api/v1/rules` | **HTTP 200**; grupo `ortomapas-operacional` carregado |
| Estado inicial das regras | `inactive`, `health: ok` (condicao de alerta nao presente durante o teste) |

## Conclusao

O monitoramento externo e a avaliacao automatica de disponibilidade e taxa de erros estao operacionais. O Alertmanager esta pronto para encaminhar notificacoes; a configuracao de um destino externo (e-mail, Slack ou webhook) permanece especifica do ambiente de implantacao e nao foi inventada nesta etapa.

## Endpoints locais

- Prometheus: `http://localhost:9090`
- Alertmanager: `http://localhost:9093`
- Grafana: `http://localhost:3010`

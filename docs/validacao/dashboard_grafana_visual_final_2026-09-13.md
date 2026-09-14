# Validação visual final do dashboard Grafana

**Data:** 13/09/2026  
**Resultado:** Aprovado com dados reais

## Evidência Playwright

O dashboard foi aberto e autenticado em `http://127.0.0.1:3010/d/ortomapas-operacional/ortomapas-operacional`. A captura está em `runtime/screenshots/grafana_dashboard_operacional_com_dados.png`.

Os cinco painéis renderizaram dados, sem ocorrências de “No data”:

- Requisições totais: **195**
- Erros: **0**
- Latência média: **0,895 ms**
- Respostas por status: série HTTP 200 visível
- Taxa de requisições: série temporal visível

## Verificação do datasource

`GET /api/datasources/uid/ortomapas-prometheus/health` retornou HTTP `200` com mensagem `Successfully queried the Prometheus API`.

## Conclusão

Prometheus, Grafana e API Ortomapas estão integrados e demonstrados visualmente com métricas reais coletadas da aplicação.

# Validação visual do dashboard Grafana

**Data:** 13/09/2026  
**Evidência:** `runtime/screenshots/grafana_dashboard_operacional.png`

## Resultado observado

- Login e navegação até `Ortomapas - Operacional` funcionaram.
- Os cinco painéis foram renderizados visualmente.
- A captura mostrou **No data** em todos os painéis.
- O endpoint Prometheus confirmou o target `ortomapas-api` como `down`, com timeout ao acessar `172.17.0.1:8888/metrics`.
- A API do Grafana respondeu HTTP 200; a API administrativa sem autenticação respondeu 401.

## Conclusão

O dashboard está provisionado e visualmente acessível, mas a coleta de dados ainda não está operacional devido ao isolamento de rede entre o container Prometheus e a API executada no host. Não considero a etapa de dados concluída. A correção requer rede host para o Prometheus (com autorização explícita) ou colocar a API em um serviço Docker na mesma rede.

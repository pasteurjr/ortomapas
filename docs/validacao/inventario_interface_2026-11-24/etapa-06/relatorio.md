# Etapa 6/6 — Regressão integrada e fechamento do inventário

**Revisão:** 26/11/2026
**Resultado:** regressão local de build e algoritmos passou; regressão integrada permanece aberta porque API e PostgreSQL estão indisponíveis.

## Roteiro tentado e estado dos serviços

| Verificação | Esperado | Obtido | Resultado |
|---|---|---|---|
| PostgreSQL local | Aceitar conexão na porta configurada pelo projeto (`127.0.0.1:5433`) | `pg_isready` não recebeu resposta em `127.0.0.1:5433` nem `127.0.0.1:5432`; `pg_lsclusters` não listou cluster | Não executável |
| Serviços em Docker Compose | Banco/app em execução para teste isolado | `docker compose ps` não listou contêineres ativos; o Compose do repositório contempla WebODM/NodeODM/GeoServer, não um PostgreSQL local já instalado | Não executável; não subi esse stack porque não é a dependência mínima desta regressão |
| Backend e frontend | HTTP disponível para jornada Playwright atual | `ss -ltnp` sem portas escutando | Não executável |
| Build do frontend | Compilar a interface de produção | Vite transformou 427 módulos e concluiu o build com sucesso | Aprovado, com aviso de chunk JavaScript >500 kB e aviso de API CJS do Vite depreciada |
| Testes direcionados de regressão | Ferramentas e fluxos relacionados sem falhas | 81 testes passaram, 0 falharam | Aprovado em nível unitário |
| Jornada integrada de login, projeto, mapa, análises, Copiloto e persistência | Playwright no checkout atual, com API/banco e capturas atuais | Não realizada nesta sessão; serviços necessários não estão ativos | Pendente — bloqueio de ambiente |

## Teste unitário executado

```bash
./.conda-env/bin/python -m pytest -q \
  tests/test_ortomapa_delete_guard.py \
  tests/test_copilot_threads.py \
  tests/test_copilot_summary.py \
  tests/test_copilot_memories.py \
  tests/test_copilot_context.py \
  tests/test_anthropic_copilot_client.py \
  tests/test_vegetation_classification.py \
  tests/test_terrain_tools.py \
  tests/test_hydrology_products.py \
  tests/test_change_detection.py \
  tests/test_elevation_change.py \
  tests/test_volume_aoi.py \
  tests/test_clip_export.py
```

**Obtido:** 81 passaram, 0 falharam em 1,67 s. Foram reportados 137 avisos de depreciação de Rasterio/Shapely; não causaram falhas.

## Capturas disponíveis para comparação

Não gerei imagens atuais de uma jornada integrada, pois ela não pôde ser aberta. As evidências visuais disponíveis são de execuções anteriores e ficam identificadas como tais:

- Navegação e viewport: [relatório da etapa 1](../etapa-01/relatorio.md), capturas `01_notificacoes_abertas.png` a `08_viewport_compacto.png`.
- Exclusão protegida na UI: [relatório da etapa 2](../etapa-02/relatorio.md), cinco estados com ortomapa descartável de fixture.
- Enquadramento do planejador: [relatório da etapa 3](../etapa-03/relatorio.md), seis cenários Playwright; a referência espacial veio do DSM Aukerman real, enquanto as respostas de API eram fixtures.
- Saídas de análises: [relatório da etapa 4](../etapa-04/relatorio.md), capturas de resultados reais anteriores; as telas do inventário inicial eram formulários pré-execução.
- Chat e privacidade: [relatório da etapa 5](../etapa-05/relatorio.md), capturas de chat reais anteriores e teste separado de duas contas.

## Critérios finais

| Área | Estado nesta revisão final |
|---|---|
| Navegação e controles da interface | Correções e testes Playwright anteriores documentados; regressão ampla atual pendente |
| Exclusão e proteção contra cascata | Teste UI com fixture e teste unitário atuais aprovados; autorização/DB real atual pendente |
| Enquadramento geográfico do Planejador | Seis cenários anteriores aprovados; repetição integrada atual pendente |
| Ferramentas de análise | 55 testes unitários desta área passaram; evidências reais anteriores referenciadas; API/DB atuais não testados |
| Copiloto, contexto e privacidade | 24 testes unitários atuais passaram; evidências PostgreSQL/Playwright anteriores passaram; repetição integrada atual pendente |
| Build | Aprovado; alertas de bundle/depreciação registrados |
| Aceite operacional científico do hidrológico/Copiloto | Não concedido; limites e pendências permanecem nos relatórios específicos |

## Conclusão e condição para fechar a etapa

O checkout compila e os 81 testes direcionados passam. Isso não basta para fechar a etapa 6: não foi possível reproduzir login, chamadas à API, persistência em PostgreSQL ou capturas Playwright atuais. A etapa permanece **parcial**, não aprovada. Para fechá-la, é necessário disponibilizar um PostgreSQL/PostGIS com o schema restaurado e os dados de validação, iniciar o backend e o frontend nas portas documentadas, então repetir o roteiro com uma conta/projeto de teste, coletar telas novas e comparar os estados com as etapas 1–5. Não é necessário subir WebODM/NodeODM/GeoServer para testar essa jornada do inventário.

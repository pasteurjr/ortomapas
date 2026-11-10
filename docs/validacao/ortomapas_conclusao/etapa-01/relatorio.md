# Relatório de validação — Fase 1/8: baseline e rastreabilidade

**Data:** 10/11/2026  
**Escopo:** auditoria documental do Ortomapas Web e dos requisitos complementares NodeODM.  
**Resultado:** concluída como baseline documental; nenhuma aprovação operacional nova foi emitida.

## O que foi verificado

- Fonte de casos de uso principal: `docs/analise/casos_de_uso_v2.md`, UC-001–020.
- Requisitos complementares: `docs/analise/integracao_odm_requisitos.md`, UC-021–029 e ODM-01–10.
- Especificação do Copiloto: `docs/analise/plano_implementacao_agentes.md` e relatórios de aceite/revalidação da Fase 8.
- Relatórios Playwright e ODM de 05–06/11/2026 referenciados na [matriz de rastreabilidade](../../../analise/matriz_rastreabilidade_ortomapas_fase1.md).
- Disponibilidade local da interface/API: consulta de sockets/processos nas portas comuns da API e Vite; nenhuma API/frontend do Ortomapas estava ouvindo durante esta auditoria.

## Comparação: esperado versus obtido

| Critério | Esperado | Obtido | Resultado |
|---|---|---|---|
| Identificar fonte normativa | Separar UCs do produto web e requisitos ODM | UC-001–020 e UC-021–029/ODM-01–10 identificados e citados | Aprovado |
| Rastrear estados sem confundir índice com prova | Para cada UC, apontar status e evidência ou lacuna | Matriz registra 29 UCs, requisitos ODM e linhas transversais; ausência de evidência é explicitada | Aprovado |
| Resolver ambiguidade Copiloto/fila | Não aceitar chat como prova de worker nem vice-versa | UC-020 delimitado para fila de análise espacial; Copiloto separado na Fase 7 | Aprovado para baseline; renomeação editorial sugerida |
| Representar limites do ODM | Distinguir execução real, serviço simulado e qualidade heurística | 77 fotos Aukerman e produtos reais foram encontrados; recovery mock, nota 100% heurística e falta de reprocessamento real ficam explícitos | Aprovado |
| Captura de tela da fase | Captura nova se houver tela executada/alterada | Nenhum serviço local ativo; fase não alterou UI. Referências históricas permanecem vinculadas e nenhuma foi reapresentada como nova | Não aplicável à auditoria documental; teste visual continua pendente nas fases correspondentes |
| Consistência de arquivo | Documento rastreável, sem erros de whitespace | `git diff --check` e conferência das referências/arquivos concluídos após geração | Aprovado |

## Decisões e correções documentais

1. A matriz de rastreabilidade passa a ser o índice de evidência para as próximas fases; os relatórios originais continuam sendo a fonte dos detalhes.
2. UC-020 é acompanhado como “solicitar análise espacial e acompanhar worker”. O nome atual “Agente de IA” não autoriza inferir uso do LLM. Recomenda-se atualizar o título na próxima revisão normativa coordenada.
3. Chat do Copiloto é uma linha independente, ainda parcial conforme a especificação/aceite da Fase 8.
4. UC-005–012 e UC-018 não são considerados operacionalmente aprovados em bloco: a matriz identifica onde há execução referenciada e onde ainda falta aceite específico.
5. A evidência NodeODM Aukerman valida o fluxo com dataset público; não comprova captura própria, Guarajuba, qualidade geodésica nem os limites de todos os requisitos ODM.

## Evidências

- [Matriz de rastreabilidade](../../../analise/matriz_rastreabilidade_ortomapas_fase1.md)
- [Relatório NodeODM em projeto novo (referência histórica)](../../odm_operacao_2026-11-05/aceite_projeto_novo/relatorio.md)
- [Validação da busca UC-002 (referência histórica)](../../uc002_busca_global_2026-11-06/relatorio.md)
- [Validação do upload UC-004 (referência histórica)](../../uc004_upload_geotiff_2026-11-06/relatorio.md)
- [Validação do UC-020/fila hidrológica (referência histórica)](../../uc020_hidrologia_queue_2026-11-06/relatorio.md)

## Saída e próxima fase

**Fase 1/8 concluída:** a baseline documental está definida e os estados são explícitos. Isso não significa que o Ortomapas esteja concluído; as linhas “parcial”, “não comprovado” ou sem evidência suficiente seguem abertas.

**Próxima etapa: Fase 2 de 8 — Identidade, projetos, autorização e persistência.** Validar criação/seleção/persistência e testar isolamento entre duas contas em projetos, produtos, análises, arquivos, downloads e tiles. Produzir evidência Playwright nova, respostas HTTP e checagem de persistência no PostgreSQL.

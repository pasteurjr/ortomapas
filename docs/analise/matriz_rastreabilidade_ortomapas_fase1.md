# Matriz de rastreabilidade Ortomapas Web — Fase 1

**Revisão:** 19/11/2026
**Propósito:** estabelecer baseline documental para as fases de conclusão do Ortomapas Web.
**Estado:** Fase 9 concluída; etapa proposta 10.1 executada; matriz atualizada com evidências. O aceite operacional global permanece retido pelas lacunas abaixo.

> Atualização de execução: resultados novos da Fase 3 constam no [relatório fotogramétrico com capturas](../validacao/ortomapas_conclusao/etapa-03/relatorio.md). O ciclo principal real passou; os cenários ODM de robustez continuam abertos.

## Como ler os estados

- **Implementado com evidência referenciada:** há relatório/captura/teste identificável para pelo menos o fluxo descrito. A evidência não é automaticamente prova de todos os critérios do UC.
- **Implementado no índice, evidência funcional insuficiente nesta revisão:** a matriz v2 marca aderente, mas nesta auditoria não foi localizada evidência individual recente e completa para aceitar todos os critérios.
- **Parcial:** existe execução documentada, mas há lacuna de escopo, calibração ou aceite.
- **Não comprovado:** requisito descrito sem evidência operacional localizada nesta revisão; não significa que inexista código.
- **Separado do UC-020:** requisito do Copiloto conversacional. Não é validado por uma fila de tarefas de análise.

## Decisão de escopo do UC-020

O fluxo detalhado de UC-020 em `casos_de_uso_v2.md` descreve abrir `AnalysisForm`, selecionar raster/tipo, marcar execução enfileirada, acompanhar estados no `AgentStatus` e exibir produto resultante. A matriz de aderência e os relatórios de 06/11 também medem execução de workers/filas. Portanto, para a rastreabilidade deste plano, **UC-020 significa solicitar e acompanhar análise espacial assíncrona**. A expressão “agente de IA” no título não significa que o LLM do Copiloto tenha escolhido o método ou executado a análise.

O Copiloto conversacional é um fluxo independente, documentado no plano de agentes e nos relatórios da Fase 8: prompt, contexto por usuário/projeto, resposta, invocação de ferramentas e eventual aprovação. Uma conversa bem-sucedida não aprova UC-020; uma tarefa enfileirada tampouco aprova o Copiloto. A Fase 7 do plano de conclusão valida o Copiloto em separado.

**Pendência editorial recomendada:** renomear futuramente UC-020 para “Solicitar análise espacial assíncrona e acompanhar execução” e manter “Copiloto conversacional” em um UC próprio com rastreabilidade de conversas/ferramentas. Esta revisão documenta a fronteira, mas não renumera nem altera contratos da aplicação.

## Casos de uso do núcleo web (UC-001–020)

| ID | Requisito resumido | Interface/ação descrita | Evidência localizada | Estado da Fase 1 e lacuna para aceite |
|---|---|---|---|---|
| UC-001 | Criar projeto | Dialog Novo e lista persistida | Projeto 64 criado pela UI no [aceite ODM](../validacao/odm_operacao_2026-11-05/aceite_projeto_novo/relatorio.md) | Implementado com evidência referenciada; conferir autorização, edição/remoção previstas e isolamento na Fase 2 |
| UC-002 | Buscar e filtrar projetos | Busca global/local e seleção | [Playwright UC-002](../validacao/uc002_busca_global_2026-11-06/relatorio.md), HTTP 200 e estados com/sem resultado | Implementado com evidência referenciada para o fluxo registrado; acesso por segunda conta continua pendente |
| UC-003 | Selecionar projeto e ver produtos | Lista, contexto ativo, catálogo e mapa | Projeto 64 selecionado e catálogo aberto no [aceite ODM](../validacao/odm_operacao_2026-11-05/aceite_projeto_novo/relatorio.md) | Implementado com evidência referenciada; conferir vazio, troca rápida de projeto e isolamento |
| UC-004 | Importar GeoTIFF e abrir no mapa | Dialog de upload, metadados, camada ativa | [Playwright UC-004](../validacao/uc004_upload_geotiff_2026-11-06/relatorio.md), incluindo rejeição de arquivo inválido | Implementado com evidência referenciada; ampliar tipos/CRS e verificar autorização na Fase 2/4 |
| UC-005 | Índice de vegetação VARI | Formulário da aba Vegetação | [Fila multi-tipo](../validacao/uc020_fila_multitipo_2026-11-06/relatorio.md) executou índices RGB com raster sintético controlado | Evidência de execução via fila; não prova todas as entradas, UX direta nem validade agronômica. RGB não equivale a NDVI |
| UC-006 | Declividade a partir de DSM | Formulário Terreno e camada derivada | Declividade calculada sobre DSM e DTM ODM no [aceite ODM](../validacao/odm_operacao_2026-11-05/aceite_projeto_novo/relatorio.md); worker também validado no [relatório de terreno](../validacao/uc020_terreno_queue_2026-11-06/relatorio.md) | Implementado com evidência referenciada; conferir unidades, bordas e referência quantitativa antes do aceite técnico |
| UC-007 | Curvas de nível | Intervalo e saída vetorial GeoJSON | Curvas executadas/renderizadas no [relatório de terreno/fila](../validacao/uc020_terreno_queue_2026-11-06/relatorio.md) | Implementado com evidência referenciada para execução descrita; testar persistência, CRS/unidade e parâmetros adicionais |
| UC-008 | Hillshade | Formulário de parâmetros e raster derivado | Hillshade executado, publicado e reaberto no [relatório de terreno/fila](../validacao/uc020_terreno_queue_2026-11-06/relatorio.md) | Implementado com evidência referenciada; conferir legenda, iluminação e recuperação |
| UC-009 | Mudança entre produtos | Dois produtos e limiar | Fase 9.6 comprovou patch conhecido; etapa 10.3 executou campanha UAV independente 2022/2024, worker, persistência e máscara visível com tiles autenticados no [relatório e capturas](../validacao/ortomapas_conclusao/etapa-10/uc009_independent_campaigns/relatorio.md) | **Fluxo funcional comprovado; aceite operacional/científico parcial.** O par passa CRS/grade/overlap e produz resultado. A diferença simples marcou 77,96% dos pixels acima do limiar; isso não é verdade de campo. Faltam polígonos rotulados/tolerâncias e separação de sazonalidade/iluminação. UI avisa que app não estima registro por feições nem corrige radiometria sazonal. |
| UC-010 | Classificação K-Means RGB | Formulário, classes, raster de saída | [Fila multi-tipo](../validacao/uc020_fila_multitipo_2026-11-06/relatorio.md) documenta execução e resultado raster | **Parcial:** execução funcional comprovada, mas interpretação semântica/operacional requer ground truth rotulado, métricas por classe e repetibilidade; RGB não equivale a classificação multiespectral |
| UC-011 | Drenagem/hidrologia | Escolha de elevação e exutório no mapa | Rede D8 e bacia foram executadas/enfileiradas/renderizadas sobre DTM real; benchmarks com hidrografia USGS/3DHP não produziram referência adequada/critério de aceite satisfeito | **Funcional demonstrativo; não aceito para uso hidrológico operacional** até comparar DTM e rede na mesma área com referência independente adequada e critérios quantitativos. Opcional depois do ODM; [relatório incremental 9.3–9.5](../validacao/ortomapas_conclusao/etapa-08/relatorio.md) |
| UC-012 | Volume acima/abaixo de referência | Superfície, AOI e cota | Recálculo independente da diferença raster para cota declarada de 241 m; erro máximo 0 m e volumes conferidos: 1.457,400 m³ acima / 6.817,207 m³ abaixo | **Aprovado matematicamente na fixture e nos parâmetros documentados**; não equivale a validação de levantamento de campo/datum nem substitui verificação em AOI operacional. [Fase 8, F8-06](../validacao/ortomapas_conclusao/etapa-08/relatorio.md) |
| UC-013 | Anotação poligonal | Desenho/formulário e persistência | Matriz v2 marca aderente; relatório individual recente não localizado | Implementado no índice, evidência funcional insuficiente nesta revisão; demonstrar criação, edição, persistência e recarga |
| UC-014 | Anotação de ponto | Clique/formulário e persistência | Matriz v2 marca aderente; relatório individual recente não localizado | Implementado no índice, evidência funcional insuficiente nesta revisão; demonstrar criação, edição, persistência e recarga |
| UC-015 | Medir distância | Barra de desenho, segmentos, desfazer/limpar | [Playwright UC-015/016](../validacao/medicao_uc015_016_2026-11-06/relatorio.md) registrou 3,509 km e estados de edição | Implementado com evidência referenciada no cenário registrado; validar CRS/medidas em outros contextos na Fase 4 |
| UC-016 | Medir área | Polígono, área, perímetro | [Playwright UC-015/016](../validacao/medicao_uc015_016_2026-11-06/relatorio.md) | Implementado com evidência referenciada no cenário registrado; confirmar unidades e geometria independente |
| UC-017 | Comparar produtos | Swipe e lado a lado | [Playwright UC-017](../validacao/uc017_comparacao_2026-11-06/relatorio.md), duas ortofotos e tiles HTTP 200 | Implementado com evidência referenciada no cenário; validar produtos diferentes e alinhamento/CRS na Fase 4 |
| UC-018 | Exportar produto | Seleção de formato/CRS e download | Requisito descrito; aceite/download verificável não localizado nesta revisão | Não comprovado nesta revisão; round-trip de metadados e conteúdo necessário na Fase 4 |
| UC-019 | Registrar voo | Dialog, fotos e parâmetros ODM | Voo 26 e 77 fotos vinculados ao projeto 64 no [aceite ODM](../validacao/odm_operacao_2026-11-05/aceite_projeto_novo/relatorio.md) | Implementado com evidência referenciada para dataset público; distinguir voo cadastrado de captura física e ampliar falhas/edição |
| UC-020 | Enfileirar análise espacial e acompanhar worker | AnalysisForm, tarefa e AgentStatus | API/DB/worker/UI Playwright aprovados para K-Means RGB, índices RGB, slope/aspect/hillshade/curvas, hidrologia D8, mudança RGB e volume; resultados persistidos e tiles autenticados HTTP 200. [Relatório e capturas etapa 10.2](../validacao/ortomapas_conclusao/etapa-10/uc020_queue_coverage/relatorio.md) | **Implementado com evidência no escopo aprovado.** A especificação v2 do UC-010 requer K-Means RGB; não define segmentação ou classificação supervisionada como critério de aceite UC-020. Os controles experimentais foram removidos do AnalysisForm para não sugerir execução disponível. A qualidade hidrológica de UC-011, o ground truth semântico de UC-010 e campanhas independentes de UC-009 permanecem critérios científicos próprios. A fila espacial continua separada do Copiloto. |

## Integração NodeODM (UC-021–029 e ODM-01–10)

| ID | Requisito | Evidência localizada | Estado documental / próximo teste |
|---|---|---|---|
| UC-021 / ODM-01–02 | Importar fotos, validar arquivos, preservar EXIF/originais | Nova prova: 77/77 JPEG com GPS, hashes SHA-256 registrados; `.txt` rejeitado HTTP 400 sem processamento | Positivo aprovado; limites de volume e persistência duradoura dos originais continuam sem ensaio específico; [relatório Fase 3](../validacao/ortomapas_conclusao/etapa-03/relatorio.md) |
| UC-022 / ODM-03–04 | Criar tarefa assíncrona e persistir estado, parâmetros e IDs | Tarefa real concluída em 36,6 min; NodeODM 2.2.4/ODM 3.5.6, UUID e processamento local registrados | Fluxo positivo aprovado; persistência de todos os parâmetros ainda requer auditoria própria; [relatório Fase 3](../validacao/ortomapas_conclusao/etapa-03/relatorio.md) |
| UC-023 | Acompanhar progresso e estado terminal | Capturas reais de processamento, marcos 42/77%, conclusão 100%, reabertura após login e cancelamento confirmado por NodeODM real com código 50 | Conclusão/cancelamento aprovados nos cenários executados; falha e retomada automática seguem pendentes; [Fase 3](../validacao/ortomapas_conclusao/etapa-03/relatorio.md) e [Fase 9.7](../validacao/ortomapas_conclusao/etapa-08/relatorio.md) |
| UC-024 / ODM-09 | Cancelar, repetir ou recuperar sem perder histórico | 9.7 comprovou cancelamento, replay idempotente HTTP 200 e conflito HTTP 409 com NodeODM real. Na 10.1, tarefa #21 ausente (resposta real HTTP 200 com erro `not found`) foi recuperada pela UI: 77 fotos preservadas reenviadas, processamento #25 concluído e seis produtos importados; seis produtos e 77 fotos da origem preservados | **Aprovado nos cenários executados** de cancelamento, idempotência/conflito e recuperação real; [relatório e manifesto cumulativos](../validacao/ortomapas_conclusao/etapa-08/relatorio.md) e [capturas 10.1](../validacao/ortomapas_conclusao/etapa-10/uc024_real_recovery/) |
| UC-025 / ODM-05/05a/06 | Importar e catalogar produtos e metadados | Seis saídas reais no projeto temporário: orto, DSM, DTM, PDF, LAZ e GLB; catálogo ligado ao voo | Importação positiva aprovada e limpa após evidência; idempotência e todos os metadados seguem abertos; [relatório Fase 3](../validacao/ortomapas_conclusao/etapa-03/relatorio.md) |
| UC-026 | Exibir qualidade do processamento | Fase 9.8 auditou API/UI e produtos reais #21: 100% são 3 verificações de completude; ODM reporta 77/77 imagens, GSD estimado 2,8 cm, GPS 0,85 m, CE90 0,717 m e LE90 1,220 m; GeoTIFFs ~5 cm/pixel em EPSG:32617 | Correção semântica aprovada; **parcial para aceite científico/operacional** até comparar com checkpoints/GCP independentes e definir tolerâncias. Evidências: [relatório acumulado](../validacao/ortomapas_conclusao/etapa-08/relatorio.md), [captura](../validacao/ortomapas_conclusao/etapa-09/playwright/uc026_quality/01_uc026_completude_e_limites.png), [manifesto](../validacao/ortomapas_conclusao/etapa-09/playwright/uc026_quality/manifest.json) |
| UC-027 / ODM-07–08 | Visualizar e baixar produtos em CRS adequado | Ortofoto com 50 tiles, DSM/DTM 3D, GLB, LAZ e diferença abertos em EPSG:32617 | Visualização positiva aprovada; download/export autenticado e cenários adicionais de CRS seguem na Fase 4 |
| UC-028 | Visualizar nuvem 3D | LAZ abriu e exibiu 16.123.377 pontos na nova execução | Abertura e existência de dados aprovadas; interação dos controles da nuvem ainda não foi exercitada |
| UC-029 | Reprocessar parâmetros e comparar versões | Fase 9.9: processo #24, versão 4, reprocessado de #21 com `orthophoto-resolution=10`, NodeODM 2.2.4/ODM 3.5.6, 77 fotos e seis produtos importados. Orto em EPSG:32617 passou de ~5 cm para ~10 cm/pixel; DSM/DTM também foram comparados em janela alinhada de 512×512, com todos os pixels da janela amostral válidos; seis produtos de #21 preservados. Diferenças amostrais MAE/RMSE: orto 5,542/7,817 DN; DSM 0,0419/0,2884 m; DTM 0,0232/0,0285 m | **Aprovado funcionalmente para linhagem, reprocessamento e comparação de saídas.** Não é aceite de acurácia: as duas execuções usam as mesmas fotos e não há pontos de controle independentes nem limites de erro predefinidos. [Relatório, manifesto e capturas da Fase 9.9](../validacao/ortomapas_conclusao/etapa-08/relatorio.md) |
| ODM-10 | Limites de recurso e espaço | Não localizado teste de limite/estimativa | Não comprovado; exercitar com entradas seguras e limites documentados |

## Copiloto conversacional e dependências transversais

O plano de agentes documenta contexto, histórico/memória, ferramentas geoespaciais, autorização e escrita com aprovação. Os relatórios da Fase 7/8 e seus adendos mantêm o Copiloto separado da fila espacial UC-020. **Estado: parcial; não declarar Copiloto pronto por causa dos workers UC-020.**

| Linha transversal | Fonte | Observação para o plano |
|---|---|---|
| Autorização e propriedade de projeto | Requisitos dos UCs, recursos autenticados e validação GeoServer | Evidência da camada GeoServer protegida não comprova isolamento de todos os endpoints de projeto/arquivos; Fase 2 |
| Banco e persistência | PostgreSQL/PostGIS é o banco Ortomapas | Conferir integridade depois de reload e entre contas; não duplicar instância nem introduzir MySQL |
| Observabilidade | Relatórios de hardening/telemetria e implementação de logs | Verificar operação e sanitização na Fase 8; não expor segredos em evidência |
| UI profissional e navegação | Plano de melhorias de 10/10 e validações Playwright pontuais | Não assumir qualidade global da navegação a partir de um modal ou aba; capturar rotas principais nas fases 2–7 |
| Dados de demonstração | Dataset Aukerman com licença CC0; raster sintético usado em validações pontuais | Rotular origem em UI e relatório; não chamar dataset público de captura DJI/Guarajuba |

## Adendo de validação — Fase 2, 10/11/2026

Playwright percorreu login, criação de projeto pela interface e estado vazio de uma segunda conta. Com duas contas temporárias no PostgreSQL configurado, foram testados detalhe/lista do projeto, listagem/detalhe de voos, metadados de ortomapa, ticket de tile, acesso a arquivo e tentativa de edição. O proprietário recebeu acesso; a conta sem associação não recebeu conteúdo ou permissão de alteração.

A execução encontrou e corrigiu dois controles insuficientes: a listagem de membros aceitava perfil global `leitor` sem vínculo ao projeto; e a listagem geral de voos não filtrava por associação. Após as correções, ambos os casos negados retornaram o resultado esperado. Os quatro testes de regressão passaram, mais um teste de path traversal; o teste Playwright integrado passou. Usuários, projeto e arquivo temporários foram removidos, e a consulta de pós-limpeza encontrou zero contas/projetos temporários. Ver [relatório detalhado e capturas](../validacao/ortomapas_conclusao/etapa-02/relatorio.md).

**Escopo do aceite:** somente os recursos/rotas enumerados no relatório e os papéis owner/reader sem associação. A cobertura de todas as rotas, compartilhamento, editor e visualizador permanece aberta.

## Resultado da auditoria da Fase 1

1. A fonte normativa do núcleo é UC-001–020 em `casos_de_uso_v2.md`; a fonte complementar de fotogrametria é UC-021–029 e ODM-01–10 em `integracao_odm_requisitos.md`.
2. A matriz oficial de aderência não substitui a verificação dos critérios e das evidências individuais. Há UCs marcados aderentes cuja tela/endpoint possui descrição, mas sem relatório de aceite localizado nesta revisão.
3. UC-020 foi delimitado como fila de processamento de análise espacial. Copiloto conversacional fica separado.
4. A integração NodeODM tem evidência ponta a ponta forte em dataset público; recuperação, reprocessamento, limites e certas dimensões de qualidade ainda não têm a mesma prova.
5. Hidrologia permanece uma análise derivada opcional e parcial; não é pré-condição para gerar produtos ODM.
6. As fases 2–8 ficam ordenadas no plano de conclusão. Esta fase não alterou UI ou APIs.

### Limite visual desta fase

Esta entrega é auditoria/rastreabilidade documental. Não havia API nem frontend do Ortomapas ouvindo nas portas locais consultadas; portanto não foi feita captura Playwright nova, e nenhum screenshot histórico foi reapresentado como captura desta fase. As evidências visuais históricas permanecem ligadas por referência à linha correspondente. A primeira fase que altera/valida fluxos visuais próprios fará capturas novas em diretório específico.


## Decisão de aceite após a subetapa 9.9 e atualização 10.1 — 19/11/2026

A fase final de nove subetapas foi encerrada. A 9.9 concluiu e comparou funcionalmente os processamentos #21 e #24 do UC-029, sem remover os produtos originais. A decisão do sistema permanece **aceite operacional global retido**. Permanecem pendentes evidências científicas independentes para UC-009/011/026, operações e cobertura explicitadas para UC-020 e validações semânticas de UC-010; UC-024 teve recuperação real aprovada na etapa 10.1; ver classificações acima e o [relatório cumulativo com esperado versus obtido, capturas e manifesto da 9.9](../validacao/ortomapas_conclusao/etapa-08/relatorio.md). Não restam subetapas numeradas na Fase 9. A etapa 10.3 comparou duas campanhas UAV independentes e confirmou o fluxo, mas não demonstrou acurácia de detecção; ver relatório UC-009 e as ressalvas acima.

### Atualização após a etapa 10.3 — 20/11/2026

A decisão global segue **aceite operacional retido**. A etapa 10.3 concluiu o escopo funcional do UC-009 com as campanhas Aklavik 2022/2024. O resultado simples marcou 77,96% dos pixels válidos acima do limiar e a UI agora explicita que isso não confirma mudança física; sem rótulos independentes, não há base para calibrar ou aprovar a detecção científica. UC-009 continua parcial. A próxima etapa proposta é 10.4; restam quatro etapas da Fase 10 proposta, 10.4–10.7.

# Matriz de rastreabilidade Ortomapas Web — Fase 1

**Revisão:** 10/11/2026  
**Propósito:** estabelecer baseline documental para as fases de conclusão do Ortomapas Web.  
**Estado:** auditoria documental concluída; validação operacional das linhas continua conforme a evidência indicada.

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
| UC-009 | Mudança entre produtos | Dois produtos e limiar | Nenhum aceite recente específico localizado nesta auditoria | Não comprovado nesta revisão; exige produtos distintos, área comum, CRS/resolução compatíveis e valores de referência |
| UC-010 | Classificação K-Means RGB | Formulário, classes, raster de saída | [Fila multi-tipo](../validacao/uc020_fila_multitipo_2026-11-06/relatorio.md) documenta execução e resultado raster | Implementado com evidência referenciada para K-Means RGB; conferir determinismo/legenda e não chamar classes RGB de classificação espectral sem sensor/bandas |
| UC-011 | Drenagem/hidrologia | Escolha de elevação e exutório no mapa | [Fila hidrológica](../validacao/uc020_hidrologia_queue_2026-11-06/relatorio.md) e [benchmark Holston](../validacao/uc020_benchmark_holston_2026-11-06/relatorio.md) | Parcial para aceite operacional: execução demonstrada, mas benchmark limitado e sensibilidade à resolução; DTM de voo ainda não validado hidrologicamente. Função opcional posterior ao ODM |
| UC-012 | Volume acima/abaixo de referência | Superfície, AOI e cota | Relatório da Fase 8 cita teste comparativo de volumetria, mas não foi localizada nesta auditoria uma evidência por UC completa com entradas/AOI e expectativa | Não comprovado nesta revisão; localizar/associar evidência e conferir CRS, datum, máscara e polígonos na Fase 6 |
| UC-013 | Anotação poligonal | Desenho/formulário e persistência | Matriz v2 marca aderente; relatório individual recente não localizado | Implementado no índice, evidência funcional insuficiente nesta revisão; demonstrar criação, edição, persistência e recarga |
| UC-014 | Anotação de ponto | Clique/formulário e persistência | Matriz v2 marca aderente; relatório individual recente não localizado | Implementado no índice, evidência funcional insuficiente nesta revisão; demonstrar criação, edição, persistência e recarga |
| UC-015 | Medir distância | Barra de desenho, segmentos, desfazer/limpar | [Playwright UC-015/016](../validacao/medicao_uc015_016_2026-11-06/relatorio.md) registrou 3,509 km e estados de edição | Implementado com evidência referenciada no cenário registrado; validar CRS/medidas em outros contextos na Fase 4 |
| UC-016 | Medir área | Polígono, área, perímetro | [Playwright UC-015/016](../validacao/medicao_uc015_016_2026-11-06/relatorio.md) | Implementado com evidência referenciada no cenário registrado; confirmar unidades e geometria independente |
| UC-017 | Comparar produtos | Swipe e lado a lado | [Playwright UC-017](../validacao/uc017_comparacao_2026-11-06/relatorio.md), duas ortofotos e tiles HTTP 200 | Implementado com evidência referenciada no cenário; validar produtos diferentes e alinhamento/CRS na Fase 4 |
| UC-018 | Exportar produto | Seleção de formato/CRS e download | Requisito descrito; aceite/download verificável não localizado nesta revisão | Não comprovado nesta revisão; round-trip de metadados e conteúdo necessário na Fase 4 |
| UC-019 | Registrar voo | Dialog, fotos e parâmetros ODM | Voo 26 e 77 fotos vinculados ao projeto 64 no [aceite ODM](../validacao/odm_operacao_2026-11-05/aceite_projeto_novo/relatorio.md) | Implementado com evidência referenciada para dataset público; distinguir voo cadastrado de captura física e ampliar falhas/edição |
| UC-020 | Enfileirar análise espacial e acompanhar worker | AnalysisForm, tarefa e AgentStatus | Revalidação K-Means, índices, terreno, curvas, hillshade e hidrologia em relatórios de 06/11 | Parcial: tipos disponíveis estão listados nos relatórios UC-020; ainda faltam operações indicadas na matriz e aceite de escala hidrológica. Não é o Copiloto conversacional |

## Integração NodeODM (UC-021–029 e ODM-01–10)

| ID | Requisito | Evidência localizada | Estado documental / próximo teste |
|---|---|---|---|
| UC-021 / ODM-01–02 | Importar fotos, validar arquivos, preservar EXIF/originais | 77/77 JPEG com GPS EXIF; seleção e envio no [aceite ODM](../validacao/odm_operacao_2026-11-05/aceite_projeto_novo/relatorio.md) | Evidência de fluxo positivo; verificar hash, limite e arquivos inválidos sob o mesmo teste reproduzível |
| UC-022 / ODM-03–04 | Criar tarefa assíncrona e persistir estado, parâmetros e IDs | NodeODM aceitou POST 202; task real documentada | Evidência de execução real para envio/estado; revisar persistência de todos os metadados do requisito |
| UC-023 | Acompanhar progresso e estado terminal | Capturas de progresso e conclusão no relatório ODM | Evidência referenciada; incluir erro/cancelamento/retomada |
| UC-024 / ODM-09 | Cancelar ou repetir sem perder histórico | Reenvio de recuperação testado contra HTTP mock, não reprocessamento NodeODM real | Parcial; cancelamento e repetição real continuam sem prova equivalente |
| UC-025 / ODM-05/05a/06 | Importar e catalogar produtos e metadados | Seis saídas reais no projeto 64: orto, DSM, DTM, PDF, LAZ e GLB | Evidência referenciada; checar idempotência e cada metadado exigido |
| UC-026 | Exibir qualidade do processamento | Tela marcou 100%/Bom; relatório alerta ser regra de presença de produtos | Parcial sem validação científica: não usar nota como acurácia/GSD/precisão |
| UC-027 / ODM-07–08 | Visualizar e baixar produtos em CRS adequado | Ortofoto, DSM/DTM, GLB, LAZ e diferença abertos; WMS/WMTS vistos | Evidência de visualização; export/download autenticado e CRS seguem na Fase 4 |
| UC-028 | Visualizar nuvem 3D | LAZ com 15.953.257 pontos e amostra exibida na interface | Evidência referenciada para cenário Aukerman; testar controles e dados inválidos |
| UC-029 | Reprocessar parâmetros e comparar versões | Nenhum reprocessamento real com novos parâmetros localizado | Não comprovado nesta revisão; execução futura necessária |
| ODM-10 | Limites de recurso e espaço | Não localizado teste de limite/estimativa | Não comprovado; exercitar com entradas seguras e limites documentados |

## Copiloto conversacional e dependências transversais

O plano de agentes documenta contexto, histórico/memória, ferramentas geoespaciais, autorização e escrita com aprovação. O relatório de aceite de 29/10 e os adendos em `plano_implementacao_agentes.md` mantêm a Fase 8 sem aceite operacional pleno; também distinguem fila de análise e chat. **Estado nesta baseline: parcial; não declarar Copiloto pronto por causa dos workers UC-020.** Detalhamento e reteste ficam na Fase 7.

| Linha transversal | Fonte | Observação para o plano |
|---|---|---|
| Autorização e propriedade de projeto | Requisitos dos UCs, recursos autenticados e validação GeoServer | Evidência da camada GeoServer protegida não comprova isolamento de todos os endpoints de projeto/arquivos; Fase 2 |
| Banco e persistência | PostgreSQL/PostGIS é o banco Ortomapas | Conferir integridade depois de reload e entre contas; não duplicar instância nem introduzir MySQL |
| Observabilidade | Relatórios de hardening/telemetria e implementação de logs | Verificar operação e sanitização na Fase 8; não expor segredos em evidência |
| UI profissional e navegação | Plano de melhorias de 10/10 e validações Playwright pontuais | Não assumir qualidade global da navegação a partir de um modal ou aba; capturar rotas principais nas fases 2–7 |
| Dados de demonstração | Dataset Aukerman com licença CC0; raster sintético usado em validações pontuais | Rotular origem em UI e relatório; não chamar dataset público de captura DJI/Guarajuba |

## Resultado da auditoria da Fase 1

1. A fonte normativa do núcleo é UC-001–020 em `casos_de_uso_v2.md`; a fonte complementar de fotogrametria é UC-021–029 e ODM-01–10 em `integracao_odm_requisitos.md`.
2. A matriz oficial de aderência não substitui a verificação dos critérios e das evidências individuais. Há UCs marcados aderentes cuja tela/endpoint possui descrição, mas sem relatório de aceite localizado nesta revisão.
3. UC-020 foi delimitado como fila de processamento de análise espacial. Copiloto conversacional fica separado.
4. A integração NodeODM tem evidência ponta a ponta forte em dataset público; recuperação, reprocessamento, limites e certas dimensões de qualidade ainda não têm a mesma prova.
5. Hidrologia permanece uma análise derivada opcional e parcial; não é pré-condição para gerar produtos ODM.
6. As fases 2–8 ficam ordenadas no plano de conclusão. Esta fase não alterou UI ou APIs.

### Limite visual desta fase

Esta entrega é auditoria/rastreabilidade documental. Não havia API nem frontend do Ortomapas ouvindo nas portas locais consultadas; portanto não foi feita captura Playwright nova, e nenhum screenshot histórico foi reapresentado como captura desta fase. As evidências visuais históricas permanecem ligadas por referência à linha correspondente. A primeira fase que altera/valida fluxos visuais próprios fará capturas novas em diretório específico.

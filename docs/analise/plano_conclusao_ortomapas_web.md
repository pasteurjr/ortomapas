# Plano de conclusão do Ortomapas Web

**Data:** 10/11/2026  
**Versão:** 1.0  
**Situação:** Fases 1–3 concluídas dentro dos critérios e limites registrados; fases 4–8 aguardam execução.
**Escopo:** concluir, validar e documentar o produto web Ortomapas.

## 1. Objetivo e limites

Este plano organiza o trabalho restante para considerar o **Ortomapas Web** coerente com seus casos de uso e demonstrável com dados, resultados e evidências reproduzíveis. O simulador do drone próprio e o aplicativo Android para controle/captura são produtos separados e ficam fora deste plano.

O trabalho usa PostgreSQL/PostGIS como banco do Ortomapas, o NodeODM já disponível para fotogrametria, GeoServer quando necessário para publicação OGC, e Playwright para percorrer a interface. Nenhuma capacidade será considerada pronta somente porque existe código, endpoint, botão ou entrada na matriz: é necessário executar um fluxo representativo, verificar o resultado e registrar evidência.

## 2. Estado conhecido e cautelas

### Evidência já registrada

O relatório [aceite integrado em projeto novo](../validacao/odm_operacao_2026-11-05/aceite_projeto_novo/relatorio.md) documenta um fluxo real no NodeODM com projeto isolado e 77 fotos públicas Aukerman, todas com GPS EXIF. Foram importados ortomosaico, DSM, DTM, relatório, LAZ e GLB; abriram-se os visualizadores 2D/3D; calculou-se e persistiu-se declividade do DSM e do DTM. O GeoTIFF foi publicado e houve validação WMS/WMTS.

Essa evidência demonstra operação fotogramétrica com um conjunto público, **não** um voo próprio, nem um levantamento de Guarajuba/Condomínio Paraíso. A nota automática de qualidade 100% é baseada em presença de produtos e não representa acurácia posicional ou vertical. A recuperação de histórico do NodeODM foi testada com POST contra servidor HTTP simulado; não se deve relatar esse reenvio como reprocessamento real.

A matriz em [casos_de_uso_v2.md](casos_de_uso_v2.md) marca UC-001–019 como aderentes e UC-020 como parcial. Os relatórios anexos têm níveis de prova diferentes. O UC-020 tem cobertura comprovada para K-Means RGB, índices RGB, declividade/orientação, hillshade, curvas, rede D8 e bacia por exutório. Na etapa 9.1, direção D8, acumulação e TWI foram adicionadas à fila e executadas pelo worker sobre DTM ODM real; falta confirmar persistência e visualização via aplicação ativa. Mudanças, volume, segmentação e classificadores supervisionados continuam fora da fila, e a calibração hidrológica permanece limitada. UC-011 é análise opcional posterior, que consome DTM/DSM georreferenciado; não é etapa necessária para produzir ortomosaico.

Há uma inconsistência documental a resolver antes de declarar aceite: UC-020 aparece denominado “Disparar Análise via Agente de IA”, mas parte dos critérios e relatórios mede fila de análises espaciais. Chat/copiloto e fila de processamento não são a mesma capacidade. A primeira fase fechará a definição e a rastreabilidade sem promover testes de fila a prova de chat ou vice-versa.

## 3. Regras de validação e evidência

Cada fase deve acrescentar entradas ao relatório incremental de validação, mantendo o histórico das fases anteriores. Para cada requisito/caso de uso testado, registrar:

1. **Identificação:** requisito e UC, versão do código, data, ambiente e perfil de usuário.
2. **Dados de entrada:** origem/licença, arquivos e hashes quando aplicável, CRS, dimensões, parâmetros, projeto/voo e indicação clara de dado real, público ou sintético.
3. **Resultado esperado:** comportamento, valores/faixas ou invariantes verificáveis, estado da interface e persistência esperada.
4. **Execução observada:** ações feitas por Playwright ou protocolo/API, respostas/status, registros do banco e produtos gerados.
5. **Comparação:** esperado versus observado, critério objetivo de aprovação/reprovação e limitações da conclusão.
6. **Evidência visual:** captura própria da etapa, com contexto suficiente para interpretar o dado e resultado; sem reciclar a mesma captura para cenas diferentes. Salvar os arquivos sob `docs/validacao/ortomapas_conclusao/etapa-NN/` e referenciá-los no relatório.
7. **Correção e reteste:** defeito, correção, nova execução e nova captura; manter registro do resultado reprovado e da retestagem.

Uma captura isolada comprova apenas o que está visível nela. Para resultados geoespaciais, complementar a tela com CRS, unidade, extensão, estatísticas, validação numérica ou comparação de referência. Dados sintéticos servem para teste controlado e precisam estar rotulados; não devem ser apresentados como voo ou observação real.

## 4. Fases de conclusão

### Fase 1 — Baseline, escopo e rastreabilidade

**Objetivo:** estabelecer uma linha de base confiável para o restante do aceite.

**Atividades:**

- Consolidar casos de uso Ortomapas existentes (UC-001–020) e requisitos ODM (UC-021–029 / ODM-01–10), eliminando duplicidade e termos ambíguos.
- Resolver formalmente a fronteira de UC-020: agente/copiloto, fila de análises, ou dois casos distintos; mapear cada capacidade à sua própria rota, componente, persistência e teste.
- Construir matriz requisito → UC → tela/ação → endpoint → tabela/arquivo → teste automatizado → evidência existente → lacuna.
- Classificar cada linha como `implementada com evidência`, `implementada sem evidência suficiente`, `parcial`, `não implementada` ou `fora do escopo`; preservar links de evidência e data.
- Revalidar ambiente de execução, banco PostgreSQL/PostGIS, API, frontend e dependências ODM/GeoServer, sem alterar dados de usuário.

**Aceite:** todas as linhas têm estado e justificativa; UC-020 não mistura fila e chat; nenhum relatório antigo é implicitamente promovido a prova atual.  
**Evidência:** [matriz de rastreabilidade](matriz_rastreabilidade_ortomapas_fase1.md) e [relatório da Fase 1](../validacao/ortomapas_conclusao/etapa-01/relatorio.md). A auditoria não alterou UI e não havia API/frontend ativo para captura inédita; as referências visuais históricas estão identificadas como históricas. Capturas novas serão produzidas nas fases com execução visual.

### Fase 2 — Identidade, projetos, autorização e persistência

**Objetivo:** provar que os dados pertencem ao usuário/projeto certo e sobrevivem ao recarregamento.

**Atividades:**

- Percorrer login, lista/busca, criação, abertura e edição de projeto pela interface.
- Usar duas contas de teste e projetos distintos; conferir tentativas de acesso cruzado a projetos, produtos, análises, arquivos, downloads e tiles.
- Comparar UI/API com PostgreSQL: proprietário, relações, estados e consistência depois de logout/login e recarga.
- Verificar autorização nas rotas de produto e arquivos, incluindo serviço GeoServer/tiles conforme o escopo publicado; não alterar ACL global nem credenciais compartilhadas sem requisito delimitado.
- Testar estados vazios, entradas inválidas, erros e remoção/arquivamento se previstos nos UCs.

**Aceite:** usuário autorizado consegue operar seus recursos; a segunda conta não lê nem altera dados não compartilhados; estado persistido é consistente e telas informam erros sem sucesso falso.  
**Resultado:** aprovada para os recursos testados em 10/11/2026. A validação encontrou e corrigiu fuga na listagem de membros para perfil global `leitor` sem associação e consulta global de voos sem filtro de usuário. Consulta pós-limpeza confirmou remoção de usuários/projeto temporários e arquivo fixture.
**Evidência:** [relatório Playwright da Fase 2 e capturas](../validacao/ortomapas_conclusao/etapa-02/relatorio.md).

### Fase 3 — Fluxo fotogramétrico ponta a ponta e reprodutibilidade

**Objetivo:** tornar repetível o ciclo projeto → voo → fotos → NodeODM → produtos → catálogo.

**Atividades:**

- Reutilizar a evidência Aukerman existente como referência, sem contá-la como uma nova execução desta fase.
- Criar um projeto de validação isolado e executar upload/validação de imagens, criação da tarefa real no NodeODM, acompanhamento, importação de produtos e reabertura após reinício/recarga.
- Conferir quantidade, EXIF, hashes/manifestações, parâmetros, versão/ID externo, tempos, falhas e ligação de cada produto ao projeto e voo.
- Testar entradas inválidas, cancelamento/erro, duplicidade/idempotência e recuperação do histórico, distinguindo serviço real de mock.
- Usar o conjunto público Aukerman já presente ou outro conjunto com licença registrada; uma missão de Guarajuba só será chamada de real se houver dados de captura próprios e georreferenciados.

**Aceite:** processamento real conclui e os produtos esperados são importados uma única vez, permanecem ligados à origem e continuam acessíveis após recarga; falhas não são mascaradas como sucesso.  
**Evidência:** capturas de cadastro, seleção/upload, progresso, conclusão, catálogo e metadados; IDs/estados do NodeODM e hashes de entrada/saída.

**Execução em 10/11/2026:** o ciclo principal passou com o dataset público CC0 `odm_data_aukerman-master`: projeto/voo novos, 77 fotos com GPS EXIF, NodeODM 2.2.4/ODM 3.5.6 concluído em 36,6 min, seis produtos importados, login/recarga, ortomosaico, GLB, DSM, DTM, LAZ, diferença DSM–DTM e indicador de qualidade validados visualmente. O teste `.txt` foi rejeitado com HTTP 400 sem criar tarefa. No complemento, a API e o PostgreSQL reais foram exercitados contra fixture NodeODM controlada: erro 503→retry, replay idempotente 200, conflito 409, cancelamento e recuperação 202 de quatro fotos preservadas; não houve novo processamento fotogramétrico no complemento. Contas, projeto, voo e arquivos temporários foram removidos. O relatório e as capturas estão em [Fase 3](../validacao/ortomapas_conclusao/etapa-03/relatorio.md).

**Estado da fase: concluída no escopo exercitado.** A prova de erro/retry/cancelamento/recuperação usa uma fixture de protocolo e não comprova desempenho fotogramétrico; a geração real foi demonstrada separadamente com NodeODM 2.2.4/ODM 3.5.6. O indicador “100% / BOM” representa cobertura operacional de produtos, não acurácia cartográfica.

### Fase 4 — Visualização cartográfica 2D, produtos e exportação

**Objetivo:** assegurar que o mapa mostra o produto certo no lugar certo e permite operações de catálogo.

**Atividades:**

- Abrir ortomosaico, DSM, DTM, vetores e resultados; testar ordem/visibilidade, legenda, opacidade, identificação, escala, coordenadas e enquadramento.
- Conferir CRS, bounding box e transformação para tiles; inspecionar bordas e tiles fora da cobertura para evitar deformação/preenchimento incorreto.
- Comparar duas ortofotos/produtos distintos e testar alternância, deslizador/lado a lado e retorno ao mapa.
- Executar download/exportação em formatos e CRS suportados e comparar conteúdo, metadados e extensão com o produto de origem.
- Testar WMS/WMTS/GeoServer apenas no escopo documentado, incluindo autenticação quando aplicável; separar teste de capabilities de teste de acesso ao conteúdo.

**Aceite:** a camada e o resultado selecionados correspondem ao nome/tipo exibidos, alinham com a referência geográfica, têm simbologia/unidades inteligíveis e exportação verificável.  
**Evidência:** capturas distintas para ortofoto, DSM/DTM e resultados, mais metadados, imagens de tile e checagem espacial.

**Execução em 10/11/2026:** aprovada para raster 2D e GeoTIFF no CRS de origem. Em dados reais do projeto Aukerman no PostgreSQL, Playwright carregou ortofoto, DSM e DTM (25 tiles HTTP 200 por camada), conferiu opacidade e os dois modos de comparação e exportou GeoTIFF de 93.824.935 bytes, com EPSG:32617, 7.470 × 5.924 pixels e bounds preservados. O comparador usa duas execuções do mesmo local/conjunto e não demonstra mudança temporal. As correções e nove capturas estão no [relatório da Fase 4](../validacao/ortomapas_conclusao/etapa-04/relatorio.md).

### Fase 5 — Visualização 3D e produtos de elevação

**Objetivo:** demonstrar modelos efetivos, com geometria e escala interpretáveis.

**Atividades:**

- Abrir DSM e DTM como superfícies 3D, GLB texturizado e nuvem LAZ, usando produtos do processamento ODM.
- Verificar contagem de pontos/triângulos, extensão, unidades, orientação, enquadramento, escala vertical e interações (zoom, rotação, tela cheia e seleção quando oferecidas).
- Comparar valores e limites apresentados na interface com metadados/estatísticas do raster e da nuvem.
- Testar comportamento em ausência de dados, modelo incompatível, geometria vazia e falha WebGL.
- Exibir perfil de terreno apenas se o requisito e o comando estiverem presentes na versão atual; exigir amostragem ao longo da linha desenhada e distâncias físicas, não média de colunas apresentada como perfil.

**Aceite:** superfícies contínuas e modelo/nuvem visíveis, extensão preservada, unidades explícitas e valores coerentes com a fonte; falhas têm mensagem clara.  
**Evidência:** capturas separadas das cenas DSM, DTM, GLB e LAZ, além de números de referência extraídos dos arquivos.

**Execução em 10/11/2026:** aprovada no projeto 64/processamento 15, com produtos reais Aukerman já persistidos. Playwright abriu DSM, DTM, GLB e LAZ; conferiu dimensões, CRS, bounds, contagem de pontos, triângulos e materiais contra os arquivos; testou arrasto/zoom, exagero vertical, wireframe, vistas, enquadramento, inspeção de ponto e tela cheia. Não houve erros JavaScript. A malha DSM/DTM é uma pré-visualização de 128 × 101 amostras e não deve ser interpretada como estatística ou superfície em resolução integral. O [relatório da Fase 5](../validacao/ortomapas_conclusao/etapa-05/relatorio.md) contém valores comparados e cinco capturas.

### Fase 6 — Análises espaciais e qualidade dos resultados

**Objetivo:** fechar a matriz de análises com entradas corretas, saídas próprias e critérios proporcionais ao uso.

**Atividades:**

- Para UC-005–012, mapear ferramenta, tipo de entrada requerido, bandas, CRS/unidades, parâmetros, resultado e limitações. Validar individualmente vegetação RGB, terreno, curvas, hillshade, mudança, classificação, hidrologia e volume conforme disponíveis.
- Não chamar índices RGB de NDVI; exigir banda NIR para índices que dependam dela. Não calcular inclinação/distância/área em graus como se fossem unidades métricas.
- Confirmar que o resultado persistido e mostrado é uma camada derivada, não o raster de entrada renomeado; conferir estatísticas, legenda e vínculo a parâmetros/AOI.
- Para mudanças, exigir produtos distintos e área/CRS comuns. Para volume, registrar superfície, datum/cota e polígono. Para hidrologia, identificar DTM/DSM e exutório.
- Revalidar hidrologia contra referência independente em mais de uma área e com dados de elevação apropriados; manter status demonstrativo até atingir tolerâncias de aceite definidas. Um benchmark LiDAR externo não substitui validação de DTM fotogramétrico.
- Verificar tarefas em fila, estado terminal, reabertura da UI, erros de entrada e publicação do produto.

**Aceite:** cada análise aprovada produz saída reproduzível e semanticamente correta para sua entrada; limitações ficam junto do resultado. Algoritmo sem referência suficiente permanece explicitamente experimental/reprovado para aceite operacional.  
**Evidência:** uma sequência de tela por análise com formulário preenchido, execução e resultado visível, ligada a tabela numérica e referência usada.

### Fase 7 — Copiloto, conversas e ferramentas

**Objetivo:** avaliar o Copiloto web como capacidade separada da fila de análises.

**Atividades:**

- Definir o escopo final do UC de Copiloto: contexto do projeto, histórico por usuário, perguntas analíticas, ferramentas consultivas e ações com aprovação.
- Testar conversas independentes entre usuários, continuidade após recarga, projeto selecionado, citações/IDs de dados usados e tratamento de contexto ausente.
- Testar perguntas que exigem consulta real a camadas/produtos, confirmação antes de mutações, erros/timeouts e respostas sem inventar resultados.
- Registrar modelo e provedor usados apenas se configurados para execução; não fazer chamadas a um modelo proibido/ocupado nem inferir que o modelo de Codex responde ao usuário final.
- Manter RAG fora desta conclusão se continua deliberadamente postergado; não marcar requisito de RAG como implementado.

**Aceite:** respostas referenciam corretamente projeto/dados, ferramentas executam a operação esperada, conversas ficam isoladas por usuário e ações de escrita seguem aprovação.  
**Evidência:** Playwright com prompts, resposta completa, ferramenta/entrada/saída e registros persistidos; consumo externo documentado quando aplicável.

### Fase 8 — Robustez, monitoramento e fechamento do aceite

**Objetivo:** provar funcionamento integrado, recuperação e rastreabilidade do que será entregue.

**Atividades:**

- Executar o roteiro final com projeto limpo desde login até produtos, mapa, análise e exportação; adicionar Copiloto somente como ramo separado do fluxo.
- Exercitar recarga, falha de API/ODM, tarefa longa, erro de upload, armazenamento insuficiente simulado com segurança, sessão expirada e retomada.
- Verificar logs/telemetria sem expor tokens, erros acionáveis, limites de arquivo/tempo e ausência de resíduos de dados temporários.
- Reexecutar os testes automatizados relevantes e verificar diferenças entre matriz, código, API e interface.
- Gerar relatório incremental consolidado e pacote de evidências; listar pendências aceitas conscientemente e bloquear declaração de “concluído” se um critério obrigatório falhar.

**Aceite final:** todos os UCs de escopo estão aprovados com evidência atual ou têm exclusão/limitação formalmente registrada; nenhuma reprovação crítica fica escondida; roteiro ponta a ponta pode ser repetido por outra pessoa.  
**Evidência:** relatório final MD/PDF, capturas únicas por cena, logs redigidos, dados/manifests e tabela de aceite.

## 5. Matriz incremental de execução

Esta tabela começa como plano. “Obtido” e “Resultado” permanecem pendentes até a execução documentada; não preencher com resultados presumidos.

| Fase | Estado inicial | Esperado / critério de saída | Obtido e evidência | Resultado |
|---|---|---|---|---|
| 1. Baseline e rastreabilidade | Concluída (documental) | Matriz reconciliada, UC-020 desambiguado, ambiente inventariado | [Relatório e matriz da Fase 1](../validacao/ortomapas_conclusao/etapa-01/relatorio.md) | Aprovada como baseline; não é aceite operacional |
| 2. Usuários, projetos e autorização | Concluída no escopo testado | Duas contas; projeto, voo, ortomapa, arquivo e ticket isolados; persistência e cleanup conferidos | [Relatório e capturas da Fase 2](../validacao/ortomapas_conclusao/etapa-02/relatorio.md) | Aprovada para endpoints testados; matriz completa de papéis segue limitada |
| 3. NodeODM ponta a ponta | Concluída no escopo | Ciclo fotogramétrico real e cenários de robustez; fixture identificada como tal | [Relatório, 19 capturas reais e complemento Playwright](../validacao/ortomapas_conclusao/etapa-03/relatorio.md) | Aprovada no escopo; limites explicitados |
| 4. Mapa 2D e exportação | Executada | Ortofoto, DSM/DTM, camadas, comparação e GeoTIFF de origem em dados reais | [Relatório e 9 capturas da Fase 4](../validacao/ortomapas_conclusao/etapa-04/relatorio.md) | Aprovada no escopo raster; comparação não temporal; demais formatos/serviços não reexecutados |
| 5. Visualização 3D | Executada | DSM, DTM, GLB e LAZ reais; metadados, extensão, controles e seleção conferidos | [Relatório e 5 capturas da Fase 5](../validacao/ortomapas_conclusao/etapa-05/relatorio.md) | Aprovada na pré-visualização; grade DSM/DTM reduzida; GLB sem aceite de georreferenciamento |
| 6. Análises espaciais | Executada como auditoria da matriz UC-005–012 | Produtos persistidos conferidos, recálculos independentes, oito telas Playwright e limites de aceite por caso de uso | [Relatório, manifesto e capturas da Fase 6](../validacao/ortomapas_conclusao/etapa-06/relatorio.md) | Executada; UC-009 parcial (sem campanhas reais independentes), UC-010 sem acurácia semântica e UC-011 demonstrativo sem referência hidrográfica local; restante aprovado no escopo matemático/visual |
| 7. Copiloto | Executada com Playwright e Anthropic Sonnet 5.5 | Medição e contexto corretos, buffer só persiste após aprovação, histórico/memória e privacidade | [Relatório, JSON e 13 capturas](../validacao/ortomapas_conclusao/etapa-07/relatorio.md) | Aprovada no escopo executado; 8 chamadas no total incluindo tentativa exploratória; custo estimado US$ 0,088184; produtos de Guarajuba são sintéticos; RAG e robustez ampla seguem pendentes |
| 8. Robustez e aceite final | Concluída no escopo executado; aceite global retido | F8-01–07 resilientes e integrados em projeto #88; F8-08: Prometheus/Grafana/OTel ativos, target `up=1`, dashboard sem erro JS, série TSDB retida após reinício Prometheus e suíte pytest 144 passed/1 skipped. Matriz reconciliada: UC-009/010/011/020/024/026/029 seguem parciais ou não aceitos. Dados ODM públicos Aukerman, não Guarajuba; sem precisão de campo/GCP | [Relatório, manifesto e capturas da Fase 8](../validacao/ortomapas_conclusao/etapa-08/relatorio.md) | Etapa 8 concluída; produto global ainda não aceito por gaps de UC documentados |
| 9. Fechamento dos UCs parciais | Em andamento — 9.1 concluída parcialmente | Direção D8, acumulação D8 e TWI conectadas à fila e executadas em DTM ODM real; suíte 148/1 passou e build passou. API/DB/UI indisponíveis para Playwright; seguem pendentes confirmação visual/persistência, operações UC-020 restantes e validações independentes para UC-009/010/011/024/026/029 | [Relatório incremental e manifesto da etapa 9.1](../validacao/ortomapas_conclusao/etapa-08/relatorio.md) | Etapa 9/9 aberta; próxima subetapa 9.2 é Playwright com serviços ativos; aceite global retido |

## 6. Próxima etapa

**Etapas 1 a 8 concluídas dentro dos limites descritos.** A Fase 8 incluiu ciclo ODM integrado num projeto novo, visualização e exportação auditada; monitoramento e persistência TSDB; suíte Python (144 passou, 1 ignorado por depender de integração com banco real); e reconciliação explícita dos UCs. Isso fecha o plano de validação da Fase 8, mas não concede aceite operacional global.

**Próxima etapa: Etapa 9 de 9 — fechar os UCs que continuam parciais: UC-009, UC-010, UC-011, UC-020, UC-024, UC-026 e UC-029.** Subetapa 9.1 conectou direção D8, acumulação e TWI à fila e executou os workers no DTM ODM real #21; 148 testes passaram (1 ignorado), o build Vite passou. Subetapa 9.2 deve iniciar PostgreSQL/API/frontend/worker nesta cópia e validar esses três produtos pela interface com Playwright, tiles e capturas. Depois completar as capacidades de fila restantes do UC-020; definir referências independentes, tolerâncias e critérios quantitativos para mudança, classificação, hidrologia e qualidade; executar cancelamento/retry e reprocessamento real de modo controlado; e atualizar a matriz/relatório com evidências. A integração visual ficou pendente porque banco/API/frontend não responderam nesta execução. RAG permanece adiado conforme decisão de escopo. Não iniciar Android/drone ou simulador antes de decidir o aceite do Ortomapas.

**Esperado:** todo UC obrigatório aprovado com evidência atual, ou exclusão/limitação assinada; nenhum critério de precisão inferido apenas de consistência interna. **Obtido:** etapa 8 aprovada, sete UCs ainda parciais/não aceitos conforme relatório. **Resultado:** aceite global retido; próxima etapa 9/9.

Consulte o [relatório detalhado da Fase 8](../validacao/ortomapas_conclusao/etapa-08/relatorio.md), incluindo a matriz reconciliada e as evidências capturadas.

## 7. Referências internas

- [Casos de uso v2](casos_de_uso_v2.md)
- [Requisitos de integração ODM](integracao_odm_requisitos.md)
- [Plano anterior de revisão técnica e UI](plano_melhorias_funcionalidades_ui_2026-10-10.md)
- [Plano anterior de consolidação (três produtos)](plano_consolidacao_ortomapas_web_mobile_simulador_2026-10-20.md)
- [Aceite ODM em projeto novo e suas limitações](../validacao/odm_operacao_2026-11-05/aceite_projeto_novo/relatorio.md)
- [Relatório atual de UC-020/hidrologia](../validacao/uc020_benchmark_holston_2026-11-06/relatorio.md)
- [Validação de acesso ao catálogo GeoServer](../validacao/geoserver_catalogo_protegido_2026-11-05/)
- [Matriz de rastreabilidade da Fase 1](matriz_rastreabilidade_ortomapas_fase1.md)
- [Relatório de validação da Fase 1](../validacao/ortomapas_conclusao/etapa-01/relatorio.md)
- [Relatório de validação da Fase 2](../validacao/ortomapas_conclusao/etapa-02/relatorio.md)
- [Relatório de validação da Fase 6](../validacao/ortomapas_conclusao/etapa-06/relatorio.md)
- [Relatório de validação da Fase 7](../validacao/ortomapas_conclusao/etapa-07/relatorio.md)
- [Relatório parcial da Fase 8](../validacao/ortomapas_conclusao/etapa-08/relatorio.md)

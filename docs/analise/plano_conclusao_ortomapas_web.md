# Plano de conclusão do Ortomapas Web

**Data:** 10/11/2026
**Versão:** 1.0
**Situação em 20/11/2026:** Fase 9 (9.1–9.9) encerrada; aceite operacional global retido. Na Fase 10 proposta, 10.1 (recuperação real UC-024), 10.2 (fila UC-020) e 10.3 (comparação funcional de campanhas independentes UC-009) foram executadas; faltam quatro etapas propostas, 10.4–10.7. O UC-009 continua parcial em qualidade científica: o resultado RGB simples marcou 77,96% dos pixels acima do limiar numa série com contraste sazonal e sem verdade de campo.
**Escopo:** concluir, validar e documentar o produto web Ortomapas.

## 1. Objetivo e limites

Este plano organiza o trabalho restante para considerar o **Ortomapas Web** coerente com seus casos de uso e demonstrável com dados, resultados e evidências reproduzíveis. O simulador do drone próprio e o aplicativo Android para controle/captura são produtos separados e ficam fora deste plano.

O trabalho usa PostgreSQL/PostGIS como banco do Ortomapas, o NodeODM já disponível para fotogrametria, GeoServer quando necessário para publicação OGC, e Playwright para percorrer a interface. Nenhuma capacidade será considerada pronta somente porque existe código, endpoint, botão ou entrada na matriz: é necessário executar um fluxo representativo, verificar o resultado e registrar evidência.

## 2. Estado conhecido e cautelas

### Evidência já registrada

O relatório [aceite integrado em projeto novo](../validacao/odm_operacao_2026-11-05/aceite_projeto_novo/relatorio.md) documenta um fluxo real no NodeODM com projeto isolado e 77 fotos públicas Aukerman, todas com GPS EXIF. Foram importados ortomosaico, DSM, DTM, relatório, LAZ e GLB; abriram-se os visualizadores 2D/3D; calculou-se e persistiu-se declividade do DSM e do DTM. O GeoTIFF foi publicado e houve validação WMS/WMTS.

Essa evidência demonstra operação fotogramétrica com um conjunto público, **não** um voo próprio, nem um levantamento de Guarajuba/Condomínio Paraíso. A nota automática de qualidade 100% é baseada em presença de produtos e não representa acurácia posicional ou vertical. A recuperação de histórico do NodeODM foi testada com POST contra servidor HTTP simulado; não se deve relatar esse reenvio como reprocessamento real.

A matriz em [matriz_rastreabilidade_ortomapas_fase1.md](matriz_rastreabilidade_ortomapas_fase1.md) registra UC-020 com evidência funcional para K-Means RGB, índices RGB, terreno, hidrologia, mudança RGB e volume. A etapa 10.2 percorreu mudança e volume pela API autenticada, PostgreSQL, worker, catálogo e mapa. Isso comprova a integração da fila; não calibra a mudança temporal nem certifica o volume de campo. O UC-010 v2 define K-Means RGB; segmentação e classificação supervisionada não são critérios aprovados para UC-020 e não devem aparecer como executáveis na interface. UC-011 é uma análise opcional posterior que consome DTM/DSM; não é necessária para produzir ortomosaico.

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

**Como ler a numeração:** existem nove fases macro. A fase final é a **Fase 9 de 9** e foi dividida em nove subetapas numeradas **9.1 a 9.9**. Assim, “9.6” significa sexta subetapa da fase final; não significa “faltam 0,4 fases” nem “último passo”. Após concluir a 9.9, não restam subetapas numeradas neste plano; a conclusão documental da fase não equivale ao aceite operacional global.

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
| 9. Fechamento dos UCs parciais | Concluída como reconciliação; aceite operacional global retido | 9.1–9.8 mantêm seus resultados e limitações descritos neste histórico. Em 9.9, UC-029 foi reprocessado até conclusão no NodeODM real: versão #24 (v4) derivada de #21, 77 fotos, resolução-alvo 10 cm/pixel, seis produtos importados. Orto/DSM/DTM foram comparados em grade amostral alinhada; 262.144 pixels válidos em cada janela amostral de 512×512, orto 5,542 DN MAE / 7,817 DN RMSE, DSM 0,0419 m / 0,2884 m, DTM 0,0232 m / 0,0285 m. Os seis produtos #21 permaneceram. Playwright sem erros JS/console; erro de rótulo “Aguardando etapa” corrigido e retestado como “Executando no NodeODM” | [Relatório incremental, capturas Playwright, manifesto e scripts](../validacao/ortomapas_conclusao/etapa-08/relatorio.md) | Subetapas 9.1–9.9 encerradas; nenhuma subetapa numerada resta. UC-029 aprovado funcionalmente, sem aceite de acurácia. UC-009/011/020/024/026 e vários critérios de cobertura continuam parciais/não comprovados conforme matriz; aceite operacional global retido |

## 6. Fechamento da fase e estado de aceite

**Plano das subetapas 9.1–9.9 concluído. Restam zero etapas numeradas da Fase 9.** A última subetapa conciliou UC-011/UC-020 e pendências anteriores, e executou duas versões completas para UC-029. Isso conclui o plano de trabalho definido para a fase; não certifica o produto para uso operacional irrestrito.

### 9.9 — UC-029: reprocessamento completo e comparação versionada

O projeto #88 usa o conjunto público Aukerman (77 fotos preservadas; não é voo do usuário nem Guarajuba). A versão original #21 e a nova versão #24 foram concluídas pelo NodeODM 2.2.4 com ODM 3.5.6. A nova versão alterou `orthophoto-resolution` para 10 cm/pixel, foi registrada como versão 4 derivada de #21 e importou ortomosaico, DSM, DTM, relatório, nuvem LAZ e modelo 3D. O processo demorou 1.438.751 ms (~24 min). Os seis produtos originais de #21 continuaram no catálogo.

| Verificação | Esperado | Obtido | Resultado |
|---|---|---|---|
| Execução/linhagem | Tarefa termina; versão e pai persistidos; origem preservada | NodeODM status code 40, #24/v4, pai #21; ambos `concluido`; seis produtos originais antes/depois | Aprovado funcionalmente |
| Ortofoto | Aplicar 10 cm/pixel e comparar área/CRS | EPSG:32617; 0,049999 m/pixel na #21 e 0,100000 m/pixel na #24; sobreposição da extensão dos produtos 100%; amostra central de 512×512 totalmente válida; MAE 5,542 e RMSE 7,817 DN RGB | Aprovado para parâmetro e comparação descritiva; sem limiar radiométrico definido |
| DSM | Manter CRS/cobertura e medir diferença em grade alinhada | EPSG:32617, janela comum 512×512, 262.144 pixels válidos; MAE 0,0419 m, RMSE 0,2884 m, máximo 11,838 m | Diferença observada; sem referência altimétrica independente ou tolerância, não aprova acurácia |
| DTM | Manter CRS/cobertura e medir diferença em grade alinhada | EPSG:32617, janela comum 512×512, 262.144 pixels válidos; MAE 0,0232 m, RMSE 0,0285 m, máximo 0,2045 m | Diferença observada; sem referência altimétrica independente ou tolerância, não aprova acurácia |
| Nuvem | Produtos e versão acessíveis no catálogo | LAZ #21: 15.889.672 pontos; #24: 15.783.502 pontos | Importação/conferência funcional aprovada; diferença de densidade sem limiar de qualidade |
| Navegador | Fluxo visível sem falhas JS/console | Importação HTTP 200, produtos listados, `page_errors=[]`, `console_errors=[]` | Aprovado; capturas 06/07 abaixo |

As comparações de pixel/elevação são **descritivas**: duas execuções sobre as mesmas fotos não constituem duas campanhas nem validam a acurácia em relação ao terreno. Não havia GCP/checkpoints independentes ou limites de erro definidos; portanto não se declara precisão certificada.

![Tarefa #24 concluída antes da importação dos produtos](../etapa-09/playwright/uc029_reprocess/06_tarefa_concluida_antes_importar.png)

![Versão #24 importada, com estado final e produtos ODM no projeto](../etapa-09/playwright/uc029_reprocess/07_produtos_importados_comparacao.png)

As etapas do envio, do parâmetro, da fila, do progresso, da correção de rótulo e da conclusão estão nas [capturas Playwright UC-029](../etapa-09/playwright/uc029_reprocess/). O [manifesto JSON](../etapa-09/playwright/uc029_reprocess/manifest.json) registra parâmetros efetivos, processamento, produtos, estatísticas, critérios e ausência de erros. O roteiro de submissão e o finalizador reproduzível estão em [`tests/e2e/playwright`](../../../../tests/e2e/playwright/validate_uc029_completed_reprocess_phase9.py) e [`finalize_uc029_reprocess_phase9.py`](../../../../tests/e2e/playwright/finalize_uc029_reprocess_phase9.py).

### Reconciliação final da matriz

| Caso de uso | Decisão na 9.9 | Pendência explícita |
|---|---|---|
| UC-009 — mudanças | Parcial operacional; comparação RGB controlada demonstrada em 9.6 | Duas campanhas reais e independentes, registro e critérios para variação de iluminação/estação |
| UC-010 — classificação | K-Means RGB funcional nos dados testados; parcial para interpretação semântica | Ground truth rotulado, métricas de classe e validação de repetibilidade; RGB não equivale a classificação multiespectral |
| UC-011 — hidrologia | Fluxos D8, drenagem e bacia funcionam como análise demonstrativa; não aceito para engenharia/hidrologia operacional | DEM e rede de referência co-localizados, critério quantitativo acordado e validação independente |
| UC-020 — fila de análise | **Implementada com evidência** para o escopo de análises espaciais assíncronas aprovado | Nenhuma lacuna funcional de fila identificada no conjunto aprovado. Qualidade científica continua rastreada separadamente em UC-009/010/011/012. Segmentação e classificadores supervisionados não pertencem ao critério v2 do UC-020. Fila permanece distinta do Copiloto. |
| UC-024 — cancelar/repetir/recuperar | Cancelamento, idempotência e nova versão exercitados com NodeODM real | Rota dedicada `/recuperar` ainda não validada contra tarefa perdida no serviço real |
| UC-026 — qualidade | Indicador corrigido para “completude de produtos”; não é score de acurácia | Checkpoints/GCP e tolerâncias posicionais/verticais adequadas ao uso |
| UC-029 — reprocessar/comparar | **Aprovado funcionalmente**: #21/#24 concluídos, versão/linhagem, parâmetro aplicado, saídas comparadas, original preservado | Validação científica fica fora desta aprovação funcional e requer referência independente/tolerâncias |

A [matriz de rastreabilidade atualizada](../../analise/matriz_rastreabilidade_ortomapas_fase1.md) é a fonte da classificação detalhada por requisito/UC. As pendências acima não são novas etapas 9.x renomeadas: descrevem critérios de aceite que seguem abertos. Para conceder o aceite operacional global, é necessário fornecer/definir as referências e critérios indicados, implementar as operações ausentes do UC-020 e executar os testes correspondentes. Até isso ocorrer, o resultado global é **aceite retido**, não “tudo aprovado”. Android, controle do drone e simulador continuam em trilhas separadas, fora desta conclusão.

## 7. Plano pós-Fase 9 — fechamento operacional (Fase 10 proposta)

Este bloco inicia o trabalho após o encerramento da numeração 9.1–9.9. A **Fase 10 é uma continuação proposta** para tratar lacunas operacionais da matriz; não reabre nem renumera a Fase 9. Cada etapa exige entradas, critério esperado, resultado observado, evidência Playwright quando houver interação visual, atualização cumulativa MD/PDF e commit/push isolado.

| Etapa proposta | Caso(s) | Trabalho e critério de saída |
|---|---|---|
| **10.1 — Recuperação real NodeODM** | UC-024 | **Concluída:** tarefa #21 ausente confirmada no serviço real; as 77 fotos preservadas foram reenviadas uma vez. NodeODM concluiu #25 (code 40, 26 min 22 s); seis produtos importados; origem e seus seis produtos preservados. [Relatório e evidências](../validacao/ortomapas_conclusao/etapa-08/relatorio.md). |
| **10.2 — Cobertura da fila espacial** | UC-020 | **Concluída:** mudança RGB e volume por cota agora usam workers e persistem resultado/comparação. API, banco, fila, mapa, estatísticas e tiles autenticados foram exercitados com Playwright. O UC-010 v2 restringe classificação à K-Means RGB; segmentação e classificadores supervisionados não são requisitos de aceite e foram removidos do formulário de enfileiramento. [Relatório e evidências](../validacao/ortomapas_conclusao/etapa-10/uc020_queue_coverage/relatorio.md). |
| **10.3 — Comparação entre campanhas** | UC-009 | **Concluída funcionalmente:** duas campanhas independentes Aklavik 2022/2024 cadastradas e processadas via fila/API/Playwright. Mesmo CRS EPSG:32608, grade/resolução idênticas, sobreposição 100%, tarefa e comparação persistidas, tiles/resultados visíveis. O limiar RGB simples marcou 77,96% dos pixels (1.846.517,01 m²) acima do limiar. Isso não é área validada de mudança física: a amostra radiométrica difere entre estações, não há polígonos de referência, e o app não estima registro por feições nem corrige iluminação sazonal. [Relatório e evidências](../validacao/ortomapas_conclusao/etapa-10/uc009_independent_campaigns/relatorio.md). UC-009 segue parcialmente aceito cientificamente. |
| **10.4 — Qualidade semântica de classificação** | UC-010 | **Auditoria funcional encerrada; aceite semântico parcial.** K-Means executado em duas campanhas UAV reais (100% de repetibilidade) e pela UI/Playwright em projeto #90, AOI desenhada, análise #173 persistida, raster/tile e cinco grupos visíveis. Corrigido o caso de imagem uniforme que mostrava grupos vazios. Não foi possível obter máscara pública rotulada nesta sessão (DNS indisponível); não foram calculadas métricas semânticas nem atribuídos rótulos aos grupos. [Relatório, manifesto e capturas](../validacao/ortomapas_conclusao/etapa-10/uc010_semantic_quality/relatorio.md). |
| **10.5 — Validação hidrológica** | UC-011 | Encontrar DTM e hidrografia oficial co-localizados; definir método e tolerâncias antes de comparar drenagem/bacias. Sem referência compatível, limitar a conclusão a demonstração funcional. |
| **10.6 — Acurácia posicional/vertical** | UC-026 | Definir usos e tolerâncias; validar produtos contra checkpoints/GCP independentes, datum/CRS documentados e relatório reprodutível. |
| **10.7 — Regressão e aceite** | Matriz completa | Reexecutar casos obrigatórios alterados, fechar rastreabilidade, documentar exclusões aceitas e decidir formalmente o aceite operacional global. |

**Estado atualizado da Fase 10:** 10.1–10.4 concluídas no escopo de auditoria funcional. UC-010 segue parcial semanticamente por falta de referência rotulada; a etapa não atribuiu classes de cobertura nem calculou acurácia. A validação UC-009 usou duas campanhas UAV reais publicadas para o mesmo local em 2022/2024, ao contrário da comparação 10.2, que usou duas resoluções de uma só missão. O aplicativo produziu e exibiu a máscara, mas o dado não inclui verdade de campo e a grande proporção acima do limiar não pode ser interpretada como mudança física confirmada. Próxima: **10.5 de 7 — validação hidrológica (UC-011)**; restam três etapas propostas.

## 8. Referências internas

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

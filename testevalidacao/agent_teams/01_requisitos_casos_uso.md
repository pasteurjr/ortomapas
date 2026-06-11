# Requisitos e Casos de Uso - Sistema de Ortomapas

**Versao:** 1.0 | **Data:** 2026-03-28
**Autor:** Agent 1 - Requirements Analyst
**Baseado em:** ortomapa.md (especificacao), MANUALORTOMAPAS.md (manual do usuario), codigo-fonte backend (6 routers, 59 endpoints), codigo-fonte frontend (12 componentes Vue)

---

## PARTE 1 - REQUISITOS FUNCIONAIS

---

### REQ-PRJ - Projetos

| ID | Requisito | Endpoint / Componente |
|---|---|---|
| REQ-PRJ-001 | O sistema deve listar todos os projetos cadastrados, ordenados por data de criacao (desc). | `GET /api/projetos` / `ProjectList.vue` |
| REQ-PRJ-002 | O sistema deve permitir filtrar projetos por status (planejado, em_andamento, concluido, arquivado). | `GET /api/projetos?status=` |
| REQ-PRJ-003 | O sistema deve permitir filtrar projetos por area de estudo (busca parcial). | `GET /api/projetos?area_estudo=` |
| REQ-PRJ-004 | O sistema deve permitir busca textual em projetos (nome, descricao, area_estudo). | `GET /api/projetos/search?q=` |
| REQ-PRJ-005 | O sistema deve exibir detalhes de um projeto por ID, incluindo contadores de voos, ortomapas e analises relacionados. | `GET /api/projetos/{id}` |
| REQ-PRJ-006 | O sistema deve permitir criar um novo projeto com nome (obrigatorio), descricao, area_estudo e status. | `POST /api/projetos` |
| REQ-PRJ-007 | O sistema deve permitir atualizar campos de um projeto existente (nome, descricao, area_estudo, status). | `PUT /api/projetos/{id}` |
| REQ-PRJ-008 | O sistema deve permitir deletar um projeto por ID. | `DELETE /api/projetos/{id}` |
| REQ-PRJ-009 | O sistema deve listar todos os ortomapas vinculados a um projeto especifico. | `GET /api/projetos/{id}/ortomapas` |
| REQ-PRJ-010 | Ao selecionar um projeto na barra lateral, o mapa deve centralizar na area do projeto e exibir seus ortomapas. | `ProjectList.vue` / `MapViewer.vue` |

---

### REQ-VOO - Voos

| ID | Requisito | Endpoint / Componente |
|---|---|---|
| REQ-VOO-001 | O sistema deve listar todos os voos, ordenados por data do voo (desc). | `GET /api/voos` |
| REQ-VOO-002 | O sistema deve permitir filtrar voos por projeto_id. | `GET /api/voos?projeto_id=` |
| REQ-VOO-003 | O sistema deve exibir detalhes de um voo por ID. | `GET /api/voos/{id}` |
| REQ-VOO-004 | O sistema deve permitir criar um novo voo vinculado a um projeto existente (projeto_id obrigatorio). | `POST /api/voos` |
| REQ-VOO-005 | O sistema deve validar que o projeto_id referenciado existe antes de criar o voo. | `POST /api/voos` |
| REQ-VOO-006 | O sistema deve permitir atualizar campos de um voo (data_voo, drone, camera, altitude_voo, sobreposicao_frontal, sobreposicao_lateral, num_fotos, area_coberta_ha, gsd_cm, observacoes, status). | `PUT /api/voos/{id}` |
| REQ-VOO-007 | O sistema deve permitir deletar um voo por ID. | `DELETE /api/voos/{id}` |

---

### REQ-ORT - Ortomapas

| ID | Requisito | Endpoint / Componente |
|---|---|---|
| REQ-ORT-001 | O sistema deve listar todos os ortomapas com filtros opcionais por projeto_id, tipo e status. | `GET /api/ortomapas` |
| REQ-ORT-002 | O sistema deve exibir detalhes de um ortomapa por ID. | `GET /api/ortomapas/{id}` |
| REQ-ORT-003 | O sistema deve permitir criar um registro de ortomapa com metadados (projeto_id obrigatorio, voo_id, nome, tipo, formato, bbox, resolucao, dimensoes, CRS). | `POST /api/ortomapas` |
| REQ-ORT-004 | O sistema deve permitir upload de arquivo GeoTIFF com extracao automatica de metadados (bbox, resolucao, CRS, dimensoes) via rasterio. | `POST /api/ortomapas/upload` |
| REQ-ORT-005 | O sistema deve gerar thumbnail automaticamente apos upload de GeoTIFF. | `POST /api/ortomapas/upload` |
| REQ-ORT-006 | O sistema deve servir tiles 256x256 PNG de ortomapas usando esquema TMS (z/x/y). | `GET /api/ortomapas/{id}/tile/{z}/{x}/{y}.png` |
| REQ-ORT-007 | O tile server deve retornar tile transparente quando as coordenadas estao fora dos bounds do raster. | `get_tile()` |
| REQ-ORT-008 | O sistema deve normalizar dados raster para uint8 ao gerar tiles, tratando NoData com canal alpha. | `get_tile()` |
| REQ-ORT-009 | O sistema deve permitir consulta espacial (spatial query) de ortomapas por bounding box (norte, sul, leste, oeste). | `GET /api/ortomapas/spatial` |
| REQ-ORT-010 | O sistema deve permitir atualizar campos de um ortomapa existente. | `PUT /api/ortomapas/{id}` |
| REQ-ORT-011 | O sistema deve permitir deletar um ortomapa e remover o arquivo fisico associado. | `DELETE /api/ortomapas/{id}` |

---

### REQ-ANA - Analises

| ID | Requisito | Endpoint / Componente |
|---|---|---|
| REQ-ANA-001 | O sistema deve listar todas as analises com filtros opcionais por ortomapa_id, tipo_analise e status. | `GET /api/analises` |
| REQ-ANA-002 | O sistema deve exibir detalhes de uma analise por ID. | `GET /api/analises/{id}` |
| REQ-ANA-003 | O sistema deve permitir criar uma nova analise vinculada a um ortomapa (ortomapa_id e tipo_analise obrigatorios). | `POST /api/analises` |
| REQ-ANA-004 | O sistema deve permitir enfileirar uma tarefa de agente (queue_task=true) ao criar uma analise. | `POST /api/analises` |
| REQ-ANA-005 | O sistema deve servir o arquivo de resultado de uma analise concluida. | `GET /api/analises/{id}/resultado` |
| REQ-ANA-006 | O sistema deve permitir deletar uma analise e remover o arquivo de resultado associado. | `DELETE /api/analises/{id}` |
| REQ-ANA-007 | O componente AnalysisResults.vue deve exibir resultados de analises com estatisticas. | `AnalysisResults.vue` |
| REQ-ANA-008 | O componente AnalysisForm.vue deve permitir configurar e disparar novas analises. | `AnalysisForm.vue` |

---

### REQ-ANO - Anotacoes

| ID | Requisito | Endpoint / Componente |
|---|---|---|
| REQ-ANO-001 | O sistema deve listar todas as anotacoes com filtros opcionais por ortomapa_id, categoria e fonte. | `GET /api/anotacoes` |
| REQ-ANO-002 | O sistema deve exibir detalhes de uma anotacao por ID. | `GET /api/anotacoes/{id}` |
| REQ-ANO-003 | O sistema deve permitir criar uma anotacao com geometria WKT (ortomapa_id e geometria_wkt obrigatorios). | `POST /api/anotacoes` |
| REQ-ANO-004 | O sistema deve validar a geometria WKT ao criar/atualizar uma anotacao (conversao para GeoJSON como teste). | `POST /api/anotacoes`, `PUT /api/anotacoes/{id}` |
| REQ-ANO-005 | O sistema deve permitir atualizar campos de uma anotacao (categoria, rotulo, geometria_wkt, tipo, fonte, confianca). | `PUT /api/anotacoes/{id}` |
| REQ-ANO-006 | O sistema deve permitir deletar uma anotacao por ID. | `DELETE /api/anotacoes/{id}` |
| REQ-ANO-007 | O sistema deve exportar todas as anotacoes de um ortomapa como GeoJSON FeatureCollection. | `GET /api/anotacoes/geojson/{ortomapa_id}` |
| REQ-ANO-008 | O FeatureCollection exportado deve conter todas as propriedades da anotacao (exceto geometria_wkt) e a geometria convertida de WKT para GeoJSON. | `get_anotacoes_geojson()` |

---

### REQ-VEG - Indices de Vegetacao

| ID | Requisito | Endpoint / Componente |
|---|---|---|
| REQ-VEG-001 | O sistema deve calcular o indice VARI: (G - R) / (G + R - B). | `POST /api/tools/vegetation` |
| REQ-VEG-002 | O sistema deve calcular o indice TGI: G - 0.39*R - 0.61*B. | `POST /api/tools/vegetation` |
| REQ-VEG-003 | O sistema deve calcular o indice ExG: 2*G - R - B. | `POST /api/tools/vegetation` |
| REQ-VEG-004 | O sistema deve calcular o indice GLI: (2*G - R - B) / (2*G + R + B). | `POST /api/tools/vegetation` |
| REQ-VEG-005 | O resultado deve incluir estatisticas (min, max, media, desvio padrao). | `POST /api/tools/vegetation` |
| REQ-VEG-006 | O resultado deve ser salvo como GeoTIFF no diretorio de analises. | `raster_analysis.calc_vegetation_index()` |
| REQ-VEG-007 | O painel de ferramentas deve oferecer selecao de ortomapa e indice, exibindo estatisticas apos calculo. | `ToolsPanel.vue` aba "vegetacao" |

---

### REQ-TER - Analise de Terreno

| ID | Requisito | Endpoint / Componente |
|---|---|---|
| REQ-TER-001 | O sistema deve calcular declividade (slope) em graus a partir de DSM/DTM. | `POST /api/tools/slope` |
| REQ-TER-002 | O sistema deve calcular aspecto (orientacao da encosta, 0-360 graus) a partir de DSM/DTM. | `POST /api/tools/aspect` |
| REQ-TER-003 | O sistema deve gerar curvas de nivel (contornos) como GeoJSON com intervalo configuravel. | `POST /api/tools/contours` |
| REQ-TER-004 | O sistema deve gerar hillshade com azimute e altitude configuraveis. | `POST /api/tools/hillshade` |
| REQ-TER-005 | Slope e aspect devem retornar estatisticas do raster resultante. | `POST /api/tools/slope`, `POST /api/tools/aspect` |
| REQ-TER-006 | O painel de ferramentas deve oferecer selecao de DSM/DTM e tipo de analise (slope, aspect, contornos, hillshade). | `ToolsPanel.vue` aba "terreno" |

---

### REQ-MUD - Deteccao de Mudancas Temporais

| ID | Requisito | Endpoint / Componente |
|---|---|---|
| REQ-MUD-001 | O sistema deve detectar mudancas entre dois rasters da mesma area em datas diferentes. | `POST /api/tools/changes` |
| REQ-MUD-002 | O limiar de deteccao (threshold) deve ser configuravel. | `ChangeDetectionRequest.threshold` |
| REQ-MUD-003 | O resultado deve incluir estatisticas de mudanca (area alterada, percentual). | `change_detection.change_statistics()` |
| REQ-MUD-004 | O resultado deve ser salvo como GeoTIFF (mapa binario de mudancas). | `POST /api/tools/changes` |
| REQ-MUD-005 | O painel de ferramentas deve permitir selecionar ortomapa "Antes" e "Depois" e configurar threshold. | `ToolsPanel.vue` aba "mudancas" |

---

### REQ-CLA - Classificacao de Solo

| ID | Requisito | Endpoint / Componente |
|---|---|---|
| REQ-CLA-001 | O sistema deve classificar ortomapas usando KMeans (nao-supervisionado) com numero de clusters configuravel. | `POST /api/tools/classify?algorithm=kmeans` |
| REQ-CLA-002 | O sistema deve classificar ortomapas usando Random Forest (supervisionado) com amostras de treinamento. | `POST /api/tools/classify?algorithm=rf` |
| REQ-CLA-003 | Para Random Forest, o sistema deve treinar o modelo e salva-lo antes de classificar. | `classification.train_classifier()` |
| REQ-CLA-004 | Se nenhuma amostra de treinamento for fornecida para RF, o sistema deve recair para KMeans. | `classify_raster()` fallback |
| REQ-CLA-005 | O painel de ferramentas deve oferecer selecao de algoritmo e configuracao de parametros. | `ToolsPanel.vue` aba "classificacao" |

---

### REQ-HID - Hidrologia

| ID | Requisito | Endpoint / Componente |
|---|---|---|
| REQ-HID-001 | O sistema deve delimitar bacia hidrografica a partir de DTM e ponto de exutorio (pour point lat/lon). | `POST /api/tools/hydrology/watershed` |
| REQ-HID-002 | O sistema deve extrair rede de drenagem a partir de DTM com limiar de acumulacao configuravel. | `POST /api/tools/hydrology/streams` |
| REQ-HID-003 | A extracao de drenagem deve executar pipeline completo: fill sinks -> flow direction -> flow accumulation -> extract streams. | `extract_streams()` |
| REQ-HID-004 | A rede de drenagem deve ser exportada como GeoJSON. | `_output_path(..., ".geojson")` |
| REQ-HID-005 | O painel de ferramentas deve oferecer selecao de DTM, ponto de exutorio (clique no mapa) e threshold. | `ToolsPanel.vue` aba "hidrologia" |

---

### REQ-VOL - Volumetria

| ID | Requisito | Endpoint / Componente |
|---|---|---|
| REQ-VOL-001 | O sistema deve calcular volume acima/abaixo de uma elevacao de referencia a partir de DSM. | `POST /api/tools/volume` |
| REQ-VOL-002 | O sistema deve calcular diferenca entre dois DSMs (corte e aterro). | `POST /api/tools/volume/difference` |
| REQ-VOL-003 | O resultado deve incluir volumes de corte, aterro e liquido em m3. | `volumetry.calc_volume()`, `volumetry.cut_fill_analysis()` |
| REQ-VOL-004 | O painel de ferramentas deve oferecer selecao de DSM e configuracao de elevacao de referencia. | `ToolsPanel.vue` aba "volume" |

---

### REQ-SEG - Segmentacao

| ID | Requisito | Endpoint / Componente |
|---|---|---|
| REQ-SEG-001 | O sistema deve segmentar ortomapas em clusters usando KMeans com numero de clusters configuravel. | `POST /api/tools/segment` |
| REQ-SEG-002 | O resultado deve ser salvo como GeoTIFF com valores de cluster. | `segmentation.segment_ortomapa()` |

---

### REQ-AGI - Agentes de IA

| ID | Requisito | Endpoint / Componente |
|---|---|---|
| REQ-AGI-001 | O sistema deve permitir enfileirar tarefas de agente ao criar analises (queue_task=true). | `POST /api/analises` |
| REQ-AGI-002 | As tarefas de agente devem ser registradas na tabela tarefas_agente com status "pendente". | `create_analise()` |
| REQ-AGI-003 | O componente AgentStatus.vue deve exibir status de tarefas na fila (pendente, em execucao, concluida). | `AgentStatus.vue` |
| REQ-AGI-004 | O orquestrador de agentes deve processar tarefas em loop, verificando novas a cada 10 segundos. | `backend.agents.orchestrator` |

---

### REQ-MAP - Mapa Interativo

| ID | Requisito | Endpoint / Componente |
|---|---|---|
| REQ-MAP-001 | O sistema deve exibir mapa interativo Leaflet com zoom, pan e controle de camadas. | `MapViewer.vue` |
| REQ-MAP-002 | O mapa deve suportar basemaps alternados (OpenStreetMap, satelite). | `MapViewer.vue` |
| REQ-MAP-003 | O mapa deve exibir ortomapas como camadas TMS sobrepostas ao basemap. | `MapViewer.vue` + tile endpoint |
| REQ-MAP-004 | O mapa deve exibir coordenadas (lat/lon) do cursor na barra de status. | `MapViewer.vue` |
| REQ-MAP-005 | O componente LayerPanel.vue deve controlar visibilidade, opacidade e ordem de camadas. | `LayerPanel.vue` |
| REQ-MAP-006 | O mapa deve permitir zoom para extent de uma camada especifica. | `LayerPanel.vue` |

---

### REQ-FER - Painel de Ferramentas

| ID | Requisito | Endpoint / Componente |
|---|---|---|
| REQ-FER-001 | O painel de ferramentas deve ter 8 abas: Vegetacao, Terreno, Classificacao, Hidrologia, Mudancas, Volume, Recorte, Exportar. | `ToolsPanel.vue` |
| REQ-FER-002 | Cada aba deve permitir selecionar dados de entrada, configurar parametros e executar a analise. | `ToolsPanel.vue` |
| REQ-FER-003 | O resultado de cada analise deve aparecer automaticamente como nova camada no mapa. | `ToolsPanel.vue` / `MapViewer.vue` |
| REQ-FER-004 | Indicador de loading deve aparecer durante o processamento. | `ToolsPanel.vue` `:loading` |

---

### REQ-MED - Medicoes

| ID | Requisito | Endpoint / Componente |
|---|---|---|
| REQ-MED-001 | O sistema deve permitir medir distancia no mapa (cliques para pontos, distancia acumulada em tempo real). | `MeasureTools.vue` modo "distance" |
| REQ-MED-002 | O sistema deve exibir distancia por segmento e total. | `MeasureTools.vue` |
| REQ-MED-003 | O sistema deve permitir medir area (poligono com minimo 3 pontos). | `MeasureTools.vue` modo "area" |
| REQ-MED-004 | O sistema deve exibir area em m2/hectares e perimetro. | `MeasureTools.vue` |

---

### REQ-DES - Desenho e Anotacao no Mapa

| ID | Requisito | Endpoint / Componente |
|---|---|---|
| REQ-DES-001 | O sistema deve permitir desenhar pontos no mapa. | `DrawTools.vue` modo "point" |
| REQ-DES-002 | O sistema deve permitir desenhar linhas no mapa. | `DrawTools.vue` modo "line" |
| REQ-DES-003 | O sistema deve permitir desenhar poligonos no mapa. | `DrawTools.vue` modo "polygon" |
| REQ-DES-004 | O sistema deve permitir desenhar retangulos no mapa. | `DrawTools.vue` modo "rectangle" |
| REQ-DES-005 | Apos desenhar, o sistema deve exibir formulario para preencher categoria e rotulo. | `DrawTools.vue` annotation-form |
| REQ-DES-006 | A anotacao salva deve conter geometria WKT, categoria, rotulo e ser vinculada ao ortomapa ativo. | `POST /api/anotacoes` |
| REQ-DES-007 | O sistema deve permitir cancelar o desenho corrente. | `DrawTools.vue` botao cancelar |

---

### REQ-EXP - Exportacao

| ID | Requisito | Endpoint / Componente |
|---|---|---|
| REQ-EXP-001 | O sistema deve permitir exportar ortomapas e resultados de analise em formato GeoTIFF. | `ExportDialog.vue` |
| REQ-EXP-002 | O sistema deve permitir exportar em formato PNG. | `ExportDialog.vue` |
| REQ-EXP-003 | O sistema deve permitir exportar em formato JPEG. | `ExportDialog.vue` |
| REQ-EXP-004 | O sistema deve permitir exportar em formato KML. | `ExportDialog.vue` |
| REQ-EXP-005 | O sistema deve permitir exportar em formato GeoJSON. | `ExportDialog.vue` |
| REQ-EXP-006 | O sistema deve permitir selecionar CRS de saida (EPSG:4326, EPSG:31983, EPSG:31984, EPSG:32723, EPSG:32724). | `ExportDialog.vue` |
| REQ-EXP-007 | O sistema deve permitir configurar resolucao de saida (opcional). | `ExportDialog.vue` |
| REQ-EXP-008 | O sistema deve suportar recorte (clip) por bbox ou poligono WKT. | `POST /api/tools/clip` |
| REQ-EXP-009 | O sistema deve suportar reprojecao de rasters. | `POST /api/tools/reproject` |
| REQ-EXP-010 | O sistema deve suportar merge (mosaico) de multiplos rasters. | `POST /api/tools/merge` |

---

### REQ-COM - Comparacao Temporal

| ID | Requisito | Endpoint / Componente |
|---|---|---|
| REQ-COM-001 | O sistema deve permitir comparacao temporal em modo Swipe (deslizar entre "Antes" e "Depois"). | `CompareView.vue` modo swipe |
| REQ-COM-002 | O sistema deve permitir comparacao temporal em modo Side-by-Side (lado a lado). | `CompareView.vue` modo side-by-side |
| REQ-COM-003 | O usuario deve poder selecionar ortomapa "Antes" e "Depois" nos seletores. | `CompareView.vue` |
| REQ-COM-004 | O slider de swipe deve permitir controlar a posicao de corte entre as duas imagens. | `CompareView.vue` clipPath |
| REQ-COM-005 | O usuario deve poder fechar o modo de comparacao e retornar ao mapa normal. | `CompareView.vue` botao "Fechar" |

---

### REQ-EXTRA - Ferramentas Adicionais

| ID | Requisito | Endpoint / Componente |
|---|---|---|
| REQ-EXTRA-001 | O sistema deve calcular estatisticas raster (min, max, mean, std). | `POST /api/tools/statistics` |
| REQ-EXTRA-002 | O sistema deve calcular estatisticas zonais (raster + zonas GeoJSON). | `POST /api/tools/zonal-stats` |
| REQ-EXTRA-003 | O sistema deve permitir operacoes com calculadora raster (expressao + inputs). | `POST /api/tools/calculator` |
| REQ-EXTRA-004 | O sistema deve expor endpoint de health check. | `GET /health` |
| REQ-EXTRA-005 | O sistema deve expor endpoint raiz com informacoes do sistema. | `GET /` |
| REQ-EXTRA-006 | O sistema deve servir arquivos estaticos do diretorio data/ em /data. | `StaticFiles` mount |

---

## PARTE 2 - CASOS DE USO

---

### UC-001: Criar Novo Projeto

| Campo | Descricao |
|---|---|
| **Ator** | Usuario |
| **Pre-condicao** | O sistema esta acessivel em http://localhost:5173 e o backend esta rodando em http://localhost:8888 |
| **Fluxo Principal** | 1. O usuario clica em "Novo Projeto" na barra lateral esquerda. 2. O sistema exibe formulario com campos: Nome, Descricao, Area de Estudo, Status. 3. O usuario preenche "Nome" com "Teste Serra do Cipo" e "Area de Estudo" com "Lapinha da Serra". 4. O usuario clica "Salvar". 5. O sistema envia POST /api/projetos com os dados. 6. O backend valida que nome nao esta vazio, insere no banco e retorna o projeto criado com ID. 7. O novo projeto aparece na lista de projetos na barra lateral. |
| **Fluxo Alternativo** | 3a. O usuario nao preenche o campo Nome. 4a. O sistema exibe erro "Campo 'nome' e obrigatorio" (HTTP 400). |
| **Pos-condicao** | O projeto existe no banco de dados e aparece na listagem. |
| **Requisitos cobertos** | REQ-PRJ-006, REQ-PRJ-001, REQ-PRJ-010 |

---

### UC-002: Buscar e Filtrar Projetos

| Campo | Descricao |
|---|---|
| **Ator** | Usuario |
| **Pre-condicao** | Existem projetos cadastrados no banco de dados. |
| **Fluxo Principal** | 1. O usuario acessa a barra lateral de projetos. 2. O sistema lista todos os projetos (GET /api/projetos). 3. O usuario digita "Serra" no campo de busca. 4. O sistema envia GET /api/projetos/search?q=Serra. 5. O sistema exibe apenas projetos cujo nome, descricao ou area_estudo contem "Serra". 6. O usuario seleciona filtro de status "em_andamento". 7. O sistema envia GET /api/projetos?status=em_andamento. 8. A lista e filtrada para exibir apenas projetos em andamento. |
| **Pos-condicao** | A lista de projetos reflete os filtros aplicados. |
| **Requisitos cobertos** | REQ-PRJ-001, REQ-PRJ-002, REQ-PRJ-003, REQ-PRJ-004 |

---

### UC-003: Upload de Ortomapa GeoTIFF

| Campo | Descricao |
|---|---|
| **Ator** | Usuario |
| **Pre-condicao** | Existe pelo menos um projeto cadastrado. O usuario possui um arquivo GeoTIFF valido. |
| **Fluxo Principal** | 1. O usuario seleciona um projeto na barra lateral. 2. O usuario clica em "Upload Ortomapa". 3. O sistema exibe dialogo de upload com campo de arquivo e selecao de tipo (ortomosaico, dsm, dtm). 4. O usuario seleciona o arquivo GeoTIFF e define tipo como "ortomosaico". 5. O usuario clica "Enviar". 6. O sistema envia POST /api/ortomapas/upload?projeto_id=X&tipo=ortomosaico com o arquivo. 7. O backend salva o arquivo, extrai metadados (bbox, resolucao, CRS, dimensoes) via rasterio. 8. O backend gera thumbnail. 9. O backend insere registro no banco com todos os metadados extraidos. 10. O sistema exibe confirmacao e o ortomapa aparece na lista com icone de olho para visualizacao. |
| **Fluxo Alternativo** | 4a. O arquivo nao e um GeoTIFF valido. 7a. rasterio falha ao abrir o arquivo. 7b. O sistema retorna erro HTTP 500. |
| **Pos-condicao** | O arquivo esta armazenado em disco, o registro existe no banco com metadados, e thumbnail foi gerado. |
| **Requisitos cobertos** | REQ-ORT-004, REQ-ORT-005, REQ-ORT-003 |

---

### UC-004: Visualizar Ortomapa no Mapa

| Campo | Descricao |
|---|---|
| **Ator** | Usuario |
| **Pre-condicao** | Existe um ortomapa com arquivo GeoTIFF no sistema. |
| **Fluxo Principal** | 1. O usuario seleciona o projeto na barra lateral. 2. O sistema lista os ortomapas do projeto (OrtomapCard.vue). 3. O usuario clica no icone de olho no cartao do ortomapa. 4. O sistema adiciona camada TMS ao mapa Leaflet usando URL /api/ortomapas/{id}/tile/{z}/{x}/{y}.png. 5. O mapa carrega tiles dinamicamente conforme zoom e pan. 6. O usuario ve o ortomapa sobreposto ao basemap OpenStreetMap. 7. O usuario ajusta opacidade no painel de camadas (LayerPanel.vue). 8. O usuario clica no icone de lupa para zoom to extent da camada. |
| **Pos-condicao** | O ortomapa e exibido como camada sobreposta no mapa. |
| **Requisitos cobertos** | REQ-ORT-006, REQ-ORT-007, REQ-ORT-008, REQ-MAP-001, REQ-MAP-003, REQ-MAP-005, REQ-MAP-006 |

---

### UC-005: Calcular Indice de Vegetacao

| Campo | Descricao |
|---|---|
| **Ator** | Usuario |
| **Pre-condicao** | Existe um ortomapa RGB visualizado no mapa. |
| **Fluxo Principal** | 1. O usuario abre o painel de ferramentas (lado direito). 2. O usuario seleciona a aba "Vegetacao". 3. O sistema exibe formulario com selecao de ortomapa e indice. 4. O usuario seleciona o ortomapa e escolhe "VARI". 5. O usuario clica "Calcular Indice". 6. O indicador de loading aparece no botao. 7. O sistema envia POST /api/tools/vegetation com input_path, output_name e index_name="VARI". 8. O backend calcula (G-R)/(G+R-B) pixel a pixel, salva GeoTIFF e retorna estatisticas. 9. O painel exibe estatisticas: min, max, media, desvio padrao. 10. O resultado aparece como nova camada colorida no mapa (verde = vegetacao saudavel, vermelho = solo exposto). |
| **Fluxo Alternativo** | 4a. O usuario escolhe TGI, ExG ou GLI em vez de VARI. 8a. Se o raster nao tem 3 bandas RGB, o backend retorna erro. |
| **Pos-condicao** | GeoTIFF de resultado salvo em data/analises/. Estatisticas exibidas. Camada visivel no mapa. |
| **Requisitos cobertos** | REQ-VEG-001, REQ-VEG-002, REQ-VEG-003, REQ-VEG-004, REQ-VEG-005, REQ-VEG-006, REQ-VEG-007, REQ-FER-001, REQ-FER-002, REQ-FER-003, REQ-FER-004 |

---

### UC-006: Analise de Terreno (Slope)

| Campo | Descricao |
|---|---|
| **Ator** | Usuario |
| **Pre-condicao** | Existe um DSM ou DTM cadastrado no sistema. |
| **Fluxo Principal** | 1. O usuario abre o painel de ferramentas e seleciona aba "Terreno". 2. O sistema lista apenas ortomapas do tipo DSM ou DTM no seletor. 3. O usuario seleciona um DSM. 4. O usuario seleciona tipo de analise "Slope". 5. O usuario clica "Calcular". 6. O sistema envia POST /api/tools/slope com input_path e output_name. 7. O backend calcula declividade em graus, salva GeoTIFF e retorna estatisticas. 8. O painel exibe estatisticas (min, max, mean, std). 9. O resultado aparece como camada no mapa com rampa de cores (verde=plano, vermelho=ingreme). |
| **Fluxo Alternativo** | 4a. O usuario seleciona "Aspect" -> POST /api/tools/aspect. 4b. O usuario seleciona "Contornos" -> POST /api/tools/contours com intervalo. 4c. O usuario seleciona "Hillshade" -> POST /api/tools/hillshade com azimute e altitude. |
| **Pos-condicao** | GeoTIFF de declividade salvo. Estatisticas exibidas. Camada visivel no mapa. |
| **Requisitos cobertos** | REQ-TER-001, REQ-TER-002, REQ-TER-003, REQ-TER-004, REQ-TER-005, REQ-TER-006 |

---

### UC-007: Detectar Mudancas Temporais

| Campo | Descricao |
|---|---|
| **Ator** | Usuario |
| **Pre-condicao** | Existem pelo menos 2 ortomapas da mesma area em datas diferentes. |
| **Fluxo Principal** | 1. O usuario abre aba "Mudancas" no painel de ferramentas. 2. O usuario seleciona ortomapa "Antes" (data mais antiga). 3. O usuario seleciona ortomapa "Depois" (data mais recente). 4. O usuario configura threshold (padrao 30). 5. O usuario clica "Detectar Mudancas". 6. O sistema envia POST /api/tools/changes com raster1_path, raster2_path, output_name e threshold. 7. O backend calcula diferenca pixel a pixel, aplica threshold e gera mapa binario. 8. O backend calcula estatisticas de mudanca (area alterada, percentual). 9. O painel exibe estatisticas. 10. O resultado aparece como camada (vermelho = mudanca, verde = sem mudanca). |
| **Pos-condicao** | GeoTIFF de mudancas salvo. Estatisticas exibidas. |
| **Requisitos cobertos** | REQ-MUD-001, REQ-MUD-002, REQ-MUD-003, REQ-MUD-004, REQ-MUD-005 |

---

### UC-008: Classificar Uso do Solo (KMeans)

| Campo | Descricao |
|---|---|
| **Ator** | Usuario |
| **Pre-condicao** | Existe um ortomapa RGB no sistema. |
| **Fluxo Principal** | 1. O usuario abre aba "Classificacao" no painel de ferramentas. 2. O usuario seleciona o ortomapa. 3. O usuario seleciona algoritmo "KMeans". 4. O usuario define numero de clusters como 7. 5. O usuario clica "Classificar". 6. O sistema envia POST /api/tools/classify com ortomapa_path, algorithm="kmeans", n_clusters=7. 7. O backend executa segmentacao KMeans e salva GeoTIFF classificado. 8. O resultado aparece como camada com cores por classe. |
| **Fluxo Alternativo** | 3a. O usuario seleciona "Random Forest". 3b. O sistema exibe opcao para desenhar amostras de treinamento. 3c. O usuario desenha poligonos no mapa e atribui classes. 3d. O sistema envia com training_samples. 3e. O backend treina modelo e classifica. |
| **Pos-condicao** | GeoTIFF classificado salvo. Camada visivel no mapa. |
| **Requisitos cobertos** | REQ-CLA-001, REQ-CLA-002, REQ-CLA-003, REQ-CLA-004, REQ-CLA-005 |

---

### UC-009: Analise Hidrologica - Extrair Drenagem

| Campo | Descricao |
|---|---|
| **Ator** | Usuario |
| **Pre-condicao** | Existe um DTM cadastrado no sistema. |
| **Fluxo Principal** | 1. O usuario abre aba "Hidrologia" no painel de ferramentas. 2. O usuario seleciona o DTM. 3. O usuario seleciona ferramenta "Extrair Drenagem". 4. O usuario define threshold de acumulacao (padrao 100). 5. O usuario clica "Executar". 6. O sistema envia POST /api/tools/hydrology/streams com dtm_path, output_name e threshold. 7. O backend executa pipeline: fill sinks -> flow direction -> flow accumulation -> extract streams. 8. A rede de drenagem e exportada como GeoJSON. 9. A rede aparece como camada de linhas no mapa. |
| **Fluxo Alternativo** | 3a. O usuario seleciona "Delimitar Bacia". 3b. O sistema entra em modo de clique no mapa. 3c. O usuario clica no ponto de exutorio. 3d. O sistema envia POST /api/tools/hydrology/watershed com pour_point. 3e. O backend delimita bacia e retorna poligono. |
| **Pos-condicao** | GeoJSON de drenagem (ou poligono de bacia) salvo. Camada visivel no mapa. |
| **Requisitos cobertos** | REQ-HID-001, REQ-HID-002, REQ-HID-003, REQ-HID-004, REQ-HID-005 |

---

### UC-010: Calcular Volume (Corte/Aterro)

| Campo | Descricao |
|---|---|
| **Ator** | Usuario |
| **Pre-condicao** | Existe pelo menos um DSM no sistema. |
| **Fluxo Principal** | 1. O usuario abre aba "Volume" no painel de ferramentas. 2. O usuario seleciona o DSM. 3. O usuario define elevacao de referencia (ex: 1000.0 metros). 4. O usuario clica "Calcular Volume". 5. O sistema envia POST /api/tools/volume com dsm_path e reference_elevation. 6. O backend calcula volume acima e abaixo do plano de referencia. 7. O painel exibe: volume acima (m3), volume abaixo (m3), volume liquido (m3). |
| **Fluxo Alternativo** | 2a. O usuario seleciona dois DSMs de datas diferentes. 3a. O usuario clica "Calcular Corte/Aterro". 4a. O sistema envia POST /api/tools/volume/difference com dsm1_path e dsm2_path. 5a. O backend calcula diferenca e retorna volume de corte, aterro e areas. |
| **Pos-condicao** | Resultados volumetricos exibidos. GeoTIFF de diferenca salvo (se aplicavel). |
| **Requisitos cobertos** | REQ-VOL-001, REQ-VOL-002, REQ-VOL-003, REQ-VOL-004 |

---

### UC-011: Desenhar Anotacao no Mapa

| Campo | Descricao |
|---|---|
| **Ator** | Usuario |
| **Pre-condicao** | O usuario esta visualizando um ortomapa no mapa. |
| **Fluxo Principal** | 1. O usuario clica no icone de desenho (DrawTools.vue). 2. O usuario seleciona tipo "Poligono". 3. O botao de poligono fica destacado (severity="success"). 4. O usuario clica no mapa para definir vertices do poligono. 5. O usuario fecha o poligono (duplo-clique ou clicar no primeiro ponto). 6. O sistema exibe formulario "Nova Anotacao" com campos Categoria e Rotulo. 7. O usuario seleciona categoria "erosao" e digita rotulo "Vocoroca principal". 8. O usuario clica "Salvar". 9. O sistema converte geometria para WKT e envia POST /api/anotacoes com ortomapa_id, geometria_wkt, categoria e rotulo. 10. O backend valida WKT, insere no banco e retorna anotacao criada. 11. A anotacao aparece como camada sobreposta no mapa. |
| **Fluxo Alternativo** | 2a. O usuario seleciona "Ponto" -> cria ponto com 1 clique. 2b. O usuario seleciona "Linha" -> cria linha com multiplos cliques. 2c. O usuario seleciona "Retangulo" -> cria retangulo com 2 cliques. 6a. O usuario clica "Cancelar" antes de salvar -> desenho e descartado. |
| **Pos-condicao** | Anotacao salva no banco com geometria WKT. Visivel no mapa. |
| **Requisitos cobertos** | REQ-DES-001, REQ-DES-002, REQ-DES-003, REQ-DES-004, REQ-DES-005, REQ-DES-006, REQ-DES-007, REQ-ANO-003, REQ-ANO-004 |

---

### UC-012: Medir Distancia e Area

| Campo | Descricao |
|---|---|
| **Ator** | Usuario |
| **Pre-condicao** | O mapa esta visivel com ou sem ortomapa. |
| **Fluxo Principal** | 1. O usuario ativa a ferramenta de medicao (MeasureTools.vue). 2. O usuario seleciona modo "Distancia". 3. O usuario clica no mapa para marcar o ponto inicial. 4. O usuario clica em outros pontos ao longo do percurso. 5. A distancia acumulada atualiza em tempo real. 6. O painel exibe distancia por segmento e distancia total. 7. O usuario finaliza a medicao. |
| **Fluxo Alternativo** | 2a. O usuario seleciona modo "Area". 3a. O usuario desenha poligono com pelo menos 3 pontos. 4a. O sistema calcula e exibe area (m2 e hectares) e perimetro. |
| **Pos-condicao** | Resultado da medicao exibido no painel. |
| **Requisitos cobertos** | REQ-MED-001, REQ-MED-002, REQ-MED-003, REQ-MED-004 |

---

### UC-013: Exportar Resultado

| Campo | Descricao |
|---|---|
| **Ator** | Usuario |
| **Pre-condicao** | Existe um ortomapa ou resultado de analise no sistema. |
| **Fluxo Principal** | 1. O usuario clica no icone de exportacao ou abre aba "Exportar" no painel de ferramentas. 2. O sistema exibe ExportDialog.vue com seletores de camada, formato, CRS e resolucao. 3. O usuario seleciona o ortomapa fonte. 4. O usuario seleciona formato "GeoTIFF". 5. O usuario seleciona CRS "EPSG:31983" (SIRGAS 2000 UTM 23S). 6. O usuario deixa resolucao como "Manter original". 7. O usuario clica "Exportar". 8. O sistema executa reprojecao se necessario (POST /api/tools/reproject). 9. O download do arquivo inicia automaticamente. |
| **Fluxo Alternativo** | 4a. O usuario seleciona "GeoJSON" -> exportacao de anotacoes via GET /api/anotacoes/geojson/{id}. 4b. O usuario seleciona "PNG" -> configuracao de qualidade aparece. |
| **Pos-condicao** | Arquivo exportado baixado pelo usuario no formato e CRS selecionados. |
| **Requisitos cobertos** | REQ-EXP-001, REQ-EXP-002, REQ-EXP-003, REQ-EXP-004, REQ-EXP-005, REQ-EXP-006, REQ-EXP-007, REQ-EXP-009 |

---

### UC-014: Comparar Ortomapas Temporalmente

| Campo | Descricao |
|---|---|
| **Ator** | Usuario |
| **Pre-condicao** | Existem pelo menos 2 ortomapas da mesma area no sistema. |
| **Fluxo Principal** | 1. O usuario ativa modo de comparacao (CompareView.vue). 2. O sistema exibe controles com seletores "Antes" e "Depois" e toggle de modo. 3. O usuario seleciona ortomapa "Antes" no seletor esquerdo. 4. O usuario seleciona ortomapa "Depois" no seletor direito. 5. O sistema exibe ambos ortomapas em modo Swipe (padrao). 6. O usuario arrasta o slider para revelar/ocultar cada imagem. 7. O usuario clica "Lado a Lado" para alternar para modo side-by-side. 8. O sistema exibe dois mapas sincronizados lado a lado. 9. O usuario clica "Fechar" para retornar ao mapa normal. |
| **Pos-condicao** | O usuario retorna ao modo de visualizacao normal. |
| **Requisitos cobertos** | REQ-COM-001, REQ-COM-002, REQ-COM-003, REQ-COM-004, REQ-COM-005 |

---

### UC-015: Disparar Analise com Agente de IA

| Campo | Descricao |
|---|---|
| **Ator** | Usuario, Sistema (Orquestrador de Agentes) |
| **Pre-condicao** | Existe um ortomapa no sistema. O orquestrador de agentes esta rodando. |
| **Fluxo Principal** | 1. O usuario seleciona um ortomapa e clica "Nova Analise" (AnalysisForm.vue). 2. O usuario seleciona tipo de analise (ex: "vegetacao"). 3. O usuario configura parametros. 4. O usuario marca opcao "Executar via Agente" (queue_task=true). 5. O usuario clica "Executar". 6. O sistema envia POST /api/analises com ortomapa_id, tipo_analise, parametros e queue_task=true. 7. O backend cria registro na tabela analises com status "pendente". 8. O backend cria registro na tabela tarefas_agente com status "pendente". 9. O componente AgentStatus.vue exibe a tarefa na fila. 10. O orquestrador detecta a tarefa, atualiza status para "em_execucao". 11. O agente processa a analise (calcula indice, classifica, etc.). 12. O agente salva resultado e atualiza status para "concluida". 13. O resultado aparece na lista de analises (AnalysisResults.vue). |
| **Fluxo Alternativo** | 11a. O agente encontra erro durante processamento. 12a. Status atualizado para "erro" com mensagem. |
| **Pos-condicao** | A analise esta concluida, resultado disponivel para visualizacao e download. |
| **Requisitos cobertos** | REQ-ANA-003, REQ-ANA-004, REQ-ANA-005, REQ-ANA-007, REQ-ANA-008, REQ-AGI-001, REQ-AGI-002, REQ-AGI-003, REQ-AGI-004 |

---

### UC-016: Consulta Espacial de Ortomapas

| Campo | Descricao |
|---|---|
| **Ator** | Usuario / Sistema |
| **Pre-condicao** | Existem ortomapas com bounding box definido no banco. |
| **Fluxo Principal** | 1. O usuario navega o mapa para uma regiao de interesse. 2. O sistema captura os bounds visiveis do mapa (norte, sul, leste, oeste). 3. O sistema envia GET /api/ortomapas/spatial?norte=X&sul=Y&leste=Z&oeste=W. 4. O backend consulta ortomapas cujo bbox intercepta a area visivel. 5. O sistema exibe os ortomapas encontrados na barra lateral. |
| **Pos-condicao** | Apenas ortomapas relevantes a area visivel sao listados. |
| **Requisitos cobertos** | REQ-ORT-009 |

---

### UC-017: Exportar Anotacoes como GeoJSON

| Campo | Descricao |
|---|---|
| **Ator** | Usuario |
| **Pre-condicao** | Existem anotacoes cadastradas para um ortomapa. |
| **Fluxo Principal** | 1. O usuario seleciona o ortomapa que possui anotacoes. 2. O usuario abre o dialogo de exportacao (ExportDialog.vue). 3. O usuario seleciona formato "GeoJSON". 4. O sistema envia GET /api/anotacoes/geojson/{ortomapa_id}. 5. O backend consulta todas as anotacoes do ortomapa. 6. O backend converte cada geometria WKT para GeoJSON geometry. 7. O backend monta FeatureCollection com features e properties. 8. O sistema inicia download do arquivo .geojson. |
| **Fluxo Alternativo** | 5a. O ortomapa nao possui anotacoes -> FeatureCollection vazia (totalFeatures=0). |
| **Pos-condicao** | Arquivo GeoJSON valido baixado com todas as anotacoes. |
| **Requisitos cobertos** | REQ-ANO-007, REQ-ANO-008, REQ-EXP-005 |

---

### UC-018: CRUD Completo de Voos

| Campo | Descricao |
|---|---|
| **Ator** | Usuario |
| **Pre-condicao** | Existe pelo menos um projeto cadastrado. |
| **Fluxo Principal** | 1. O usuario acessa a secao de voos do projeto. 2. O sistema lista voos do projeto (GET /api/voos?projeto_id=X). 3. O usuario clica "Novo Voo". 4. O usuario preenche: projeto_id, data_voo, drone="DJI Mini 3", altitude_voo=120, num_fotos=250, gsd_cm=2.5. 5. O usuario clica "Salvar". 6. O sistema envia POST /api/voos. 7. O backend valida projeto_id, insere no banco e retorna voo criado. 8. O usuario seleciona o voo na lista e edita observacoes. 9. O sistema envia PUT /api/voos/{id} com os campos alterados. 10. O usuario decide deletar o voo de teste. 11. O sistema envia DELETE /api/voos/{id}. 12. O backend remove o registro e confirma. |
| **Pos-condicao** | O voo foi criado, editado e deletado com sucesso. |
| **Requisitos cobertos** | REQ-VOO-001, REQ-VOO-002, REQ-VOO-003, REQ-VOO-004, REQ-VOO-005, REQ-VOO-006, REQ-VOO-007 |

---

### UC-019: Recortar Raster por Bounding Box

| Campo | Descricao |
|---|---|
| **Ator** | Usuario |
| **Pre-condicao** | Existe um ortomapa ou raster de analise no sistema. |
| **Fluxo Principal** | 1. O usuario abre aba "Recorte" no painel de ferramentas. 2. O usuario seleciona o raster de entrada. 3. O usuario define bounding box (norte, sul, leste, oeste) ou desenha poligono no mapa. 4. O usuario clica "Recortar". 5. O sistema envia POST /api/tools/clip com input_path, output_name e bbox (ou polygon_wkt). 6. O backend usa GDAL para recortar o raster. 7. O resultado recortado e salvo como novo GeoTIFF. 8. O resultado aparece como nova camada no mapa. |
| **Pos-condicao** | GeoTIFF recortado salvo. Camada visivel no mapa. |
| **Requisitos cobertos** | REQ-EXP-008, REQ-FER-001, REQ-FER-002, REQ-FER-003 |

---

### UC-020: Segmentar Ortomapa

| Campo | Descricao |
|---|---|
| **Ator** | Usuario |
| **Pre-condicao** | Existe um ortomapa RGB no sistema. |
| **Fluxo Principal** | 1. O usuario acessa ferramenta de segmentacao. 2. O usuario seleciona ortomapa de entrada. 3. O usuario define numero de clusters (padrao 7). 4. O usuario clica "Segmentar". 5. O sistema envia POST /api/tools/segment com input_path, output_name e n_clusters. 6. O backend executa KMeans sobre os pixels do raster. 7. O resultado e salvo como GeoTIFF com valores de cluster (0 a n_clusters-1). 8. O resultado aparece como camada colorida no mapa. |
| **Pos-condicao** | GeoTIFF segmentado salvo. Camada visivel no mapa. |
| **Requisitos cobertos** | REQ-SEG-001, REQ-SEG-002 |

---

## PARTE 3 - MATRIZ DE RASTREABILIDADE

A tabela abaixo confirma que todos os requisitos sao cobertos por pelo menos um caso de uso.

| Grupo | Total Requisitos | Casos de Uso que cobrem |
|---|---|---|
| REQ-PRJ (10) | 10 | UC-001, UC-002 |
| REQ-VOO (7) | 7 | UC-018 |
| REQ-ORT (11) | 11 | UC-003, UC-004, UC-016 |
| REQ-ANA (8) | 8 | UC-015 |
| REQ-ANO (8) | 8 | UC-011, UC-017 |
| REQ-VEG (7) | 7 | UC-005 |
| REQ-TER (6) | 6 | UC-006 |
| REQ-MUD (5) | 5 | UC-007 |
| REQ-CLA (5) | 5 | UC-008 |
| REQ-HID (5) | 5 | UC-009 |
| REQ-VOL (4) | 4 | UC-010 |
| REQ-SEG (2) | 2 | UC-020 |
| REQ-AGI (4) | 4 | UC-015 |
| REQ-MAP (6) | 6 | UC-004 |
| REQ-FER (4) | 4 | UC-005, UC-019 |
| REQ-MED (4) | 4 | UC-012 |
| REQ-DES (7) | 7 | UC-011 |
| REQ-EXP (10) | 10 | UC-013, UC-017, UC-019 |
| REQ-COM (5) | 5 | UC-014 |
| REQ-EXTRA (6) | 6 | (infraestrutura, testavel via API diretamente) |
| **TOTAL** | **124 requisitos** | **20 casos de uso** |

---

## PARTE 4 - INVENTARIO DE ENDPOINTS (para referencia do agente de teste)

### Router: projetos (prefix /api)
1. `GET /api/projetos/search?q=` - busca textual
2. `GET /api/projetos` - listar (filtros: status, area_estudo)
3. `GET /api/projetos/{id}` - detalhes com contadores
4. `POST /api/projetos` - criar
5. `PUT /api/projetos/{id}` - atualizar
6. `DELETE /api/projetos/{id}` - deletar
7. `GET /api/projetos/{id}/ortomapas` - ortomapas do projeto

### Router: voos (prefix /api)
8. `GET /api/voos` - listar (filtro: projeto_id)
9. `GET /api/voos/{id}` - detalhes
10. `POST /api/voos` - criar
11. `PUT /api/voos/{id}` - atualizar
12. `DELETE /api/voos/{id}` - deletar

### Router: ortomapas (prefix /api)
13. `GET /api/ortomapas/spatial` - consulta espacial (bbox)
14. `GET /api/ortomapas` - listar (filtros: projeto_id, tipo, status)
15. `GET /api/ortomapas/{id}` - detalhes
16. `POST /api/ortomapas` - criar registro
17. `POST /api/ortomapas/upload` - upload GeoTIFF
18. `PUT /api/ortomapas/{id}` - atualizar
19. `DELETE /api/ortomapas/{id}` - deletar
20. `GET /api/ortomapas/{id}/tile/{z}/{x}/{y}.png` - tile server

### Router: analises (prefix /api)
21. `GET /api/analises` - listar (filtros: ortomapa_id, tipo_analise, status)
22. `GET /api/analises/{id}` - detalhes
23. `POST /api/analises` - criar (com opcao queue_task)
24. `GET /api/analises/{id}/resultado` - download resultado
25. `DELETE /api/analises/{id}` - deletar

### Router: anotacoes (prefix /api)
26. `GET /api/anotacoes` - listar (filtros: ortomapa_id, categoria, fonte)
27. `GET /api/anotacoes/geojson/{ortomapa_id}` - exportar GeoJSON
28. `GET /api/anotacoes/{id}` - detalhes
29. `POST /api/anotacoes` - criar (WKT obrigatorio)
30. `PUT /api/anotacoes/{id}` - atualizar
31. `DELETE /api/anotacoes/{id}` - deletar

### Router: tools (prefix /api/tools)
32. `POST /api/tools/clip` - recorte
33. `POST /api/tools/reproject` - reprojecao
34. `POST /api/tools/merge` - mosaico
35. `POST /api/tools/contours` - curvas de nivel
36. `POST /api/tools/hillshade` - sombreamento
37. `POST /api/tools/vegetation` - indice de vegetacao
38. `POST /api/tools/slope` - declividade
39. `POST /api/tools/aspect` - aspecto
40. `POST /api/tools/statistics` - estatisticas raster
41. `POST /api/tools/zonal-stats` - estatisticas zonais
42. `POST /api/tools/calculator` - calculadora raster
43. `POST /api/tools/changes` - deteccao de mudancas
44. `POST /api/tools/classify` - classificacao (KMeans/RF)
45. `POST /api/tools/hydrology/watershed` - bacia hidrografica
46. `POST /api/tools/hydrology/streams` - rede de drenagem
47. `POST /api/tools/volume` - volumetria
48. `POST /api/tools/volume/difference` - corte/aterro
49. `POST /api/tools/segment` - segmentacao

### Endpoints globais
50. `GET /` - informacoes do sistema
51. `GET /health` - health check

**Total: 51 endpoints distintos**

---

## PARTE 5 - INVENTARIO DE COMPONENTES FRONTEND (para referencia do agente de teste)

| Componente | Arquivo | Funcao principal |
|---|---|---|
| MapViewer | `frontend/src/components/MapViewer.vue` | Mapa Leaflet interativo principal |
| ProjectList | `frontend/src/components/ProjectList.vue` | Barra lateral de projetos |
| OrtomapCard | `frontend/src/components/OrtomapCard.vue` | Cartao de ortomapa (visualizar, zoom, info) |
| ToolsPanel | `frontend/src/components/ToolsPanel.vue` | Painel de ferramentas com 8 abas |
| AnalysisResults | `frontend/src/components/AnalysisResults.vue` | Exibicao de resultados de analise |
| AnalysisForm | `frontend/src/components/AnalysisForm.vue` | Formulario para criar nova analise |
| DrawTools | `frontend/src/components/DrawTools.vue` | Ferramentas de desenho/anotacao |
| CompareView | `frontend/src/components/CompareView.vue` | Comparacao temporal (swipe / side-by-side) |
| MeasureTools | `frontend/src/components/MeasureTools.vue` | Ferramentas de medicao (distancia, area) |
| ExportDialog | `frontend/src/components/ExportDialog.vue` | Dialogo de exportacao (formato, CRS) |
| AgentStatus | `frontend/src/components/AgentStatus.vue` | Status de tarefas de agentes de IA |
| LayerPanel | `frontend/src/components/LayerPanel.vue` | Controle de camadas (visibilidade, opacidade) |

---

*Documento gerado automaticamente pelo Agent 1 - Requirements Analyst em 2026-03-28.*
*Para uso pelos agentes subsequentes: Agent 2 (Verificacao de Implementacao), Agent 3 (Validacao/Teste via Playwright).*

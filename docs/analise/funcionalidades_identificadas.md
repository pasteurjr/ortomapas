# Funcionalidades Identificadas - Sistema de Ortomapas

**Data da analise:** 2026-03-28
**Versao do sistema:** 1.0.0

---

## 1. Gestao de Projetos

| ID | Funcionalidade | Endpoint | Componente Frontend |
|----|---------------|----------|---------------------|
| F-PRJ-01 | Listar projetos com filtros (status, area) | `GET /api/projetos` | `ProjectList.vue` |
| F-PRJ-02 | Buscar projetos (fulltext: nome, descricao, area) | `GET /api/projetos/search?q=` | `App.vue` (search input) |
| F-PRJ-03 | Detalhar projeto com contagens relacionadas | `GET /api/projetos/{id}` | `ProjectList.vue` |
| F-PRJ-04 | Criar projeto | `POST /api/projetos` | `ProjectList.vue` |
| F-PRJ-05 | Atualizar projeto | `PUT /api/projetos/{id}` | `ProjectList.vue` |
| F-PRJ-06 | Excluir projeto | `DELETE /api/projetos/{id}` | `ProjectList.vue` |
| F-PRJ-07 | Listar ortomapas de um projeto | `GET /api/projetos/{id}/ortomapas` | `OrtomapCard.vue` |

---

## 2. Gestao de Voos

| ID | Funcionalidade | Endpoint | Componente Frontend |
|----|---------------|----------|---------------------|
| F-VOO-01 | Listar voos com filtro por projeto | `GET /api/voos?projeto_id=` | `VoosList.vue` |
| F-VOO-02 | Detalhar voo | `GET /api/voos/{id}` | `VoosList.vue` |
| F-VOO-03 | Registrar voo (22 campos) | `POST /api/voos` | `VoosList.vue` |
| F-VOO-04 | Atualizar voo | `PUT /api/voos/{id}` | `VoosList.vue` |
| F-VOO-05 | Excluir voo | `DELETE /api/voos/{id}` | `VoosList.vue` |

---

## 3. Gestao de Ortomapas

| ID | Funcionalidade | Endpoint | Componente Frontend |
|----|---------------|----------|---------------------|
| F-ORT-01 | Listar ortomapas (filtros: projeto, tipo, status) | `GET /api/ortomapas` | `OrtomapCard.vue` |
| F-ORT-02 | Detalhar ortomapa | `GET /api/ortomapas/{id}` | `OrtomapCard.vue` |
| F-ORT-03 | Criar registro de ortomapa | `POST /api/ortomapas` | `OrtomapCard.vue` |
| F-ORT-04 | Upload GeoTIFF com extracao automatica de metadados | `POST /api/ortomapas/upload` | `OrtomapCard.vue` |
| F-ORT-05 | Atualizar ortomapa | `PUT /api/ortomapas/{id}` | `OrtomapCard.vue` |
| F-ORT-06 | Excluir ortomapa (deleta arquivo se existir) | `DELETE /api/ortomapas/{id}` | `OrtomapCard.vue` |
| F-ORT-07 | Servir tiles 256x256 (TMS) | `GET /api/ortomapas/{id}/tile/{z}/{x}/{y}.png` | `MapViewer.vue` |
| F-ORT-08 | Consulta espacial por bounding box | `GET /api/ortomapas/spatial?norte&sul&leste&oeste` | - |

---

## 4. Gestao de Analises

| ID | Funcionalidade | Endpoint | Componente Frontend |
|----|---------------|----------|---------------------|
| F-ANA-01 | Listar analises (filtros: ortomapa, projeto, tipo, status) | `GET /api/analises` | `AnalysisResults.vue` |
| F-ANA-02 | Detalhar analise | `GET /api/analises/{id}` | `AnalysisResults.vue` |
| F-ANA-03 | Criar analise (com opcao de enfileirar tarefa de agente) | `POST /api/analises` | `AnalysisForm.vue` |
| F-ANA-04 | Download do arquivo de resultado | `GET /api/analises/{id}/resultado` | `AnalysisResults.vue` |
| F-ANA-05 | Excluir analise (remove arquivo resultado) | `DELETE /api/analises/{id}` | `AnalysisResults.vue` |

---

## 5. Gestao de Anotacoes

| ID | Funcionalidade | Endpoint | Componente Frontend |
|----|---------------|----------|---------------------|
| F-ANO-01 | Listar anotacoes (filtros: ortomapa, projeto, categoria, fonte) | `GET /api/anotacoes` | `MapViewer.vue` |
| F-ANO-02 | Detalhar anotacao | `GET /api/anotacoes/{id}` | - |
| F-ANO-03 | Criar anotacao (WKT validado) | `POST /api/anotacoes` | `DrawTools.vue` |
| F-ANO-04 | Atualizar anotacao (com revalidacao WKT) | `PUT /api/anotacoes/{id}` | - |
| F-ANO-05 | Excluir anotacao | `DELETE /api/anotacoes/{id}` | - |
| F-ANO-06 | Exportar anotacoes como GeoJSON FeatureCollection | `GET /api/anotacoes/geojson/{ortomapa_id}` | `ExportDialog.vue` |

---

## 6. Ferramentas de Analise Espacial (18 endpoints)

### 6.1 Indices de Vegetacao

| ID | Ferramenta | Endpoint | Indices |
|----|-----------|----------|---------|
| F-VEG-01 | Calculo de indice de vegetacao | `POST /api/tools/vegetation` | VARI, TGI, ExG, GLI |

Formula de cada indice:
- **VARI**: (G - R) / (G + R - B)
- **TGI**: G - 0.39*R - 0.61*B
- **ExG**: 2*G - R - B
- **GLI**: (2*G - R - B) / (2*G + R + B)

Componente: `ToolsPanel.vue` (aba Vegetacao)

### 6.2 Analise de Terreno

| ID | Ferramenta | Endpoint | Modulo |
|----|-----------|----------|--------|
| F-TER-01 | Declividade (slope) em graus | `POST /api/tools/slope` | raster_analysis.py |
| F-TER-02 | Aspecto (aspect) em graus (0-360) | `POST /api/tools/aspect` | raster_analysis.py |
| F-TER-03 | Sombreamento (hillshade) | `POST /api/tools/hillshade` | gdal_tools.py |
| F-TER-04 | Curvas de nivel (contours) | `POST /api/tools/contours` | gdal_tools.py |
| F-TER-05 | TPI (Topographic Position Index) | via gdal_tools.calc_tpi | gdal_tools.py |
| F-TER-06 | TRI (Terrain Ruggedness Index) | via gdal_tools.calc_tri | gdal_tools.py |

Componente: `ToolsPanel.vue` (aba Terreno)

### 6.3 Deteccao de Mudancas

| ID | Ferramenta | Endpoint | Descricao |
|----|-----------|----------|-----------|
| F-MUD-01 | Deteccao binaria de mudancas | `POST /api/tools/changes` | Diff media entre bandas, mascara binaria por threshold |

Componente: `ToolsPanel.vue` (aba Mudancas)

### 6.4 Classificacao

| ID | Ferramenta | Endpoint | Algoritmos |
|----|-----------|----------|------------|
| F-CLA-01 | Classificacao supervisionada/nao-supervisionada | `POST /api/tools/classify` | KMeans, Random Forest, SVM |

7 classes de cobertura: vegetacao_densa, vegetacao_rasteira, solo_exposto, agua, urbano, agricola, rocha

Componente: `ToolsPanel.vue` (aba Classificacao)

### 6.5 Hidrologia

| ID | Ferramenta | Endpoint | Descricao |
|----|-----------|----------|-----------|
| F-HID-01 | Delimitacao de bacia hidrografica | `POST /api/tools/hydrology/watershed` | Fill + D8 flow direction + BFS upstream |
| F-HID-02 | Extracao de rede de drenagem | `POST /api/tools/hydrology/streams` | Fill + flow dir + accumulation + threshold + vectorize |

Funcoes internas: fill_sinks, flow_direction, flow_accumulation, extract_streams, delineate_watershed, calc_twi

Componente: `ToolsPanel.vue` (aba Hidrologia)

### 6.6 Volumetria

| ID | Ferramenta | Endpoint | Descricao |
|----|-----------|----------|-----------|
| F-VOL-01 | Calculo de volume (acima/abaixo referencia) | `POST /api/tools/volume` | Volume acima e abaixo de um plano de elevacao |
| F-VOL-02 | Diferenca entre DSMs + corte/aterro | `POST /api/tools/volume/difference` | Cut-fill analysis com areas e volumes |

Componente: `ToolsPanel.vue` (aba Volume)

### 6.7 Segmentacao

| ID | Ferramenta | Endpoint | Descricao |
|----|-----------|----------|-----------|
| F-SEG-01 | Segmentacao por clustering | `POST /api/tools/segment` | KMeans em RGB normalizado, estatisticas por cluster |

### 6.8 Operacoes GDAL

| ID | Ferramenta | Endpoint | Descricao |
|----|-----------|----------|-----------|
| F-GDA-01 | Recorte de raster | `POST /api/tools/clip` | gdalwarp com bbox ou poligono WKT |
| F-GDA-02 | Reprojecao | `POST /api/tools/reproject` | gdalwarp para EPSG alvo |
| F-GDA-03 | Merge de rasters | `POST /api/tools/merge` | gdal_merge.py |
| F-GDA-04 | Estatisticas raster | `POST /api/tools/statistics` | min, max, mean, std, median, histograma |
| F-GDA-05 | Estatisticas zonais | `POST /api/tools/zonal-stats` | Estatisticas por zona (GeoJSON de zonas) |
| F-GDA-06 | Calculadora raster | `POST /api/tools/calculator` | Expressao numpy com rasters nomeados |

Componente: `ToolsPanel.vue` (aba Recorte)

---

## 7. Mapa Interativo

| ID | Funcionalidade | Componente |
|----|---------------|------------|
| F-MAP-01 | Visualizacao de ortomapas como tile layers TMS | `MapViewer.vue` |
| F-MAP-02 | Alternancia de basemaps (OpenStreetMap, Satellite/Esri) | `MapViewer.vue` |
| F-MAP-03 | Controle de opacidade por camada (slider) | `MapViewer.vue`, `LayerPanel.vue` |
| F-MAP-04 | Exibicao de anotacoes como GeoJSON com popups | `MapViewer.vue` |
| F-MAP-05 | Exibicao de resultados de analise como GeoJSON | `MapViewer.vue` |
| F-MAP-06 | Coordenadas do cursor em tempo real (lat, lng) | `App.vue` (status bar) |
| F-MAP-07 | Indicador de zoom corrente | `App.vue` (status bar) |
| F-MAP-08 | Escala metrica (L-control-scale) | `MapViewer.vue` |
| F-MAP-09 | Zoom para bbox do projeto ao selecionar | `MapViewer.vue` |
| F-MAP-10 | Captura de ponto no mapa (pour point para hidrologia) | `MapViewer.vue`, `ToolsPanel.vue` |

---

## 8. Painel de Ferramentas (8 abas)

| Aba | ID Tab | Funcionalidades |
|-----|--------|----------------|
| Vegetacao | `vegetacao` | Selecao de ortomapa, indice (VARI/TGI/ExG/GLI), calculo, exibicao stats |
| Terreno | `terreno` | Selecao DSM/DTM, tipo (slope/aspect/contours/hillshade), intervalo curvas |
| Classificacao | `classificacao` | Selecao ortomapa, algoritmo (RF/KMeans), num classes, areas de treino |
| Hidrologia | `hidrologia` | Selecao DTM, tipo (watershed/streams/TWI), threshold, pour point |
| Mudancas | `mudancas` | Selecao antes/depois, slider de threshold |
| Volume | `volume` | Selecao DSM, elevacao referencia, resultado corte/aterro |
| Recorte | `recorte` | Selecao ortomapa, desenho poligono de recorte |
| Exportar | `exportar` | Selecao camada, formato (6 opcoes), CRS (5 opcoes) |

Componente: `ToolsPanel.vue` (706 linhas)

---

## 9. Medicoes

| ID | Funcionalidade | Componente |
|----|---------------|------------|
| F-MED-01 | Medicao de distancia (polyline no mapa) | `MeasureTools.vue` |
| F-MED-02 | Medicao de area (polygon no mapa) | `MeasureTools.vue` |

Ativacao via `mapStore.setMeasureMode('distance'|'area')`. Pontos capturados via clique no mapa. Exibidos como polyline/polygon com markers nos vertices.

---

## 10. Desenho e Anotacao

| ID | Funcionalidade | Componente |
|----|---------------|------------|
| F-DES-01 | Desenho de ponto | `DrawTools.vue` |
| F-DES-02 | Desenho de linha | `DrawTools.vue` |
| F-DES-03 | Desenho de poligono | `DrawTools.vue` |
| F-DES-04 | Desenho de retangulo | `DrawTools.vue` |

Ativacao via `mapStore.setDrawMode('point'|'line'|'polygon'|'rectangle')`. Geometria convertida para WKT e salva como anotacao via POST /api/anotacoes.

---

## 11. Exportacao

| ID | Funcionalidade | Formatos |
|----|---------------|----------|
| F-EXP-01 | Exportacao de camada/ortomapa | GeoTIFF, PNG, JPEG, KML, GeoJSON, Shapefile |

CRS disponiveis: EPSG:4326, EPSG:31983, EPSG:31984, EPSG:32723, EPSG:32724

Componentes: `ExportDialog.vue`, `ToolsPanel.vue` (aba Exportar)

---

## 12. Comparacao Temporal

| ID | Funcionalidade | Componente |
|----|---------------|------------|
| F-COM-01 | Comparacao swipe (deslizante) entre 2 ortomapas | `CompareView.vue` |
| F-COM-02 | Comparacao lado a lado (side-by-side) | `CompareView.vue` |

Ativacao via `mapStore.setCompareMode(true)` e `mapStore.setCompareLayers(left, right)`. Usa leaflet-side-by-side.

---

## 13. Agentes de IA (5 + Orquestrador)

| ID | Agente | Tipo Tarefa | Descricao |
|----|--------|-------------|-----------|
| F-AGI-01 | Orchestrator | (despacho) | Polling tarefas_agentes, despacho, retry (max 3), status management |
| F-AGI-02 | VegetationAgent | indice_vegetacao | 8 indices (VARI, TGI, ExG, ExR, ExGR, GLI, RGBVI, MGRVI), classificacao saude |
| F-AGI-03 | DetectionAgent | deteccao_objetos | YOLOv8 com tiling 640x640, overlap 64px, NMS cross-tile, GeoJSON output |
| F-AGI-04 | ChangeAgent | deteccao_mudancas | Comparacao temporal, classificacao heuristica (desmatamento, construcao, erosao, inundacao) |
| F-AGI-05 | ClassificationAgent | classificacao_solo | KMeans ou RF, 7 classes, majority filter 3x3 |
| F-AGI-06 | ReportAgent | personalizada | Relatorio Markdown com integracao Claude API (fallback template) |

Componente: `AgentStatus.vue` (monitoramento em tempo real), `AnalysisForm.vue` (disparo)

---

## 14. Funcionalidades do Sistema (Automaticas)

| ID | Funcionalidade | Descricao |
|----|---------------|-----------|
| F-SYS-01 | Fallback automatico MySQL -> SQLite | Detecta indisponibilidade e cria schema SQLite |
| F-SYS-02 | Extracao automatica de metadados no upload | bbox, resolucao, CRS, dimensoes, tamanho |
| F-SYS-03 | Geracao automatica de thumbnail | PNG 512x512 ao upload |
| F-SYS-04 | Limpeza de exports antigos | cleanup_old_exports (>24h) |
| F-SYS-05 | Seed de projetos | 10 projetos reais de Minas Gerais |
| F-SYS-06 | Polling de status de agentes | Frontend poll a cada 5s |
| F-SYS-07 | Retry automatico de tarefas falhadas | Ate max_tentativas (default 3) |

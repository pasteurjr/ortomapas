# Inventario do Sistema - Sistema de Ortomapas

**Data da analise:** 2026-03-28
**Versao do sistema:** 1.0.0

---

## 1. Resumo Quantitativo

| Categoria | Arquivos | Linhas de Codigo |
|-----------|----------|------------------|
| Backend (Python) | 22 | 5.544 |
| Frontend (Vue/JS) | 18 | 5.280 |
| Infraestrutura | 3 | 122 |
| Testes | 4 | 2.772 |
| Documentacao | 8 | ~2.500 |
| **Total (excl. node_modules)** | **55** | **~16.218** |

---

## 2. Backend (Python)

### 2.1 Aplicacao Principal

| Arquivo | Linhas | Descricao |
|---------|--------|-----------|
| `backend/main.py` | 85 | FastAPI app, CORS, routers, startup, root/health endpoints |
| `backend/config.py` | 31 | Configuracao centralizada: diretorios, DB, portas, URLs externas |
| `backend/__init__.py` | 0 | Pacote Python |

### 2.2 Routers (API Endpoints)

| Arquivo | Linhas | Endpoints | Descricao |
|---------|--------|-----------|-----------|
| `backend/routers/projetos.py` | 235 | 7 | CRUD projetos + busca + listagem de ortomapas por projeto |
| `backend/routers/voos.py` | 192 | 5 | CRUD voos (flights) |
| `backend/routers/ortomapas.py` | 466 | 8 | CRUD ortomapas + upload + tiles + consulta espacial |
| `backend/routers/analises.py` | 217 | 5 | CRUD analises + download de resultado |
| `backend/routers/anotacoes.py` | 279 | 6 | CRUD anotacoes + exportacao GeoJSON |
| `backend/routers/tools.py` | 331 | 18 | Ferramentas espaciais: clip, reproject, merge, vegetation, slope, aspect, contours, hillshade, statistics, zonal-stats, calculator, changes, classify, watershed, streams, volume, volume/difference, segment |
| `backend/routers/__init__.py` | 0 | - | Pacote |

**Total de endpoints nos routers:** 49
**Endpoints adicionais (main.py):** 2 (root `/`, health `/health`)
**Static files mount:** 1 (`/data`)
**Total geral de endpoints:** 51+

### 2.3 Modulos de Ferramentas (Tools)

| Arquivo | Linhas | Funcoes | Descricao |
|---------|--------|---------|-----------|
| `backend/tools/raster_analysis.py` | 404 | 7 | Indices vegetacao (VARI, TGI, ExG, GLI), slope, aspect, roughness, raster_statistics, zonal_statistics, raster_calculator |
| `backend/tools/gdal_tools.py` | 267 | 10 | clip_raster, reproject_raster, merge_rasters, translate_raster, raster_info, generate_contours, hillshade, build_overviews, calc_tpi, calc_tri |
| `backend/tools/change_detection.py` | 255 | 4 | _align_rasters, detect_changes, vegetation_change, change_statistics |
| `backend/tools/classification.py` | 375 | 4 | _extract_features_from_bands, train_classifier (RF/SVM), classify_raster, accuracy_assessment |
| `backend/tools/hydrology.py` | 475 | 7 | fill_sinks, flow_direction, flow_accumulation, extract_streams, delineate_watershed, calc_twi |
| `backend/tools/volumetry.py` | 139 | 3 | calc_volume, dsm_difference, cut_fill_analysis |
| `backend/tools/segmentation.py` | 85 | 1 | segment_ortomapa (KMeans clustering) |
| `backend/tools/__init__.py` | 0 | - | Pacote |

### 2.4 Agentes de IA

| Arquivo | Linhas | Classe | Descricao |
|---------|--------|--------|-----------|
| `backend/agents/orchestrator.py` | 183 | Orchestrator | Orquestrador: polling tarefas_agentes, despacho, retry, status |
| `backend/agents/vegetation_agent.py` | 237 | VegetationAgent | Calcula 8 indices de vegetacao, classifica saude, gera GeoTIFF |
| `backend/agents/detection_agent.py` | 395 | DetectionAgent | YOLOv8 com tiling 640x640, NMS cross-tile, GeoJSON output |
| `backend/agents/change_agent.py` | 316 | ChangeAgent | Comparacao temporal entre 2 ortomapas, classificacao heuristica |
| `backend/agents/classification_agent.py` | 279 | ClassificationAgent | KMeans ou Random Forest, 7 classes cobertura do solo |
| `backend/agents/report_agent.py` | 343 | ReportAgent | Relatorios Markdown, integracao Anthropic API (Claude) |
| `backend/agents/__init__.py` | 0 | - | Pacote |

### 2.5 Utilitarios

| Arquivo | Linhas | Funcoes | Descricao |
|---------|--------|---------|-----------|
| `backend/utils/geo_utils.py` | 137 | 5 | get_raster_info, get_raster_bounds, wkt_to_geojson, geojson_to_wkt, calc_area_from_wkt, pixel_to_coords |
| `backend/utils/file_manager.py` | 114 | 4 | save_upload, get_file_size_mb, cleanup_old_exports, ensure_dir |
| `backend/utils/thumbnail.py` | 96 | 1 | generate_thumbnail (GeoTIFF para PNG) |
| `backend/utils/__init__.py` | 0 | - | Pacote |

### 2.6 Banco de Dados

| Arquivo | Linhas | Descricao |
|---------|--------|-----------|
| `backend/database/connection.py` | 362 | Pool MySQL, fallback SQLite, execute_query, execute_many, init_database |
| `backend/database/models.py` | 258 | Pydantic schemas: Create, Update, Response para 8 entidades |
| `backend/database/seed.py` | 304 | Seed de 10 projetos reais de Minas Gerais |
| `backend/database/__init__.py` | 33 | Exports do pacote |

### 2.7 Dependencias Python (requirements.txt)

| Categoria | Pacotes |
|-----------|---------|
| Framework | fastapi, uvicorn, python-multipart, aiofiles |
| Database | mysql-connector-python |
| Geospatial | rasterio, geopandas, shapely, fiona, pyproj |
| Cientifico | numpy, scikit-learn, scipy, opencv-python-headless |
| Imagem | pillow |
| IA/ML | ultralytics (YOLOv8), anthropic (Claude API) |
| Visualizacao | matplotlib, folium |
| Utilitarios | joblib |

---

## 3. Frontend (Vue 3 + Leaflet)

### 3.1 Estrutura

| Arquivo | Linhas | Descricao |
|---------|--------|-----------|
| `frontend/src/App.vue` | 401 | Layout principal: toolbar, sidebars, mapa, status bar |
| `frontend/src/main.js` | 22 | Bootstrap Vue 3 + Pinia + PrimeVue |
| `frontend/index.html` | 13 | HTML raiz |
| `frontend/package.json` | 26 | Dependencias npm |
| `frontend/vite.config.js` | 20 | Configuracao Vite com proxy para API |

### 3.2 Componentes (13)

| Componente | Linhas | Descricao |
|------------|--------|-----------|
| `ToolsPanel.vue` | 706 | Painel com 8 abas de ferramentas (Veg, Ter, Cls, Hid, Mud, Vol, Rec, Exp) |
| `AnalysisForm.vue` | 541 | Formulario modal para configurar e disparar analises |
| `AgentStatus.vue` | 438 | Monitora status dos agentes de IA em tempo real |
| `LayerPanel.vue` | 420 | Gerenciamento de camadas: visibilidade, opacidade, reordenacao |
| `AnalysisResults.vue` | 351 | Lista de resultados de analises com estatisticas |
| `MapViewer.vue` | 352 | Mapa Leaflet: tiles, GeoJSON, anotacoes, medicoes, basemaps |
| `ExportDialog.vue` | 345 | Modal de exportacao: formato, CRS, area |
| `MeasureTools.vue` | 341 | Ferramentas de medicao: distancia e area |
| `CompareView.vue` | 329 | Comparacao temporal: swipe e side-by-side |
| `DrawTools.vue` | 321 | Ferramentas de desenho: ponto, linha, poligono, retangulo |
| `ProjectList.vue` | 294 | Lista de projetos com CRUD |
| `VoosList.vue` | 277 | Lista de voos com detalhes |
| `OrtomapCard.vue` | 200 | Card de ortomapa com thumbnail e acoes |

### 3.3 Stores (Pinia)

| Store | Linhas | Descricao |
|-------|--------|-----------|
| `stores/projectStore.js` | 140 | Estado global: projetos, ortomapas, analises, anotacoes, polling |
| `stores/mapStore.js` | 99 | Estado do mapa: camadas, zoom, coordenadas, modos (draw/measure/compare) |

### 3.4 API Client

| Arquivo | Linhas | Descricao |
|---------|--------|-----------|
| `api/client.js` | 139 | Axios wrapper: 25 funcoes de API para todos os endpoints |

### 3.5 Dependencias Frontend (package.json)

| Pacote | Versao | Funcao |
|--------|--------|--------|
| vue | ^3.5.0 | Framework reativo |
| pinia | ^2.3.0 | State management |
| primevue | ^4.3.0 | Biblioteca UI |
| primeicons | ^7.0.0 | Icones |
| @primevue/themes | ^4.5.4 | Temas PrimeVue |
| leaflet | ^1.9.4 | Motor de mapa |
| @vue-leaflet/vue-leaflet | ^0.10.0 | Componentes Leaflet para Vue |
| leaflet-draw | ^1.0.4 | Ferramentas de desenho no mapa |
| leaflet-side-by-side | ^2.2.0 | Comparacao swipe |
| axios | ^1.7.0 | HTTP client |
| vue-router | ^4.5.0 | Roteamento SPA |
| vite | ^6.0.0 | Build tool |
| @vitejs/plugin-vue | ^5.0.0 | Plugin Vue para Vite |

---

## 4. Banco de Dados

### 4.1 Tabelas (8)

| Tabela | Campos | Descricao |
|--------|--------|-----------|
| `projetos` | 17 | Projetos de mapeamento |
| `voos` | 23 | Registros de voo do drone |
| `ortomapas` | 31 | Metadados de ortomosaicos |
| `analises` | 18 | Resultados de analises |
| `anotacoes` | 15 | Geometrias e rotulos |
| `gcps` | 13 | Pontos de controle de solo |
| `comparacoes_temporais` | 12 | Comparacoes entre ortomapas |
| `tarefas_agentes` | 14 | Fila de tarefas dos agentes de IA |

### 4.2 Configuracao

- **Primario:** MySQL 8 (<YOUR_DB_HOST>:3308, database ortomapas)
- **Fallback:** SQLite (data/ortomapas.db) com adaptador automatico
- **Pool:** 5 conexoes, lazy init, reset_session
- **Charset:** utf8mb4, collation utf8mb4_unicode_ci

---

## 5. Infraestrutura

### 5.1 Docker Compose

| Servico | Imagem | Porta | Funcao |
|---------|--------|-------|--------|
| webapp | opendronemap/webodm_webapp | 8000 | WebODM - processamento fotogrametrico |
| db-webodm | opendronemap/webodm_db | - | PostgreSQL para WebODM |
| broker | redis:7-alpine | - | Fila de mensagens para WebODM |
| worker | opendronemap/webodm_webapp | - | Worker de processamento |
| nodeodm | opendronemap/nodeodm | 3000 | No de processamento ODM |
| geoserver | kartoza/geoserver:2.25.2 | 8080 | Publicacao WMS/WMTS |

### 5.2 Portas do Sistema

| Servico | Porta | Protocolo |
|---------|-------|-----------|
| FastAPI Backend | 8888 | HTTP/REST |
| Vite Dev Server (Frontend) | 5176 | HTTP |
| WebODM | 8000 | HTTP |
| NodeODM | 3000 | HTTP |
| GeoServer | 8080 | HTTP/WMS/WMTS |
| MySQL | 3308 | TCP |

---

## 6. Testes

| Arquivo | Linhas | Tipo |
|---------|--------|------|
| `testevalidacao/test_ui_completo.py` | 657 | Testes Playwright UI end-to-end |
| `testevalidacao/agent_teams/03_validador_playwright.py` | 1.367 | Validacao automatizada completa |
| `testevalidacao/agent_teams/05_revalidacao.py` | 532 | Revalidacao apos correcoes |
| `tests/e2e/playwright/conftest.py` | 16 | Configuracao Playwright |

---

## 7. Dados e Diretorios

| Diretorio | Conteudo |
|-----------|----------|
| `data/ortomapas/` | Arquivos GeoTIFF dos ortomosaicos |
| `data/dsm/` | Modelos Digitais de Superficie |
| `data/dtm/` | Modelos Digitais de Terreno |
| `data/analises/` | Resultados de analises (GeoTIFF, GeoJSON, Markdown) |
| `data/thumbnails/` | Miniaturas PNG |
| `data/uploads/` | Uploads temporarios |
| `data/exports/` | Exportacoes temporarias |
| `geojson/` | Arquivos GeoJSON de referencia |

---

## 8. Documentacao Existente

| Arquivo | Descricao |
|---------|-----------|
| `MANUALORTOMAPAS.md` | Manual do usuario |
| `ANALISE AREAS.md` | Analise de areas de estudo |
| `ortomapa.md` | Documentacao do ortomapa |
| `configdrone.md` | Configuracao do DJI Mini 3 |
| `DJI_Mini3_Orthomapping_Research.md` | Pesquisa sobre mapeamento com Mini 3 |
| `Serra_do_Cipo_Drone_Orthomapping_Research.md` | Pesquisa Serra do Cipo |

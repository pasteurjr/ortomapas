# Atores do Sistema - Sistema de Ortomapas

**Data da analise:** 2026-03-28
**Versao do sistema:** 1.0.0

---

## 1. Visao Geral dos Atores

O sistema possui 4 atores com papeis distintos:

| # | Ator | Tipo | Descricao |
|---|------|------|-----------|
| 1 | Usuario | Humano (primario) | Pesquisador/operador de drone que interage via interface web |
| 2 | Sistema | Automatizado | Backend FastAPI + ferramentas GDAL/rasterio que processam requisicoes |
| 3 | Agente IA | Autonomo (software) | 5 agentes especializados + orquestrador que executam analises |
| 4 | Administrador | Humano (secundario) | Gerencia infraestrutura Docker, banco de dados e configuracao |

```
+------------------------------------------------------------------+
|                                                                    |
|  +------------------+    interage via    +---------------------+   |
|  |     Usuario      | ----------------> |   Frontend (SPA)    |   |
|  |  (Pesquisador)   | <---------------- |   Vue 3 + Leaflet   |   |
|  +------------------+                   +---------------------+   |
|                                                |                   |
|                                                | HTTP/REST         |
|                                                v                   |
|                                         +---------------------+   |
|                                         |   Sistema (Backend)  |   |
|                                         |   FastAPI + Tools    |   |
|                                         +---------------------+   |
|                                                |                   |
|                                         +------v--------------+   |
|                                         |   Agentes de IA     |   |
|                                         |   (Autonomos)       |   |
|                                         +---------------------+   |
|                                                |                   |
|  +------------------+    configura      +------v--------------+   |
|  |  Administrador   | ----------------> |   Infraestrutura    |   |
|  |  (DevOps)        |                   |   Docker/DB/Config  |   |
|  +------------------+                   +---------------------+   |
|                                                                    |
+------------------------------------------------------------------+
```

---

## 2. Ator: Usuario (Pesquisador / Operador de Drone)

### 2.1 Perfil

- **Tipo:** Ator primario (humano)
- **Descricao:** Pesquisador com PhD em informacao espacial ou profissional de geociencias que opera drones (DJI Mini 3) para captura de imagens aereas e analisa os ortomosaicos resultantes via interface web.
- **Quantidade:** Um ou mais usuarios simultaneos (sem autenticacao, acesso irrestrito)
- **Competencias esperadas:** Conhecimento em SIG, sensoriamento remoto, interpretacao de indices de vegetacao, analise de terreno, fotogrametria basica.
- **Idioma:** Portugues (BR)

### 2.2 Capacidades

| Categoria | Acoes | Componente UI |
|-----------|-------|---------------|
| **Gestao de Projetos** | Criar, listar, buscar (fulltext), filtrar (status/area), editar, excluir projetos | `ProjectList.vue`, `App.vue` |
| **Gestao de Voos** | Registrar voos com 22 campos de parametros, editar, excluir | `VoosList.vue` |
| **Gestao de Ortomapas** | Upload de GeoTIFF, visualizar no mapa como tiles TMS, consultar metadados, excluir | `OrtomapCard.vue`, `MapViewer.vue` |
| **Analises Espaciais** | Solicitar analises de vegetacao (VARI/TGI/ExG/GLI), terreno (slope/aspect/contours/hillshade), classificacao (KMeans/RF), hidrologia (watershed/streams), deteccao de mudancas, volumetria, segmentacao | `ToolsPanel.vue` |
| **Anotacoes** | Criar anotacoes manuais (ponto, linha, poligono, retangulo), categorizar, rotular, exportar como GeoJSON | `DrawTools.vue` |
| **Mapa Interativo** | Alternar basemaps (OSM/Satellite), controlar opacidade de camadas, zoom para projeto | `MapViewer.vue`, `LayerPanel.vue` |
| **Medicoes** | Medir distancias (haversine) e areas (shoelace formula) diretamente no mapa | `MeasureTools.vue` |
| **Comparacao Temporal** | Comparar 2 ortomapas via swipe deslizante ou lado a lado | `CompareView.vue` |
| **Exportacao** | Exportar camadas em 6 formatos (GeoTIFF, PNG, JPEG, KML, GeoJSON, Shapefile) com 5 opcoes de CRS | `ExportDialog.vue`, `ToolsPanel.vue` |
| **Agentes IA** | Disparar tarefas para agentes de IA, monitorar status de execucao em tempo real | `AnalysisForm.vue`, `AgentStatus.vue` |

### 2.3 Interacoes com o Sistema

```
Usuario
  |
  +-- Navegar na interface (SPA Vue 3 + PrimeVue)
  |     +-- Selecionar projeto (toolbar: Select ou sidebar: ProjectList)
  |     +-- Buscar projetos por texto (toolbar: InputText)
  |     +-- Visualizar mapa com ortomapas (area central: MapViewer)
  |     +-- Alternar basemaps (OSM / Satellite) e ajustar camadas
  |     +-- Ver coordenadas e zoom na barra de status
  |
  +-- Gerenciar dados
  |     +-- CRUD completo de projetos (ProjectList dialog)
  |     +-- Registrar voos com parametros do drone (VoosList dialog)
  |     +-- Upload de GeoTIFF com extracao automatica de metadados
  |     +-- Criar/editar anotacoes geometricas (DrawTools)
  |
  +-- Executar analises espaciais
  |     +-- Selecionar ferramenta em uma das 8 abas (ToolsPanel)
  |     +-- Configurar parametros (ortomapa, indice, algoritmo, threshold)
  |     +-- Visualizar resultado como camada no mapa
  |     +-- Ver estatisticas do resultado
  |     +-- Baixar arquivo resultado
  |
  +-- Medir e comparar
  |     +-- Medir distancia/area clicando no mapa (MeasureTools)
  |     +-- Comparar ortomapas temporalmente (CompareView: swipe ou side-by-side)
  |
  +-- Exportar dados
        +-- Selecionar camada, formato e CRS (ExportDialog ou ToolsPanel aba Exportar)
        +-- Baixar arquivo exportado
```

### 2.4 Permissoes

| Recurso | Criar | Ler | Atualizar | Excluir |
|---------|-------|-----|-----------|---------|
| Projetos | Sim | Sim | Sim | Sim |
| Voos | Sim | Sim | Sim | Sim |
| Ortomapas | Sim (upload) | Sim | Sim | Sim |
| Analises | Sim | Sim | Nao | Sim |
| Anotacoes | Sim | Sim | Sim | Sim |
| GCPs | Sim | Sim | Nao | Nao |
| Ferramentas | Sim (executar) | Sim (resultados) | - | - |

**Nota:** Nao ha controle de acesso (autenticacao/autorizacao). O sistema e aberto para uso local/pesquisa.

---

## 3. Ator: Sistema (Backend Automatizado)

### 3.1 Perfil

- **Tipo:** Ator de sistema (automatizado)
- **Descricao:** Conjunto de processos automaticos que o backend FastAPI executa sem intervencao humana direta, incluindo ferramentas GDAL, rasterio, numpy, scikit-learn e PIL.
- **Componentes:** FastAPI (main.py), Routers (7), Tools (7 modulos), Utils (3), Database (connection pool)

### 3.2 Capacidades

| Funcao | Descricao | Gatilho |
|--------|-----------|---------|
| **Extracao de metadados** | Extrai bbox, resolucao, CRS, dimensoes e tamanho do GeoTIFF via rasterio | Upload de ortomapa (POST /api/ortomapas/upload) |
| **Geracao de thumbnail** | Cria miniatura PNG 512x512 do GeoTIFF via PIL | Upload de ortomapa |
| **Tile server embutido** | Gera tiles PNG 256x256 on-the-fly via rasterio window read | GET /api/ortomapas/{id}/tile/{z}/{x}/{y}.png |
| **Fallback MySQL->SQLite** | Detecta indisponibilidade do MySQL e cria/usa banco SQLite local | Falha na primeira conexao MySQL |
| **Adaptacao SQL** | Converte placeholders %s para ? e remove sintaxe MySQL-especifica | Modo SQLite ativo |
| **Pool de conexoes** | Gerencia pool de 5 conexoes MySQL com lazy init e pool_reset_session | Primeira requisicao ao DB |
| **Sanitizacao de upload** | Limpa nome do arquivo, adiciona UUID parcial, salva em chunks de 1MB | Upload de qualquer arquivo |
| **Limpeza de exports** | Remove arquivos de exportacao com mais de 24 horas | cleanup_old_exports() |
| **Processamento raster** | Executa calculos de indices, terreno, classificacao, hidrologia, volumetria via numpy/rasterio/GDAL | POST /api/tools/* |
| **Consulta espacial** | Filtra ortomapas por intersecao de bounding box | GET /api/ortomapas/spatial |
| **Conversao WKT/GeoJSON** | Valida geometrias WKT e converte para GeoJSON via shapely | CRUD de anotacoes |
| **Seed de dados** | Popula 10 projetos de exemplo de Minas Gerais | Execucao do seed script |

### 3.3 Interacoes

```
Sistema
  |
  +-- Startup
  |     +-- Criar diretorios necessarios (data/ortomapas, data/dsm, data/dtm, data/analises, data/thumbnails, data/uploads, data/exports)
  |     +-- Inicializar pool MySQL (ou fallback SQLite com schema completo)
  |     +-- Montar static files (/data -> data/)
  |     +-- Registrar 7 routers com prefix /api
  |     +-- Configurar CORS (allow_origins=["*"])
  |
  +-- Upload Pipeline
  |     +-- Receber arquivo via multipart/form-data
  |     +-- Sanitizar nome + UUID parcial
  |     +-- Salvar em chunks de 1MB em data/ortomapas/
  |     +-- Abrir com rasterio: extrair bounds, shape, crs, res
  |     +-- Se CRS != EPSG:4326: reprojetar bounds
  |     +-- Gerar thumbnail PNG 512x512 via PIL
  |     +-- Calcular tamanho em MB
  |     +-- INSERT INTO ortomapas com todos os metadados
  |
  +-- Tile Serving Pipeline
  |     +-- Converter TMS z/x/y para lat/lon bounds
  |     +-- Abrir GeoTIFF com rasterio
  |     +-- Ler janela (window read) correspondente ao tile
  |     +-- Normalizar para uint8 (0-255)
  |     +-- Redimensionar para 256x256 via PIL
  |     +-- Retornar StreamingResponse com content-type image/png
  |
  +-- Analise Espacial Pipeline
        +-- Receber parametros via POST JSON
        +-- Resolver paths relativos para absolutos (_resolve_path)
        +-- Executar ferramenta (numpy/rasterio/GDAL subprocess/scikit-learn)
        +-- Salvar resultado em data/analises/ (_output_path)
        +-- Retornar JSON com output_path e statistics
```

### 3.4 Ferramentas Disponveis (18 endpoints)

| Endpoint | Modulo Backend | Descricao |
|----------|---------------|-----------|
| POST /api/tools/clip | gdal_tools.clip_raster | Recorte por bbox ou WKT |
| POST /api/tools/reproject | gdal_tools.reproject_raster | Reprojecao para EPSG alvo |
| POST /api/tools/merge | gdal_tools.merge_rasters | Merge de multiplos rasters |
| POST /api/tools/contours | gdal_tools.generate_contours | Curvas de nivel GeoJSON |
| POST /api/tools/hillshade | gdal_tools.hillshade | Sombreamento (azimuth, altitude) |
| POST /api/tools/vegetation | raster_analysis.calc_vegetation_index | VARI, TGI, ExG, GLI |
| POST /api/tools/slope | raster_analysis.calc_slope | Declividade em graus |
| POST /api/tools/aspect | raster_analysis.calc_aspect | Aspecto em graus (0-360) |
| POST /api/tools/statistics | raster_analysis.raster_statistics | Estatisticas min/max/mean/std |
| POST /api/tools/zonal-stats | raster_analysis.zonal_statistics | Estatisticas por zona |
| POST /api/tools/calculator | raster_analysis.raster_calculator | Expressao numpy |
| POST /api/tools/changes | change_detection.detect_changes | Deteccao binaria de mudancas |
| POST /api/tools/classify | classification/segmentation | KMeans, RF, SVM |
| POST /api/tools/hydrology/watershed | hydrology.delineate_watershed | Bacia hidrografica |
| POST /api/tools/hydrology/streams | hydrology.extract_streams | Rede de drenagem |
| POST /api/tools/volume | volumetry.calc_volume | Volume acima/abaixo referencia |
| POST /api/tools/volume/difference | volumetry.cut_fill_analysis | Corte/aterro entre DSMs |
| POST /api/tools/segment | segmentation.segment_ortomapa | Segmentacao KMeans RGB |

---

## 4. Ator: Agente de IA (Processos Autonomos)

### 4.1 Perfil

- **Tipo:** Ator autonomo (software)
- **Descricao:** Conjunto de 5 agentes especializados + 1 orquestrador que executam tarefas de analise de forma autonoma a partir da fila de tarefas (tabela tarefas_agentes).
- **Execucao:** Processo separado via `python -m backend.agents.orchestrator`

### 4.2 Orquestrador (Orchestrator)

- **Arquivo:** `backend/agents/orchestrator.py` (183 linhas)
- **Funcao:** Gerenciamento da fila de tarefas
- **Capacidades:**
  - Polling da tabela tarefas_agentes a cada 10 segundos
  - Selecao atomica de tarefas pendentes via SELECT ... FOR UPDATE SKIP LOCKED
  - Despacho para o agente correto baseado no campo `agente`
  - Gerenciamento de retentativas (ate max_tentativas, default 3)
  - Atualizacao de status (pendente -> em_execucao -> concluida/erro)
  - Serializacao de resultado como JSON
  - Registro de timestamps inicio_execucao e fim_execucao
- **Interacoes:** Banco de dados (tarefas_agentes, analises), Agentes especializados

### 4.3 Agentes Especializados

#### 4.3.1 VegetationAgent (Agente de Vegetacao)

- **Arquivo:** `backend/agents/vegetation_agent.py` (237 linhas)
- **Chave de despacho:** `VegetationAgent`
- **Tipo de tarefa:** `indice_vegetacao`
- **Capacidades:**
  - Calculo de 8 indices de vegetacao visivel: VARI, TGI, ExG, ExR, ExGR, GLI, RGBVI, MGRVI
  - Classificacao em 3 categorias: saudavel, estressada, sem_vegetacao (baseada em thresholds)
  - Geracao de GeoTIFF do indice e da classificacao
  - Calculo de estatisticas: media, desvio padrao, min, max, area por classe
  - Registro na tabela analises com resultado_json contendo estatisticas
- **Permissoes:** Leitura de ortomapas (disco), escrita em data/analises/, INSERT em analises

#### 4.3.2 DetectionAgent (Agente de Deteccao)

- **Arquivo:** `backend/agents/detection_agent.py` (395 linhas)
- **Chave de despacho:** `DetectionAgent`
- **Tipo de tarefa:** `deteccao_objetos`
- **Capacidades:**
  - Deteccao de objetos via YOLOv8 (ultralytics)
  - Tiling do ortomapa em patches 640x640 com overlap de 64px
  - Conversao de coordenadas pixel para coordenadas geograficas
  - Non-Maximum Suppression (NMS) cross-tile para evitar duplicatas
  - Exportacao como GeoJSON com bounding boxes e classes
  - Registro de cada deteccao como anotacao individual (INSERT INTO anotacoes)
  - Filtragem por classes e threshold de confianca
- **Permissoes:** Leitura de ortomapas (disco), escrita em data/analises/, INSERT em analises e anotacoes

#### 4.3.3 ChangeAgent (Agente de Mudancas)

- **Arquivo:** `backend/agents/change_agent.py` (316 linhas)
- **Chave de despacho:** `ChangeAgent`
- **Tipo de tarefa:** `deteccao_mudancas`
- **Capacidades:**
  - Comparacao de 2 ortomapas de datas diferentes
  - Recorte automatico para area de intersecao (alinhamento de rasters)
  - Calculo de diferenca media entre bandas
  - Classificacao heuristica de mudancas: desmatamento, construcao, erosao, inundacao, outro
  - Estatisticas: area alterada, percentual, area por tipo de mudanca
  - Registro na tabela analises e comparacoes_temporais
- **Permissoes:** Leitura de ortomapas (disco), escrita em data/analises/, INSERT em analises e comparacoes_temporais

#### 4.3.4 ClassificationAgent (Agente de Classificacao)

- **Arquivo:** `backend/agents/classification_agent.py` (279 linhas)
- **Chave de despacho:** `ClassificationAgent`
- **Tipo de tarefa:** `classificacao_solo`
- **Capacidades:**
  - Classificacao nao-supervisionada (KMeans) ou supervisionada (Random Forest)
  - Extracao de 6 features por pixel: R, G, B, VARI, TGI, ExG
  - 7 classes de cobertura do solo: vegetacao_densa, vegetacao_rasteira, solo_exposto, agua, urbano, agricola, rocha
  - Filtro de maioria 3x3 para suavizacao do resultado
  - Subamostragem para imagens grandes (max 500k pixels para KMeans)
  - Estatisticas de area por classe
- **Permissoes:** Leitura de ortomapas (disco), escrita em data/analises/, INSERT em analises

#### 4.3.5 ReportAgent (Agente de Relatorio)

- **Arquivo:** `backend/agents/report_agent.py` (343 linhas)
- **Chave de despacho:** `ReportAgent`
- **Tipo de tarefa:** `personalizada`
- **Capacidades:**
  - Coleta de resultados de multiplas analises do projeto
  - Geracao de relatorio Markdown estruturado
  - Integracao com Anthropic API (Claude claude-sonnet-4-20250514) para comentarios interpretativos
  - Fallback para relatorio baseado em template se API indisponivel
  - Secoes: Resumo Executivo, Resultados por Analise, Observacoes, Recomendacoes
- **Permissoes:** Leitura de analises (banco), chamada API externa (Anthropic), escrita em data/analises/, INSERT em analises

### 4.4 Fluxo de Interacao dos Agentes

```
Usuario -> POST /api/analises (com agente_ia especificado)
  |
  v
Backend -> INSERT INTO tarefas_agentes (status='pendente', agente='*Agent')
  |
  v
Orchestrator (processo separado, polling 10s)
  |
  +-- SELECT ... FROM tarefas_agentes WHERE status='pendente'
  |   ORDER BY prioridade ASC, criado_em ASC
  |   FOR UPDATE SKIP LOCKED
  +-- UPDATE status='em_execucao', inicio_execucao=now()
  |
  v
Agent.execute(task)
  |
  +-- Ler ortomapa do disco (rasterio.open)
  +-- Processar (numpy/rasterio/sklearn/YOLO/Anthropic)
  +-- Salvar resultado em data/analises/
  +-- INSERT INTO analises (resultado completo)
  +-- [DetectionAgent] INSERT INTO anotacoes (cada deteccao)
  +-- [ChangeAgent] INSERT INTO comparacoes_temporais
  +-- UPDATE tarefas_agentes SET status='concluida', fim_execucao=now()
  |
  v
Frontend (polling 5s via projectStore) -> GET /api/analises -> Exibe resultado no mapa
```

### 4.5 Matriz Agente x Tabela

| Agente | analises | anotacoes | comparacoes_temporais | tarefas_agentes |
|--------|----------|-----------|----------------------|-----------------|
| VegetationAgent | INSERT | - | - | UPDATE |
| DetectionAgent | INSERT | INSERT (N) | - | UPDATE |
| ChangeAgent | INSERT | - | INSERT | UPDATE |
| ClassificationAgent | INSERT | - | - | UPDATE |
| ReportAgent | INSERT | - | - | UPDATE |

---

## 5. Ator: Administrador (DevOps / Infraestrutura)

### 5.1 Perfil

- **Tipo:** Ator secundario (humano)
- **Descricao:** Profissional responsavel pela instalacao, configuracao, monitoramento e manutencao da infraestrutura do sistema. Nao possui interface propria no sistema -- atua exclusivamente via terminal, Docker e edicao de arquivos de configuracao.
- **Competencias esperadas:** Docker, Linux, MySQL, Python, Node.js

### 5.2 Capacidades

| Funcao | Descricao | Ferramenta/Comando |
|--------|-----------|-------------------|
| **Instalacao backend** | Instalar dependencias Python | `pip install -r backend/requirements.txt` |
| **Instalacao frontend** | Instalar dependencias Node.js | `cd frontend && npm install` |
| **Configuracao DB** | Configurar conexao MySQL (host, porta, credenciais) | `backend/config.py` ou variaveis de ambiente |
| **Iniciar schema** | Criar tabelas no banco de dados | `python -m backend.database.connection` |
| **Seed de dados** | Popular banco com 10 projetos de exemplo (MG) | `python -m backend.database.seed` |
| **Docker compose** | Iniciar/parar WebODM, NodeODM, GeoServer | `docker compose up -d` / `docker compose down` |
| **Iniciar backend** | Iniciar servidor FastAPI na porta 8888 | `python -m backend.main` ou `uvicorn backend.main:app` |
| **Iniciar frontend** | Iniciar dev server Vite na porta 5176 | `cd frontend && npm run dev` |
| **Iniciar orchestrator** | Iniciar orquestrador de agentes | `python -m backend.agents.orchestrator` |
| **Health check** | Verificar saude do sistema | `GET /health` (HTTP) |
| **Monitoramento** | Verificar logs, status dos servicos Docker | `docker compose logs`, journalctl |
| **Backup** | Backup do banco MySQL e dos arquivos GeoTIFF | mysqldump, rsync |

### 5.3 Variaveis de Ambiente Configuráveis

| Variavel | Default | Descricao |
|----------|---------|-----------|
| DB_HOST | <YOUR_DB_HOST> | Host do MySQL |
| DB_PORT | 3308 | Porta do MySQL |
| DB_USER | producao | Usuario do MySQL |
| DB_PASSWORD | <YOUR_DB_PASSWORD> | Senha do MySQL |
| DB_NAME | ortomapas | Nome do banco de dados |
| DB_POOL_SIZE | 5 | Tamanho do pool de conexoes |

### 5.4 Servicos Docker Gerenciados

| Servico | Imagem | Porta | Funcao |
|---------|--------|-------|--------|
| webapp | opendronemap/webodm_webapp | 8000 | WebODM - processamento fotogrametrico |
| db-webodm | opendronemap/webodm_db | - | PostgreSQL para WebODM |
| broker | redis:7-alpine | - | Fila de mensagens para WebODM |
| worker | opendronemap/webodm_webapp | - | Worker de processamento |
| nodeodm | opendronemap/nodeodm | 3000 | No de processamento ODM |
| geoserver | kartoza/geoserver:2.25.2 | 8080 | Publicacao WMS/WMTS |

### 5.5 Permissoes

- Acesso total ao servidor (SSH, root ou sudo)
- Acesso direto ao banco de dados MySQL
- Acesso ao filesystem (data/*, logs)
- Gerenciamento de containers Docker
- Nao interage com a interface web (nao e ator da UI)

---

## 6. Matriz Ator x Funcionalidade

| Funcionalidade | Usuario | Sistema | Agente IA | Administrador |
|---------------|---------|---------|-----------|---------------|
| Gerenciar projetos (CRUD) | X | | | |
| Gerenciar voos (CRUD) | X | | | |
| Upload de ortomapas | X | X (metadados, thumbnail) | | |
| Visualizar mapa (tiles) | X | X (tile serving) | | |
| Executar analises manuais (tools) | X | X (processamento) | | |
| Executar analises autonomas (agentes) | X (disparo) | X (fila) | X (execucao) | |
| Criar anotacoes manuais | X | | | |
| Criar anotacoes automaticas (deteccao) | | | X | |
| Medir distancia/area no mapa | X | | | |
| Comparar ortomapas (swipe/side-by-side) | X | X (tiles) | | |
| Exportar dados (6 formatos, 5 CRS) | X | X (conversao) | | |
| Gerar relatorios interpretativos | X (disparo) | | X (geracao) | |
| Monitorar status de agentes | X (visualizacao) | X (polling) | X (atualizacao) | |
| Configurar banco de dados | | | | X |
| Gerenciar servicos Docker | | | | X |
| Inicializar schema e seed | | X (fallback SQLite) | | X (schema/seed MySQL) |
| Backup e restauracao | | | | X |
| Health check | | X (endpoint /health) | | X (verificacao) |

# Arquitetura Observada - Sistema de Ortomapas

**Data da analise:** 2026-03-28
**Versao do sistema:** 1.0.0

---

## 1. Diagrama de Arquitetura

```
+------------------------------------------------------------------+
|                        USUARIO (Navegador)                        |
|  +------------------------------------------------------------+  |
|  |                Vue 3 + PrimeVue (SPA)                       |  |
|  |  +----------+  +----------+  +-----------+  +------------+ |  |
|  |  |ProjectList|  |MapViewer |  |ToolsPanel |  |CompareView | |  |
|  |  +----------+  +----------+  +-----------+  +------------+ |  |
|  |  |OrtomapCard|  |DrawTools |  |MeasureTools| |ExportDialog| |  |
|  |  +----------+  +----------+  +-----------+  +------------+ |  |
|  |  |VoosList  |  |LayerPanel|  |AgentStatus |  |AnalysisForm| |  |
|  |  +----------+  +----------+  +-----------+  +------------+ |  |
|  |  |AnalysisResults|                                          |  |
|  |  +------------------------------------------------------------+|
|  |              |                     |                            |
|  |  +-----------v-----+  +-----------v--------+                   |
|  |  | projectStore.js |  |   mapStore.js      |                   |
|  |  +-----------+-----+  +-----------+--------+                   |
|  |              |                     |                            |
|  |  +-----------v---------------------v--------+                   |
|  |  |          api/client.js (Axios)           |                   |
|  +--+-----------+------------------------------+------------------+
                   |
                   | HTTP/REST (proxy :5176 -> :8888)
                   v
+------------------------------------------------------------------+
|                    FastAPI Backend (:8888)                         |
|  +------------------------------------------------------------+  |
|  |  main.py (CORS, StaticFiles /data, Router Includes)         |  |
|  +------------------------------------------------------------+  |
|                                                                   |
|  +--Routes (prefix=/api)--------------------------------------+  |
|  |                                                             |  |
|  |  projetos.py    GET/POST/PUT/DELETE /api/projetos[/...]     |  |
|  |  voos.py        GET/POST/PUT/DELETE /api/voos[/...]         |  |
|  |  ortomapas.py   GET/POST/PUT/DELETE /api/ortomapas[/...]    |  |
|  |                 POST /api/ortomapas/upload                  |  |
|  |                 GET  /api/ortomapas/{id}/tile/{z}/{x}/{y}   |  |
|  |                 GET  /api/ortomapas/spatial                 |  |
|  |  analises.py    GET/POST/DELETE /api/analises[/...]         |  |
|  |                 GET /api/analises/{id}/resultado             |  |
|  |  anotacoes.py   GET/POST/PUT/DELETE /api/anotacoes[/...]    |  |
|  |                 GET /api/anotacoes/geojson/{ortomapa_id}    |  |
|  |  tools.py       POST /api/tools/{tool_name}                |  |
|  |                 (18 endpoints de analise espacial)          |  |
|  +-------------------------------------------------------------+  |
|                                                                   |
|  +--Tools Layer------------------------------------------------+  |
|  |  gdal_tools.py      (subprocess: gdalwarp, gdal_contour...) |  |
|  |  raster_analysis.py (numpy/rasterio: indices, terreno)      |  |
|  |  change_detection.py(alinhamento, diff, mascara binaria)    |  |
|  |  classification.py  (scikit-learn: RF, SVM, KMeans)         |  |
|  |  hydrology.py       (D8 flow, watershed, TWI)              |  |
|  |  volumetry.py       (corte/aterro, diferenca DSM)          |  |
|  |  segmentation.py    (KMeans clustering RGB)                 |  |
|  +-------------------------------------------------------------+  |
|                                                                   |
|  +--Utils Layer------------------------------------------------+  |
|  |  geo_utils.py    (metadados raster, conversao WKT/GeoJSON)  |  |
|  |  file_manager.py (upload, cleanup, file size)               |  |
|  |  thumbnail.py    (geracao de miniaturas PNG)                |  |
|  +-------------------------------------------------------------+  |
|                                                                   |
|  +--Agents (processo separado ou background)-------------------+  |
|  |  orchestrator.py  (polling tarefas_agentes, despacho)       |  |
|  |  vegetation_agent.py  -> tools/raster_analysis              |  |
|  |  detection_agent.py   -> ultralytics/YOLOv8                 |  |
|  |  change_agent.py      -> comparacao temporal                |  |
|  |  classification_agent.py -> scikit-learn                    |  |
|  |  report_agent.py      -> Anthropic API (Claude)             |  |
|  +-------------------------------------------------------------+  |
+------------------------------------------------------------------+
              |                    |
              v                    v
+------------------+    +------------------+
|   MySQL (:3308)  |    | SQLite (fallback)|
|   ortomapas DB   |    | data/ortomapas.db|
|   8 tabelas      |    | 8 tabelas        |
+------------------+    +------------------+
              |
              |    +---------------------------+
              |    | Sistema de Arquivos       |
              |    |  data/ortomapas/  (TIFF)  |
              |    |  data/dsm/       (TIFF)  |
              |    |  data/dtm/       (TIFF)  |
              |    |  data/analises/  (TIFF/  |
              |    |                  GeoJSON/|
              |    |                  MD)     |
              |    |  data/thumbnails/ (PNG)  |
              |    |  data/exports/   (temp)  |
              |    +---------------------------+
              |
+------------------------------------------------------------------+
|                   Docker Services                                 |
|  +------------------+  +------------------+  +------------------+ |
|  |   WebODM (:8000) |  | NodeODM (:3000)  |  | GeoServer(:8080)| |
|  |  Processamento   |  |  No ODM          |  |  WMS/WMTS       | |
|  |  fotogrametrico   |  |                  |  |  Publicacao     | |
|  +------------------+  +------------------+  +------------------+ |
|  +------------------+  +------------------+                       |
|  | PostgreSQL (int) |  | Redis (broker)   |                       |
|  | (WebODM DB)      |  | (fila tarefas)   |                       |
|  +------------------+  +------------------+                       |
+------------------------------------------------------------------+
```

---

## 2. Fluxo de Comunicacao

### 2.1 Frontend <-> Backend

```
Browser (:5176)
    |
    | Vite Dev Proxy: /api/* -> http://localhost:8888/api/*
    |                 /data/* -> http://localhost:8888/data/*
    |
    v
FastAPI (:8888)
    |
    | JSON (Content-Type: application/json)
    | multipart/form-data (upload)
    | image/png (tiles)
    | application/octet-stream (download resultado)
    |
    v
Respostas: JSON, StreamingResponse (tiles), FileResponse (arquivos)
```

### 2.2 Backend <-> Banco de Dados

```
FastAPI / Agents
    |
    | mysql.connector.pooling (pool_size=5)
    | ou SQLite (fallback automatico)
    |
    | Protocolo: SQL via %s placeholders
    | Adaptacao: SQLite cursor wrapper converte %s -> ?
    |
    v
MySQL (:3308) ou SQLite (data/ortomapas.db)
```

### 2.3 Backend <-> Sistema de Arquivos

```
Upload: UploadFile -> file_manager.save_upload() -> data/ortomapas/
Tiles:  rasterio.open() -> window read -> PIL -> PNG stream
Analise: tools/*.py -> rasterio.open() -> numpy -> rasterio.write() -> data/analises/
Thumbnail: rasterio.open() -> PIL resize -> data/thumbnails/
Export: gdal_tools -> data/exports/
```

### 2.4 Agents <-> Servicos Externos

```
DetectionAgent -> ultralytics.YOLO (local, model weights file)
ReportAgent    -> anthropic.Anthropic() -> api.anthropic.com (Claude API)
                  Fallback: template-based report se API indisponivel
```

---

## 3. Fluxo de Dados Completo

### Captura (Drone) -> Processamento -> Armazenamento -> Visualizacao -> Analise

```
1. CAPTURA
   DJI Mini 3 -> Fotos JPEG/RAW -> SD Card
                                          |
2. PROCESSAMENTO                          v
   Upload fotos -> WebODM (:8000) -> NodeODM (:3000)
                                          |
                            Ortomosaico GeoTIFF + DSM + DTM
                                          |
3. UPLOAD/ARMAZENAMENTO                   v
   POST /api/ortomapas/upload
   -> save_upload() -> data/ortomapas/
   -> get_raster_info() (bbox, resolucao, CRS, dimensoes)
   -> generate_thumbnail() -> data/thumbnails/
   -> INSERT INTO ortomapas (metadados)
                                          |
4. VISUALIZACAO                           v
   GET /api/ortomapas/{id}/tile/{z}/{x}/{y}.png
   -> rasterio window read -> numpy -> PIL -> PNG 256x256
   -> Leaflet L-tile-layer no frontend
   -> Alternancia basemaps (OSM, Satellite)
   -> Controle opacidade por camada
                                          |
5. ANALISE ESPACIAL                       v
   POST /api/tools/{ferramenta}
   -> tools/*.py (rasterio + numpy + scikit-learn + GDAL)
   -> Resultado GeoTIFF ou GeoJSON -> data/analises/
   -> Camada adicionada ao mapa via mapStore.addLayer()
                                          |
6. AGENTES DE IA                          v
   INSERT INTO tarefas_agentes (tarefa pendente)
   -> Orchestrator polling (10s)
   -> Agent.execute(task)
   -> INSERT INTO analises (resultado)
   -> INSERT INTO anotacoes (deteccoes)
                                          |
7. EXPORTACAO                             v
   POST /api/tools/exportar
   -> gdal_translate / rasterio
   -> Download blob (GeoTIFF, PNG, JPEG, KML, GeoJSON)
```

---

## 4. Padrao de Camadas (Layered Architecture)

```
+---------------------------------------------------+
|              Apresentacao (Vue 3 SPA)              |
|  Componentes, Stores, API Client                   |
+---------------------------------------------------+
|              API REST (FastAPI Routers)             |
|  Endpoints HTTP, validacao, serializacao            |
+---------------------------------------------------+
|              Logica de Negocio                      |
|  Tools (analise), Agents (autonomos), Utils         |
+---------------------------------------------------+
|              Acesso a Dados                         |
|  connection.py, models.py (Pydantic schemas)        |
+---------------------------------------------------+
|              Persistencia                           |
|  MySQL / SQLite, Sistema de Arquivos (GeoTIFF)     |
+---------------------------------------------------+
|              Infraestrutura                         |
|  Docker (WebODM, GeoServer), GDAL CLI              |
+---------------------------------------------------+
```

---

## 5. Protocolos e Formatos

| Conexao | Protocolo | Formato |
|---------|-----------|---------|
| Frontend <-> Backend | HTTP/1.1 REST | JSON, multipart/form-data, image/png |
| Backend <-> MySQL | MySQL Protocol (TCP:3308) | SQL |
| Backend <-> SQLite | Embedded (sqlite3) | SQL |
| Backend <-> GDAL | subprocess (CLI) | Argumentos CLI + arquivos |
| Backend <-> Rasterio | Python API | NumPy arrays |
| Backend <-> YOLOv8 | Python API (ultralytics) | NumPy arrays / tensors |
| Backend <-> Claude | HTTPS (api.anthropic.com) | JSON |
| Tile Server | HTTP GET | PNG 256x256 |
| Anotacoes | WKT (armazenamento), GeoJSON (exportacao) | Texto/JSON |
| Raster I/O | GeoTIFF (LZW compressed) | Binario |

---

## 6. Decisoes Arquiteturais Observadas

1. **Monolito com potencial de desacoplamento**: Backend unico com separacao clara em routers/tools/agents
2. **Fallback de banco de dados**: MySQL primario com SQLite automatico se MySQL indisponivel
3. **Tile server embutido**: Sem necessidade de tile server externo; tiles gerados on-the-fly via rasterio
4. **Agentes como processo separado**: Orchestrator pode rodar como `python -m backend.agents.orchestrator`
5. **CORS permissivo**: `allow_origins=["*"]` para desenvolvimento
6. **Static file serving**: Diretorio `data/` montado diretamente via FastAPI StaticFiles
7. **Sem autenticacao**: Nenhum middleware de autenticacao implementado (sistema para uso local/pesquisa)
8. **Proxy Vite**: Frontend em dev proxeia `/api` e `/data` para o backend

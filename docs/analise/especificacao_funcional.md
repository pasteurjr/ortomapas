# Especificacao Funcional - Sistema de Ortomapas

**Data da analise:** 2026-03-28
**Versao do sistema:** 1.0.0

---

## EF-PRJ: Projetos

### EF-PRJ-01: Listar Projetos

| Campo | Descricao |
|-------|-----------|
| **ID** | EF-PRJ-01 |
| **Descricao** | Listar todos os projetos com filtros opcionais por status e area de estudo |
| **Entrada** | Query params opcionais: `status` (string), `area_estudo` (string, LIKE) |
| **Saida** | `{total: int, projetos: [{id, nome, descricao, area_estudo, status, ...}]}` |
| **Endpoint** | `GET /api/projetos` |
| **Componente** | `ProjectList.vue` |
| **Regras** | Ordenacao por criado_em DESC. Filtro area_estudo usa LIKE %termo%. |

### EF-PRJ-02: Buscar Projetos

| Campo | Descricao |
|-------|-----------|
| **ID** | EF-PRJ-02 |
| **Descricao** | Busca fulltext em nome, descricao e area_estudo |
| **Entrada** | Query param obrigatorio: `q` (string, min_length=1) |
| **Saida** | `{total: int, projetos: [...]}` |
| **Endpoint** | `GET /api/projetos/search` |
| **Componente** | `App.vue` (campo de busca na toolbar) |
| **Regras** | LIKE %q% aplicado em 3 campos simultaneamente (OR). Ordenacao por criado_em DESC. |

### EF-PRJ-03: Detalhar Projeto

| Campo | Descricao |
|-------|-----------|
| **ID** | EF-PRJ-03 |
| **Descricao** | Obter detalhes de um projeto com contagens de entidades relacionadas |
| **Entrada** | Path param: `projeto_id` (int) |
| **Saida** | `{id, nome, ..., total_voos: int, total_ortomapas: int, total_analises: int}` |
| **Endpoint** | `GET /api/projetos/{projeto_id}` |
| **Componente** | `ProjectList.vue` |
| **Regras** | Retorna 404 se projeto nao existe. Contagens obtidas via COUNT(*) em voos, ortomapas, analises. |

### EF-PRJ-04: Criar Projeto

| Campo | Descricao |
|-------|-----------|
| **ID** | EF-PRJ-04 |
| **Descricao** | Criar um novo projeto de mapeamento |
| **Entrada** | JSON body: `{nome: string (obrigatorio), descricao: string, area_estudo: string, status: string}` |
| **Saida** | Registro completo do projeto criado (HTTP 201) |
| **Endpoint** | `POST /api/projetos` |
| **Componente** | `ProjectList.vue` |
| **Regras** | Campo `nome` obrigatorio (400 se ausente). Status default "ativo". Timestamp criado_em preenchido automaticamente. |

### EF-PRJ-05: Atualizar Projeto

| Campo | Descricao |
|-------|-----------|
| **ID** | EF-PRJ-05 |
| **Descricao** | Atualizar campos de um projeto existente |
| **Entrada** | Path: `projeto_id`. Body: `{nome?, descricao?, area_estudo?, status?}` |
| **Saida** | Registro atualizado do projeto |
| **Endpoint** | `PUT /api/projetos/{projeto_id}` |
| **Componente** | `ProjectList.vue` |
| **Regras** | 404 se projeto nao existe. 400 se nenhum campo para atualizar. Timestamp atualizado_em preenchido. Apenas campos nome, descricao, area_estudo, status sao atualizaveis. |

### EF-PRJ-06: Excluir Projeto

| Campo | Descricao |
|-------|-----------|
| **ID** | EF-PRJ-06 |
| **Descricao** | Excluir um projeto |
| **Entrada** | Path: `projeto_id` |
| **Saida** | `{message: "Projeto deletado com sucesso", id: int}` |
| **Endpoint** | `DELETE /api/projetos/{projeto_id}` |
| **Componente** | `ProjectList.vue` |
| **Regras** | 404 se projeto nao existe. Nao remove voos/ortomapas associados (sem cascading delete). |

### EF-PRJ-07: Listar Ortomapas de Projeto

| Campo | Descricao |
|-------|-----------|
| **ID** | EF-PRJ-07 |
| **Descricao** | Listar todos os ortomapas de um projeto especifico |
| **Entrada** | Path: `projeto_id` |
| **Saida** | `{total: int, ortomapas: [...]}` |
| **Endpoint** | `GET /api/projetos/{projeto_id}/ortomapas` |
| **Componente** | `OrtomapCard.vue` |
| **Regras** | 404 se projeto nao existe. Ordenacao por criado_em DESC. |

---

## EF-VOO: Voos

### EF-VOO-01: Listar Voos

| Campo | Descricao |
|-------|-----------|
| **ID** | EF-VOO-01 |
| **Descricao** | Listar todos os voos com filtro opcional por projeto |
| **Entrada** | Query param opcional: `projeto_id` (int) |
| **Saida** | `{total: int, voos: [...]}` |
| **Endpoint** | `GET /api/voos` |
| **Componente** | `VoosList.vue` |
| **Regras** | Ordenacao por data_voo DESC. |

### EF-VOO-02: Detalhar Voo

| Campo | Descricao |
|-------|-----------|
| **ID** | EF-VOO-02 |
| **Descricao** | Obter detalhes completos de um voo |
| **Entrada** | Path: `voo_id` |
| **Saida** | Registro completo do voo (22+ campos) |
| **Endpoint** | `GET /api/voos/{voo_id}` |
| **Componente** | `VoosList.vue` |
| **Regras** | 404 se voo nao existe. |

### EF-VOO-03: Registrar Voo

| Campo | Descricao |
|-------|-----------|
| **ID** | EF-VOO-03 |
| **Descricao** | Registrar um novo voo de drone |
| **Entrada** | JSON body com 22 campos. Obrigatorio: `projeto_id`. Defaults: resolucao_foto="48MP", formato_foto="JPEG", tipo_bateria="standard", app_voo="Litchi Pilot" |
| **Saida** | Registro completo do voo criado (HTTP 201) |
| **Endpoint** | `POST /api/voos` |
| **Componente** | `VoosList.vue` |
| **Regras** | 400 se projeto_id ausente. 404 se projeto nao existe. |

### EF-VOO-04: Atualizar Voo

| Campo | Descricao |
|-------|-----------|
| **ID** | EF-VOO-04 |
| **Descricao** | Atualizar campos de um voo |
| **Entrada** | Path: `voo_id`. Body com campos atualizaveis: data_voo, drone, camera, altitude_voo, sobreposicao_*, num_fotos, area_coberta_ha, gsd_cm, observacoes, status |
| **Saida** | Registro atualizado do voo |
| **Endpoint** | `PUT /api/voos/{voo_id}` |
| **Componente** | `VoosList.vue` |
| **Regras** | 404 se voo nao existe. 400 se nenhum campo para atualizar. |

### EF-VOO-05: Excluir Voo

| Campo | Descricao |
|-------|-----------|
| **ID** | EF-VOO-05 |
| **Descricao** | Excluir um voo |
| **Entrada** | Path: `voo_id` |
| **Saida** | `{message: "Voo deletado com sucesso", id: int}` |
| **Endpoint** | `DELETE /api/voos/{voo_id}` |
| **Componente** | `VoosList.vue` |
| **Regras** | 404 se voo nao existe. |

---

## EF-ORT: Ortomapas

### EF-ORT-01: Listar Ortomapas

| Campo | Descricao |
|-------|-----------|
| **ID** | EF-ORT-01 |
| **Descricao** | Listar ortomapas com filtros por projeto, tipo e status |
| **Entrada** | Query params opcionais: `projeto_id`, `tipo`, `status` |
| **Saida** | `{total: int, ortomapas: [...]}` |
| **Endpoint** | `GET /api/ortomapas` |
| **Componente** | `OrtomapCard.vue` |
| **Regras** | Ordenacao por criado_em DESC. |

### EF-ORT-02: Detalhar Ortomapa

| Campo | Descricao |
|-------|-----------|
| **ID** | EF-ORT-02 |
| **Descricao** | Obter metadados completos de um ortomapa |
| **Entrada** | Path: `ortomapa_id` |
| **Saida** | Registro completo (30+ campos) |
| **Endpoint** | `GET /api/ortomapas/{ortomapa_id}` |
| **Componente** | `OrtomapCard.vue` |
| **Regras** | 404 se ortomapa nao existe. |

### EF-ORT-03: Criar Ortomapa (metadados)

| Campo | Descricao |
|-------|-----------|
| **ID** | EF-ORT-03 |
| **Descricao** | Criar registro de ortomapa com metadados manuais |
| **Entrada** | JSON body. Obrigatorio: `projeto_id`. Defaults: tipo="ortomosaico", formato="GeoTIFF", sistema_coordenadas="EPSG:4326", status="processando" |
| **Saida** | Registro criado (HTTP 201) |
| **Endpoint** | `POST /api/ortomapas` |
| **Componente** | `OrtomapCard.vue` |
| **Regras** | 400 se projeto_id ausente. 404 se projeto nao existe. |

### EF-ORT-04: Upload de Ortomapa (GeoTIFF)

| Campo | Descricao |
|-------|-----------|
| **ID** | EF-ORT-04 |
| **Descricao** | Upload de arquivo GeoTIFF com extracao automatica de metadados |
| **Entrada** | multipart/form-data: `file` (obrigatorio). Query params: `projeto_id` (obrigatorio), `nome`, `voo_id`, `tipo` (default "ortomosaico") |
| **Saida** | `{ortomapa: {...}, raster_info: {bbox, resolution, size, crs, bands}, file_size_mb: float}` (HTTP 201) |
| **Endpoint** | `POST /api/ortomapas/upload` |
| **Componente** | `OrtomapCard.vue` |
| **Regras** | 404 se projeto nao existe. Arquivo salvo em data/ortomapas/ com nome sanitizado + UUID. Metadados extraidos via rasterio: bbox, resolucao (convertida para cm), largura, altura, CRS, tamanho. Thumbnail PNG gerado automaticamente. Se CRS nao e WGS84, bounds reprojetados para EPSG:4326. Status definido como "disponivel". |

### EF-ORT-05: Atualizar Ortomapa

| Campo | Descricao |
|-------|-----------|
| **ID** | EF-ORT-05 |
| **Descricao** | Atualizar metadados de um ortomapa |
| **Entrada** | Path: `ortomapa_id`. Body com campos atualizaveis: nome, tipo, caminho_arquivo, resolucao_cm, bbox_*, largura_px, altura_px, tamanho_arquivo_mb, sistema_coordenadas, status, observacoes |
| **Saida** | Registro atualizado |
| **Endpoint** | `PUT /api/ortomapas/{ortomapa_id}` |
| **Componente** | `OrtomapCard.vue` |
| **Regras** | 404 se nao existe. 400 se nenhum campo para atualizar. |

### EF-ORT-06: Excluir Ortomapa

| Campo | Descricao |
|-------|-----------|
| **ID** | EF-ORT-06 |
| **Descricao** | Excluir ortomapa e opcionalmente seu arquivo |
| **Entrada** | Path: `ortomapa_id` |
| **Saida** | `{message: "Ortomapa deletado com sucesso", id: int}` |
| **Endpoint** | `DELETE /api/ortomapas/{ortomapa_id}` |
| **Componente** | `OrtomapCard.vue` |
| **Regras** | 404 se nao existe. Arquivo GeoTIFF removido do filesystem se existir. |

### EF-ORT-07: Tile Server (TMS)

| Campo | Descricao |
|-------|-----------|
| **ID** | EF-ORT-07 |
| **Descricao** | Servir tiles raster 256x256 no formato TMS |
| **Entrada** | Path: `ortomapa_id`, `z` (zoom), `x`, `y` (coordenadas tile) |
| **Saida** | PNG 256x256 (image/png) via StreamingResponse |
| **Endpoint** | `GET /api/ortomapas/{ortomapa_id}/tile/{z}/{x}/{y}.png` |
| **Componente** | `MapViewer.vue` (L-tile-layer) |
| **Regras** | 404 se ortomapa ou arquivo nao existe. Coordenadas TMS convertidas para bounds geograficos. Se tile fora dos bounds do raster: retorna tile transparente RGBA. Window clamped aos bounds do raster. Dados lidos via rasterio window. 3 bandas (RGB) ou 1 banda (grayscale). Nodata tratado como alpha=0. Dados normalizados para uint8 se necessario. Resize para 256x256 via PIL LANCZOS. |

### EF-ORT-08: Consulta Espacial

| Campo | Descricao |
|-------|-----------|
| **ID** | EF-ORT-08 |
| **Descricao** | Consultar ortomapas que intersectam um bounding box |
| **Entrada** | Query params obrigatorios: `norte`, `sul`, `leste`, `oeste` (float) |
| **Saida** | `{total: int, ortomapas: [...]}` |
| **Endpoint** | `GET /api/ortomapas/spatial` |
| **Componente** | - |
| **Regras** | Intersecao calculada como: bbox_norte >= sul AND bbox_sul <= norte AND bbox_leste >= oeste AND bbox_oeste <= leste. Ordenacao por criado_em DESC. |

---

## EF-ANA: Analises

### EF-ANA-01: Listar Analises

| Campo | Descricao |
|-------|-----------|
| **ID** | EF-ANA-01 |
| **Descricao** | Listar analises com filtros |
| **Entrada** | Query params opcionais: `ortomapa_id`, `projeto_id`, `tipo_analise`, `status` |
| **Saida** | `{total: int, analises: [...]}` |
| **Endpoint** | `GET /api/analises` |
| **Componente** | `AnalysisResults.vue` |
| **Regras** | Ordenacao por criado_em DESC. |

### EF-ANA-02: Detalhar Analise

| Campo | Descricao |
|-------|-----------|
| **ID** | EF-ANA-02 |
| **Descricao** | Obter detalhes de uma analise |
| **Entrada** | Path: `analise_id` |
| **Saida** | Registro completo |
| **Endpoint** | `GET /api/analises/{analise_id}` |
| **Componente** | `AnalysisResults.vue` |
| **Regras** | 404 se nao existe. |

### EF-ANA-03: Criar Analise

| Campo | Descricao |
|-------|-----------|
| **ID** | EF-ANA-03 |
| **Descricao** | Criar analise e opcionalmente enfileirar tarefa de agente |
| **Entrada** | JSON body. Obrigatorios: `ortomapa_id`, `tipo_analise`. Opcionais: `parametros`, `status`, `queue_task` (bool) |
| **Saida** | Registro criado (HTTP 201) |
| **Endpoint** | `POST /api/analises` |
| **Componente** | `AnalysisForm.vue` |
| **Regras** | 400 se ortomapa_id ou tipo_analise ausente. 404 se ortomapa nao existe. Se queue_task=true: insere registro na tabela tarefas_agente com tipo=analise_{tipo}. |

### EF-ANA-04: Download de Resultado

| Campo | Descricao |
|-------|-----------|
| **ID** | EF-ANA-04 |
| **Descricao** | Baixar arquivo de resultado de uma analise |
| **Entrada** | Path: `analise_id` |
| **Saida** | FileResponse (application/octet-stream) |
| **Endpoint** | `GET /api/analises/{analise_id}/resultado` |
| **Componente** | `AnalysisResults.vue` |
| **Regras** | 404 se analise ou arquivo nao existe. |

### EF-ANA-05: Excluir Analise

| Campo | Descricao |
|-------|-----------|
| **ID** | EF-ANA-05 |
| **Descricao** | Excluir analise e seu arquivo resultado |
| **Entrada** | Path: `analise_id` |
| **Saida** | `{message: "Analise deletada com sucesso", id: int}` |
| **Endpoint** | `DELETE /api/analises/{analise_id}` |
| **Componente** | `AnalysisResults.vue` |
| **Regras** | 404 se nao existe. Remove arquivo de resultado do filesystem se existir. |

---

## EF-ANO: Anotacoes

### EF-ANO-01: Listar Anotacoes

| Campo | Descricao |
|-------|-----------|
| **ID** | EF-ANO-01 |
| **Descricao** | Listar anotacoes com filtros |
| **Entrada** | Query params opcionais: `ortomapa_id`, `projeto_id` (via subquery), `categoria`, `fonte` |
| **Saida** | `{total: int, anotacoes: [...]}` |
| **Endpoint** | `GET /api/anotacoes` |
| **Componente** | `MapViewer.vue` |
| **Regras** | Filtro por projeto_id usa subquery: ortomapa_id IN (SELECT id FROM ortomapas WHERE projeto_id=?). Ordenacao por criado_em DESC. |

### EF-ANO-02: Detalhar Anotacao

| Campo | Descricao |
|-------|-----------|
| **ID** | EF-ANO-02 |
| **Descricao** | Obter detalhes de uma anotacao |
| **Entrada** | Path: `anotacao_id` |
| **Saida** | Registro completo |
| **Endpoint** | `GET /api/anotacoes/{anotacao_id}` |
| **Componente** | - |
| **Regras** | 404 se nao existe. |

### EF-ANO-03: Criar Anotacao

| Campo | Descricao |
|-------|-----------|
| **ID** | EF-ANO-03 |
| **Descricao** | Criar anotacao com geometria WKT |
| **Entrada** | JSON body. Obrigatorios: `ortomapa_id`, `geometria_wkt`. Opcionais: tipo (default "poligono"), categoria, rotulo, centro_lat/lon, area_m2, atributos (JSON), confianca, fonte (default "manual"), criado_por |
| **Saida** | Registro criado (HTTP 201) |
| **Endpoint** | `POST /api/anotacoes` |
| **Componente** | `DrawTools.vue` |
| **Regras** | 400 se ortomapa_id ou geometria_wkt ausente. 404 se ortomapa nao existe. geometria_wkt validada via wkt_to_geojson() antes de salvar (400 se invalida). Atributos serializados como JSON. |

### EF-ANO-04: Atualizar Anotacao

| Campo | Descricao |
|-------|-----------|
| **ID** | EF-ANO-04 |
| **Descricao** | Atualizar campos de uma anotacao |
| **Entrada** | Path: `anotacao_id`. Body com campos atualizaveis: categoria, rotulo, geometria_wkt, tipo, fonte, confianca, centro_lat, centro_lon, criado_por |
| **Saida** | Registro atualizado |
| **Endpoint** | `PUT /api/anotacoes/{anotacao_id}` |
| **Componente** | - |
| **Regras** | 404 se nao existe. 400 se nenhum campo para atualizar. Se geometria_wkt presente: revalidada via wkt_to_geojson() (400 se invalida). |

### EF-ANO-05: Excluir Anotacao

| Campo | Descricao |
|-------|-----------|
| **ID** | EF-ANO-05 |
| **Descricao** | Excluir uma anotacao |
| **Entrada** | Path: `anotacao_id` |
| **Saida** | `{message: "Anotacao deletada com sucesso", id: int}` |
| **Endpoint** | `DELETE /api/anotacoes/{anotacao_id}` |
| **Componente** | - |
| **Regras** | 404 se nao existe. |

### EF-ANO-06: Exportar Anotacoes como GeoJSON

| Campo | Descricao |
|-------|-----------|
| **ID** | EF-ANO-06 |
| **Descricao** | Exportar todas as anotacoes de um ortomapa como GeoJSON FeatureCollection |
| **Entrada** | Path: `ortomapa_id` |
| **Saida** | `{type: "FeatureCollection", features: [{type: "Feature", id, geometry, properties}], totalFeatures: int}` |
| **Endpoint** | `GET /api/anotacoes/geojson/{ortomapa_id}` |
| **Componente** | `ExportDialog.vue` |
| **Regras** | 404 se ortomapa nao existe. Cada anotacao convertida: geometria_wkt -> GeoJSON geometry via wkt_to_geojson(). Se conversao falha para uma anotacao: geometry=null, log warning. Properties inclui todos os campos exceto geometria_wkt. Datetime convertido para ISO string. |

---

## EF-VEG: Indices de Vegetacao

### EF-VEG-01: Calcular Indice de Vegetacao

| Campo | Descricao |
|-------|-----------|
| **ID** | EF-VEG-01 |
| **Descricao** | Calcular indice de vegetacao visivel a partir de ortomapa RGB |
| **Entrada** | `{input_path: string, output_name: string, index_name: "VARI"|"TGI"|"ExG"|"GLI"}` |
| **Saida** | `{status: "success", output_path: string, statistics: {band_1: {min, max, mean, std, median, histogram, valid_pixels, total_pixels}}}` |
| **Endpoint** | `POST /api/tools/vegetation` |
| **Componente** | `ToolsPanel.vue` (aba Vegetacao) |
| **Regras** | Bandas lidas como float64 (R=banda1, G=banda2, B=banda3). Formulas: VARI=(G-R)/(G+R-B), TGI=G-0.39*R-0.61*B, ExG=2*G-R-B, GLI=(2*G-R-B)/(2*G+R+B). Divisao por zero tratada com epsilon 1e-10. Valores extremos clampados a [-1e6, 1e6]. Nodata=-9999. Output GeoTIFF float32 com compressao LZW. Estatisticas calculadas apos geracao. |

---

## EF-TER: Terreno

### EF-TER-01: Calcular Declividade (Slope)

| Campo | Descricao |
|-------|-----------|
| **ID** | EF-TER-01 |
| **Descricao** | Calcular slope em graus a partir de DSM/DTM |
| **Entrada** | `{input_path: string, output_name: string}` |
| **Saida** | `{status: "success", output_path: string, statistics: {...}}` |
| **Endpoint** | `POST /api/tools/slope` |
| **Componente** | `ToolsPanel.vue` (aba Terreno) |
| **Regras** | Gradiente calculado via numpy.gradient com cell size da transform. slope = degrees(arctan(sqrt(dx^2 + dy^2))). Nodata substituido por NaN antes do calculo. Output float32, nodata=-9999, LZW. |

### EF-TER-02: Calcular Aspecto (Aspect)

| Campo | Descricao |
|-------|-----------|
| **ID** | EF-TER-02 |
| **Descricao** | Calcular aspect em graus (0=Norte, 90=Leste, 180=Sul, 270=Oeste) |
| **Entrada** | `{input_path: string, output_name: string}` |
| **Saida** | `{status: "success", output_path: string, statistics: {...}}` |
| **Endpoint** | `POST /api/tools/aspect` |
| **Componente** | `ToolsPanel.vue` (aba Terreno) |
| **Regras** | Angulo calculado via arctan2(-grad_y, grad_x). Convertido de angulo matematico para bearing compasso: compass = 90 - math_angle, normalizado 0-360. Output float32. |

### EF-TER-03: Gerar Hillshade

| Campo | Descricao |
|-------|-----------|
| **ID** | EF-TER-03 |
| **Descricao** | Gerar sombreamento de relevo |
| **Entrada** | `{input_path: string, output_name: string, azimuth: float (default 315), altitude: float (default 45)}` |
| **Saida** | `{status: "success", output_path: string}` |
| **Endpoint** | `POST /api/tools/hillshade` |
| **Componente** | `ToolsPanel.vue` (aba Terreno) |
| **Regras** | Executado via subprocess: `gdaldem hillshade -az -alt -compute_edges`. |

### EF-TER-04: Gerar Curvas de Nivel

| Campo | Descricao |
|-------|-----------|
| **ID** | EF-TER-04 |
| **Descricao** | Gerar curvas de nivel como GeoJSON |
| **Entrada** | `{input_path: string, output_name: string, interval: float (default 5.0)}` |
| **Saida** | `{status: "success", output_path: string}` |
| **Endpoint** | `POST /api/tools/contours` |
| **Componente** | `ToolsPanel.vue` (aba Terreno) |
| **Regras** | Executado via subprocess: `gdal_contour -a elevation -i {interval} -f GeoJSON`. Output em formato GeoJSON. |

---

## EF-MUD: Deteccao de Mudancas

### EF-MUD-01: Detectar Mudancas entre Ortomapas

| Campo | Descricao |
|-------|-----------|
| **ID** | EF-MUD-01 |
| **Descricao** | Detectar mudancas entre dois ortomapas de datas diferentes |
| **Entrada** | `{raster1_path: string, raster2_path: string, output_name: string, threshold: float (default 30.0)}` |
| **Saida** | `{status: "success", output_path: string, statistics: {total_pixels, changed_pixels, unchanged_pixels, percent_changed, area_changed_m2, area_changed_ha}}` |
| **Endpoint** | `POST /api/tools/changes` |
| **Componente** | `ToolsPanel.vue` (aba Mudancas) |
| **Regras** | Rasters alinhados ao mesmo grid (raster1 como referencia). Diferenca absoluta media entre bandas. Mascara binaria: 255=mudou (diff > threshold), 0=nao mudou. Area calculada como pixels * pixel_area_m2. Estatisticas incluem area em m2 e hectares. |

---

## EF-CLA: Classificacao

### EF-CLA-01: Classificar Ortomapa

| Campo | Descricao |
|-------|-----------|
| **ID** | EF-CLA-01 |
| **Descricao** | Classificar cobertura do solo via KMeans, Random Forest ou SVM |
| **Entrada** | `{ortomapa_path: string, algorithm: "kmeans"|"random_forest"|"svm" (default "kmeans"), n_clusters: int (default 7), training_samples: [{class_name, geometry_wkt}] (opcional)}` |
| **Saida** | `{status: "success", output_path: string, result: {...}}` |
| **Endpoint** | `POST /api/tools/classify` |
| **Componente** | `ToolsPanel.vue` (aba Classificacao) |
| **Regras** | KMeans: subsampling 100k pixels, n_init=10, max_iter=300, clustering em RGB normalizado [0,1]. RF/SVM: requer training_samples, 6 features (R,G,B,VARI,TGI,ExG), train/test split 80/20, accuracy + kappa reportados. Filtro de maioria 3x3 aplicado apos classificacao. 7 classes: vegetacao_densa, vegetacao_rasteira, solo_exposto, agua, urbano, agricola, rocha. |

---

## EF-HID: Hidrologia

### EF-HID-01: Delimitar Bacia Hidrografica

| Campo | Descricao |
|-------|-----------|
| **ID** | EF-HID-01 |
| **Descricao** | Delimitar bacia hidrografica a partir de ponto de exutorio |
| **Entrada** | `{dtm_path: string, pour_point: {lat, lon}, output_name: string}` |
| **Saida** | `{status: "success", output_path: string}` |
| **Endpoint** | `POST /api/tools/hydrology/watershed` |
| **Componente** | `ToolsPanel.vue` (aba Hidrologia) |
| **Regras** | Pipeline: fill_sinks -> flow_direction (D8) -> BFS upstream do pour point. Pour point convertido de coordenadas geo para pixel. Erro se pour point fora do raster. Output: mascara binaria (1=bacia, 0=fora). Arquivos intermediarios em tempfile (removidos apos). |

### EF-HID-02: Extrair Rede de Drenagem

| Campo | Descricao |
|-------|-----------|
| **ID** | EF-HID-02 |
| **Descricao** | Extrair rede de cursos dagua |
| **Entrada** | `{dtm_path: string, output_name: string, threshold: int (default 100)}` |
| **Saida** | `{status: "success", output_path: string}` (GeoJSON) |
| **Endpoint** | `POST /api/tools/hydrology/streams` |
| **Componente** | `ToolsPanel.vue` (aba Hidrologia) |
| **Regras** | Pipeline: fill_sinks -> flow_direction -> flow_accumulation (topological sort) -> threshold -> vectorize (rasterio.features.shapes). Output GeoJSON com features de poligono. Arquivos intermediarios nomeados com prefixo output_name. |

---

## EF-VOL: Volumetria

### EF-VOL-01: Calcular Volume

| Campo | Descricao |
|-------|-----------|
| **ID** | EF-VOL-01 |
| **Descricao** | Calcular volume acima e abaixo de uma elevacao de referencia |
| **Entrada** | `{dsm_path: string, reference_elevation: float, output_name: string (opcional)}` |
| **Saida** | `{status: "success", volume_above_m3, volume_below_m3, net_volume_m3, reference_elevation_m, pixel_area_m2, output_path}` |
| **Endpoint** | `POST /api/tools/volume` |
| **Componente** | `ToolsPanel.vue` (aba Volume) |
| **Regras** | Volume = sum(diff) * pixel_area. Se CRS geografico: pixel_area calculada com conversao graus->metros usando latitude central. Output opcional: GeoTIFF da diferenca em relacao ao plano. |

### EF-VOL-02: Diferenca de DSMs (Cut-Fill)

| Campo | Descricao |
|-------|-----------|
| **ID** | EF-VOL-02 |
| **Descricao** | Calcular diferenca entre dois DSMs e analise corte/aterro |
| **Entrada** | `{dsm1_path: string, dsm2_path: string, output_name: string}` |
| **Saida** | `{status: "success", output_path, min_diff_m, max_diff_m, mean_diff_m, std_diff_m, cut_volume_m3, fill_volume_m3, cut_area_m2, fill_area_m2, net_volume_m3}` |
| **Endpoint** | `POST /api/tools/volume/difference` |
| **Componente** | `ToolsPanel.vue` (aba Volume) |
| **Regras** | Diff = dsm2 - dsm1. Cut: diff < -0.1m. Fill: diff > 0.1m. Volumes e areas calculados com pixel_area. |

---

## EF-SEG: Segmentacao

### EF-SEG-01: Segmentar Ortomapa

| Campo | Descricao |
|-------|-----------|
| **ID** | EF-SEG-01 |
| **Descricao** | Segmentar ortomapa usando KMeans clustering |
| **Entrada** | `{input_path: string, output_name: string, n_clusters: int (default 7)}` |
| **Saida** | `{status: "success", output_path, n_clusters, total_valid_pixels, clusters: [{cluster, pixel_count, area_m2, area_ha, center_rgb, percent}]}` |
| **Endpoint** | `POST /api/tools/segment` |
| **Componente** | - |
| **Regras** | Subsampling a 100k pixels para fit. RGB normalizado [0,1]. Labels 1-based (0=nodata). Estatisticas por cluster: contagem, area, percentual, centroide RGB. |

---

## EF-MAP: Mapa Interativo

### EF-MAP-01: Visualizacao de Ortomapas

| Campo | Descricao |
|-------|-----------|
| **ID** | EF-MAP-01 |
| **Descricao** | Exibir ortomapas como camadas tile no mapa Leaflet |
| **Entrada** | Selecao de ortomapa pelo usuario |
| **Saida** | Tiles PNG renderizados no mapa |
| **Endpoint** | `GET /api/ortomapas/{id}/tile/{z}/{x}/{y}.png` |
| **Componente** | `MapViewer.vue` (L-tile-layer com URL template) |
| **Regras** | URL template: `/api/ortomapas/${sourceId}/tile/{z}/{x}/{y}.png`. Max zoom: 22. Opacidade controlavel via slider. |

### EF-MAP-02: Basemaps

| Campo | Descricao |
|-------|-----------|
| **ID** | EF-MAP-02 |
| **Descricao** | Alternar entre mapas base |
| **Entrada** | Clique nos botoes do basemap switcher |
| **Saida** | Troca de tile layer base |
| **Componente** | `MapViewer.vue` |
| **Regras** | 2 basemaps: OSM (openstreetmap.org), Satellite (ArcGIS World_Imagery). Mutuamente exclusivos. |

### EF-MAP-03: Coordenadas e Zoom

| Campo | Descricao |
|-------|-----------|
| **ID** | EF-MAP-03 |
| **Descricao** | Exibir coordenadas do cursor e nivel de zoom |
| **Saida** | Lat/Lng com 6 casas decimais, zoom level |
| **Componente** | `App.vue` (status bar), `MapViewer.vue` (eventos mousemove) |
| **Regras** | Atualizado a cada movimento do mouse via mapStore.setCursorCoords(). |

---

## EF-FER: Painel de Ferramentas

### EF-FER-01: Painel com 8 Abas

| Campo | Descricao |
|-------|-----------|
| **ID** | EF-FER-01 |
| **Descricao** | Painel lateral direito com 8 abas de ferramentas de analise |
| **Componente** | `ToolsPanel.vue` |
| **Regras** | Abas: Veg, Ter, Cls, Hid, Mud, Vol, Rec, Exp. Cada aba tem: seletor de input, parametros especificos, botao de execucao com loading state. Resultados adicionados como camadas no mapa via mapStore.addLayer(). |

---

## EF-MED: Medicoes

### EF-MED-01: Medir Distancia

| Campo | Descricao |
|-------|-----------|
| **ID** | EF-MED-01 |
| **Descricao** | Medir distancia no mapa por cliques sucessivos |
| **Entrada** | Cliques no mapa (pontos da polyline) |
| **Saida** | Polyline amarela tracejada com markers nos vertices |
| **Componente** | `MeasureTools.vue`, `MapViewer.vue` |
| **Regras** | Ativado via mapStore.setMeasureMode('distance'). Desativa drawMode. Pontos acumulados via clique. |

### EF-MED-02: Medir Area

| Campo | Descricao |
|-------|-----------|
| **ID** | EF-MED-02 |
| **Descricao** | Medir area no mapa por poligono |
| **Entrada** | Cliques no mapa (vertices do poligono) |
| **Saida** | Poligono amarelo semi-transparente com markers |
| **Componente** | `MeasureTools.vue`, `MapViewer.vue` |
| **Regras** | Ativado via mapStore.setMeasureMode('area'). Minimo 3 pontos. |

---

## EF-DES: Desenho e Anotacao

### EF-DES-01: Ferramentas de Desenho

| Campo | Descricao |
|-------|-----------|
| **ID** | EF-DES-01 |
| **Descricao** | Desenhar geometrias no mapa e salvar como anotacoes |
| **Entrada** | Interacao do usuario com ferramentas de desenho |
| **Saida** | Geometria WKT salva como anotacao via POST /api/anotacoes |
| **Componente** | `DrawTools.vue` |
| **Regras** | 4 modos: point, line, polygon, rectangle. Ativado via mapStore.setDrawMode(). Desativa measureMode. Geometria convertida para WKT. Anotacao criada com tipo, categoria e rotulo configurados. |

---

## EF-EXP: Exportacao

### EF-EXP-01: Exportar Camada

| Campo | Descricao |
|-------|-----------|
| **ID** | EF-EXP-01 |
| **Descricao** | Exportar ortomapa ou camada de analise em formato escolhido |
| **Entrada** | `{layer_id, format: "geotiff"|"png"|"jpeg"|"kml"|"geojson"|"shapefile", crs: "EPSG:..."}` |
| **Saida** | Download de arquivo blob |
| **Componente** | `ExportDialog.vue`, `ToolsPanel.vue` (aba Exportar) |
| **Regras** | 6 formatos suportados. 5 CRS disponiveis (WGS84, SIRGAS UTM 23S/24S, WGS84 UTM 23S/24S). Download via URL.createObjectURL + elemento <a>. |

---

## EF-COM: Comparacao Temporal

### EF-COM-01: Comparacao Swipe e Side-by-Side

| Campo | Descricao |
|-------|-----------|
| **ID** | EF-COM-01 |
| **Descricao** | Comparar visualmente dois ortomapas de datas diferentes |
| **Entrada** | Selecao de ortomapa esquerdo e direito |
| **Saida** | Visualizacao lado a lado ou com controle deslizante |
| **Componente** | `CompareView.vue` |
| **Regras** | Ativado via mapStore.setCompareMode(true). Usa leaflet-side-by-side para swipe. CompareView substitui MapViewer quando ativo. Camadas definidas via mapStore.setCompareLayers(left, right). |

---

## EF-AGI: Agentes de IA

### EF-AGI-01: Orquestrador de Agentes

| Campo | Descricao |
|-------|-----------|
| **ID** | EF-AGI-01 |
| **Descricao** | Sistema de fila e despacho de tarefas para agentes especializados |
| **Entrada** | Tarefa na tabela tarefas_agentes com status=pendente |
| **Saida** | Resultado na tabela tarefas_agentes e analises |
| **Componente** | `AgentStatus.vue` (monitoramento) |
| **Regras** | Polling 10s. Selecao atomica (FOR UPDATE). Despacho por campo `agente`. 5 agentes registrados: agente_vegetacao, agente_deteccao, agente_classificacao, agente_mudanca, agente_relatorio. Retry: ate max_tentativas (default 3). Status: pendente -> em_execucao -> concluido/erro. |

### EF-AGI-02: Agente de Vegetacao

| Campo | Descricao |
|-------|-----------|
| **ID** | EF-AGI-02 |
| **Descricao** | Analise autonoma de vegetacao com indices e classificacao |
| **Entrada** | task.parametros: `{index: string, threshold_high: float, threshold_low: float}` |
| **Saida** | GeoTIFF do indice, GeoTIFF classificado, estatisticas, registro em analises |
| **Regras** | 8 indices disponiveis (VARI, TGI, ExG, ExR, ExGR, GLI, RGBVI, MGRVI). 3 classes: saudavel (>threshold_high), estressada (entre thresholds), sem_vegetacao (<threshold_low). Defaults: high=0.1, low=-0.1. |

### EF-AGI-03: Agente de Deteccao

| Campo | Descricao |
|-------|-----------|
| **ID** | EF-AGI-03 |
| **Descricao** | Deteccao de objetos via YOLOv8 com tiling |
| **Entrada** | task.parametros: `{model_path, confidence_threshold, iou_threshold, classes}` |
| **Saida** | GeoJSON com deteccoes, anotacoes individuais, registro em analises |
| **Regras** | Tiles 640x640 com overlap 64px. Padding para tiles menores. NMS cross-tile por classe. Coordenadas pixel convertidas para geo via transform. Cada deteccao: bbox WKT como anotacao com fonte="ia". |

### EF-AGI-04: Agente de Mudancas

| Campo | Descricao |
|-------|-----------|
| **ID** | EF-AGI-04 |
| **Descricao** | Deteccao e classificacao de mudancas temporais |
| **Entrada** | task.parametros: `{ortomapa_antes_id, ortomapa_depois_id, threshold}` |
| **Saida** | GeoTIFF classificado, estatisticas, registro em analises e comparacoes_temporais |
| **Regras** | Ambos ortomapas obrigatorios. Intersecao espacial verificada (erro se nao overlap). 5 classes de mudanca: desmatamento, construcao, erosao, inundacao, outro. Classificacao heuristica baseada em banda dominante e sinal da diferenca. |

### EF-AGI-05: Agente de Classificacao

| Campo | Descricao |
|-------|-----------|
| **ID** | EF-AGI-05 |
| **Descricao** | Classificacao autonoma de cobertura do solo |
| **Entrada** | task.parametros: `{algorithm, n_clusters, training_samples, smooth}` |
| **Saida** | GeoTIFF classificado, estatisticas por classe, registro em analises |
| **Regras** | Se training_samples fornecido: forca random_forest. 6 features por pixel. Subsampling 500k para KMeans. Filtro maioria 3x3 por default. |

### EF-AGI-06: Agente de Relatorio

| Campo | Descricao |
|-------|-----------|
| **ID** | EF-AGI-06 |
| **Descricao** | Geracao de relatorio consolidado com IA |
| **Entrada** | task.parametros: `{analise_ids: [int], projeto_id, language}` |
| **Saida** | Arquivo Markdown, registro em analises |
| **Regras** | Coleta dados de multiplas analises. Tenta Anthropic API (Claude claude-sonnet-4-20250514, max_tokens=4096). Se API indisponivel: relatorio template com secoes fixas. Secoes: Resumo Executivo, Resultados, Observacoes, Recomendacoes. |

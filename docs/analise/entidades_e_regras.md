# Entidades e Regras de Negocio - Sistema de Ortomapas

**Data da analise:** 2026-03-28
**Versao do sistema:** 1.0.0

---

## 1. Visao Geral das Entidades

O sistema possui 8 tabelas no banco de dados (MySQL primario / SQLite fallback):

| # | Tabela | Campos | FK | Descricao |
|---|--------|--------|----|-----------|
| 1 | projetos | 17 | - | Projetos de mapeamento aereo |
| 2 | voos | 23 | projeto_id | Registros de voo do drone |
| 3 | ortomapas | 31 | voo_id, projeto_id | Metadados de ortomosaicos GeoTIFF |
| 4 | analises | 18 | ortomapa_id, projeto_id | Resultados de analises espaciais |
| 5 | anotacoes | 15 | ortomapa_id, analise_id (nullable) | Geometrias e rotulos sobre ortomapas |
| 6 | gcps | 13 | projeto_id, voo_id (nullable) | Pontos de controle de solo |
| 7 | comparacoes_temporais | 12 | projeto_id, ortomapa_antes_id, ortomapa_depois_id | Comparacoes entre ortomapas |
| 8 | tarefas_agentes | 14 | ortomapa_id | Fila de tarefas dos agentes de IA |

---

## 2. Diagrama de Entidades e Relacionamentos

```
+-------------------+       +-------------------+
|     projetos      |       |       gcps        |
|-------------------|       |-------------------|
| PK id             |<------| FK projeto_id     |
|    nome           |   |   | FK voo_id (opt)   |
|    descricao      |   |   |    nome           |
|    area_estudo    |   |   |    latitude       |
|    bbox_*         |   |   |    longitude      |
|    centro_lat/lon |   |   |    altitude_m     |
|    objetivo       |   |   |    precisao_*     |
|    responsavel    |   |   |    metodo_coleta  |
|    data_inicio/fim|   |   |    equipamento    |
|    status         |   |   |    data_coleta    |
|    criado_em      |   |   |    criado_em      |
|    atualizado_em  |   |   +-------------------+
+--------+----------+
         |
         | 1:N
         v
+-------------------+       +------------------------+
|       voos        |       |  comparacoes_temporais |
|-------------------|       |------------------------|
| PK id             |       | PK id                  |
| FK projeto_id     |       | FK projeto_id          |
|    data_voo       |       | FK ortomapa_antes_id   |
|    local_lat/lon  |       | FK ortomapa_depois_id  |
|    altitude_voo_m |       |    data_antes/depois   |
|    sobreposicao_* |       |    tipo_comparacao     |
|    velocidade_ms  |       |    resultado_path      |
|    num_fotos      |       |    resultado_thumbnail |
|    resolucao_foto |       |    estatisticas (JSON) |
|    formato_foto   |       |    criado_em           |
|    gsd_cm         |       +------------------------+
|    area_coberta_ha|
|    num_baterias   |
|    tipo_bateria   |
|    condicoes_*    |
|    temperatura_c  |
|    app_voo        |
|    missao_csv_path|
|    fotos_path     |
|    observacoes    |
|    criado_em      |
+--------+----------+
         |
         | 1:N
         v
+-------------------+
|    ortomapas      |
|-------------------|
| PK id             |
| FK voo_id         |
| FK projeto_id     |
|    nome           |
|    tipo           |
|    formato        |
|    resolucao_cm   |
|    largura_px     |
|    altura_px      |
|    tamanho_mb     |
|    sistema_coords |
|    bbox_*         |
|    centro_lat/lon |
|    caminho_arquivo|
|    caminho_thumb  |
|    webodm_task_id |
|    parametros_proc|
|    qualidade_proc |
|    num_fotos_proc |
|    tempo_proc_min |
|    erro_rms       |
|    gcps_utilizados|
|    num_gcps       |
|    status         |
|    data_processam.|
|    observacoes    |
|    criado_em      |
|    atualizado_em  |
+--------+----------+
         |
    +----+--------+
    |              |
    | 1:N          | 1:N
    v              v
+-------------------+    +-------------------+
|     analises      |    |    anotacoes      |
|-------------------|    |-------------------|
| PK id             |    | PK id             |
| FK ortomapa_id    |    | FK ortomapa_id    |
| FK projeto_id     |    | FK analise_id(opt)|
|    tipo_analise   |    |    tipo           |
|    nome           |    |    categoria      |
|    descricao      |    |    rotulo         |
|    parametros     |    |    geometria_wkt  |
|    resultado_path |    |    centro_lat/lon |
|    resultado_thumb|    |    area_m2        |
|    resultado_json |    |    atributos(JSON)|
|    modelo_ia      |    |    confianca      |
|    versao_modelo  |    |    fonte          |
|    metricas       |    |    criado_por     |
|    agente_ia      |    |    criado_em      |
|    status         |    +-------------------+
|    tempo_proc_seg |
|    data_analise   |
|    observacoes    |
|    criado_em      |
+-------------------+

+------------------------+
|   tarefas_agentes      |
|------------------------|
| PK id                  |
| FK ortomapa_id         |
|    tipo_tarefa         |
|    agente              |
|    prioridade          |
|    parametros (JSON)   |
|    status              |
|    resultado (JSON)    |
|    erro_msg            |
|    tentativas          |
|    max_tentativas      |
|    inicio_execucao     |
|    fim_execucao        |
|    criado_em           |
+------------------------+
```

---

## 3. Detalhamento das Entidades

### 3.1 projetos

| Atributo | Tipo | Obrigatorio | Default | Descricao |
|----------|------|-------------|---------|-----------|
| id | INTEGER PK AUTO | Sim (auto) | AUTO_INCREMENT | Identificador unico |
| nome | TEXT (max 255) | **Sim** | - | Nome do projeto |
| descricao | TEXT | Nao | NULL | Descricao detalhada |
| area_estudo | TEXT (max 255) | Nao | NULL | Local de estudo (ex: "Fazenda Norte") |
| bbox_norte | REAL | Nao | NULL | Latitude norte do bounding box |
| bbox_sul | REAL | Nao | NULL | Latitude sul do bounding box |
| bbox_leste | REAL | Nao | NULL | Longitude leste do bounding box |
| bbox_oeste | REAL | Nao | NULL | Longitude oeste do bounding box |
| centro_lat | REAL | Nao | NULL | Latitude do centro do projeto |
| centro_lon | REAL | Nao | NULL | Longitude do centro do projeto |
| objetivo | TEXT | Nao | NULL | Objetivo do projeto |
| responsavel | TEXT (max 255) | Nao | NULL | Nome do responsavel |
| data_inicio | DATE | Nao | NULL | Data de inicio prevista |
| data_fim | DATE | Nao | NULL | Data de conclusao prevista |
| status | TEXT | Nao | 'planejado' | Estado atual do projeto |
| criado_em | TIMESTAMP | Sim (auto) | CURRENT_TIMESTAMP | Data de criacao |
| atualizado_em | TIMESTAMP | Sim (auto) | CURRENT_TIMESTAMP | Data da ultima atualizacao |

**Chaves Estrangeiras:** Nenhuma. Entidade raiz.

**Status validos:** `planejado`, `ativo`, `em_andamento`, `concluido`, `arquivado`

**Transicoes de status:**
```
planejado -> ativo -> em_andamento -> concluido -> arquivado
                                   \-> arquivado
```

**Regras de negocio:**

| # | Regra | Descricao |
|---|-------|-----------|
| RN-PRJ-01 | Nome obrigatorio | Campo `nome` e obrigatorio e nao pode ser vazio (HTTP 400 se ausente) |
| RN-PRJ-02 | Status default | Se nao informado, status inicia como `planejado` |
| RN-PRJ-03 | Busca fulltext | Busca pesquisa em nome, descricao e area_estudo via LIKE %q% |
| RN-PRJ-04 | Filtros de listagem | Listagem pode ser filtrada por status e area_estudo |
| RN-PRJ-05 | Contagens relacionadas | GET /api/projetos/{id} retorna num_ortomapas e num_analises |
| RN-PRJ-06 | Exclusao simples | DELETE remove apenas o registro; sem cascade automatico |

---

### 3.2 voos

| Atributo | Tipo | Obrigatorio | Default | Descricao |
|----------|------|-------------|---------|-----------|
| id | INTEGER PK AUTO | Sim (auto) | AUTO_INCREMENT | Identificador unico |
| projeto_id | INTEGER FK | **Sim** | - | Referencia ao projeto |
| data_voo | TIMESTAMP | **Sim** | - | Data e hora do voo |
| local_decolagem_lat | REAL | Nao | NULL | Latitude de decolagem |
| local_decolagem_lon | REAL | Nao | NULL | Longitude de decolagem |
| altitude_voo_m | REAL | Nao | NULL | Altitude em metros |
| sobreposicao_frontal | REAL | Nao | NULL | Sobreposicao frontal (%) |
| sobreposicao_lateral | REAL | Nao | NULL | Sobreposicao lateral (%) |
| velocidade_ms | REAL | Nao | NULL | Velocidade em m/s |
| num_fotos | INTEGER | Nao | NULL | Numero de fotos capturadas |
| resolucao_foto | TEXT (max 50) | Nao | NULL | Resolucao da foto (ex: "48MP") |
| formato_foto | TEXT (max 20) | Nao | NULL | Formato (JPEG, RAW, DNG) |
| gsd_cm | REAL | Nao | NULL | Ground Sampling Distance em cm/px |
| area_coberta_ha | REAL | Nao | NULL | Area coberta em hectares |
| num_baterias | INTEGER | Nao | NULL | Baterias utilizadas |
| tipo_bateria | TEXT (max 100) | Nao | NULL | Tipo/modelo da bateria |
| condicoes_vento | TEXT (max 100) | Nao | NULL | Condicoes de vento |
| condicoes_ceu | TEXT (max 100) | Nao | NULL | Condicoes do ceu |
| temperatura_c | REAL | Nao | NULL | Temperatura em Celsius |
| app_voo | TEXT (max 100) | Nao | NULL | Aplicativo de voo |
| missao_csv_path | TEXT (max 500) | Nao | NULL | Caminho do CSV de missao |
| fotos_path | TEXT (max 500) | Nao | NULL | Caminho das fotos |
| observacoes | TEXT | Nao | NULL | Observacoes |
| criado_em | TIMESTAMP | Sim (auto) | CURRENT_TIMESTAMP | Data de criacao |

**Chaves Estrangeiras:**

| FK | Tabela | Campo | Cascade |
|----|--------|-------|---------|
| projeto_id | projetos | id | Nao (aplicacao) |

**Regras de negocio:**

| # | Regra | Descricao |
|---|-------|-----------|
| RN-VOO-01 | Projeto obrigatorio | Campo `projeto_id` e obrigatorio |
| RN-VOO-02 | Data obrigatoria | Campo `data_voo` e obrigatorio no Pydantic model |
| RN-VOO-03 | Filtro por projeto | Listagem filtrada por projeto_id (query param) |
| RN-VOO-04 | Carregamento reativo | Frontend recarrega voos ao trocar de projeto ativo |

---

### 3.3 ortomapas

| Atributo | Tipo | Obrigatorio | Default | Descricao |
|----------|------|-------------|---------|-----------|
| id | INTEGER PK AUTO | Sim (auto) | AUTO_INCREMENT | Identificador unico |
| voo_id | INTEGER FK | **Sim** | - | Referencia ao voo |
| projeto_id | INTEGER FK | **Sim** | - | Referencia ao projeto |
| nome | TEXT (max 255) | **Sim** | - | Nome do ortomapa |
| tipo | TEXT | Nao | 'ortomosaico' | Tipo: ortomosaico, DSM, DTM, NDVI, multispectral, RGB |
| formato | TEXT (max 50) | Nao | NULL | Formato do arquivo (GeoTIFF) |
| resolucao_cm | REAL | Nao | NULL | Resolucao em cm/pixel |
| largura_px | INTEGER | Nao | NULL | Largura em pixels |
| altura_px | INTEGER | Nao | NULL | Altura em pixels |
| tamanho_arquivo_mb | REAL | Nao | NULL | Tamanho do arquivo em MB |
| sistema_coordenadas | TEXT (max 100) | Nao | NULL | CRS (ex: EPSG:4326) |
| bbox_norte | REAL | Nao | NULL | Latitude norte |
| bbox_sul | REAL | Nao | NULL | Latitude sul |
| bbox_leste | REAL | Nao | NULL | Longitude leste |
| bbox_oeste | REAL | Nao | NULL | Longitude oeste |
| centro_lat | REAL | Nao | NULL | Latitude do centro |
| centro_lon | REAL | Nao | NULL | Longitude do centro |
| caminho_arquivo | TEXT (max 500) | Nao | NULL | Caminho relativo do GeoTIFF |
| caminho_thumbnail | TEXT (max 500) | Nao | NULL | Caminho do thumbnail PNG |
| webodm_task_id | TEXT (max 255) | Nao | NULL | ID da tarefa no WebODM |
| parametros_processamento | TEXT (JSON) | Nao | NULL | Parametros de processamento |
| qualidade_processamento | TEXT (max 50) | Nao | NULL | Qualidade do processamento |
| num_fotos_processadas | INTEGER | Nao | NULL | Numero de fotos processadas |
| tempo_processamento_min | INTEGER | Nao | NULL | Tempo em minutos |
| erro_rms | REAL | Nao | NULL | Erro RMS em metros |
| gcps_utilizados | INTEGER | Nao | 0 | Se GCPs foram utilizados (0/1) |
| num_gcps | INTEGER | Nao | 0 | Numero de GCPs utilizados |
| status | TEXT | Nao | 'processando' | Estado do processamento |
| data_processamento | TEXT | Nao | NULL | Data do processamento |
| observacoes | TEXT | Nao | NULL | Observacoes |
| criado_em | TIMESTAMP | Sim (auto) | CURRENT_TIMESTAMP | Data de criacao |
| atualizado_em | TIMESTAMP | Sim (auto) | CURRENT_TIMESTAMP | Data da ultima atualizacao |

**Chaves Estrangeiras:**

| FK | Tabela | Campo | Cascade |
|----|--------|-------|---------|
| voo_id | voos | id | Nao (aplicacao) |
| projeto_id | projetos | id | Nao (aplicacao) |

**Status validos:** `pendente`, `processando`, `pronto`, `disponivel`, `erro`

**Transicoes de status:**
```
pendente -> processando -> pronto/disponivel
                        \-> erro -> processando (retry)
```

**Regras de negocio:**

| # | Regra | Descricao |
|---|-------|-----------|
| RN-ORT-01 | Nome obrigatorio | Campo `nome` e obrigatorio |
| RN-ORT-02 | FKs obrigatorias | `voo_id` e `projeto_id` sao obrigatorios no Pydantic model |
| RN-ORT-03 | Upload extracao | No upload GeoTIFF, extrai automaticamente bbox, resolucao, CRS, dimensoes via rasterio |
| RN-ORT-04 | Thumbnail automatico | Gera PNG 512x512 ao fazer upload via PIL |
| RN-ORT-05 | Tamanho automatico | Calcula tamanho_arquivo_mb via get_file_size_mb() |
| RN-ORT-06 | Sanitizacao de nome | Caracteres nao-alfanumericos substituidos por `_`, UUID parcial (8 chars) adicionado |
| RN-ORT-07 | Upload em chunks | Upload salvo em chunks de 1MB para eficiencia de memoria |
| RN-ORT-08 | Reprojecao de bounds | Se CRS nao e EPSG:4326, bounds sao reprojetados para WGS84 |
| RN-ORT-09 | Exclusao com arquivo | DELETE remove o registro e tenta deletar o arquivo fisico do disco |
| RN-ORT-10 | Tiles on-the-fly | Tiles 256x256 PNG gerados dinamicamente via rasterio window read |
| RN-ORT-11 | Consulta espacial | Filtragem por bounding box via GET /ortomapas/spatial |
| RN-ORT-12 | Resolucao em cm | Resolucao convertida de metros para centimetros (metros * 100) |

---

### 3.4 analises

| Atributo | Tipo | Obrigatorio | Default | Descricao |
|----------|------|-------------|---------|-----------|
| id | INTEGER PK AUTO | Sim (auto) | AUTO_INCREMENT | Identificador unico |
| ortomapa_id | INTEGER FK | **Sim** | - | Ortomapa analisado |
| projeto_id | INTEGER FK | **Sim** | - | Projeto associado |
| tipo_analise | TEXT | **Sim** | - | Tipo da analise |
| nome | TEXT (max 255) | **Sim** | - | Nome da analise |
| descricao | TEXT | Nao | NULL | Descricao |
| parametros | TEXT (JSON) | Nao | NULL | Parametros utilizados |
| resultado_path | TEXT (max 500) | Nao | NULL | Caminho do arquivo resultado |
| resultado_thumbnail | TEXT (max 500) | Nao | NULL | Caminho do thumbnail do resultado |
| resultado_json | TEXT (JSON) | Nao | NULL | Resultado em formato JSON |
| modelo_ia | TEXT (max 255) | Nao | NULL | Modelo de IA utilizado |
| versao_modelo | TEXT (max 50) | Nao | NULL | Versao do modelo |
| metricas | TEXT (JSON) | Nao | NULL | Metricas de qualidade |
| agente_ia | TEXT (max 255) | Nao | NULL | Nome do agente executor |
| status | TEXT | Nao | 'em_fila' | Estado da analise |
| tempo_processamento_seg | INTEGER | Nao | NULL | Tempo em segundos |
| data_analise | TEXT | Nao | NULL | Data da execucao |
| observacoes | TEXT | Nao | NULL | Observacoes |
| criado_em | TIMESTAMP | Sim (auto) | CURRENT_TIMESTAMP | Data de criacao |

**Chaves Estrangeiras:**

| FK | Tabela | Campo | Cascade |
|----|--------|-------|---------|
| ortomapa_id | ortomapas | id | Nao (aplicacao) |
| projeto_id | projetos | id | Nao (aplicacao) |

**Status validos:** `em_fila`, `pendente`, `processando`, `concluida`, `erro`

**Transicoes de status:**
```
em_fila -> pendente -> processando -> concluida
                                   \-> erro
```

**Tipos de analise validos:** `indice_vegetacao`, `deteccao_objetos`, `deteccao_mudancas`, `classificacao_solo`, `personalizada`, `vegetacao`, `terreno`, `classificacao`, `mudancas`, `hidrologia`, `volume`, `segmentacao`

**Regras de negocio:**

| # | Regra | Descricao |
|---|-------|-----------|
| RN-ANA-01 | Campos obrigatorios | ortomapa_id, projeto_id, tipo_analise e nome sao obrigatorios |
| RN-ANA-02 | Enfileirar agente | Se agente_ia informado, cria tarefa correspondente em tarefas_agentes |
| RN-ANA-03 | Download resultado | GET /analises/{id}/resultado retorna FileResponse do resultado_path |
| RN-ANA-04 | Exclusao com arquivo | DELETE remove o registro e deleta arquivo de resultado se existir |
| RN-ANA-05 | Status default | Status inicia como 'em_fila' se via agente, 'pendente' se direto |

---

### 3.5 anotacoes

| Atributo | Tipo | Obrigatorio | Default | Descricao |
|----------|------|-------------|---------|-----------|
| id | INTEGER PK AUTO | Sim (auto) | AUTO_INCREMENT | Identificador unico |
| ortomapa_id | INTEGER FK | **Sim** | - | Ortomapa associado |
| analise_id | INTEGER FK (nullable) | Nao | NULL | Analise geradora (NULL se manual) |
| tipo | TEXT | **Sim** | - | Tipo geometrico: point, line, polygon, rectangle |
| categoria | TEXT (max 255) | Nao | NULL | vegetacao, construcao, agua, solo, erosao, infraestrutura |
| rotulo | TEXT (max 255) | Nao | NULL | Rotulo/nome da anotacao |
| geometria_wkt | TEXT | **Sim*** | NULL | Geometria em formato WKT |
| centro_lat | REAL | Nao | NULL | Latitude do centroide |
| centro_lon | REAL | Nao | NULL | Longitude do centroide |
| area_m2 | REAL | Nao | NULL | Area em metros quadrados |
| atributos | TEXT (JSON) | Nao | NULL | Atributos adicionais |
| confianca | REAL | Nao | NULL | Grau de confianca (0.0 a 1.0) |
| fonte | TEXT | Nao | 'manual' | Origem: 'manual' ou nome do agente |
| criado_por | TEXT (max 255) | Nao | NULL | Identificacao do criador |
| criado_em | TIMESTAMP | Sim (auto) | CURRENT_TIMESTAMP | Data de criacao |

**Chaves Estrangeiras:**

| FK | Tabela | Campo | Cascade | Observacao |
|----|--------|-------|---------|------------|
| ortomapa_id | ortomapas | id | Nao (aplicacao) | Obrigatoria |
| analise_id | analises | id | Nao (aplicacao) | Nullable -- NULL se manual |

**Regras de negocio:**

| # | Regra | Descricao |
|---|-------|-----------|
| RN-ANO-01 | Campos obrigatorios | ortomapa_id e tipo sao obrigatorios |
| RN-ANO-02 | Validacao WKT | geometria_wkt validada via wkt_to_geojson() (shapely) ao criar e atualizar |
| RN-ANO-03 | Fonte default | Se nao informada, fonte = 'manual' |
| RN-ANO-04 | Exportacao GeoJSON | GET /anotacoes/geojson/{ortomapa_id} exporta FeatureCollection completa |
| RN-ANO-05 | Categorias validas | vegetacao, construcao, agua, solo, erosao, infraestrutura |
| RN-ANO-06 | Confianca automatica | Campo confianca preenchido automaticamente quando fonte != 'manual' (deteccao IA) |
| RN-ANO-07 | Filtros de listagem | Filtro por ortomapa_id, projeto_id, categoria, fonte |

---

### 3.6 gcps

| Atributo | Tipo | Obrigatorio | Default | Descricao |
|----------|------|-------------|---------|-----------|
| id | INTEGER PK AUTO | Sim (auto) | AUTO_INCREMENT | Identificador unico |
| projeto_id | INTEGER FK | **Sim** | - | Projeto associado |
| voo_id | INTEGER FK (nullable) | Nao | NULL | Voo associado |
| nome | TEXT (max 255) | **Sim** | - | Nome/identificacao do GCP |
| latitude | REAL | **Sim** | - | Latitude do ponto |
| longitude | REAL | **Sim** | - | Longitude do ponto |
| altitude_m | REAL | Nao | NULL | Altitude em metros |
| precisao_horizontal_m | REAL | Nao | NULL | Precisao horizontal em metros |
| precisao_vertical_m | REAL | Nao | NULL | Precisao vertical em metros |
| metodo_coleta | TEXT (max 100) | Nao | NULL | Metodo: GPS, RTK, PPK, topografico |
| equipamento | TEXT (max 255) | Nao | NULL | Equipamento utilizado |
| data_coleta | TEXT | Nao | NULL | Data da coleta |
| observacoes | TEXT | Nao | NULL | Observacoes |
| criado_em | TIMESTAMP | Sim (auto) | CURRENT_TIMESTAMP | Data de criacao |

**Chaves Estrangeiras:**

| FK | Tabela | Campo | Cascade |
|----|--------|-------|---------|
| projeto_id | projetos | id | Nao (aplicacao) |
| voo_id | voos | id | Nao (aplicacao), nullable |

**Regras de negocio:**

| # | Regra | Descricao |
|---|-------|-----------|
| RN-GCP-01 | Campos obrigatorios | projeto_id, nome, latitude e longitude sao obrigatorios |
| RN-GCP-02 | Coordenadas validas | Latitude [-90, 90], Longitude [-180, 180] |
| RN-GCP-03 | Vinculo opcional ao voo | Pode ser vinculado a um voo especifico ou apenas ao projeto |

---

### 3.7 comparacoes_temporais

| Atributo | Tipo | Obrigatorio | Default | Descricao |
|----------|------|-------------|---------|-----------|
| id | INTEGER PK AUTO | Sim (auto) | AUTO_INCREMENT | Identificador unico |
| projeto_id | INTEGER FK | **Sim** | - | Projeto associado |
| ortomapa_antes_id | INTEGER FK | **Sim** | - | Ortomapa anterior (referencia temporal) |
| ortomapa_depois_id | INTEGER FK | **Sim** | - | Ortomapa posterior |
| data_antes | TEXT | Nao | NULL | Data do ortomapa anterior |
| data_depois | TEXT | Nao | NULL | Data do ortomapa posterior |
| tipo_comparacao | TEXT | **Sim** | - | Tipo: visual, ndvi, mudancas, deteccao_mudancas |
| resultado_path | TEXT (max 500) | Nao | NULL | Caminho do resultado |
| resultado_thumbnail | TEXT (max 500) | Nao | NULL | Caminho do thumbnail |
| estatisticas | TEXT (JSON) | Nao | NULL | Estatisticas da comparacao |
| observacoes | TEXT | Nao | NULL | Observacoes |
| criado_em | TIMESTAMP | Sim (auto) | CURRENT_TIMESTAMP | Data de criacao |

**Chaves Estrangeiras:**

| FK | Tabela | Campo | Cascade |
|----|--------|-------|---------|
| projeto_id | projetos | id | Nao (aplicacao) |
| ortomapa_antes_id | ortomapas | id | Nao (aplicacao) |
| ortomapa_depois_id | ortomapas | id | Nao (aplicacao) |

**Regras de negocio:**

| # | Regra | Descricao |
|---|-------|-----------|
| RN-COM-01 | Campos obrigatorios | projeto_id, ortomapa_antes_id, ortomapa_depois_id, tipo_comparacao |
| RN-COM-02 | Ortomapas distintos | ortomapa_antes_id != ortomapa_depois_id |
| RN-COM-03 | Mesmo projeto | Ambos ortomapas devem pertencer ao mesmo projeto |
| RN-COM-04 | Overlap espacial | Ortomapas devem ter intersecao espacial para comparacao |

---

### 3.8 tarefas_agentes

| Atributo | Tipo | Obrigatorio | Default | Descricao |
|----------|------|-------------|---------|-----------|
| id | INTEGER PK AUTO | Sim (auto) | AUTO_INCREMENT | Identificador unico |
| ortomapa_id | INTEGER FK | **Sim** | - | Ortomapa alvo da tarefa |
| tipo_tarefa | TEXT (max 255) | **Sim** | - | Tipo da tarefa |
| agente | TEXT (max 255) | **Sim** | - | Nome do agente executor |
| prioridade | INTEGER | Nao | 5 | Prioridade (1=maxima, 10=minima) |
| parametros | TEXT (JSON) | Nao | NULL | Parametros da tarefa |
| status | TEXT | Nao | 'pendente' | Estado da tarefa |
| resultado | TEXT (JSON) | Nao | NULL | Resultado da execucao |
| erro_msg | TEXT | Nao | NULL | Mensagem de erro |
| tentativas | INTEGER | Nao | 0 | Tentativas realizadas |
| max_tentativas | INTEGER | Nao | 3 | Maximo de tentativas |
| inicio_execucao | TEXT | Nao | NULL | Timestamp do inicio |
| fim_execucao | TEXT | Nao | NULL | Timestamp do fim |
| criado_em | TIMESTAMP | Sim (auto) | CURRENT_TIMESTAMP | Data de criacao |

**Chaves Estrangeiras:**

| FK | Tabela | Campo | Cascade |
|----|--------|-------|---------|
| ortomapa_id | ortomapas | id | Nao (aplicacao) |

**Status validos:** `pendente`, `em_execucao`, `concluida`, `erro`, `cancelada`

**Transicoes de status:**
```
pendente -> em_execucao -> concluida
                        \-> erro -> pendente (retry, se tentativas < max_tentativas)
                                 \-> cancelada (se tentativas >= max_tentativas)
```

**Tipos de tarefa validos:** `indice_vegetacao`, `deteccao_objetos`, `deteccao_mudancas`, `classificacao_solo`, `personalizada`

**Agentes validos:** `VegetationAgent`, `DetectionAgent`, `ChangeAgent`, `ClassificationAgent`, `ReportAgent`

**Regras de negocio:**

| # | Regra | Descricao |
|---|-------|-----------|
| RN-TAR-01 | Campos obrigatorios | ortomapa_id, tipo_tarefa e agente sao obrigatorios |
| RN-TAR-02 | Retry automatico | Se status='erro' e tentativas < max_tentativas, tarefa volta para 'pendente' |
| RN-TAR-03 | Max tentativas default | Default de 3 tentativas |
| RN-TAR-04 | Polling do orchestrator | Orchestrator faz polling a cada 10 segundos |
| RN-TAR-05 | Lock de tarefa | SELECT ... FOR UPDATE SKIP LOCKED (MySQL) para evitar processamento duplicado |
| RN-TAR-06 | Prioridade de despacho | Tarefas despachadas por ORDER BY prioridade ASC, criado_em ASC |
| RN-TAR-07 | Timestamps automaticos | inicio_execucao e fim_execucao preenchidos automaticamente pelo orchestrator |
| RN-TAR-08 | Resultado serializado | Resultado serializado como JSON no campo resultado |

---

## 4. Relacionamentos (Foreign Keys)

| Entidade Origem | Atributo FK | Entidade Destino | Cardinalidade | Obrigatoria |
|----------------|-------------|------------------|---------------|-------------|
| voos | projeto_id | projetos | N:1 | Sim |
| ortomapas | projeto_id | projetos | N:1 | Sim |
| ortomapas | voo_id | voos | N:1 | Sim |
| analises | ortomapa_id | ortomapas | N:1 | Sim |
| analises | projeto_id | projetos | N:1 | Sim |
| anotacoes | ortomapa_id | ortomapas | N:1 | Sim |
| anotacoes | analise_id | analises | N:1 | Nao (nullable) |
| gcps | projeto_id | projetos | N:1 | Sim |
| gcps | voo_id | voos | N:1 | Nao (nullable) |
| comparacoes_temporais | projeto_id | projetos | N:1 | Sim |
| comparacoes_temporais | ortomapa_antes_id | ortomapas | N:1 | Sim |
| comparacoes_temporais | ortomapa_depois_id | ortomapas | N:1 | Sim |
| tarefas_agentes | ortomapa_id | ortomapas | N:1 | Sim |

---

## 5. Regras de Exclusao

| Regra | Entidade | Descricao |
|-------|----------|-----------|
| RE-01 | projetos | DELETE remove apenas o registro do banco; nao cascateia para voos/ortomapas |
| RE-02 | voos | DELETE remove apenas o registro do banco |
| RE-03 | ortomapas | DELETE remove registro + arquivo GeoTIFF + thumbnail do filesystem |
| RE-04 | analises | DELETE remove registro + arquivo de resultado do filesystem |
| RE-05 | anotacoes | DELETE remove apenas o registro do banco |
| RE-06 | gcps | DELETE remove apenas o registro do banco |

**Observacao importante:** Nao ha ON DELETE CASCADE no banco de dados. A exclusao de um projeto nao remove automaticamente seus voos, ortomapas ou analises. Isso pode deixar registros orfaos.

---

## 6. Regras de Upload de GeoTIFF

| # | Regra | Descricao |
|---|-------|-----------|
| RU-01 | Sanitizacao | Caracteres nao-alfanumericos do nome substituidos por `_` |
| RU-02 | Unicidade | UUID parcial (8 chars) adicionado ao nome do arquivo |
| RU-03 | Chunks | Upload salvo em chunks de 1MB para eficiencia de memoria |
| RU-04 | Extracao | Metadados extraidos via rasterio: bbox, resolucao, CRS, dimensoes |
| RU-05 | Thumbnail | PNG 512x512 gerado automaticamente via PIL |
| RU-06 | Conversao | Resolucao convertida para centimetros (metros * 100) |
| RU-07 | Reprojecao | Se CRS nao e EPSG:4326, bounds sao reprojetados para WGS84 |

---

## 7. Regras de Validacao Global

| # | Regra | Descricao |
|---|-------|-----------|
| RV-01 | Charset | Banco usa utf8mb4 / utf8mb4_unicode_ci |
| RV-02 | Autocommit | MySQL configurado com autocommit=True |
| RV-03 | Fallback SQLite | Se MySQL indisponivel, schema recriado em SQLite automaticamente |
| RV-04 | Adaptacao SQL | Queries usam %s (MySQL), adaptado para ? (SQLite) pelo _SQLiteCursorWrapper |
| RV-05 | Campos JSON | parametros, resultado_json, metricas, estatisticas armazenados como TEXT e interpretados como JSON |
| RV-06 | Pool de conexoes | Pool de 5 conexoes MySQL com pool_reset_session=True |
| RV-07 | WKT obrigatorio para anotacoes | geometria_wkt validada via shapely wkt_to_geojson() |
| RV-08 | Expressao segura no calculator | Bloqueia import, exec, eval, __, open, os., sys., subprocess |

---

## 8. Regras dos Agentes de IA

| # | Regra | Descricao |
|---|-------|-----------|
| RA-01 | Polling 10s | Orchestrator faz polling da fila a cada 10 segundos |
| RA-02 | Ordem de despacho | Tarefas selecionadas por ORDER BY prioridade ASC, criado_em ASC |
| RA-03 | Atomicidade | Tarefa marcada como em_execucao atomicamente via SELECT ... FOR UPDATE |
| RA-04 | Falha com retry | tentativas incrementada; se < max_tentativas, status volta para pendente |
| RA-05 | Falha definitiva | Se tentativas >= max_tentativas, status = erro definitivo |
| RA-06 | Resultado JSON | Resultado serializado como JSON no campo resultado |
| RA-07 | Registro em analises | Cada agente registra resultado na tabela analises |
| RA-08 | Anotacoes de deteccao | DetectionAgent registra deteccoes individuais como anotacoes |
| RA-09 | Comparacoes | ChangeAgent registra na tabela comparacoes_temporais |
| RA-10 | Fallback Claude | ReportAgent tenta Anthropic API (Claude); fallback para template se indisponivel |

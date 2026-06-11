# Sistema de Ortomapas - Especificacao Completa

**Versao:** 1.0 | **Data:** Marco 2026
**Drone:** DJI Mini 3 | **Base:** Belo Horizonte, MG

---

## Sumario

1. [Visao Geral do Sistema](#1-visao-geral-do-sistema)
2. [Arquitetura do Sistema](#2-arquitetura-do-sistema)
3. [Repositorio de Ortomapas (Banco MySQL)](#3-repositorio-de-ortomapas-banco-mysql)
4. [Pipeline de Processamento](#4-pipeline-de-processamento)
5. [Visualizacao de Ortomapas](#5-visualizacao-de-ortomapas)
6. [Edicao e Alteracao de Ortomapas](#6-edicao-e-alteracao-de-ortomapas)
7. [Analises Espaciais](#7-analises-espaciais)
8. [Agentes de IA para Analise de Imagens](#8-agentes-de-ia-para-analise-de-imagens)
9. [Regioes de Interesse Proximas a BH](#9-regioes-de-interesse-proximas-a-bh)
10. [Tipos de Pesquisa com Imagens de Drone](#10-tipos-de-pesquisa-com-imagens-de-drone)
11. [Stack Tecnologico Completo](#11-stack-tecnologico-completo)
12. [Plano de Implementacao](#12-plano-de-implementacao)

---

## 1. Visao Geral do Sistema

O sistema de ortomapas e uma plataforma completa para:

- **Captura:** Planejamento e execucao de voos com DJI Mini 3 via Litchi Pilot
- **Processamento:** Geracao de ortomosaicos, DSM, DTM e nuvens de pontos via WebODM
- **Armazenamento:** Repositorio centralizado em banco MySQL com metadados geoespaciais
- **Visualizacao:** Interface web para visualizacao de ortomapas com camadas sobreposiveis
- **Edicao:** Ferramentas para anotacao, recorte, reclassificacao e exportacao
- **Analise Espacial:** Indices de vegetacao, deteccao de mudancas, classificacao de uso do solo
- **IA:** Agentes inteligentes para deteccao de objetos, analise de vegetacao e monitoramento

---

## 2. Arquitetura do Sistema

```
+------------------------------------------------------------------+
|                         CAPTURA                                   |
|  DJI Mini 3 + Litchi Pilot + Drone Grid Mission Planner          |
+------------------------------------------------------------------+
                              |
                              v
+------------------------------------------------------------------+
|                      PROCESSAMENTO                                |
|  WebODM/OpenDroneMap (Docker)                                     |
|  - Ortomosaico (GeoTIFF)                                         |
|  - DSM/DTM (GeoTIFF)                                             |
|  - Nuvem de Pontos (LAS/LAZ)                                     |
|  - Malha 3D (OBJ)                                                |
+------------------------------------------------------------------+
                              |
                              v
+------------------------------------------------------------------+
|                    ARMAZENAMENTO                                  |
|  MySQL (<YOUR_DB_HOST>:3308)                              |
|  - Metadados de projetos, voos, ortomapas                        |
|  - Indice espacial (bounding box, coordenadas)                   |
|  - Registro de analises e resultados                              |
|                                                                   |
|  Sistema de Arquivos / Object Storage                             |
|  - Arquivos GeoTIFF (ortomosaicos, DSM, DTM)                     |
|  - Nuvens de pontos (LAS/LAZ)                                    |
|  - Fotos originais do drone                                       |
|  - Thumbnails e previews                                          |
+------------------------------------------------------------------+
                              |
                              v
+------------------------------------------------------------------+
|                    SERVICOS                                        |
|  GeoServer (WMS/WFS/WMTS) - servir tiles de ortomapas            |
|  API Python (FastAPI/Flask) - CRUD, analises, agentes IA         |
|  WebODM API - disparo de processamentos                           |
+------------------------------------------------------------------+
                              |
                              v
+------------------------------------------------------------------+
|                   VISUALIZACAO / EDICAO                            |
|  Frontend Web (Leaflet/OpenLayers + React/Vue)                    |
|  QGIS Desktop (analise avancada)                                  |
|  Jupyter Notebooks (analise interativa)                           |
+------------------------------------------------------------------+
                              |
                              v
+------------------------------------------------------------------+
|                   AGENTES DE IA                                    |
|  Deteccao de Objetos (YOLOv8/v11)                                |
|  Classificacao de Uso do Solo (scikit-learn, SCP)                 |
|  Indices de Vegetacao (VARI, TGI, ExG)                            |
|  Deteccao de Mudancas (rasterio + numpy / deep learning)          |
|  Segmentacao (SAM - Segment Anything Model)                       |
|  Agente Claude/LLM para interpretacao e relatorios                |
+------------------------------------------------------------------+
```

---

## 3. Repositorio de Ortomapas (Banco MySQL)

### 3.1 Configuracao do Banco

```
Host: <YOUR_DB_HOST>
Porta: 3308
Usuario: producao
Senha: <YOUR_DB_PASSWORD>
Banco: ortomapas
```

### 3.2 Esquema do Banco de Dados

#### Tabela: `projetos`
Agrupa ortomapas por area de estudo ou campanha.

```sql
CREATE TABLE projetos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    descricao TEXT,
    area_estudo VARCHAR(255),          -- Ex: "Serra do Cipo", "Serra da Moeda"
    bbox_norte DOUBLE,                  -- Bounding box norte (latitude)
    bbox_sul DOUBLE,                    -- Bounding box sul (latitude)
    bbox_leste DOUBLE,                  -- Bounding box leste (longitude)
    bbox_oeste DOUBLE,                  -- Bounding box oeste (longitude)
    centro_lat DOUBLE,                  -- Centro da area (latitude)
    centro_lon DOUBLE,                  -- Centro da area (longitude)
    objetivo TEXT,                       -- Objetivo da pesquisa
    responsavel VARCHAR(255),
    data_inicio DATE,
    data_fim DATE,
    status ENUM('planejado','em_andamento','concluido','arquivado') DEFAULT 'planejado',
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

#### Tabela: `voos`
Registra cada voo realizado com o drone.

```sql
CREATE TABLE voos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    projeto_id INT NOT NULL,
    data_voo DATETIME NOT NULL,
    local_decolagem_lat DOUBLE,
    local_decolagem_lon DOUBLE,
    altitude_voo_m DOUBLE,             -- Altitude AGL em metros
    sobreposicao_frontal DOUBLE,       -- Percentual (ex: 75.0)
    sobreposicao_lateral DOUBLE,       -- Percentual (ex: 70.0)
    velocidade_ms DOUBLE,              -- Velocidade em m/s
    num_fotos INT,
    resolucao_foto VARCHAR(20),        -- Ex: "48MP", "12MP"
    formato_foto VARCHAR(10),          -- Ex: "JPEG", "DNG"
    gsd_cm DOUBLE,                     -- Ground Sampling Distance em cm/px
    area_coberta_ha DOUBLE,            -- Area coberta em hectares
    num_baterias INT,                  -- Baterias utilizadas
    tipo_bateria VARCHAR(50),          -- "standard" ou "plus"
    condicoes_vento VARCHAR(50),       -- Ex: "calmo", "moderado"
    condicoes_ceu VARCHAR(50),         -- Ex: "nublado", "ensolarado"
    temperatura_c DOUBLE,
    app_voo VARCHAR(50),               -- Ex: "Litchi Pilot 5.0"
    missao_csv_path VARCHAR(500),      -- Caminho do CSV da missao
    fotos_path VARCHAR(500),           -- Diretorio das fotos originais
    observacoes TEXT,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (projeto_id) REFERENCES projetos(id)
);
```

#### Tabela: `ortomapas`
Armazena metadados dos ortomosaicos gerados.

```sql
CREATE TABLE ortomapas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    voo_id INT NOT NULL,
    projeto_id INT NOT NULL,
    nome VARCHAR(255) NOT NULL,
    tipo ENUM('ortomosaico','dsm','dtm','nuvem_pontos','malha_3d') NOT NULL,
    formato VARCHAR(20),               -- Ex: "GeoTIFF", "LAS", "OBJ"
    resolucao_cm DOUBLE,               -- Resolucao final em cm/px
    largura_px INT,                    -- Largura em pixels
    altura_px INT,                     -- Altura em pixels
    tamanho_arquivo_mb DOUBLE,
    sistema_coordenadas VARCHAR(50),   -- Ex: "EPSG:4326", "EPSG:31983"
    bbox_norte DOUBLE,
    bbox_sul DOUBLE,
    bbox_leste DOUBLE,
    bbox_oeste DOUBLE,
    centro_lat DOUBLE,
    centro_lon DOUBLE,
    caminho_arquivo VARCHAR(500),      -- Caminho do arquivo no filesystem
    caminho_thumbnail VARCHAR(500),    -- Thumbnail para preview
    webodm_task_id VARCHAR(100),       -- ID da tarefa no WebODM
    parametros_processamento JSON,     -- Parametros usados no WebODM
    qualidade_processamento VARCHAR(20), -- "ultra","high","medium","low"
    num_fotos_processadas INT,
    tempo_processamento_min INT,       -- Tempo de processamento em minutos
    erro_rms DOUBLE,                   -- Erro RMS em metros
    gcps_utilizados BOOLEAN DEFAULT FALSE,
    num_gcps INT DEFAULT 0,
    status ENUM('processando','concluido','erro','arquivado') DEFAULT 'processando',
    data_processamento DATETIME,
    observacoes TEXT,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (voo_id) REFERENCES voos(id),
    FOREIGN KEY (projeto_id) REFERENCES projetos(id)
);
```

#### Tabela: `analises`
Registra analises espaciais e de IA realizadas sobre os ortomapas.

```sql
CREATE TABLE analises (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ortomapa_id INT NOT NULL,
    projeto_id INT NOT NULL,
    tipo_analise ENUM(
        'indice_vegetacao',     -- VARI, TGI, ExG
        'classificacao_solo',   -- Uso e cobertura do solo
        'deteccao_objetos',     -- YOLO, detectron2
        'deteccao_mudancas',    -- Comparacao temporal
        'segmentacao',          -- SAM, U-Net
        'volumetria',           -- Calculo de volumes
        'contorno',             -- Curvas de nivel
        'perfil_terreno',       -- Perfis topograficos
        'ndvi_rgb',             -- NDVI aproximado via RGB
        'personalizada'         -- Analise customizada
    ) NOT NULL,
    nome VARCHAR(255) NOT NULL,
    descricao TEXT,
    parametros JSON,                    -- Parametros da analise
    resultado_path VARCHAR(500),        -- Caminho do arquivo de resultado
    resultado_thumbnail VARCHAR(500),
    resultado_json JSON,                -- Resultados numericos/estatisticos
    modelo_ia VARCHAR(255),             -- Nome do modelo usado (se IA)
    versao_modelo VARCHAR(50),
    metricas JSON,                      -- Accuracy, precision, recall, etc.
    agente_ia VARCHAR(100),             -- Nome do agente de IA que executou
    status ENUM('em_fila','processando','concluido','erro') DEFAULT 'em_fila',
    tempo_processamento_seg INT,
    data_analise DATETIME,
    observacoes TEXT,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ortomapa_id) REFERENCES ortomapas(id),
    FOREIGN KEY (projeto_id) REFERENCES projetos(id)
);
```

#### Tabela: `anotacoes`
Anotacoes manuais e automaticas sobre areas dos ortomapas.

```sql
CREATE TABLE anotacoes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ortomapa_id INT NOT NULL,
    analise_id INT,                     -- NULL se anotacao manual
    tipo ENUM('ponto','linha','poligono','bbox','texto') NOT NULL,
    categoria VARCHAR(100),             -- Ex: "erosao", "vegetacao_doente", "construcao"
    rotulo VARCHAR(255),
    geometria_wkt TEXT,                 -- WKT (Well-Known Text) da geometria
    centro_lat DOUBLE,
    centro_lon DOUBLE,
    area_m2 DOUBLE,                     -- Area em m2 (para poligonos)
    atributos JSON,                     -- Atributos extras
    confianca DOUBLE,                   -- Confianca da deteccao (0-1, para deteccoes IA)
    fonte ENUM('manual','ia_yolo','ia_sam','ia_classificacao','ia_mudanca') DEFAULT 'manual',
    criado_por VARCHAR(100),
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ortomapa_id) REFERENCES ortomapas(id),
    FOREIGN KEY (analise_id) REFERENCES analises(id)
);
```

#### Tabela: `gcps` (Ground Control Points)
Pontos de controle terrestre usados para georreferenciamento.

```sql
CREATE TABLE gcps (
    id INT AUTO_INCREMENT PRIMARY KEY,
    projeto_id INT NOT NULL,
    voo_id INT,
    nome VARCHAR(100) NOT NULL,
    latitude DOUBLE NOT NULL,
    longitude DOUBLE NOT NULL,
    altitude_m DOUBLE,
    precisao_horizontal_m DOUBLE,
    precisao_vertical_m DOUBLE,
    metodo_coleta VARCHAR(100),         -- Ex: "GPS RTK", "GPS celular", "Google Earth"
    equipamento VARCHAR(255),
    data_coleta DATETIME,
    observacoes TEXT,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (projeto_id) REFERENCES projetos(id),
    FOREIGN KEY (voo_id) REFERENCES voos(id)
);
```

#### Tabela: `comparacoes_temporais`
Registra comparacoes entre ortomapas de datas diferentes.

```sql
CREATE TABLE comparacoes_temporais (
    id INT AUTO_INCREMENT PRIMARY KEY,
    projeto_id INT NOT NULL,
    ortomapa_antes_id INT NOT NULL,
    ortomapa_depois_id INT NOT NULL,
    data_antes DATE,
    data_depois DATE,
    tipo_comparacao ENUM('diferenca_rgb','diferenca_ndvi','classificacao_mudanca','volumetria') NOT NULL,
    resultado_path VARCHAR(500),
    resultado_thumbnail VARCHAR(500),
    estatisticas JSON,                  -- Area alterada, percentuais, etc.
    observacoes TEXT,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (projeto_id) REFERENCES projetos(id),
    FOREIGN KEY (ortomapa_antes_id) REFERENCES ortomapas(id),
    FOREIGN KEY (ortomapa_depois_id) REFERENCES ortomapas(id)
);
```

#### Tabela: `tarefas_agentes`
Fila de tarefas para agentes de IA.

```sql
CREATE TABLE tarefas_agentes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ortomapa_id INT NOT NULL,
    tipo_tarefa VARCHAR(100) NOT NULL,   -- Ex: "detectar_arvores", "classificar_solo"
    agente VARCHAR(100) NOT NULL,        -- Nome do agente
    prioridade INT DEFAULT 5,            -- 1=maxima, 10=minima
    parametros JSON,
    status ENUM('pendente','em_execucao','concluido','erro','cancelado') DEFAULT 'pendente',
    resultado JSON,
    erro_msg TEXT,
    tentativas INT DEFAULT 0,
    max_tentativas INT DEFAULT 3,
    inicio_execucao DATETIME,
    fim_execucao DATETIME,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ortomapa_id) REFERENCES ortomapas(id)
);
```

### 3.3 Indices para Performance

```sql
-- Indices espaciais (bounding box queries)
CREATE INDEX idx_projetos_bbox ON projetos(bbox_norte, bbox_sul, bbox_leste, bbox_oeste);
CREATE INDEX idx_ortomapas_bbox ON ortomapas(bbox_norte, bbox_sul, bbox_leste, bbox_oeste);
CREATE INDEX idx_ortomapas_centro ON ortomapas(centro_lat, centro_lon);

-- Indices de busca
CREATE INDEX idx_voos_data ON voos(data_voo);
CREATE INDEX idx_voos_projeto ON voos(projeto_id);
CREATE INDEX idx_ortomapas_voo ON ortomapas(voo_id);
CREATE INDEX idx_ortomapas_projeto ON ortomapas(projeto_id);
CREATE INDEX idx_ortomapas_tipo ON ortomapas(tipo);
CREATE INDEX idx_ortomapas_status ON ortomapas(status);
CREATE INDEX idx_analises_ortomapa ON analises(ortomapa_id);
CREATE INDEX idx_analises_tipo ON analises(tipo_analise);
CREATE INDEX idx_anotacoes_ortomapa ON anotacoes(ortomapa_id);
CREATE INDEX idx_anotacoes_categoria ON anotacoes(categoria);
CREATE INDEX idx_tarefas_status ON tarefas_agentes(status, prioridade);

-- Full-text para buscas
CREATE FULLTEXT INDEX idx_projetos_busca ON projetos(nome, descricao, area_estudo);
CREATE FULLTEXT INDEX idx_ortomapas_busca ON ortomapas(nome, observacoes);
CREATE FULLTEXT INDEX idx_anotacoes_busca ON anotacoes(rotulo, categoria);
```

### 3.4 Consultas Espaciais Uteis

```sql
-- Ortomapas que cobrem uma coordenada especifica
SELECT * FROM ortomapas
WHERE bbox_norte >= -19.9 AND bbox_sul <= -19.9
  AND bbox_leste >= -43.9 AND bbox_oeste <= -43.9
  AND status = 'concluido';

-- Ortomapas de uma regiao (ex: Serra da Moeda)
SELECT o.*, v.data_voo, p.nome as projeto
FROM ortomapas o
JOIN voos v ON o.voo_id = v.id
JOIN projetos p ON o.projeto_id = p.id
WHERE o.centro_lat BETWEEN -20.15 AND -20.05
  AND o.centro_lon BETWEEN -44.00 AND -43.90
ORDER BY v.data_voo DESC;

-- Evolucao temporal de uma area
SELECT o.id, o.nome, v.data_voo, o.resolucao_cm,
       o.caminho_arquivo, o.tipo
FROM ortomapas o
JOIN voos v ON o.voo_id = v.id
WHERE o.projeto_id = ?
  AND o.tipo = 'ortomosaico'
ORDER BY v.data_voo ASC;

-- Analises de IA pendentes
SELECT ta.*, o.nome as ortomapa_nome
FROM tarefas_agentes ta
JOIN ortomapas o ON ta.ortomapa_id = o.id
WHERE ta.status = 'pendente'
ORDER BY ta.prioridade ASC, ta.criado_em ASC;
```

---

## 4. Pipeline de Processamento

### 4.1 Fluxo Automatizado

```python
# pipeline_ortomapa.py - Fluxo automatizado de processamento

"""
ETAPAS:
1. Importacao de fotos do drone
2. Processamento no WebODM (ortomosaico + DSM + DTM)
3. Registro no banco MySQL
4. Geracao de thumbnails
5. Publicacao no GeoServer
6. Disparo de analises de IA
"""

from datetime import datetime
import mysql.connector
import requests
import os

class PipelineOrtomapa:

    def __init__(self):
        self.db = mysql.connector.connect(
            host='<YOUR_DB_HOST>',
            port=3308,
            user='producao',
            password='<YOUR_DB_PASSWORD>',
            database='ortomapas'
        )
        self.webodm_url = 'http://localhost:8000'

    def importar_fotos(self, diretorio_fotos, projeto_id, metadados_voo):
        """Registra o voo e importa fotos para processamento."""
        cursor = self.db.cursor()
        cursor.execute("""
            INSERT INTO voos (projeto_id, data_voo, altitude_voo_m,
                sobreposicao_frontal, sobreposicao_lateral, num_fotos, ...)
            VALUES (%s, %s, %s, %s, %s, %s, ...)
        """, (projeto_id, metadados_voo['data'], ...))
        voo_id = cursor.lastrowid
        self.db.commit()
        return voo_id

    def processar_webodm(self, diretorio_fotos, parametros):
        """Envia fotos ao WebODM para processamento."""
        # WebODM API: criar projeto e task
        # POST /api/projects/{project_id}/tasks/
        pass

    def registrar_ortomapa(self, voo_id, projeto_id, resultados):
        """Registra o ortomapa gerado no banco."""
        cursor = self.db.cursor()
        cursor.execute("""
            INSERT INTO ortomapas (voo_id, projeto_id, nome, tipo, formato, ...)
            VALUES (%s, %s, %s, %s, %s, ...)
        """, (...))
        self.db.commit()

    def disparar_analises(self, ortomapa_id):
        """Enfileira analises automaticas de IA."""
        analises_padrao = [
            ('indice_vegetacao', 'agente_vegetacao', {'indice': 'VARI'}),
            ('classificacao_solo', 'agente_classificacao', {}),
            ('deteccao_objetos', 'agente_yolo', {'classes': ['arvore', 'edificacao']}),
        ]
        cursor = self.db.cursor()
        for tipo, agente, params in analises_padrao:
            cursor.execute("""
                INSERT INTO tarefas_agentes
                    (ortomapa_id, tipo_tarefa, agente, parametros)
                VALUES (%s, %s, %s, %s)
            """, (ortomapa_id, tipo, agente, json.dumps(params)))
        self.db.commit()
```

### 4.2 Processamento com WebODM

**Instalacao:**
```bash
git clone https://github.com/OpenDroneMap/WebODM
cd WebODM
./webodm.sh start
# Acessar em http://localhost:8000
```

**Parametros recomendados para DJI Mini 3:**
```
--dsm --dtm
--orthophoto-resolution 2
--dem-resolution 5
--feature-quality high
--mesh-octree-depth 11
--min-num-features 10000
```

**Produtos gerados:**
| Produto | Arquivo | Uso |
|---|---|---|
| Ortomosaico | `odm_orthophoto.tif` | Mapa aereo georreferenciado |
| DSM | `dsm.tif` | Modelo de superficie (c/ edificios e arvores) |
| DTM | `dtm.tif` | Modelo de terreno (solo nu) |
| Nuvem de Pontos | `georeferenced_model.laz` | Dados 3D |
| Malha 3D | `textured_model.obj` | Visualizacao 3D |

---

## 5. Visualizacao de Ortomapas

### 5.1 Interface Web (Leaflet + GeoServer)

**Componentes:**
- **GeoServer** para servir ortomapas como tiles WMS/WMTS
- **Leaflet.js** ou **OpenLayers** como biblioteca de mapas no frontend
- **Camadas sobreposiveis:** ortomapa, DSM (colorido por elevacao), indices de vegetacao, anotacoes, classificacao do solo

**Funcionalidades da interface:**
- Visualizar ortomapa em mapa base (OpenStreetMap, satelite)
- Zoom de alta resolucao com carregamento progressivo de tiles
- Alternar entre camadas (ortomosaico, DSM, VARI, classificacao)
- Medir distancias e areas diretamente no mapa
- Comparar ortomapas de datas diferentes (side-by-side / swipe)
- Exportar recortes em diversos formatos
- Visualizar anotacoes e deteccoes de IA

### 5.2 GeoServer: Publicacao de Ortomapas

```bash
# Instalacao via Docker
docker run -d -p 8080:8080 \
  -v /dados/geoserver:/opt/geoserver/data_dir \
  kartoza/geoserver:latest
```

**Configuracao:**
1. Criar Workspace: `ortomapas`
2. Criar Store: conectar ao diretorio de GeoTIFFs
3. Publicar cada ortomapa como Layer
4. Configurar estilo SLD para visualizacao
5. Habilitar WMTS para tiles cacheados

### 5.3 QGIS Desktop (Analise Avancada)

O QGIS conecta diretamente ao GeoServer via WMS/WFS para:
- Analise de raster avancada
- Calculadora de raster (indices de vegetacao)
- Geracao de curvas de nivel
- Analise de declividade e aspecto
- Layouts de mapa para relatorios
- Classificacao supervisionada (plugin SCP)

### 5.4 Jupyter Notebooks (Analise Interativa)

```python
# Exemplo: visualizar ortomapa com rasterio e matplotlib
import rasterio
from rasterio.plot import show
import matplotlib.pyplot as plt

with rasterio.open('ortomosaico.tif') as src:
    fig, ax = plt.subplots(figsize=(15, 15))
    show(src, ax=ax)
    ax.set_title('Ortomosaico - Serra da Moeda')
    plt.show()
```

---

## 6. Edicao e Alteracao de Ortomapas

### 6.1 Operacoes Disponiveis

| Operacao | Ferramenta | Descricao |
|---|---|---|
| **Recorte (Clip)** | QGIS, rasterio | Recortar ortomapa por poligono ou bbox |
| **Reprojecao** | QGIS, gdalwarp | Mudar sistema de coordenadas |
| **Reamostragem** | QGIS, gdal_translate | Mudar resolucao (upscale/downscale) |
| **Mosaicagem** | QGIS, gdal_merge | Unir multiplos ortomapas |
| **Anotacao** | Interface web, QGIS | Adicionar pontos, linhas, poligonos |
| **Classificacao** | QGIS SCP, scikit-learn | Classificar pixels por uso do solo |
| **Correcao Radiometrica** | QGIS, OpenCV | Ajustar brilho, contraste, histograma |
| **Exportacao** | QGIS, gdal_translate | Converter formatos (TIFF, PNG, KML, etc.) |

### 6.2 Exemplo: Recorte por Area de Interesse

```python
import rasterio
from rasterio.mask import mask
from shapely.geometry import box
import geopandas as gpd

# Definir area de interesse (bbox)
aoi = box(-43.95, -20.12, -43.90, -20.08)
aoi_gdf = gpd.GeoDataFrame({'geometry': [aoi]}, crs='EPSG:4326')

with rasterio.open('ortomosaico.tif') as src:
    out_image, out_transform = mask(src, aoi_gdf.geometry, crop=True)
    out_meta = src.meta.copy()
    out_meta.update({
        'height': out_image.shape[1],
        'width': out_image.shape[2],
        'transform': out_transform
    })

with rasterio.open('recorte.tif', 'w', **out_meta) as dest:
    dest.write(out_image)
```

---

## 7. Analises Espaciais

### 7.1 Indices de Vegetacao (RGB)

O DJI Mini 3 possui **camera RGB apenas** (sem multiespectal/NIR). Indices disponiveis:

| Indice | Formula | Uso |
|---|---|---|
| **VARI** | (G - R) / (G + R - B) | Saude da planta, resistente a atmosfera |
| **TGI** | G - 0.39*R - 0.61*B | Proxy de clorofila em alta cobertura foliar |
| **ExG** | 2*G - R - B | Deteccao simples de vegetacao verde |
| **GLI** | (2*G - R - B) / (2*G + R + B) | Deteccao normalizada de verde |
| **vNDVI** | Usa R e G para prever NDVI | Requer calibracao, menos preciso |

**Calculo no QGIS (Calculadora de Raster):**
```
VARI = ("ortho@2" - "ortho@1") / ("ortho@2" + "ortho@1" - "ortho@3")
Onde: @1 = Banda Vermelha, @2 = Banda Verde, @3 = Banda Azul
```

**Calculo em Python:**
```python
import rasterio
import numpy as np

with rasterio.open('ortomosaico.tif') as src:
    red = src.read(1).astype(float)
    green = src.read(2).astype(float)
    blue = src.read(3).astype(float)

# VARI
vari = (green - red) / (green + red - blue + 1e-10)

# TGI
tgi = green - 0.39 * red - 0.61 * blue

# ExG
exg = 2 * green - red - blue
```

> **IMPORTANTE:** Indices RGB nao sao tao confiaveis quanto NDVI real de cameras multiespectrais. Use para comparacoes relativas dentro de um mesmo levantamento, nao para medicoes absolutas.

### 7.2 Analise de Terreno (DSM/DTM)

```python
# Curvas de nivel a partir do DTM
# No QGIS: Raster > Extraction > Contour
# Parametro: intervalo de 1m, 5m ou 10m conforme necessidade

# Declividade (slope)
# QGIS: Raster > Analysis > Slope

# Aspecto (orientacao da encosta)
# QGIS: Raster > Analysis > Aspect

# Calculo de volume (ex: corte de mineracao)
# Comparar DSM atual com DSM de referencia
```

### 7.3 Deteccao de Mudancas Temporais

```python
import rasterio
import numpy as np

with rasterio.open('ortho_data1.tif') as src1:
    img1 = src1.read().astype(float)
with rasterio.open('ortho_data2.tif') as src2:
    img2 = src2.read().astype(float)

# Mapa de diferenca simples
diff = np.abs(img2 - img1)

# Mascara de mudanca significativa
threshold = 30  # ajustar conforme necessidade
change_mask = np.mean(diff, axis=0) > threshold

# Calcular area alterada
pixel_area_m2 = gsd_cm * gsd_cm / 10000  # area de 1 pixel em m2
area_alterada_m2 = np.sum(change_mask) * pixel_area_m2
area_alterada_ha = area_alterada_m2 / 10000
```

### 7.4 Classificacao de Uso do Solo

**Abordagens:**

1. **QGIS Semi-Automatic Classification Plugin (SCP)**
   - Classificacao supervisionada e nao-supervisionada
   - Funciona com ortomosaicos RGB
   - Random Forest, SVM e outros classificadores
   - Gratuito e integrado ao QGIS

2. **Scikit-learn (Python)**
   ```python
   from sklearn.ensemble import RandomForestClassifier
   from sklearn.model_selection import train_test_split

   # Extrair features por pixel (R, G, B, indices)
   # Treinar classificador com amostras rotuladas
   clf = RandomForestClassifier(n_estimators=100)
   clf.fit(X_train, y_train)
   classification = clf.predict(X_all_pixels)
   ```

3. **Segment Anything Model (SAM) - Meta**
   - Segmentacao zero-shot de imagens de drone
   - Segmenta features sem treinamento previo
   - Util para extracao inicial de feicoes

### 7.5 Analise Hidrologica

- **Delimitacao de bacias:** A partir do DTM usando algoritmos D8/D-infinity
- **Rede de drenagem:** Extrair rede de cursos d'agua automaticamente
- **Areas de acumulo:** Identificar zonas de acumulo de agua
- **Zonas riparias:** Mapear vegetacao ciliar ao longo de cursos d'agua

---

## 8. Agentes de IA para Analise de Imagens

### 8.1 Arquitetura dos Agentes

```
+------------------------------------------------------+
|              ORQUESTRADOR DE AGENTES                  |
|  (Python + fila de tarefas MySQL)                     |
+------------------------------------------------------+
       |            |            |            |
       v            v            v            v
+-----------+ +-----------+ +-----------+ +-----------+
| Agente    | | Agente    | | Agente    | | Agente    |
| Vegetacao | | Deteccao  | | Classif.  | | Mudanca   |
| (VARI/TGI)| | (YOLOv8)  | | (RF/SVM)  | | (diff)    |
+-----------+ +-----------+ +-----------+ +-----------+
       |            |            |            |
       v            v            v            v
+-----------+ +-----------+ +-----------+ +-----------+
| Agente    | | Agente    | | Agente    | | Agente    |
| Segment.  | | Volume    | | Relatorio | | Claude    |
| (SAM)     | | (DSM)     | | (PDF)     | | (LLM)     |
+-----------+ +-----------+ +-----------+ +-----------+
```

### 8.2 Agente de Vegetacao

**Funcao:** Calcular indices de vegetacao e gerar mapas de saude vegetal.

```python
class AgenteVegetacao:
    """Calcula indices de vegetacao RGB e gera mapas classificados."""

    INDICES = {
        'VARI': lambda r, g, b: (g - r) / (g + r - b + 1e-10),
        'TGI':  lambda r, g, b: g - 0.39*r - 0.61*b,
        'ExG':  lambda r, g, b: 2*g - r - b,
        'GLI':  lambda r, g, b: (2*g - r - b) / (2*g + r + b + 1e-10),
    }

    def executar(self, ortomapa_path, indice='VARI'):
        # 1. Ler ortomapa
        # 2. Calcular indice
        # 3. Classificar (saudavel, estressado, sem vegetacao)
        # 4. Gerar mapa GeoTIFF classificado
        # 5. Calcular estatisticas (area por classe)
        # 6. Salvar resultados no banco
        pass
```

### 8.3 Agente de Deteccao de Objetos (YOLOv8)

**Funcao:** Detectar e contar objetos em ortomapas (arvores, edificacoes, veiculos, etc.).

```python
class AgenteDeteccao:
    """Detecta objetos em ortomapas usando YOLOv8."""

    def executar(self, ortomapa_path, classes=['arvore', 'edificacao']):
        # 1. Dividir ortomapa em tiles (ex: 640x640 px)
        # 2. Executar YOLOv8 em cada tile
        # 3. Unir deteccoes e remover duplicatas (NMS)
        # 4. Georreferenciar deteccoes (pixel -> lat/lon)
        # 5. Contar objetos por classe
        # 6. Gerar mapa de deteccoes (GeoJSON)
        # 7. Salvar resultados no banco
        pass
```

**Datasets disponiveis no Roboflow Universe:**
- 1.863+ datasets aereos/drone
- Classes comuns: arvores, edificacoes, veiculos, paneis solares, animais
- Treinamento customizado via Roboflow ou local

### 8.4 Agente de Classificacao de Solo

**Funcao:** Classificar pixels em categorias de uso do solo.

```python
class AgenteClassificacao:
    """Classifica uso do solo usando Random Forest / SVM."""

    CLASSES = [
        'vegetacao_densa',    # Floresta, mata
        'vegetacao_rasteira', # Cerrado, campo
        'solo_exposto',       # Mineracao, erosao
        'agua',               # Rios, lagos
        'urbano',             # Edificacoes, estradas
        'agricola',           # Cultivos
        'rocha',              # Afloramentos rochosos
    ]

    def executar(self, ortomapa_path, modelo_treinado=None):
        # 1. Extrair features (R, G, B, VARI, TGI, textura)
        # 2. Carregar ou treinar modelo
        # 3. Classificar todos os pixels
        # 4. Pos-processamento (filtro majoritario, suavizacao)
        # 5. Calcular area por classe
        # 6. Gerar mapa classificado (GeoTIFF)
        # 7. Salvar resultados
        pass
```

### 8.5 Agente de Deteccao de Mudancas

**Funcao:** Comparar ortomapas de datas diferentes e identificar alteracoes.

```python
class AgenteMudanca:
    """Detecta mudancas entre ortomapas temporais."""

    def executar(self, ortomapa_antes_path, ortomapa_depois_path):
        # 1. Alinhar espacialmente os dois ortomapas
        # 2. Calcular diferenca por banda
        # 3. Aplicar threshold para deteccao
        # 4. Classificar tipo de mudanca (desmatamento, construcao, erosao)
        # 5. Calcular area e percentuais
        # 6. Gerar mapa de mudancas
        # 7. Salvar resultados
        pass
```

### 8.6 Agente de Segmentacao (SAM)

**Funcao:** Segmentar automaticamente feicoes no ortomapa sem treinamento.

```python
class AgenteSegmentacao:
    """Segmenta feicoes usando Segment Anything Model (SAM)."""

    def executar(self, ortomapa_path, pontos_interesse=None):
        # 1. Carregar modelo SAM
        # 2. Dividir ortomapa em tiles
        # 3. Gerar mascaras de segmentacao
        # 4. Vetorizar segmentos em poligonos
        # 5. Georreferenciar poligonos
        # 6. Classificar segmentos por cor/textura
        # 7. Exportar como GeoJSON/Shapefile
        pass
```

### 8.7 Agente de Relatorios (Claude/LLM)

**Funcao:** Gerar relatorios interpretativos automaticos usando LLM.

```python
class AgenteRelatorio:
    """Gera relatorios em linguagem natural a partir de analises."""

    def executar(self, analise_ids):
        # 1. Coletar resultados das analises do banco
        # 2. Montar contexto para o LLM
        # 3. Gerar relatorio interpretativo:
        #    - Resumo das condicoes observadas
        #    - Comparacao com levantamentos anteriores
        #    - Alertas de mudancas significativas
        #    - Recomendacoes de acao
        # 4. Exportar como PDF/Markdown
        # 5. Salvar no banco
        pass
```

### 8.8 Orquestrador de Agentes

```python
class OrquestradorAgentes:
    """Monitora fila de tarefas e despacha para agentes."""

    AGENTES = {
        'agente_vegetacao': AgenteVegetacao,
        'agente_deteccao': AgenteDeteccao,
        'agente_classificacao': AgenteClassificacao,
        'agente_mudanca': AgenteMudanca,
        'agente_segmentacao': AgenteSegmentacao,
        'agente_relatorio': AgenteRelatorio,
    }

    def processar_fila(self):
        """Loop principal: busca tarefas pendentes e executa."""
        while True:
            tarefa = self.buscar_proxima_tarefa()
            if tarefa:
                self.executar_tarefa(tarefa)
            else:
                time.sleep(10)  # Aguardar novas tarefas

    def buscar_proxima_tarefa(self):
        cursor = self.db.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM tarefas_agentes
            WHERE status = 'pendente'
            ORDER BY prioridade ASC, criado_em ASC
            LIMIT 1
            FOR UPDATE SKIP LOCKED
        """)
        return cursor.fetchone()
```

---

## 9. Regioes de Interesse Proximas a Belo Horizonte

### 9.1 Serra do Cipo (Parque Nacional)

| Item | Detalhe |
|---|---|
| **Coordenadas** | 19 20'S, 43 32'W |
| **Distancia de BH** | ~100 km NE (1.5-2h de carro via MG-010) |
| **Area** | 31.639 ha (parque) + 100.000+ ha (APA Morro da Pedreira) |
| **Altitude** | Ate ~1.700m |
| **Risco Espaco Aereo** | Baixo (longe de aeroportos) |
| **Necessita Autorizacao** | Sim - ICMBio/SISBIO (Parque Nacional Federal) |

**Vegetacao:** Campos rupestres (biodiversidade extraordinaria com alto endemismo), cerrado em varias fisionomias, manchas de Mata Atlantica, matas de galeria. Mais de 1.600 especies de plantas catalogadas, incluindo bromelias, orquideas e Velloziaceae (canela-de-ema) endemicas.

**Geologia:** Afloramentos de quartzito formados a partir de depositos marinhos ~1.7 bilhoes de anos atras. Paisagens erosionais dramaticas, canyons e cachoeiras. Camadas geologicas e dobras visiveis em faces rochosas expostas.

**Pesquisas possiveis com ortomapas:**
- Mapeamento e classificacao de vegetacao (campos rupestres vs. cerrado vs. floresta)
- Monitoramento de erosao em trilhas
- Mapeamento de cicatrizes de fogo e recuperacao
- Modelagem de habitat de especies endemicas
- Monitoramento fenologico (floracao de campos rupestres)
- Mapeamento hidrologico de nascentes e zonas umidas

**Questoes ambientais para monitoramento:**
- Manejo e recuperacao de areas queimadas
- Erosao por turismo crescente
- Especies invasoras (especialmente gramineas)
- Ameacas de mineracao nas bordas do parque

---

### 9.2 Serra do Rola-Moca (Parque Estadual)

| Item | Detalhe |
|---|---|
| **Coordenadas** | 20 02'S, 44 00'W |
| **Distancia de BH** | ~15-20 km sul (dentro da regiao metropolitana) |
| **Area** | 3.941 ha |
| **Risco Espaco Aereo** | Medio (proximidade de Pampulha) |
| **Necessita Autorizacao** | Sim - IEF-MG (Parque Estadual) |

**Vegetacao:** Campos rupestres ferruginosos (campos ferruginosos) - vegetacao extremamente rara que cresce sobre crosta de canga ferrica. Encontrada globalmente apenas no Quadrilatero Ferrifero (MG) e Serra dos Carajas (PA). Cerrado e remanescentes de Mata Atlantica.

**Geologia:** Canga (crosta laterita ferruginosa) formada pelo intemperismo do itabirito. Zona de transicao entre biomas Cerrado e Mata Atlantica.

**Recursos Hidricos:** Contem nascentes criticas para o abastecimento de agua de BH.

**Pesquisas possiveis:**
- Mapeamento de alta resolucao da vegetacao de canga (extremamente rara)
- Monitoramento da interface urbano-silvestre
- Protecao de nascentes e zonas riparias
- Analise de cicatrizes de fogo
- Avaliacao de impacto de mineracao nas bordas
- Mapeamento de corredores de biodiversidade

**Questoes ambientais:**
- Pressao de expansao urbana de todos os municipios ao redor
- Mineracao nas bordas (Quadrilatero Ferrifero)
- Qualidade da agua das nascentes
- Ocupacoes irregulares e construcoes ilegais

---

### 9.3 Inhotim (Instituto Inhotim)

| Item | Detalhe |
|---|---|
| **Coordenadas** | 20 07'S, 44 13'W |
| **Distancia de BH** | ~60 km oeste (1.5h de carro) |
| **Area Total** | 786 ha (visitavel: 140 ha, RPPN: 250 ha) |
| **Risco Espaco Aereo** | Baixo (longe de aeroportos) |
| **Necessita Autorizacao** | Sim - Propriedade privada (Instituto Inhotim) |

**Jardim Botanico:** Mais de 4.300 especies de plantas nativas brasileiras. Jardim botanico certificado com programas de pesquisa. 250 ha de RPPN (Reserva Particular do Patrimonio Natural) com Mata Atlantica.

**Instalacoes de Arte:** ~24 pavilhoes distribuidos pela paisagem. Mais de 500 obras de 100+ artistas de 30 paises. Esculturas e instalacoes de grande escala visiveis do ar.

**Pesquisas possiveis:**
- Mapeamento de dossel do jardim botanico
- Estudo de integracao arte-paisagem (nicho academico unico)
- Monitoramento da RPPN de Mata Atlantica
- Modelagem de fluxo de visitantes
- Monitoramento de corpos d'agua
- Transicao urbano-rural pos-desastre da barragem de Brumadinho

**Contexto ambiental:**
- **Desastre da Barragem de Brumadinho (25/01/2019):** Barragem de rejeitos da Vale S.A. rompeu ~10 km de Inhotim, liberando 12 milhoes de m3 de rejeitos toxicos, matando 270 pessoas e devastando o Rio Paraopeba. Monitoramento ambiental por drone da recuperacao e extremamente relevante.

---

### 9.4 Serra da Piedade

| Item | Detalhe |
|---|---|
| **Coordenadas** | 19 49'S, 43 40'W |
| **Distancia de BH** | ~50 km leste |
| **Altitude** | 1.746m |
| **Risco Espaco Aereo** | Medio |
| **Necessita Autorizacao** | Parcial (monumento natural) |

**Geologia:** Itabirito (formacao ferrifera bandada) da Formacao Caue, Supergrupo Minas. Grandes afloramentos com intercalacoes de camadas ricas em ferro e silica. Estruturas ducteis (dobras, zonas de cisalhamento, falhas). Canga ferrica acima de ~1.200m. Uma das melhores exposicoes geologicas de itabirito no Quadrilatero Ferrifero.

**Pesquisas possiveis:**
- Mapeamento de afloramentos geologicos em 3D (geologia estrutural)
- Mapeamento do ecossistema de canga
- Avaliacao de proximidade de mineracao
- Estudos de erosao e intemperismo
- Documentacao do patrimonio religioso (Santuario da Serra da Piedade)
- Transectos altitudinais de vegetacao

---

### 9.5 Parque Nacional da Serra do Gandarela

| Item | Detalhe |
|---|---|
| **Coordenadas** | ~20 00'S, 43 40'W |
| **Distancia de BH** | ~40-60 km sudeste |
| **Area** | 31.270 ha |
| **Risco Espaco Aereo** | Baixo |
| **Necessita Autorizacao** | Sim - ICMBio/SISBIO (Parque Nacional Federal) |

**Contexto:** Criado em 2014 especificamente para **proteger fontes de agua de BH da mineracao de ferro**. Contem aquiferos criticos, nascentes e areas de recarga. As formacoes de canga atuam como filtros e reservatorios naturais de agua.

**Conflito mineracao-conservacao:** Vale S.A. busca aprovacao para construir minas adjacentes ao parque. Compromissos durante a criacao permitiram algumas operacoes de mineracao. Limite do parque controversamente desenhado para excluir concessoes minerarias.

**Pesquisas possiveis:**
- Monitoramento de zonas-tampao de mineracao
- Mapeamento de recursos hidricos (nascentes, zonas umidas)
- Avaliacao de integridade da canga
- Rastreamento de desmatamento
- Monitoramento de barragens de rejeitos
- Mapeamento de corredores ecologicos

---

### 9.6 Serra do Curral

| Item | Detalhe |
|---|---|
| **Coordenadas** | ~19 58'S, 43 54'W |
| **Distancia de BH** | ~5-10 km sul |
| **Altitude** | 1.538m (Pico Belo Horizonte) |
| **Risco Espaco Aereo** | Alto (proximo a Pampulha) |
| **Necessita Autorizacao** | Varia |

**Importancia:** Moldura natural de BH, patrimonio cultural protegido. Abriga nascentes que fornecem ~70% da agua da capital e ~40% da regiao metropolitana.

**Conflito ativo:** Empresa Tamisa tentando instalar complexo minerador em area preservada (Nova Lima). Gute Sicht multada em R$1.2+ milhao por impactos ambientais. Batalha judicial de 6+ anos.

**Pesquisas possiveis:**
- Monitoramento de avanco de mineracao (multitemporal)
- Analise de expansao urbana
- Documentacao da paisagem cultural (patrimonio)
- Mapeamento de nascentes e captacoes
- Avaliacao de saude da vegetacao (poeira de mineracao)
- Coleta de evidencias legais para litigios ambientais

---

### 9.7 Lagoa Santa / Regiao das Cavernas de Peter Lund

| Item | Detalhe |
|---|---|
| **Coordenadas** | ~19 38'S, 43 53'W |
| **Distancia de BH** | ~30 km norte |
| **Risco Espaco Aereo** | **MUITO ALTO** (proximo a Confins e Base Aerea Lagoa Santa) |
| **Necessita Autorizacao** | Varia |

**Interesse arqueologico:** Peter Lund investigou cavernas de 1833 a 1843, descrevendo megafauna extinta. Lapa Vermelha IV: sitio de descoberta de "Luzia", um dos esqueletos humanos mais antigos das Americas (11.000-11.500 anos). Mais de 1.000 cavernas documentadas.

**Paisagem carstica:** Calcarios da Formacao Sete Lagoas (Grupo Bambui). Paredoes calcareos, torres carsticas, lagos carsticos, dolinas (sumidouros), sistemas de drenagem subterranea.

**Pesquisas possiveis:**
- Mapeamento geomorfologico carstico (dolinas, sumidouros)
- Inventario aereo de entradas de cavernas
- Documentacao de sitios arqueologicos
- Expansao urbana sobre terreno carstico (risco de subsidencia)
- Mudanca de uso do solo em areas arqueologicamente sensiveis

> **ATENCAO:** Area mais restrita em termos de espaco aereo entre todas as 10 localidades. Considere voos bem cedo ou em areas mais afastadas dos aeroportos.

---

### 9.8 Serra da Moeda

| Item | Detalhe |
|---|---|
| **Coordenadas** | ~20 10'S, 43 55'W |
| **Distancia de BH** | ~40-50 km sul/sudoeste |
| **Risco Espaco Aereo** | Baixo |
| **Necessita Autorizacao** | Nao (na maioria das areas) |

**Geologia:** Quartzitos da Formacao Moeda (2.62 Ga). Itabiritos da Formacao Caue. Depositos cenozoicos nas areas elevadas. Estrutura sinclinal dramatica visivel do ar. Escarpamento com vistas panoramicas.

**Pesquisas possiveis:**
- Mapeamento de estruturas geologicas (sinclinal)
- Documentacao de impacto de mineracao
- Monitoramento de erosao de escarpamento
- Mapeamento de depositos cenozoicos
- Correlacao vegetacao-geologia
- Planejamento de rotas de geoturismo

**RECOMENDADO PARA INICIANTES:** Areas abertas, baixo risco de espaco aereo, geologia dramatica, sem necessidade de permissao de parque.

---

### 9.9 Quadrilatero Ferrifero (Visao Geral)

| Item | Detalhe |
|---|---|
| **Coordenadas** | 19 30'S - 20 30'S, 43 20'W - 44 10'W |
| **Area** | ~7.000 km2 |
| **Risco Espaco Aereo** | Varia por localizacao |

Principal regiao produtora de minerio de ferro do Brasil. Mudancas documentadas (1985-2018): pastagens diminuiram 12%, floresta e mineracao aumentaram 4% e 0.2%. Mineracao responsavel por 14% da perda de vegetacao desde 1990.

**Pesquisas possiveis:**
- Monitoramento multitemporal de expansao mineraria
- Monitoramento de barragens de rejeitos (critico pos-Brumadinho/Mariana)
- Avaliacao de reabilitacao de areas mineradas
- Mapeamento de drenagem acida de minas (AMD)
- Documentacao de patrimonio geologico
- Conectividade de fragmentos florestais

---

### 9.10 Bacia do Rio das Velhas

| Item | Detalhe |
|---|---|
| **Coordenadas** | Nascentes proximo a Ouro Preto ate confluencia com o Sao Francisco |
| **Trecho superior** | 1.943 km2 |
| **Distancia de BH** | 0-60 km (passa por/perto de BH) |
| **Risco Espaco Aereo** | Varia (alto em trechos urbanos) |

Fornece ~50% da agua da populacao metropolitana de BH (~2 milhoes de habitantes). Recebe esgoto nao tratado ou parcialmente tratado da regiao metropolitana. Estacoes AV310 e AV320 identificadas como as de pior qualidade de agua.

**Pesquisas possiveis:**
- Mapeamento de zonas riparias
- Mapeamento de turbidez e algas por indices RGB de agua
- Identificacao de pontos de despejo de esgoto
- Identificacao de fontes de erosao
- Mapeamento de planicie de inundacao
- Monitoramento de restauracao (Projeto Manuelzao)
- Rastreamento de sedimentos de mineracao
- Mapeamento de ocupacoes irregulares em APPs

---

### 9.11 Tabela Comparativa e Priorizacao

| Localidade | Distancia | Espaco Aereo | Permissao | Foco Principal | Facilidade |
|---|---|---|---|---|---|
| Serra do Cipo | 100 km NE | Baixo | ICMBio | Biodiversidade | Moderada |
| Serra do Rola-Moca | 15-20 km S | Medio | IEF-MG | Canga, borda urbana | Facil |
| Inhotim | 60 km W | Baixo | Privada | Arte+natureza, Mata Atl. | Facil |
| Serra da Piedade | 50 km E | Medio | Parcial | Geologia itabirito | Moderada |
| Serra do Gandarela | 40-60 km SE | Baixo | ICMBio | Mineracao vs. agua | Moderada |
| **Serra do Curral** | 5-10 km S | **Alto** | Varia | **Conflito mineracao** | Facil |
| **Lagoa Santa** | 30 km N | **Muito Alto** | Varia | Arqueologia, carste | **Dificil** |
| **Serra da Moeda** | 40-50 km SW | **Baixo** | **Nao** | Geologia estrutural | **Facil** |
| Q. Ferrifero | 0-100 km | Varia | Varia | Paisagem mineraria | Varia |
| Rio das Velhas | 0-60 km | Varia | Nao (maioria) | Qualidade da agua | Varia |

### 9.12 Recomendacoes de Priorizacao

**Para comecar (menor burocracia, mais facil):**
1. **Serra da Moeda** - Sem parque, espaco aereo livre, geologia espetacular
2. **Arredores de Inhotim** - Espaco aereo livre, paisagem interessante

**Maior valor cientifico:**
1. **Serra do Cipo** - Biodiversidade globalmente significativa
2. **Serra do Gandarela** - Conflito mineracao-conservacao-agua
3. **Bacia do Rio das Velhas** - Aplicacoes praticas de monitoramento ambiental

**Monitoramento ambiental urgente:**
1. **Serra do Curral** - Conflito ativo ameacando paisagem iconica e agua de BH
2. **Quadrilatero Ferrifero** - Barragens de rejeitos, pos-desastre
3. **Lagoa Santa** - Expansao urbana destruindo patrimonio arqueologico

---

## 10. Tipos de Pesquisa com Imagens de Drone

### 10.1 Pesquisas Ambientais

| Tipo | Descricao | Ferramentas | Aplicacao Local |
|---|---|---|---|
| **Monitoramento de desmatamento** | Deteccao de mudancas na cobertura florestal | Deteccao de mudancas, classificacao | Serra do Gandarela, Quadrilatero Ferrifero |
| **Saude da vegetacao** | Indices de estresse vegetal | VARI, TGI, ExG | Serra do Cipo, Serra do Rola-Moca |
| **Monitoramento de fogo** | Mapeamento de cicatrizes e recuperacao | Classificacao, deteccao de mudancas | Serra do Cipo, cerrado em geral |
| **Especies invasoras** | Deteccao de populacoes de gramineas exoticas | Classificacao, YOLO | Serra do Cipo, unidades de conservacao |
| **Erosao** | Mapeamento de vocorocas e sulcos erosivos | DSM/DTM, volumetria | Trilhas em parques, areas mineradas |
| **Qualidade da agua** | Indices de turbidez e cor da agua | Indices RGB da agua | Rio das Velhas, rios no QF |
| **Zonas riparias** | Mapeamento de mata ciliar | Classificacao, segmentacao | Rio das Velhas, cursos d'agua em geral |

### 10.2 Pesquisas Geologicas e Geomorfologicas

| Tipo | Descricao | Ferramentas | Aplicacao Local |
|---|---|---|---|
| **Mapeamento geologico** | Delineacao de unidades e estruturas | Ortomapa + DSM 3D | Serra da Piedade, Serra da Moeda |
| **Geomorfologia carstica** | Mapeamento de dolinas, cavernas | DTM, deteccao | Lagoa Santa |
| **Paisagem de mineracao** | Documentacao de impactos | Multitemporal, volumetria | Quadrilatero Ferrifero |
| **Barragens de rejeitos** | Monitoramento de seguranca | DSM, deteccao de mudancas | Brumadinho, QF |
| **Geoconservacao** | Documentacao de patrimonio geologico | Modelos 3D | Serra da Piedade, Serra da Moeda |

### 10.3 Pesquisas Urbanas e Sociais

| Tipo | Descricao | Ferramentas | Aplicacao Local |
|---|---|---|---|
| **Expansao urbana** | Crescimento de areas construidas | Classificacao, deteccao de mudancas | Serra do Curral, Lagoa Santa |
| **Ocupacoes irregulares** | Deteccao de construcoes em areas protegidas | YOLO, classificacao | APPs, beiras de rio |
| **Planejamento urbano** | Mapeamento de alta resolucao | Ortomapa + DSM | Areas metropolitanas |
| **Patrimonio cultural** | Documentacao 3D de sitios historicos | Modelos 3D | Serra da Piedade, sitios coloniais |
| **Infraestrutura** | Inspecao de estradas, pontes | Ortomapa detalhado, YOLO | Areas rurais |

### 10.4 Pesquisas Ecologicas

| Tipo | Descricao | Ferramentas | Aplicacao Local |
|---|---|---|---|
| **Contagem de arvores** | Inventario florestal | YOLO, SAM | Mata Atlantica, reflorestamento |
| **Cobertura de dossel** | Porcentagem e gaps do dossel | Segmentacao, classificacao | Inhotim RPPN, matas de galeria |
| **Fragmentacao** | Analise de conectividade de fragmentos | Classificacao, metricas de paisagem | Quadrilatero Ferrifero |
| **Fenologia** | Mudancas sazonais da vegetacao | Multitemporal, indices RGB | Serra do Cipo (floracao) |
| **Habitat** | Modelagem de distribuicao de especies | Classificacao, correlacao | Serra do Cipo (endemismos) |

### 10.5 Pesquisas em Agricultura e Recursos

| Tipo | Descricao | Ferramentas | Aplicacao Local |
|---|---|---|---|
| **Saude de cultivos** | Deteccao de estresse/pragas | VARI, TGI | Areas rurais ao redor de BH |
| **Contagem de plantas** | Inventario de plantios | YOLO | Silvicultura, cafeicultura |
| **Irrigacao** | Mapeamento de areas irrigadas | Classificacao, indices agua | Vales agricolas |
| **Pastagens** | Qualidade e degradacao | VARI, classificacao | Entorno do QF |

### 10.6 Potencial Academico e Publicacoes

Temas com alto potencial para artigos cientificos:

1. **"Monitoramento de mineracao no Quadrilatero Ferrifero por drone de baixo custo"** - Comparar com satelite, demonstrar vantagem de resolucao
2. **"Indices de vegetacao RGB vs. multiespectrais em campos rupestres"** - Validar VARI/TGI contra NDVI real
3. **"Deteccao de mudancas na Serra do Curral usando ortomosaicos de drone"** - Documentar conflito mineracao-conservacao
4. **"Mapeamento carstico de alta resolucao em Lagoa Santa"** - Geomorfologia com DTM de drone
5. **"Recuperacao ambiental pos-Brumadinho: monitoramento por drone"** - Tema de alta relevancia social
6. **"IA para deteccao de erosao em trilhas de parques naturais"** - Aplicacao pratica de YOLO em gestao de areas protegidas
7. **"Monitoramento de mata ciliar do Rio das Velhas com drone RGB e classificacao automatizada"** - Contribuicao direta para gestao de recursos hidricos

---

## 11. Stack Tecnologico Completo

### 11.1 Hardware

| Componente | Especificacao |
|---|---|
| **Drone** | DJI Mini 3 + Fly More Combo (3 baterias) |
| **Cartao SD** | SanDisk Extreme V30 64GB+ |
| **Celular/Tablet** | Android/iOS com Litchi Pilot |
| **Computador** | 16GB+ RAM, SSD, GPU dedicada (para WebODM) |
| **Servidor** | MySQL em <YOUR_DB_HOST>:3308 |

### 11.2 Software - Captura

| Software | Funcao | Custo |
|---|---|---|
| **Litchi Pilot** | Controle de voo autonomo | ~US$25 unico |
| **Drone Grid Mission Planner** | Geracao de rotas grid | Gratis |
| **Litchi Mission Hub** | Planejamento web de missoes | Incluido no Litchi |

### 11.3 Software - Processamento

| Software | Funcao | Custo |
|---|---|---|
| **WebODM / OpenDroneMap** | Geracao de ortomosaicos | Gratis (self-hosted) |
| **Docker** | Container para WebODM | Gratis |
| **GDAL** | Manipulacao de rasters | Gratis |

### 11.4 Software - Armazenamento e Servicos

| Software | Funcao | Custo |
|---|---|---|
| **MySQL 8.0** | Banco de metadados | Ja disponivel |
| **GeoServer** | Servir tiles WMS/WMTS | Gratis |
| **FastAPI / Flask** | API backend | Gratis |

### 11.5 Software - Visualizacao e Analise

| Software | Funcao | Custo |
|---|---|---|
| **QGIS** | GIS desktop completo | Gratis |
| **Leaflet.js / OpenLayers** | Mapas web | Gratis |
| **Jupyter Notebooks** | Analise interativa | Gratis |
| **rasterio / geopandas** | Manipulacao de dados espaciais em Python | Gratis |

### 11.6 Software - IA / Machine Learning

| Software | Funcao | Custo |
|---|---|---|
| **YOLOv8 / v11 (Ultralytics)** | Deteccao de objetos | Gratis (AGPL) |
| **Roboflow** | Datasets, treinamento, deploy | Freemium |
| **Segment Anything Model (SAM)** | Segmentacao zero-shot | Gratis |
| **scikit-learn** | Classificacao de uso do solo | Gratis |
| **QGIS SCP Plugin** | Classificacao supervisionada | Gratis |
| **OpenCV** | Processamento de imagens | Gratis |
| **PyTorch / TensorFlow** | Deep learning customizado | Gratis |

### 11.7 Bibliotecas Python Essenciais

```
rasterio          # Leitura/escrita de rasters georreferenciados
geopandas         # Dados vetoriais com geometria
shapely           # Operacoes geometricas
numpy             # Computacao numerica
scikit-learn      # Machine learning classico
ultralytics       # YOLOv8/v11
torch             # PyTorch para deep learning
opencv-python     # Processamento de imagens
matplotlib        # Visualizacao
folium            # Mapas interativos
mysql-connector   # Conexao MySQL
fastapi           # API REST
pillow            # Manipulacao de imagens
pyproj            # Projecoes cartograficas
fiona             # Leitura/escrita de vetores
```

---

## 12. Plano de Implementacao

### Fase 1: Infraestrutura Base (Semana 1-2)

- [ ] Criar banco de dados `ortomapas` no MySQL
- [ ] Executar scripts SQL de criacao de tabelas
- [ ] Instalar WebODM via Docker
- [ ] Instalar QGIS Desktop
- [ ] Instalar GeoServer via Docker
- [ ] Configurar ambiente Python com bibliotecas
- [ ] Comprar licenca do Litchi Pilot

### Fase 2: Primeiro Voo de Teste (Semana 3)

- [ ] Planejar missao de teste em area proxima e segura (Serra da Moeda)
- [ ] Usar Drone Grid Planner para criar rota
- [ ] Exportar CSV e importar no Litchi Mission Hub
- [ ] Executar voo de teste (~5 hectares)
- [ ] Processar imagens no WebODM
- [ ] Validar qualidade do ortomosaico

### Fase 3: Pipeline de Processamento (Semana 4-5)

- [ ] Desenvolver script de importacao de fotos
- [ ] Automatizar processamento WebODM via API
- [ ] Implementar registro automatico no banco MySQL
- [ ] Configurar publicacao automatica no GeoServer
- [ ] Criar interface web basica (Leaflet + FastAPI)

### Fase 4: Analises Espaciais (Semana 6-8)

- [ ] Implementar calculo de indices de vegetacao
- [ ] Implementar classificacao de uso do solo
- [ ] Implementar deteccao de mudancas temporais
- [ ] Treinar modelos YOLOv8 para objetos de interesse
- [ ] Integrar SAM para segmentacao

### Fase 5: Agentes de IA (Semana 9-12)

- [ ] Implementar orquestrador de agentes
- [ ] Implementar agente de vegetacao
- [ ] Implementar agente de deteccao de objetos
- [ ] Implementar agente de classificacao
- [ ] Implementar agente de deteccao de mudancas
- [ ] Implementar agente de relatorios (LLM)

### Fase 6: Campanhas de Campo (Continuo)

- [ ] Serra da Moeda - Mapeamento geologico
- [ ] Serra do Rola-Moca - Vegetacao de canga (apos autorizacao IEF)
- [ ] Serra do Cipo - Campos rupestres (apos autorizacao ICMBio)
- [ ] Rio das Velhas - Monitoramento de mata ciliar
- [ ] Serra do Curral - Documentacao de conflito minerario
- [ ] Quadrilatero Ferrifero - Barragens de rejeitos

---

## Apendice: Regulamentacao Resumida

### DJI Mini 3 com Bateria Padrao (248g) - Uso Recreativo
- ANAC: Isento de registro
- Seguro: Nao obrigatorio
- Licenca: Nao necessaria
- DECEA/SARPAS: Necessario em espaco aereo controlado
- Altitude maxima: 120m AGL
- VLOS obrigatorio
- 30m de distancia de pessoas

### DJI Mini 3 com Bateria Plus (~290g) - Uso Recreativo
- ANAC: **Registro obrigatorio**
- Seguro: **Obrigatorio**
- Demais regras iguais

### Em Parques Nacionais (ICMBio)
- Autorizacao previa via SISBIO
- Parceria com universidade recomendada
- Processo pode levar semanas a meses

### Em Parques Estaduais (IEF-MG)
- Autorizacao previa do IEF
- Regras especificas por parque

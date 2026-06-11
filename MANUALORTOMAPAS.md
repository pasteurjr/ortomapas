# Manual do Sistema de Ortomapas

**Versao:** 1.0 | **Data:** Marco 2026

---

## Sumario

1. [Introducao](#1-introducao)
2. [Requisitos do Sistema](#2-requisitos-do-sistema)
3. [Instalacao e Configuracao](#3-instalacao-e-configuracao)
4. [Primeiro Acesso](#4-primeiro-acesso)
5. [Gerenciamento de Projetos](#5-gerenciamento-de-projetos)
6. [Upload e Processamento de Imagens](#6-upload-e-processamento-de-imagens)
7. [Visualizacao de Ortomapas](#7-visualizacao-de-ortomapas)
8. [Ferramentas de Analise Espacial](#8-ferramentas-de-analise-espacial)
9. [Indices de Vegetacao](#9-indices-de-vegetacao)
10. [Analise de Terreno](#10-analise-de-terreno)
11. [Classificacao de Uso do Solo](#11-classificacao-de-uso-do-solo)
12. [Analise Hidrologica](#12-analise-hidrologica)
13. [Deteccao de Mudancas Temporais](#13-deteccao-de-mudancas-temporais)
14. [Calculo de Volumes](#14-calculo-de-volumes)
15. [Anotacoes e Medidas](#15-anotacoes-e-medidas)
16. [Exportacao de Resultados](#16-exportacao-de-resultados)
17. [Agentes de IA](#17-agentes-de-ia)
18. [API REST](#18-api-rest)
19. [Troubleshooting](#19-troubleshooting)

---

## 1. Introducao

O Sistema de Ortomapas e uma plataforma completa para armazenamento, visualizacao e **analise espacial** de ortomosaicos gerados por drone (DJI Mini 3). O sistema vai alem de um simples visualizador — oferece ferramentas de processamento geoespacial que integram GDAL, rasterio e algoritmos de machine learning para analise de vegetacao, terreno, hidrologia, classificacao de solo e deteccao de mudancas.

### O Que o Sistema Faz

- **Armazena** ortomapas com metadados completos em banco MySQL
- **Visualiza** ortomosaicos, DSMs e DTMs em mapa interativo web
- **Analisa** vegetacao via indices RGB (VARI, TGI, ExG, GLI)
- **Classifica** uso do solo com Random Forest e KMeans
- **Calcula** declividade, aspecto, curvas de nivel e sombreamento
- **Detecta** mudancas entre levantamentos de datas diferentes
- **Calcula** volumes (corte/aterro) a partir de modelos de superficie
- **Extrai** redes de drenagem e delimita bacias hidrograficas
- **Detecta** objetos em imagens com YOLOv8
- **Gera** relatorios automaticos com IA (Claude)

---

## 2. Requisitos do Sistema

### Hardware Minimo

| Componente | Minimo | Recomendado |
|---|---|---|
| CPU | 4 cores | 8+ cores |
| RAM | 8 GB | 16+ GB |
| Disco | 50 GB livres | 500+ GB SSD |
| GPU | Nao obrigatorio | NVIDIA para YOLOv8/SAM |

### Software

| Software | Versao | Uso |
|---|---|---|
| Python | 3.10+ | Backend e ferramentas |
| Node.js | 18+ | Frontend |
| Docker | 20+ | WebODM e GeoServer |
| GDAL | 3.x | Processamento geoespacial |
| MySQL | 8.0 | Banco de dados |
| Navegador | Chrome/Firefox atualizado | Interface web |

### Pacotes Python Principais

```
fastapi, uvicorn          # API REST
rasterio, geopandas       # Geoespacial
numpy, scikit-learn       # Analise e ML
ultralytics               # YOLOv8
anthropic                 # Relatorios IA
mysql-connector-python    # Banco de dados
```

---

## 3. Instalacao e Configuracao

### 3.1 Clonar/Copiar o Projeto

```bash
cd /mnt/data1/progpython/ortomapas
```

### 3.2 Instalar Dependencias Python

```bash
pip install -r backend/requirements.txt
```

### 3.3 Instalar Dependencias Frontend

```bash
cd frontend
npm install
cd ..
```

### 3.4 Configurar Banco de Dados

O banco MySQL esta em `<YOUR_DB_HOST>:3308`. Para criar as tabelas:

```bash
# Via mysql client
mysql -h <YOUR_DB_HOST> -P 3308 -u producao -p<YOUR_DB_PASSWORD> < backend/database/schema.sql

# Ou via script Python
python -c "from backend.database.connection import init_database; init_database()"
```

### 3.5 Popular com Dados Iniciais

```bash
python backend/database/seed.py
```

Isso cria 10 projetos reais pre-configurados (Serra do Cipo, Brumadinho, Serra da Moeda, etc.).

### 3.6 Iniciar Servicos Docker (Opcional)

```bash
# WebODM (processamento de ortomosaicos)
docker compose up webapp nodeodm -d

# GeoServer (publicacao de tiles WMS)
docker compose up geoserver -d
```

### 3.7 Iniciar o Backend

```bash
cd /mnt/data1/progpython/ortomapas
uvicorn backend.main:app --host 0.0.0.0 --port 8888 --reload
```

API disponivel em: http://localhost:8888
Documentacao Swagger: http://localhost:8888/docs

### 3.8 Iniciar o Frontend

```bash
cd frontend
npm run dev
```

Interface disponivel em: http://localhost:5173

### 3.9 Iniciar Orquestrador de Agentes (Opcional)

```bash
python -m backend.agents.orchestrator
```

---

## 4. Primeiro Acesso

### 4.1 Abrindo a Interface

Abra o navegador em `http://localhost:5173`. Voce vera:

```
+------------------------------------------+
| [Logo] Sistema de Ortomapas  [Projeto v] |
+--------+---------------------------+------+
|Projetos| Mapa (OpenStreetMap)      |Ferra-|
|--------|                           |mentas|
|Serra   |  [Mapa interativo com     |------|
|do Cipo |   base layers e controles]|[Veg] |
|--------|                           |[Terr]|
|Bruma-  |                           |[Clas]|
|dinho   |                           |[Hidr]|
|--------|                           |[Mud] |
|Serra   |                           |[Vol] |
|da Moeda|                           |[Rec] |
|--------|                           |[Exp] |
+--------+---------------------------+------+
| Status: 0 tarefas | Lat: -- Lon: --      |
+------------------------------------------+
```

### 4.2 Selecionando um Projeto

1. Clique em um projeto na barra lateral esquerda
2. O mapa centraliza na area do projeto
3. Ortomapas do projeto aparecem na lista abaixo

### 4.3 Alternando Mapa Base

Use o controle de camadas no canto superior direito do mapa para alternar entre OpenStreetMap e imagem de satelite.

---

## 5. Gerenciamento de Projetos

### 5.1 Criar Novo Projeto

1. Clique em "Novo Projeto" na barra lateral
2. Preencha: Nome, Area de Estudo, Descricao, Objetivo
3. Opcionalmente defina a bbox (bounding box) clicando no mapa
4. Clique "Salvar"

### 5.2 Projetos Pre-Configurados

O sistema vem com 10 projetos baseados em areas proximas a Belo Horizonte:

| Projeto | Area | Foco |
|---|---|---|
| Serra do Cipo - Lapinha | Lapinha da Serra | Campos rupestres |
| Brumadinho - Paraopeba | Rio Paraopeba | Monitoramento pos-desastre |
| Serra da Moeda | Topo do Mundo | Geologia estrutural |
| Rio das Velhas | Rio Acima | Qualidade hidrica |
| Serra da Piedade | Caete | Geologia de itabirito |
| Serra do Gandarela | Rio Acima-Itabirito | Mineracao vs. conservacao |
| Serra do Curral | Nova Lima | Conflito minerario |
| Lagoa Santa | Matozinhos | Geomorfologia carstica |
| QF - Lavras Novas | Ouro Preto | Mineracao historica |
| Serra de Ouro Branco | Ouro Branco | Campos rupestres |

---

## 6. Upload e Processamento de Imagens

### 6.1 Upload de Ortomapa (GeoTIFF)

1. Selecione um projeto
2. Clique em "Upload Ortomapa" na barra lateral
3. Selecione o arquivo GeoTIFF
4. O sistema automaticamente extrai: bbox, resolucao, CRS, dimensoes
5. O ortomapa aparece na lista e pode ser visualizado no mapa

### 6.2 Processamento via WebODM

Para gerar ortomosaicos a partir de fotos do drone:

1. Acesse WebODM em http://localhost:8000
2. Crie um novo projeto
3. Faca upload das fotos JPEG do drone
4. Configure parametros de processamento:
   - `--dsm --dtm` (gerar modelos de elevacao)
   - `--orthophoto-resolution 2` (2 cm/px)
   - `--feature-quality high`
5. Inicie o processamento
6. Apos conclusao, faca download dos GeoTIFFs
7. Faca upload no Sistema de Ortomapas

### 6.3 Tipos de Produtos

| Tipo | Descricao | Extensao |
|---|---|---|
| **Ortomosaico** | Mapa aereo georreferenciado | .tif (RGB) |
| **DSM** | Modelo Digital de Superficie | .tif (1 banda) |
| **DTM** | Modelo Digital de Terreno | .tif (1 banda) |
| **Nuvem de Pontos** | Modelo 3D | .laz |
| **Malha 3D** | Modelo texturizado | .obj |

---

## 7. Visualizacao de Ortomapas

### 7.1 Visualizar no Mapa

1. Na lista de ortomapas, clique no icone de olho para ativar a camada
2. O ortomapa aparece sobreposto ao mapa base
3. Use zoom para ver em alta resolucao
4. Arraste para navegar

### 7.2 Controles de Camada

- **Opacidade:** Slider para ajustar transparencia da camada
- **Ordem:** Arraste camadas para mudar a sobreposicao
- **Visibilidade:** Clique no olho para ligar/desligar
- **Zoom para camada:** Clique no icone de lupa para enquadrar

### 7.3 Comparacao Temporal

1. Acesse a aba "Mudancas" no painel de ferramentas
2. Selecione ortomapa "Antes" e "Depois"
3. Use o modo Swipe para deslizar entre as duas imagens
4. Ou use Side-by-Side para ver lado a lado

### 7.4 Informacoes do Pixel

Passe o mouse sobre o ortomapa para ver:
- Coordenadas (latitude/longitude) na barra de status
- Valores RGB do pixel (ao clicar)

---

## 8. Ferramentas de Analise Espacial

O painel de ferramentas (lado direito) contem 8 categorias de analise. Cada ferramenta processa o raster e gera um novo resultado que pode ser visualizado como camada no mapa.

### Fluxo Geral de Qualquer Ferramenta

1. Selecione o ortomapa/DSM/DTM de entrada
2. Configure os parametros
3. Clique no botao de execucao
4. Aguarde o processamento (barra de progresso)
5. O resultado aparece automaticamente como nova camada no mapa
6. Estatisticas sao exibidas no painel

### Ferramentas Disponiveis

| Categoria | Ferramentas | Entrada |
|---|---|---|
| **Vegetacao** | VARI, TGI, ExG, GLI | Ortomosaico RGB |
| **Terreno** | Slope, Aspect, Contornos, Hillshade | DSM ou DTM |
| **Classificacao** | Random Forest, KMeans | Ortomosaico RGB |
| **Hidrologia** | Bacia, Drenagem, TWI | DTM |
| **Mudancas** | Deteccao temporal | 2 Ortomosaicos |
| **Volume** | Corte/aterro | DSM |
| **Recorte** | Clip por poligono | Qualquer raster |
| **Exportar** | Converter formato | Qualquer raster |

---

## 9. Indices de Vegetacao

### 9.1 O Que Sao

Indices de vegetacao sao combinacoes matematicas das bandas RGB que realcam a presenca e saude da vegetacao. Como o DJI Mini 3 possui **camera RGB apenas** (sem NIR/multiespectral), usamos indices adaptados para RGB.

### 9.2 Indices Disponiveis

| Indice | Formula | Melhor Para |
|---|---|---|
| **VARI** | (G - R) / (G + R - B) | Saude geral, resistente a variacao atmosferica |
| **TGI** | G - 0.39R - 0.61B | Proxy de clorofila em alta cobertura |
| **ExG** | 2G - R - B | Deteccao simples de verde |
| **GLI** | (2G - R - B) / (2G + R + B) | Deteccao normalizada de verde |

### 9.3 Como Usar

1. No painel de ferramentas, selecione a aba **Vegetacao**
2. Selecione o ortomapa de entrada
3. Escolha o indice (ex: VARI)
4. Clique "Calcular"
5. O resultado aparece como camada colorida:
   - **Verde escuro:** Vegetacao saudavel (valores altos)
   - **Amarelo:** Vegetacao estressada (valores medios)
   - **Vermelho/Marrom:** Solo exposto ou sem vegetacao (valores baixos)

### 9.4 Interpretacao

- **Valores VARI > 0.2:** Vegetacao densa e saudavel
- **Valores VARI 0 a 0.2:** Vegetacao presente mas estressada ou esparsa
- **Valores VARI < 0:** Solo exposto, agua ou rocha

### 9.5 Limitacoes

> **IMPORTANTE:** Indices RGB nao substituem NDVI real de cameras multiespectrais. Use para comparacoes **relativas** dentro de um mesmo levantamento. Nao compare valores absolutos entre datas diferentes ou condicoes de iluminacao diferentes.

### 9.6 Via API

```bash
curl -X POST http://localhost:8888/api/tools/vegetation \
  -H "Content-Type: application/json" \
  -d '{
    "input_path": "data/ortomapas/serra_moeda_ortho.tif",
    "output_name": "serra_moeda_vari",
    "index_name": "VARI"
  }'
```

---

## 10. Analise de Terreno

### 10.1 Declividade (Slope)

Calcula o angulo de inclinacao do terreno em graus (0-90).

**Entrada:** DSM ou DTM
**Saida:** Raster com valores de 0 (plano) a 90 (vertical)

**Interpretacao:**
| Classe | Graus | Descricao |
|---|---|---|
| Plano | 0-3 | Terreno plano |
| Suave | 3-8 | Suavemente ondulado |
| Ondulado | 8-20 | Ondulado |
| Forte | 20-45 | Fortemente ondulado |
| Montanhoso | 45-75 | Montanhoso |
| Escarpado | >75 | Escarpamento |

### 10.2 Aspecto (Orientacao)

Indica a direcao para onde a encosta esta voltada (0-360 graus).

**Interpretacao:**
- 0/360 = Norte
- 90 = Leste
- 180 = Sul
- 270 = Oeste

Util para entender exposicao solar e padroes de vegetacao.

### 10.3 Curvas de Nivel (Contornos)

Gera linhas de mesma altitude a intervalos regulares.

**Parametros:**
- **Intervalo:** Distancia vertical entre curvas (ex: 5m, 10m)
- **Saida:** GeoJSON com linhas de contorno

### 10.4 Sombreamento (Hillshade)

Simula a iluminacao do terreno para visualizacao 3D.

**Parametros:**
- **Azimute:** Direcao do sol (0-360, padrao 315 = noroeste)
- **Altitude:** Angulo do sol (0-90, padrao 45)

### 10.5 Como Usar

1. Selecione aba **Terreno** no painel de ferramentas
2. Selecione o DSM ou DTM
3. Clique no botao da analise desejada (Slope, Aspect, Contornos ou Hillshade)
4. Para contornos, defina o intervalo
5. Resultado aparece como nova camada

---

## 11. Classificacao de Uso do Solo

### 11.1 Metodos Disponiveis

**Supervisionado (Random Forest):**
1. Voce marca areas de exemplo no mapa (amostras de treinamento)
2. Define a classe de cada area (ex: vegetacao, agua, solo)
3. O algoritmo aprende os padroes e classifica todo o ortomapa

**Nao-Supervisionado (KMeans):**
1. O algoritmo agrupa pixels similares automaticamente
2. Voce interpreta os grupos apos a classificacao
3. Nao requer amostras de treinamento

### 11.2 Classes Padrao

| Codigo | Classe | Cor |
|---|---|---|
| 1 | Vegetacao densa | Verde escuro |
| 2 | Vegetacao rasteira | Verde claro |
| 3 | Solo exposto | Marrom |
| 4 | Agua | Azul |
| 5 | Urbano | Cinza |
| 6 | Agricola | Amarelo |
| 7 | Rocha | Cinza claro |

### 11.3 Como Usar (Supervisionado)

1. Selecione aba **Classificacao**
2. Selecione o ortomapa
3. Escolha "Random Forest"
4. Clique "Desenhar Amostras"
5. No mapa, desenhe poligonos sobre areas representativas de cada classe
6. Para cada poligono, selecione a classe
7. Quando tiver amostras suficientes (minimo 5 por classe), clique "Classificar"
8. Aguarde o processamento
9. O mapa classificado aparece como camada

### 11.4 Como Usar (Nao-Supervisionado)

1. Selecione aba **Classificacao**
2. Selecione o ortomapa
3. Escolha "KMeans"
4. Defina numero de clusters (padrao: 7)
5. Clique "Classificar"
6. Interprete os clusters resultantes

### 11.5 Metricas de Qualidade

Apos classificacao supervisionada, o sistema exibe:
- **Acuracia geral:** Percentual de pixels corretamente classificados
- **Kappa:** Concordancia alem do acaso (>0.8 = excelente)
- **Matriz de confusao:** Erros por classe

---

## 12. Analise Hidrologica

### 12.1 Funcionalidades

Todas as ferramentas hidrologicas usam o **DTM** (Modelo Digital de Terreno) como entrada.

| Ferramenta | Descricao |
|---|---|
| **Delimitacao de Bacia** | Delimita a bacia hidrografica a montante de um ponto |
| **Rede de Drenagem** | Extrai automaticamente a rede de cursos d'agua |
| **TWI** | Indice Topografico de Umidade — indica zonas umidas |

### 12.2 Delimitacao de Bacia

1. Selecione aba **Hidrologia**
2. Selecione o DTM
3. Clique "Delimitar Bacia"
4. Clique no mapa para definir o ponto de exutorio (pour point)
5. O sistema calcula a bacia a montante e exibe como poligono

### 12.3 Rede de Drenagem

1. Selecione o DTM
2. Defina o limiar de acumulacao (threshold):
   - Baixo (50): muitos cursos d'agua, incluindo efemeros
   - Medio (100): rede principal + tributarios
   - Alto (500): apenas rios principais
3. Clique "Extrair Drenagem"
4. A rede aparece como camada de linhas

### 12.4 TWI (Indice Topografico de Umidade)

Indica zonas com maior probabilidade de acumulo de agua.

**Formula:** TWI = ln(area_acumulacao / tan(declividade))

**Interpretacao:**
- Valores altos: zonas umidas, fundos de vale
- Valores baixos: topos de morro, areas bem drenadas

---

## 13. Deteccao de Mudancas Temporais

### 13.1 Conceito

Compara dois ortomapas da **mesma area** em **datas diferentes** para identificar o que mudou.

### 13.2 Como Usar

1. Selecione aba **Mudancas**
2. Selecione ortomapa "Antes" (data mais antiga)
3. Selecione ortomapa "Depois" (data mais recente)
4. Ajuste o limiar de deteccao:
   - Baixo (10): detecta mudancas sutis (mais falsos positivos)
   - Medio (30): equilibrio (recomendado)
   - Alto (50): detecta apenas mudancas grandes
5. Clique "Detectar Mudancas"

### 13.3 Resultado

O mapa de mudancas mostra:
- **Vermelho:** Areas com mudanca significativa
- **Verde:** Areas sem mudanca

Estatisticas exibidas:
- Area total mapeada
- Area alterada (m2 e hectares)
- Percentual de mudanca

### 13.4 Aplicacoes

- Desmatamento entre campanhas
- Avanco de mineracao
- Erosao de trilhas
- Recuperacao de vegetacao pos-fogo
- Expansao urbana

---

## 14. Calculo de Volumes

### 14.1 Volume Sobre Plano de Referencia

Calcula o volume de material acima ou abaixo de uma altitude de referencia.

1. Selecione aba **Volume**
2. Selecione o DSM
3. Defina a elevacao de referencia (metros)
4. Clique "Calcular Volume"

**Resultado:**
- Volume acima do plano (m3)
- Volume abaixo do plano (m3)
- Volume liquido (m3)

### 14.2 Diferenca Entre DSMs (Corte/Aterro)

Compara dois DSMs de datas diferentes para calcular corte e aterro.

1. Selecione DSM "Antes"
2. Selecione DSM "Depois"
3. Clique "Calcular Corte/Aterro"

**Resultado:**
- Volume de corte (m3) — material removido
- Volume de aterro (m3) — material adicionado
- Area de corte (m2)
- Area de aterro (m2)

### 14.3 Aplicacoes

- Monitoramento de mineracao (volume extraido)
- Erosao (volume de solo perdido)
- Construcao (terraplenagem)

---

## 15. Anotacoes e Medidas

### 15.1 Ferramentas de Anotacao

| Ferramenta | Uso |
|---|---|
| **Ponto** | Marcar locais de interesse |
| **Linha** | Tracar caminhos, trilhas |
| **Poligono** | Delimitar areas (erosao, vegetacao, etc.) |
| **Retangulo** | Selecao rapida de area |

### 15.2 Como Anotar

1. Clique no icone de desenho na toolbar do mapa
2. Selecione o tipo de geometria
3. Desenhe no mapa
4. Preencha: Categoria (ex: "erosao") e Rotulo (ex: "Voçoroca principal")
5. Clique "Salvar"

### 15.3 Medir Distancia

1. Clique no icone de regua
2. Clique nos pontos do percurso
3. A distancia acumulada aparece em tempo real
4. Duplo-clique para finalizar

### 15.4 Medir Area

1. Clique no icone de medida de area
2. Desenhe o poligono
3. A area aparece em m2 e hectares

---

## 16. Exportacao de Resultados

### 16.1 Formatos Disponiveis

| Formato | Extensao | Uso |
|---|---|---|
| **GeoTIFF** | .tif | Dados raster georreferenciados |
| **PNG** | .png | Imagem para relatorio |
| **KML** | .kml | Google Earth |
| **GeoJSON** | .geojson | Dados vetoriais web |
| **Shapefile** | .shp | SIG desktop (QGIS, ArcGIS) |

### 16.2 Como Exportar

1. Selecione a camada/resultado desejado
2. Clique no icone de exportacao ou use a aba "Exportar"
3. Selecione o formato
4. Opcionalmente selecione CRS de saida (EPSG:4326, EPSG:31983)
5. Clique "Exportar"
6. O download inicia automaticamente

---

## 17. Agentes de IA

### 17.1 O Que Sao

Agentes de IA sao processos autonomos que executam analises automaticamente. Eles consultam uma fila de tarefas no banco de dados e processam ortomapas sem intervencao manual.

### 17.2 Agentes Disponiveis

| Agente | Funcao |
|---|---|
| **Vegetacao** | Calcula indices e classifica saude vegetal |
| **Deteccao** | Detecta objetos com YOLOv8 (arvores, edificacoes) |
| **Classificacao** | Classifica uso do solo automaticamente |
| **Mudancas** | Detecta alteracoes entre datas |
| **Relatorio** | Gera relatorio interpretativo com Claude |

### 17.3 Como Disparar Uma Analise

1. Selecione um ortomapa
2. Clique em "Nova Analise" no painel inferior
3. Escolha o tipo de analise
4. Configure parametros (se necessario)
5. Clique "Executar"
6. A tarefa entra na fila
7. O orquestrador processa automaticamente
8. Quando concluida, o resultado aparece na lista de analises

### 17.4 Monitoramento

A barra de status inferior mostra:
- Numero de tarefas na fila
- Tarefas em execucao
- Ultima tarefa concluida

### 17.5 Iniciar o Orquestrador

O orquestrador e um processo separado:

```bash
python -m backend.agents.orchestrator
```

Ele roda em loop, verificando novas tarefas a cada 10 segundos.

---

## 18. API REST

Todos os endpoints estao documentados no Swagger: http://localhost:8888/docs

### 18.1 Endpoints Principais

| Metodo | Endpoint | Descricao |
|---|---|---|
| GET | /api/projetos | Listar projetos |
| POST | /api/projetos | Criar projeto |
| GET | /api/ortomapas | Listar ortomapas |
| POST | /api/ortomapas/upload | Upload de GeoTIFF |
| GET | /api/ortomapas/{id}/tile/{z}/{x}/{y}.png | Tile do ortomapa |
| POST | /api/tools/vegetation | Calcular indice de vegetacao |
| POST | /api/tools/slope | Calcular declividade |
| POST | /api/tools/classify | Classificar uso do solo |
| POST | /api/tools/changes | Detectar mudancas |
| POST | /api/tools/volume | Calcular volume |
| POST | /api/tools/hydrology/streams | Extrair drenagem |
| GET | /api/analises | Listar analises |
| POST | /api/anotacoes | Criar anotacao |

### 18.2 Exemplo: Calcular VARI

```bash
curl -X POST http://localhost:8888/api/tools/vegetation \
  -H "Content-Type: application/json" \
  -d '{
    "input_path": "data/ortomapas/exemplo.tif",
    "output_name": "exemplo_vari",
    "index_name": "VARI"
  }'
```

**Resposta:**
```json
{
  "status": "success",
  "output_path": "data/analises/exemplo_vari.tif",
  "statistics": {
    "min": -0.85,
    "max": 0.72,
    "mean": 0.15,
    "std": 0.23,
    "area_vegetacao_ha": 12.5,
    "area_solo_ha": 3.2
  }
}
```

---

## 19. Troubleshooting

### 19.1 Backend Nao Inicia

```
Erro: Connection refused <YOUR_DB_HOST>:3308
```
- Verificar se o servidor MySQL esta acessivel
- Testar: `mysql -h <YOUR_DB_HOST> -P 3308 -u producao -p`
- O sistema funciona em modo offline (sem banco) para as ferramentas de analise

### 19.2 Ortomapa Nao Aparece no Mapa

- Verificar se o arquivo e um GeoTIFF valido: `gdalinfo arquivo.tif`
- Verificar se possui CRS definido (EPSG:4326 ou outro)
- Verificar se as coordenadas estao corretas (nao invertidas)
- Tentar reprojetar: usar a ferramenta Reprojetar para EPSG:4326

### 19.3 Analise de Vegetacao Com Valores Estranhos

- Verificar ordem das bandas: o sistema assume R=1, G=2, B=3
- Verificar se nao ha valores NoData afetando o calculo
- Para imagens DJI Mini 3, a ordem das bandas e R,G,B (padrao)

### 19.4 Classificacao Com Baixa Acuracia

- Aumentar o numero de amostras de treinamento (minimo 50 pixels por classe)
- Verificar se as amostras sao representativas
- Tentar outro algoritmo (SVM em vez de RF)
- Adicionar indices de vegetacao como features extras

### 19.5 Anomalia Magnetica na Captura

Se o drone apresentou comportamento erratico durante o voo (areas do Quadrilatero Ferrifero):
- Verificar fotos com posicao GPS incorreta
- Remover fotos outliers antes do processamento
- Usar GCPs para corrigir o georreferenciamento

### 19.6 Memoria Insuficiente

Para ortomapas muito grandes (>10.000 x 10.000 pixels):
- Use a ferramenta Recorte para processar areas menores
- Reduza a resolucao com a ferramenta Reamostragem
- Aumente o swap do sistema

### 19.7 Frontend Nao Conecta ao Backend

- Verificar se o backend esta rodando na porta 8888
- Verificar o proxy no vite.config.js
- Verificar CORS no backend

### 19.8 WebODM Nao Processa

- Verificar se os containers Docker estao rodando: `docker ps`
- Verificar logs: `docker logs ortomapas-webodm`
- Verificar se o NodeODM esta acessivel: http://localhost:3000

---

## Apendice: Atalhos de Teclado

| Tecla | Acao |
|---|---|
| **+/-** | Zoom in/out no mapa |
| **Esc** | Cancelar desenho/medida |
| **Delete** | Remover anotacao selecionada |
| **1-8** | Alternar abas de ferramentas |

---

## Apendice: Estrutura de Diretorios

```
/mnt/data1/progpython/ortomapas/
├── backend/           # API FastAPI + ferramentas
├── frontend/          # Interface Vue + Leaflet
├── data/              # Dados (ortomapas, DSMs, resultados)
├── geojson/           # Limites de areas (Serra do Cipo, etc.)
├── docs/              # Documentacao
├── docker-compose.yml # WebODM + GeoServer
└── MANUALORTOMAPAS.md # Este manual
```

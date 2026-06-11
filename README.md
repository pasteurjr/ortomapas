# Sistema de Ortomapas

Plataforma web completa para armazenamento, visualizacao e **analise espacial** de ortomosaicos gerados por drone (DJI Mini 3 e similares). Vai alem de um simples visualizador — oferece ferramentas de processamento geoespacial que integram GDAL, rasterio, scikit-learn e agentes de IA para analise de vegetacao, terreno, hidrologia, classificacao de solo e deteccao de mudancas.

## Funcionalidades

- **Armazenamento** com metadados completos em banco MySQL (com fallback SQLite)
- **Visualizacao** de ortomosaicos, DSMs e DTMs em mapa interativo (Leaflet)
- **Indices de vegetacao** RGB: VARI, TGI, ExG, GLI
- **Analise de terreno**: declividade, aspecto, hillshade, curvas de nivel
- **Classificacao** de uso do solo (KMeans, Random Forest, SVM)
- **Hidrologia**: bacia hidrografica, rede de drenagem, TWI
- **Volumetria**: volume acima/abaixo de referencia, corte/aterro
- **Deteccao de mudancas** temporais entre datas
- **Segmentacao** de imagens
- **Anotacoes** com geometria WKT (ponto, linha, poligono)
- **Medicoes** de distancia e area diretamente no mapa
- **Comparacao** lado-a-lado e swipe entre ortomapas
- **Exportacao** em GeoTIFF, PNG, KML, GeoJSON
- **Agentes de IA** autonomos (vegetacao, deteccao YOLOv8, classificacao, mudancas, relatorios)
- **18 ferramentas espaciais** expostas como endpoints REST + integradas a UI

## Arquitetura

```
+-----------------------------------------------------+
|  Frontend Vue 3 + Leaflet + PrimeVue (port 5176)    |
+-----------------------------------------------------+
                         |  HTTP
+-----------------------------------------------------+
|  Backend FastAPI (port 8888)                        |
|  ├─ 6 routers (projetos, voos, ortomapas, etc.)     |
|  ├─ 7 modulos de tools (GDAL, rasterio, sklearn)    |
|  └─ 5 agentes IA + orquestrador                     |
+-----------------------------------------------------+
       |                |                  |
   MySQL/SQLite     File system        Docker (opcional)
                   (GeoTIFFs)          ├─ WebODM
                                       └─ GeoServer
```

## Stack Tecnologica

| Camada | Tecnologia |
|---|---|
| Backend | FastAPI 0.129+, Python 3.10+ |
| Frontend | Vue 3, Vite, Leaflet, PrimeVue, Pinia |
| Geoespacial | GDAL 3.4+, rasterio, geopandas, shapely |
| ML/IA | scikit-learn, ultralytics (YOLOv8), Anthropic API |
| Banco | MySQL 8.0 (fallback SQLite) |
| Container | Docker (WebODM + GeoServer opcionais) |

## Instalacao Rapida

```bash
# 1. Clonar
git clone https://github.com/pasteurjr/ortomapas.git
cd ortomapas

# 2. Configurar credenciais
cp .env.example .env
# Editar .env com suas credenciais reais

# 3. Backend
pip install -r backend/requirements.txt
uvicorn backend.main:app --host 0.0.0.0 --port 8888 --reload

# 4. Frontend (em outro terminal)
cd frontend && npm install && npm run dev

# 5. Acesse:
#    Interface: http://localhost:5173 (ou 5176)
#    API docs:  http://localhost:8888/docs
```

## Estrutura do Projeto

```
ortomapas/
├── backend/                # FastAPI app
│   ├── main.py
│   ├── config.py
│   ├── database/           # schema, connection, models, seed
│   ├── routers/            # 6 routers REST
│   ├── tools/              # 7 modulos de analise espacial
│   ├── agents/             # 5 agentes IA + orquestrador
│   └── utils/              # geo, thumbnail, file_manager
├── frontend/               # Vue 3 + Vite
│   ├── package.json
│   └── src/
│       ├── App.vue
│       ├── main.js
│       ├── api/client.js
│       ├── stores/         # 2 Pinia stores
│       └── components/     # 13 componentes Vue
├── docs/                   # Documentacao tecnica
│   ├── analise/            # 6 docs de analise/spec
│   └── validacao/          # Relatorios E2E
├── tests/e2e/playwright/   # Testes Playwright
├── geojson/                # Limites de UCs (Serra do Cipo, etc.)
├── data/                   # GeoTIFFs (gitignored, gerados localmente)
├── docker-compose.yml      # WebODM + GeoServer
├── .env.example
├── .gitignore
└── README.md
```

## Documentacao

- [Manual do Usuario](MANUALORTOMAPAS.md) — guia completo passo-a-passo
- [Especificacao Funcional](docs/analise/especificacao_funcional.md) — 19 grupos de funcionalidades
- [Casos de Uso](docs/analise/casos_de_uso.md) — 20 UCs detalhados com fluxos
- [Arquitetura](docs/analise/arquitetura_observada.md) — diagramas e fluxos
- [Entidades e Regras](docs/analise/entidades_e_regras.md) — modelo de dados
- [Operacao do Drone](configdrone.md) — configurar DJI Mini 3 + Litchi Pilot
- [Analise de Areas](ANALISE%20AREAS.md) — 19 regioes de interesse no entorno de BH
- [Parecer de Validacao](docs/validacao/parecer_final_multi_dataset.md) — 100/100 testes em 7 datasets reais

## Validacao

O sistema foi validado com auto research iterativo (Playwright + multi-dataset):

| Metrica | Valor |
|---|---|
| Datasets reais testados | 7 (Sentinel-2, Landsat, ortofoto Trento, Derna, DEMs) |
| Casos de uso | 20 documentados, 17 testados |
| Total de testes E2E | 133 |
| Aprovados | 100 (100% excluindo SKIPs esperados) |
| Divergencias residuais | 0 |
| Cobertura de requisitos | 125/128 (97.7%) |

Ver [parecer_final_multi_dataset.md](docs/validacao/parecer_final_multi_dataset.md).

## Variaveis de Ambiente

Veja [.env.example](.env.example). Principais:

| Variavel | Descricao |
|---|---|
| `DB_HOST` | Host do MySQL (fallback SQLite se inacessivel) |
| `DB_PORT` | Porta MySQL |
| `DB_USER` | Usuario MySQL |
| `DB_PASSWORD` | Senha MySQL |
| `DB_NAME` | Nome do banco |
| `WEBODM_URL` | URL do WebODM (opcional) |
| `GEOSERVER_URL` | URL do GeoServer (opcional) |
| `ANTHROPIC_API_KEY` | Para gerar relatorios via Claude (opcional) |

## Licenca

Projeto em desenvolvimento. Licenca a definir.

## Contexto

Sistema desenvolvido para pesquisa em ortomapeamento por drone (DJI Mini 3, 248g) na regiao metropolitana de Belo Horizonte, MG. Foco em:

- Monitoramento ambiental (Serra do Cipo, Serra da Moeda, Brumadinho/Paraopeba)
- Geologia estrutural do Quadrilatero Ferrifero
- Hidrologia e mata ciliar do Rio das Velhas
- Documentacao do conflito minerario na Serra do Curral
- Geomorfologia carstica de Lagoa Santa

Ver [ANALISE AREAS.md](ANALISE%20AREAS.md) para detalhes.

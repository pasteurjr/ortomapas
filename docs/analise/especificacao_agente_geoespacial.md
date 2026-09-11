# Especificação do Agente Geoespacial Ortomapas

**Versão:** 1.0  
**Data:** 11/09/2026  
**Status:** Especificação para implementação

## 1. Objetivo

O Ortomapas terá um copiloto geoespacial capaz de receber prompts do usuário, consultar os dados do projeto, executar análises raster, vetoriais, altimétricas e de nuvem de pontos, e explicar os resultados com rastreabilidade.

O agente não substituirá os algoritmos. Cálculos serão executados por ferramentas determinísticas; o modelo de linguagem planejará, interpretará e apresentará os resultados.

## 2. Modelo e infraestrutura

- Provedor local: LM Studio.
- API: `http://127.0.0.1:1234/v1`.
- Modelo inicial: Qwen 2.5 32B Coder.
- Interface: API compatível com OpenAI (`chat/completions`, tool calling e JSON Schema).
- Banco principal: PostgreSQL/PostGIS do Ortomapas.
- Processamento: Python, Rasterio, GDAL, NumPy, GeoPandas, Shapely e laspy.
- ODM: WebODM/NodeODM para fotogrametria.
- Publicação cartográfica: QGIS Server usando serviços OGC.

## 3. Orquestração

Será usado LangGraph para workflows com estado, checkpoints, retries, aprovação humana e tarefas longas. LangChain Core será utilizado apenas para mensagens, schemas e ferramentas. CrewAI não será adotado inicialmente.

O usuário verá um único **Ortomapas Copilot**. Internamente haverá módulos especializados: qualidade, raster, terreno, nuvem de pontos, temporal e relatório.

## 4. Catálogo de ferramentas

### Projeto e dados

| Ferramenta | Entrada | Saída |
|---|---|---|
| `listar_projetos` | usuário, filtro | projetos autorizados |
| `listar_produtos` | projeto, tipo | produtos e metadados |
| `consultar_voos` | projeto, intervalo | voos e parâmetros |
| `consultar_anotacoes` | projeto, bbox | geometrias e atributos |

### Raster

| Ferramenta | Entrada | Saída |
|---|---|---|
| `estatisticas_raster` | produto | min, max, média, NoData, CRS |
| `recortar_raster` | produto, bbox/polígono | novo raster |
| `calcular_indice` | ortomosaico, índice | raster temático |
| `calcular_declividade` | DSM/DTM | raster de declividade |
| `calcular_aspecto` | DSM/DTM | raster de orientação |
| `gerar_hillshade` | DSM/DTM, parâmetros | raster sombreado |
| `curvas_de_nivel` | DSM/DTM, intervalo | GeoJSON/GeoPackage |
| `estatistica_zonal` | raster, polígonos | tabela por zona |

### Terreno e volumes

| Ferramenta | Entrada | Saída |
|---|---|---|
| `comparar_dsm_dtm` | DSM, DTM | diferença, estatísticas, raster |
| `calcular_volume` | superfície, polígono, cota | corte, aterro ou volume |
| `perfil_altimetrico` | superfície, linha | perfil e gráfico |
| `detectar_anomalias_altimetria` | DSM/DTM | áreas suspeitas |

### Nuvem de pontos

| Ferramenta | Entrada | Saída |
|---|---|---|
| `estatisticas_laz` | LAZ | pontos, densidade, faixa Z |
| `filtrar_nuvem` | LAZ, bbox, faixa Z | novo LAZ/CSV |
| `detectar_outliers` | LAZ | pontos anômalos |
| `classificar_pontos` | LAZ, método | classes e métricas |

### Vetorial, PostGIS e OGC

| Ferramenta | Entrada | Saída |
|---|---|---|
| `intersectar_camadas` | camadas, predicado | feições resultantes |
| `buffer` | camada, distância | polígono buffer |
| `calcular_distancia` | feições | distância/tempo espacial |
| `consulta_postgis` | operação tipada | GeoJSON/tabela |
| `publicar_wms` | resultado, estilo | camada WMS |
| `consultar_wfs` | camada, filtro | GeoJSON |

### ODM e relatórios

- `consultar_processamento_odm`
- `importar_produtos_odm`
- `baixar_relatorio_odm`
- `avaliar_qualidade_odm`
- `gerar_relatorio_consolidado`

## 5. Fontes de dados cadastrais e contextuais

Para interseção com propriedades, estradas, rios e limites administrativos, o sistema deverá aceitar:

1. dados fornecidos pelo usuário em GeoPackage, GeoJSON, Shapefile ou GeoTIFF;
2. camadas PostGIS importadas pelo administrador;
3. serviços WFS/OGC de órgãos públicos;
4. camadas publicadas pelo QGIS Server;
5. futuramente, bases oficiais como CAR, SIGEF, IBGE, hidrografia e limites municipais, sempre com fonte, data, licença e CRS registrados.

Não será permitido baixar bases públicas automaticamente sem registrar origem, versão, licença e responsável pela importação.

Cada camada cadastral terá: `nome`, `fonte`, `data_referencia`, `crs`, `escala`, `licenca`, `projeto_id` e metadados de qualidade.

## 6. Fluxo de uma solicitação

1. Usuário envia um prompt.
2. Agente identifica projeto, produtos e área de interesse.
3. LangGraph monta o plano e solicita aprovação quando houver escrita ou processamento caro.
4. Ferramentas executam cálculos determinísticos.
5. Resultado é validado por schema.
6. Artefatos são salvos em `analises`, `anotacoes` ou `produtos_processamento`.
7. Qwen interpreta os dados e redige a resposta.
8. Interface apresenta mapa, camada, números, limitações e recomendações.

## 7. Segurança e rastreabilidade

- ferramentas com schemas fechados;
- sem SQL livre ou shell livre para o modelo;
- autorização por projeto;
- confirmação humana para escrita, exclusão, publicação ou novo processamento;
- auditoria de prompt, ferramentas, parâmetros, modelo e versão dos dados;
- resultados reproduzíveis e vinculados ao produto de origem.

## 8. Roadmap do agente

1. Catálogo e schemas das ferramentas.
2. Adaptador LM Studio e resposta JSON estruturada.
3. Grafo LangGraph básico com consulta e análise raster.
4. Ferramentas PostGIS e QGIS/OGC.
5. Análise de nuvem e terreno.
6. Memória por projeto e aprovação humana.
7. Relatório consolidado e avaliação de qualidade com IA.


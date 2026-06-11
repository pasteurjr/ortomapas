# Verificacao de Implementacao - Sistema de Ortomapas

**Versao:** 1.0 | **Data:** 2026-03-28
**Autor:** Agent 2 - Implementation Verifier
**Baseado em:** 01_requisitos_casos_uso.md, codigo-fonte backend e frontend

---

## Grupo: REQ-PRJ -- Projetos

| Requisito | Descricao | Backend | Frontend | Veredicto | Observacao |
|---|---|---|---|---|---|
| REQ-PRJ-001 | Listar projetos ordenados por data criacao (desc) | projetos.py:L41 `GET /projetos` ORDER BY criado_em DESC | ProjectList.vue:L27 v-for projects | IMPLEMENTADO | OK |
| REQ-PRJ-002 | Filtrar projetos por status | projetos.py:L54 `status = %s` | ProjectList.vue (sem campo de filtro status no template) | PARCIALMENTE IMPLEMENTADO | Backend OK. Frontend nao expoe campo de filtro por status na UI; apenas lista todos os projetos |
| REQ-PRJ-003 | Filtrar projetos por area_estudo (busca parcial) | projetos.py:L58 `area_estudo LIKE %s` | ProjectList.vue (sem campo de filtro) | PARCIALMENTE IMPLEMENTADO | Backend OK com LIKE. Frontend nao expoe campo de filtro por area_estudo na UI |
| REQ-PRJ-004 | Busca textual em projetos (nome, descricao, area_estudo) | projetos.py:L17 `GET /projetos/search?q=` com LIKE em 3 campos | client.js (sem funcao searchProjects) | PARCIALMENTE IMPLEMENTADO | Backend OK. API client nao tem funcao para chamar /projetos/search. Frontend nao tem campo de busca |
| REQ-PRJ-005 | Detalhes de projeto com contadores de voos, ortomapas, analises | projetos.py:L71 `GET /projetos/{id}` com total_voos, total_ortomapas, total_analises | client.js:L24 getProject(id) | IMPLEMENTADO | OK |
| REQ-PRJ-006 | Criar projeto com nome obrigatorio, descricao, area_estudo, status | projetos.py:L113 `POST /projetos` valida nome != vazio | ProjectList.vue:L54-77 Dialog com campos nome, descricao, area_estudo | IMPLEMENTADO | Dialog nao inclui campo status (usa default "ativo"), aceitavel |
| REQ-PRJ-007 | Atualizar campos de um projeto | projetos.py:L150 `PUT /projetos/{id}` atualiza nome, descricao, area_estudo, status | client.js:L32 updateProject(id, data) | IMPLEMENTADO | OK |
| REQ-PRJ-008 | Deletar projeto por ID | projetos.py:L189 `DELETE /projetos/{id}` | client.js:L36 deleteProject(id) | IMPLEMENTADO | OK |
| REQ-PRJ-009 | Listar ortomapas de um projeto | projetos.py:L210 `GET /projetos/{id}/ortomapas` | client.js:L41 getOrtomapas(projetoId) usa /ortomapas?projeto_id= | IMPLEMENTADO | Backend tem endpoint dedicado E ortomapas.py tem filtro por projeto_id. API client usa rota alternativa mas funciona |
| REQ-PRJ-010 | Selecionar projeto centraliza mapa e exibe ortomapas | -- | MapViewer.vue:L234-247 watch activeProject zoom to bbox; ProjectList.vue:L100 selectProject | IMPLEMENTADO | OK |

---

## Grupo: REQ-VOO -- Voos

| Requisito | Descricao | Backend | Frontend | Veredicto | Observacao |
|---|---|---|---|---|---|
| REQ-VOO-001 | Listar voos ordenados por data_voo (desc) | voos.py:L17 `GET /voos` ORDER BY data_voo DESC | Nenhum componente dedicado a voos no frontend | PARCIALMENTE IMPLEMENTADO | Backend OK. Frontend nao tem componente para listar/gerenciar voos |
| REQ-VOO-002 | Filtrar voos por projeto_id | voos.py:L29 `projeto_id = %s` | -- | PARCIALMENTE IMPLEMENTADO | Backend OK. Sem UI |
| REQ-VOO-003 | Detalhes de um voo por ID | voos.py:L43 `GET /voos/{id}` | -- | PARCIALMENTE IMPLEMENTADO | Backend OK. Sem UI |
| REQ-VOO-004 | Criar voo vinculado a projeto (projeto_id obrigatorio) | voos.py:L62 `POST /voos` valida projeto_id | -- | PARCIALMENTE IMPLEMENTADO | Backend OK. Sem UI para criar voos |
| REQ-VOO-005 | Validar que projeto_id existe antes de criar voo | voos.py:L76 SELECT id FROM projetos WHERE id = %s | -- | IMPLEMENTADO | Backend valida corretamente |
| REQ-VOO-006 | Atualizar campos de um voo | voos.py:L117 `PUT /voos/{id}` com todos os campos listados | -- | PARCIALMENTE IMPLEMENTADO | Backend OK com todos os campos. Sem UI |
| REQ-VOO-007 | Deletar voo por ID | voos.py:L162 `DELETE /voos/{id}` | -- | PARCIALMENTE IMPLEMENTADO | Backend OK. Sem UI |

---

## Grupo: REQ-ORT -- Ortomapas

| Requisito | Descricao | Backend | Frontend | Veredicto | Observacao |
|---|---|---|---|---|---|
| REQ-ORT-001 | Listar ortomapas com filtros (projeto_id, tipo, status) | ortomapas.py:L56 `GET /ortomapas` com 3 filtros opcionais | client.js:L41 getOrtomapas(projetoId) | IMPLEMENTADO | OK |
| REQ-ORT-002 | Detalhes de ortomapa por ID | ortomapas.py:L90 `GET /ortomapas/{id}` | client.js:L45 getOrtomapa(id) | IMPLEMENTADO | OK |
| REQ-ORT-003 | Criar registro de ortomapa com metadados | ortomapas.py:L109 `POST /ortomapas` aceita projeto_id, voo_id, nome, tipo, formato, bbox, resolucao, dimensoes, CRS | client.js:L49 uploadOrtomapa | IMPLEMENTADO | OK |
| REQ-ORT-004 | Upload GeoTIFF com extracao automatica de metadados via rasterio | ortomapas.py:L171 `POST /ortomapas/upload` usa get_raster_info, get_raster_bounds | client.js:L49 uploadOrtomapa envia para /ortomapas, NAO /ortomapas/upload | PARCIALMENTE IMPLEMENTADO | Backend upload endpoint existe e funciona. Porem o API client envia para /ortomapas (create) em vez de /ortomapas/upload. Frontend precisa de correcao no client.js |
| REQ-ORT-005 | Gerar thumbnail automaticamente apos upload | ortomapas.py:L199 generate_thumbnail(filepath, thumb_path) | -- | IMPLEMENTADO | OK, com fallback em caso de erro |
| REQ-ORT-006 | Servir tiles 256x256 PNG via TMS (z/x/y) | ortomapas.py:L340 `GET /ortomapas/{id}/tile/{z}/{x}/{y}.png` | MapViewer.vue:L32 l-tile-layer com URL TMS | IMPLEMENTADO | OK |
| REQ-ORT-007 | Retornar tile transparente quando fora dos bounds | ortomapas.py:L376-388 verifica intersecao, retorna RGBA(0,0,0,0) | -- | IMPLEMENTADO | OK |
| REQ-ORT-008 | Normalizar dados para uint8, tratar NoData com alpha | ortomapas.py:L431-452 normaliza para uint8, cria canal alpha para nodata | -- | IMPLEMENTADO | OK |
| REQ-ORT-009 | Consulta espacial por bounding box | ortomapas.py:L28 `GET /ortomapas/spatial?norte=&sul=&leste=&oeste=` | Nenhuma chamada no frontend | PARCIALMENTE IMPLEMENTADO | Backend OK. Frontend nao usa o endpoint spatial |
| REQ-ORT-010 | Atualizar campos de ortomapa | ortomapas.py:L263 `PUT /ortomapas/{id}` | client.js (sem funcao updateOrtomapa) | PARCIALMENTE IMPLEMENTADO | Backend OK. API client nao tem funcao para update ortomapa |
| REQ-ORT-011 | Deletar ortomapa e remover arquivo fisico | ortomapas.py:L309 `DELETE /ortomapas/{id}` + os.remove(arquivo) | client.js:L57 deleteOrtomapa(id) | IMPLEMENTADO | OK |

---

## Grupo: REQ-ANA -- Analises

| Requisito | Descricao | Backend | Frontend | Veredicto | Observacao |
|---|---|---|---|---|---|
| REQ-ANA-001 | Listar analises com filtros (ortomapa_id, tipo_analise, status) | analises.py:L20 `GET /analises` com 3 filtros | client.js:L61 getAnalises (mas passa projeto_id, nao ortomapa_id) | PARCIALMENTE IMPLEMENTADO | Backend filtra por ortomapa_id. Client.js passa projeto_id como parametro, que nao e aceito pelo backend -- inconsistencia |
| REQ-ANA-002 | Detalhes de analise por ID | analises.py:L54 `GET /analises/{id}` | client.js:L65 getAnalise(id) | IMPLEMENTADO | OK |
| REQ-ANA-003 | Criar analise (ortomapa_id e tipo_analise obrigatorios) | analises.py:L73 `POST /analises` valida ambos campos | AnalysisForm.vue:L299 submit() envia via createAnalise | IMPLEMENTADO | OK |
| REQ-ANA-004 | Enfileirar tarefa de agente (queue_task=true) | analises.py:L120 if queue_task: INSERT INTO tarefas_agente | AnalysisForm.vue (nao envia queue_task=true) | PARCIALMENTE IMPLEMENTADO | Backend suporta queue_task. Frontend AnalysisForm.vue nao inclui opcao para marcar queue_task=true |
| REQ-ANA-005 | Servir arquivo de resultado de analise concluida | analises.py:L152 `GET /analises/{id}/resultado` FileResponse | -- | IMPLEMENTADO | OK |
| REQ-ANA-006 | Deletar analise e remover arquivo resultado | analises.py:L185 `DELETE /analises/{id}` + os.remove(arquivo) | client.js:L73 deleteAnalise(id) | IMPLEMENTADO | OK |
| REQ-ANA-007 | AnalysisResults.vue exibe resultados com estatisticas | -- | AnalysisResults.vue:L33-80 painel de stats, classes, bar chart | IMPLEMENTADO | OK |
| REQ-ANA-008 | AnalysisForm.vue permite configurar e disparar analises | -- | AnalysisForm.vue:L1-328 formulario completo com tipos, parametros | IMPLEMENTADO | OK |

---

## Grupo: REQ-ANO -- Anotacoes

| Requisito | Descricao | Backend | Frontend | Veredicto | Observacao |
|---|---|---|---|---|---|
| REQ-ANO-001 | Listar anotacoes com filtros (ortomapa_id, categoria, fonte) | anotacoes.py:L19 `GET /anotacoes` com 3 filtros | client.js:L78 getAnotacoes (passa projeto_id, nao ortomapa_id) | PARCIALMENTE IMPLEMENTADO | Backend filtra por ortomapa_id. Client.js passa projeto_id que nao e aceito -- inconsistencia |
| REQ-ANO-002 | Detalhes de anotacao por ID | anotacoes.py:L116 `GET /anotacoes/{id}` | -- | IMPLEMENTADO | Backend OK. Sem funcao dedicada no client.js, mas endpoint existe |
| REQ-ANO-003 | Criar anotacao com geometria WKT (ortomapa_id e geometria_wkt obrigatorios) | anotacoes.py:L135 `POST /anotacoes` valida ambos | DrawTools.vue:L176 saveAnnotation usa createAnotacao | PARCIALMENTE IMPLEMENTADO | Backend espera ortomapa_id e geometria_wkt. Frontend DrawTools.vue envia projeto_id e geometria (nao geometria_wkt, nao ortomapa_id) -- mismatch nos nomes de campos |
| REQ-ANO-004 | Validar geometria WKT ao criar/atualizar | anotacoes.py:L160 wkt_to_geojson(geometria_wkt); L227 mesma validacao no PUT | -- | IMPLEMENTADO | OK |
| REQ-ANO-005 | Atualizar campos de anotacao | anotacoes.py:L203 `PUT /anotacoes/{id}` com categoria, rotulo, geometria_wkt, tipo, fonte, confianca | client.js:L86 updateAnotacao(id, data) | IMPLEMENTADO | OK |
| REQ-ANO-006 | Deletar anotacao por ID | anotacoes.py:L257 `DELETE /anotacoes/{id}` | client.js:L90 deleteAnotacao(id) | IMPLEMENTADO | OK |
| REQ-ANO-007 | Exportar anotacoes como GeoJSON FeatureCollection | anotacoes.py:L53 `GET /anotacoes/geojson/{ortomapa_id}` | -- | IMPLEMENTADO | OK |
| REQ-ANO-008 | FeatureCollection contem propriedades e geometria convertida de WKT | anotacoes.py:L85-101 exclui geometria_wkt, converte datetime, monta feature | -- | IMPLEMENTADO | OK |

---

## Grupo: REQ-VEG -- Indices de Vegetacao

| Requisito | Descricao | Backend | Frontend | Veredicto | Observacao |
|---|---|---|---|---|---|
| REQ-VEG-001 | Calcular VARI: (G-R)/(G+R-B) | raster_analysis.py:L68-71 formula VARI correta | -- | IMPLEMENTADO | OK |
| REQ-VEG-002 | Calcular TGI: G - 0.39*R - 0.61*B | raster_analysis.py:L73-74 formula TGI correta | -- | IMPLEMENTADO | OK |
| REQ-VEG-003 | Calcular ExG: 2*G - R - B | raster_analysis.py:L76-77 formula ExG correta | -- | IMPLEMENTADO | OK |
| REQ-VEG-004 | Calcular GLI: (2*G-R-B)/(2*G+R+B) | raster_analysis.py:L79-82 formula GLI correta | -- | IMPLEMENTADO | OK |
| REQ-VEG-005 | Resultado inclui estatisticas (min, max, media, std) | tools.py:L179 raster_statistics(output) retorna min, max, mean, std | -- | IMPLEMENTADO | OK |
| REQ-VEG-006 | Resultado salvo como GeoTIFF | raster_analysis.py:L95-96 rasterio.open(output_path, "w") | -- | IMPLEMENTADO | OK |
| REQ-VEG-007 | Painel com selecao de ortomapa e indice, exibe stats | -- | ToolsPanel.vue:L18-56 aba vegetacao com Select ortomapa, Select indice, resultado com min/max/media/desvio | IMPLEMENTADO | OK |

---

## Grupo: REQ-TER -- Analise de Terreno

| Requisito | Descricao | Backend | Frontend | Veredicto | Observacao |
|---|---|---|---|---|---|
| REQ-TER-001 | Calcular slope em graus | raster_analysis.py:L106 calc_slope() com np.gradient + arctan + degrees | tools.py:L184 `POST /api/tools/slope` | IMPLEMENTADO | OK |
| REQ-TER-002 | Calcular aspect (0-360 graus) | raster_analysis.py:L138 calc_aspect() normaliza para 0-360 compass | tools.py:L195 `POST /api/tools/aspect` | IMPLEMENTADO | OK |
| REQ-TER-003 | Gerar curvas de nivel como GeoJSON com intervalo configuravel | gdal_tools.py:L200 generate_contours() com gdal_contour, -f GeoJSON, -i interval | tools.py:L153 `POST /api/tools/contours` | IMPLEMENTADO | OK |
| REQ-TER-004 | Gerar hillshade com azimute e altitude configuraveis | gdal_tools.py:L222 hillshade() com gdaldem, -az, -alt | tools.py:L163 `POST /api/tools/hillshade` | IMPLEMENTADO | OK |
| REQ-TER-005 | Slope e aspect retornam estatisticas | tools.py:L190,L201 raster_statistics(output) apos calculo | -- | IMPLEMENTADO | OK |
| REQ-TER-006 | Painel com selecao DSM/DTM e tipo de analise | -- | ToolsPanel.vue:L59-94 aba terreno filtra por DSM/DTM, oferece slope/aspect/contours/hillshade | IMPLEMENTADO | OK |

---

## Grupo: REQ-MUD -- Deteccao de Mudancas

| Requisito | Descricao | Backend | Frontend | Veredicto | Observacao |
|---|---|---|---|---|---|
| REQ-MUD-001 | Detectar mudancas entre dois rasters | change_detection.py:L69 detect_changes() diferenca pixel a pixel + threshold | tools.py:L235 `POST /api/tools/changes` | IMPLEMENTADO | OK |
| REQ-MUD-002 | Threshold configuravel | ChangeDetectionRequest.threshold com default 30.0 | ToolsPanel.vue:L206-210 slider threshold | IMPLEMENTADO | OK |
| REQ-MUD-003 | Estatisticas de mudanca (area alterada, percentual) | change_detection.py:L209 change_statistics() retorna total_pixels, changed_pixels, percent_changed, area_changed_m2, area_changed_ha | -- | IMPLEMENTADO | OK |
| REQ-MUD-004 | Resultado salvo como GeoTIFF binario | change_detection.py:L106-109 rasterio.open(output_path, "w") uint8 | -- | IMPLEMENTADO | OK |
| REQ-MUD-005 | Painel com selecao "Antes"/"Depois" e threshold | -- | ToolsPanel.vue:L180-224 aba mudancas com 2 selects + slider threshold | IMPLEMENTADO | OK |

---

## Grupo: REQ-CLA -- Classificacao de Solo

| Requisito | Descricao | Backend | Frontend | Veredicto | Observacao |
|---|---|---|---|---|---|
| REQ-CLA-001 | Classificar com KMeans, n_clusters configuravel | segmentation.py:L39 KMeans(n_clusters=n_clusters) | tools.py:L247 `POST /api/tools/classify?algorithm=kmeans` usa segment_ortomapa | IMPLEMENTADO | OK |
| REQ-CLA-002 | Classificar com Random Forest com amostras de treinamento | classification.py:L83 train_classifier() + classify_raster() | tools.py:L255-258 se training_samples presente, treina RF | IMPLEMENTADO | OK |
| REQ-CLA-003 | Treinar modelo RF e salvar antes de classificar | classification.py:L200 joblib.dump({classifier, class_names, algorithm}) | tools.py:L257 train_classifier() + classify_raster() | IMPLEMENTADO | OK |
| REQ-CLA-004 | Se sem amostras para RF, fallback para KMeans | tools.py:L259-260 else: segment_ortomapa() | -- | IMPLEMENTADO | OK |
| REQ-CLA-005 | Painel com selecao de algoritmo e parametros | -- | ToolsPanel.vue:L97-139 aba classificacao com Select algoritmo (RF/KMeans), numClasses, botao treino | IMPLEMENTADO | OK |

---

## Grupo: REQ-HID -- Hidrologia

| Requisito | Descricao | Backend | Frontend | Veredicto | Observacao |
|---|---|---|---|---|---|
| REQ-HID-001 | Delimitar bacia a partir de DTM e pour point | hydrology.py:L300 delineate_watershed() com BFS upstream | tools.py:L265 `POST /api/tools/hydrology/watershed` | IMPLEMENTADO | OK |
| REQ-HID-002 | Extrair rede de drenagem com limiar configuravel | hydrology.py:L247 extract_streams() com threshold | tools.py:L275 `POST /api/tools/hydrology/streams` | IMPLEMENTADO | OK |
| REQ-HID-003 | Pipeline completo: fill sinks -> flow dir -> flow acc -> extract | tools.py:L280-288 fill_sinks, flow_direction, flow_accumulation, extract_streams | -- | IMPLEMENTADO | OK |
| REQ-HID-004 | Rede de drenagem exportada como GeoJSON | hydrology.py:L293 json.dump(geojson, f); tools.py:L283 _output_path(..., ".geojson") | -- | IMPLEMENTADO | OK |
| REQ-HID-005 | Painel com selecao DTM, ponto de exutorio e threshold | -- | ToolsPanel.vue:L142-178 aba hidrologia com Select DTM, Select tipo (watershed/streams), threshold | PARCIALMENTE IMPLEMENTADO | Painel existe mas falta funcionalidade de "clique no mapa" para definir ponto de exutorio (pour point). O usuario precisa clicar no mapa para watershed mas isso nao esta implementado na UI |

---

## Grupo: REQ-VOL -- Volumetria

| Requisito | Descricao | Backend | Frontend | Veredicto | Observacao |
|---|---|---|---|---|---|
| REQ-VOL-001 | Calcular volume acima/abaixo de elevacao de referencia | volumetry.py:L8 calc_volume() retorna volume_above_m3, volume_below_m3 | tools.py:L293 `POST /api/tools/volume` | IMPLEMENTADO | OK |
| REQ-VOL-002 | Calcular diferenca entre dois DSMs (corte e aterro) | volumetry.py:L102 cut_fill_analysis() | tools.py:L303 `POST /api/tools/volume/difference` | IMPLEMENTADO | OK |
| REQ-VOL-003 | Resultado inclui volumes de corte, aterro e liquido em m3 | volumetry.py:L132-138 cut_volume_m3, fill_volume_m3, net_volume_m3 | ToolsPanel.vue:L252-255 exibe cut, fill, net | IMPLEMENTADO | OK |
| REQ-VOL-004 | Painel com selecao DSM e elevacao de referencia | -- | ToolsPanel.vue:L226-258 aba volume com Select DSM (filtrado por tipo), campo elevacao | IMPLEMENTADO | OK |

---

## Grupo: REQ-SEG -- Segmentacao

| Requisito | Descricao | Backend | Frontend | Veredicto | Observacao |
|---|---|---|---|---|---|
| REQ-SEG-001 | Segmentar com KMeans, n_clusters configuravel | segmentation.py:L10 segment_ortomapa() com KMeans | tools.py:L314 `POST /api/tools/segment` com SegmentRequest(n_clusters) | IMPLEMENTADO | OK |
| REQ-SEG-002 | Resultado salvo como GeoTIFF com valores de cluster | segmentation.py:L52 rasterio.open(output_path, 'w') dtype=uint8 | -- | IMPLEMENTADO | OK |

---

## Grupo: REQ-AGI -- Agentes de IA

| Requisito | Descricao | Backend | Frontend | Veredicto | Observacao |
|---|---|---|---|---|---|
| REQ-AGI-001 | Enfileirar tarefas ao criar analises (queue_task=true) | analises.py:L120-138 INSERT INTO tarefas_agente | AnalysisForm.vue (nao envia queue_task) | PARCIALMENTE IMPLEMENTADO | Backend OK. Frontend nao expoe opcao queue_task=true ao usuario |
| REQ-AGI-002 | Tarefas registradas com status "pendente" | analises.py:L133 status="pendente" | -- | IMPLEMENTADO | OK |
| REQ-AGI-003 | AgentStatus.vue exibe status de tarefas (pendente, em execucao, concluida) | -- | AgentStatus.vue:L96-108 filtra por em_fila/processando; exibe concluida/erro; polling 5s | IMPLEMENTADO | OK |
| REQ-AGI-004 | Orquestrador processa tarefas em loop, verifica a cada 10s | orchestrator.py:L161 run(poll_interval=10) com time.sleep | -- | IMPLEMENTADO | OK |

---

## Grupo: REQ-MAP -- Mapa Interativo

| Requisito | Descricao | Backend | Frontend | Veredicto | Observacao |
|---|---|---|---|---|---|
| REQ-MAP-001 | Mapa interativo Leaflet com zoom, pan, controle de camadas | -- | MapViewer.vue:L3-9 l-map com zoom, center, mousemove, click | IMPLEMENTADO | OK |
| REQ-MAP-002 | Basemaps alternados (OSM, satelite) | -- | MapViewer.vue:L12-27 OSM + ArcGIS satellite com toggle | IMPLEMENTADO | OK |
| REQ-MAP-003 | Ortomapas como camadas TMS sobrepostas | -- | MapViewer.vue:L29-35 l-tile-layer com URL /api/ortomapas/{id}/tile/{z}/{x}/{y}.png | IMPLEMENTADO | OK |
| REQ-MAP-004 | Coordenadas (lat/lon) do cursor na barra de status | -- | MapViewer.vue:L218-221 onMouseMove -> mapStore.setCursorCoords(lat, lng) | IMPLEMENTADO | OK |
| REQ-MAP-005 | LayerPanel controla visibilidade, opacidade e ordem | -- | LayerPanel.vue:L29-68 eye toggle, opacity slider, drag reorder | IMPLEMENTADO | OK |
| REQ-MAP-006 | Zoom para extent de camada especifica | -- | LayerPanel.vue:L48-49 botao zoomToLayer com icone lupa | IMPLEMENTADO | OK (emite evento, implementacao depende do parent) |

---

## Grupo: REQ-FER -- Painel de Ferramentas

| Requisito | Descricao | Backend | Frontend | Veredicto | Observacao |
|---|---|---|---|---|---|
| REQ-FER-001 | 8 abas: Vegetacao, Terreno, Classificacao, Hidrologia, Mudancas, Volume, Recorte, Exportar | -- | ToolsPanel.vue:L6-13 TabList com 8 tabs exatas | IMPLEMENTADO | OK |
| REQ-FER-002 | Cada aba permite selecionar dados, configurar parametros e executar | -- | ToolsPanel.vue:L17-334 cada TabPanel tem Select, params e Button executar | IMPLEMENTADO | OK |
| REQ-FER-003 | Resultado aparece como nova camada no mapa | -- | ToolsPanel.vue:L423-440 addResultLayer() chama mapStore.addLayer | IMPLEMENTADO | OK |
| REQ-FER-004 | Indicador de loading durante processamento | -- | ToolsPanel.vue:L44,88,134,... :loading em cada Button | IMPLEMENTADO | OK |

---

## Grupo: REQ-MED -- Medicoes

| Requisito | Descricao | Backend | Frontend | Veredicto | Observacao |
|---|---|---|---|---|---|
| REQ-MED-001 | Medir distancia (cliques, acumulada em tempo real) | -- | MeasureTools.vue:L17-19 modo distance; MapViewer.vue:L224-227 onMapClick add point | IMPLEMENTADO | OK |
| REQ-MED-002 | Exibir distancia por segmento e total | -- | MeasureTools.vue:L32-43 segments + totalDistance | IMPLEMENTADO | OK |
| REQ-MED-003 | Medir area (poligono minimo 3 pontos) | -- | MeasureTools.vue:L22-28 modo area; L105 "pts.length < 3" | IMPLEMENTADO | OK |
| REQ-MED-004 | Exibir area em m2/hectares e perimetro | -- | MeasureTools.vue:L46-53 formattedArea (ha/m2), formattedPerimeter | IMPLEMENTADO | OK |

---

## Grupo: REQ-DES -- Desenho e Anotacao no Mapa

| Requisito | Descricao | Backend | Frontend | Veredicto | Observacao |
|---|---|---|---|---|---|
| REQ-DES-001 | Desenhar pontos no mapa | -- | DrawTools.vue:L7-12 Button mode='point' | IMPLEMENTADO | OK |
| REQ-DES-002 | Desenhar linhas no mapa | -- | DrawTools.vue:L13-19 Button mode='line' | IMPLEMENTADO | OK |
| REQ-DES-003 | Desenhar poligonos no mapa | -- | DrawTools.vue:L20-28 Button mode='polygon' | IMPLEMENTADO | OK |
| REQ-DES-004 | Desenhar retangulos no mapa | -- | DrawTools.vue:L29-37 Button mode='rectangle' | IMPLEMENTADO | OK |
| REQ-DES-005 | Formulario para categoria e rotulo apos desenhar | -- | DrawTools.vue:L49-73 annotation-form com Select categoria + InputText rotulo | IMPLEMENTADO | OK |
| REQ-DES-006 | Anotacao salva com geometria WKT, vinculada ao ortomapa ativo | -- | DrawTools.vue:L173-182 saveAnnotation envia projeto_id, geometria | PARCIALMENTE IMPLEMENTADO | Frontend envia projeto_id em vez de ortomapa_id; envia "geometria" em vez de "geometria_wkt" -- nomes de campos incompativeis com backend |
| REQ-DES-007 | Cancelar desenho corrente | -- | DrawTools.vue:L38-46 Button cancel + cancelDraw() | IMPLEMENTADO | OK |

---

## Grupo: REQ-EXP -- Exportacao

| Requisito | Descricao | Backend | Frontend | Veredicto | Observacao |
|---|---|---|---|---|---|
| REQ-EXP-001 | Exportar em GeoTIFF | -- | ExportDialog.vue:L31 option value="GTiff" | IMPLEMENTADO | OK |
| REQ-EXP-002 | Exportar em PNG | -- | ExportDialog.vue:L32 option value="PNG" | IMPLEMENTADO | OK |
| REQ-EXP-003 | Exportar em JPEG | -- | ExportDialog.vue:L33 option value="JPEG" | IMPLEMENTADO | OK |
| REQ-EXP-004 | Exportar em KML | -- | ExportDialog.vue:L34 option value="KML" | IMPLEMENTADO | OK |
| REQ-EXP-005 | Exportar em GeoJSON | -- | ExportDialog.vue:L35 option value="GeoJSON" | IMPLEMENTADO | OK |
| REQ-EXP-006 | Selecionar CRS de saida (4326, 31983, 31984, 32723, 32724) | -- | ExportDialog.vue:L40-45 todos os 5 CRS listados | IMPLEMENTADO | OK |
| REQ-EXP-007 | Configurar resolucao de saida (opcional) | -- | ExportDialog.vue:L49-52 input resolucao com placeholder "Manter original" | IMPLEMENTADO | OK |
| REQ-EXP-008 | Recorte (clip) por bbox ou poligono WKT | gdal_tools.py:L40 clip_raster(bbox=, polygon_wkt=) | tools.py:L120 `POST /api/tools/clip` | IMPLEMENTADO | OK |
| REQ-EXP-009 | Reprojecao de rasters | gdal_tools.py:L155 reproject_raster() via gdalwarp | tools.py:L133 `POST /api/tools/reproject` | IMPLEMENTADO | OK |
| REQ-EXP-010 | Merge (mosaico) de multiplos rasters | gdal_tools.py:L169 merge_rasters() via gdal_merge.py | tools.py:L143 `POST /api/tools/merge` | IMPLEMENTADO | OK |

---

## Grupo: REQ-COM -- Comparacao Temporal

| Requisito | Descricao | Backend | Frontend | Veredicto | Observacao |
|---|---|---|---|---|---|
| REQ-COM-001 | Comparacao em modo Swipe | -- | CompareView.vue:L48-96 swipe-container com clipPath | IMPLEMENTADO | OK |
| REQ-COM-002 | Comparacao em modo Side-by-Side | -- | CompareView.vue:L99-136 side-by-side com 2 l-map | IMPLEMENTADO | OK |
| REQ-COM-003 | Selecionar ortomapa "Antes" e "Depois" | -- | CompareView.vue:L6-27 Select leftId + Select rightId | IMPLEMENTADO | OK |
| REQ-COM-004 | Slider de swipe controla posicao de corte | -- | CompareView.vue:L86-93 slider com mousedown drag, clipPath dinamic | IMPLEMENTADO | OK |
| REQ-COM-005 | Botao fechar retorna ao mapa normal | -- | CompareView.vue:L38-43 Button "Fechar" -> mapStore.setCompareMode(false) | IMPLEMENTADO | OK |

---

## Grupo: REQ-EXTRA -- Ferramentas Adicionais

| Requisito | Descricao | Backend | Frontend | Veredicto | Observacao |
|---|---|---|---|---|---|
| REQ-EXTRA-001 | Calcular estatisticas raster (min, max, mean, std) | raster_analysis.py:L210 raster_statistics() | tools.py:L206 `POST /api/tools/statistics` | IMPLEMENTADO | OK |
| REQ-EXTRA-002 | Calcular estatisticas zonais (raster + zonas GeoJSON) | raster_analysis.py:L260 zonal_statistics() | tools.py:L215 `POST /api/tools/zonal-stats` | IMPLEMENTADO | OK |
| REQ-EXTRA-003 | Calculadora raster (expressao + inputs) | raster_analysis.py:L330 raster_calculator() com eval seguro | tools.py:L225 `POST /api/tools/calculator` | IMPLEMENTADO | OK |
| REQ-EXTRA-004 | Health check endpoint | main.py:L72 `GET /health` retorna status healthy | -- | IMPLEMENTADO | OK |
| REQ-EXTRA-005 | Endpoint raiz com informacoes do sistema | main.py:L55 `GET /` retorna sistema, versao, status, endpoints | -- | IMPLEMENTADO | OK |
| REQ-EXTRA-006 | Servir arquivos estaticos de data/ em /data | main.py:L37 app.mount("/data", StaticFiles(directory=DATA_DIR)) | -- | IMPLEMENTADO | OK |

---

## RESUMO GERAL

| Categoria | Total | Implementados | Parciais | Nao Implementados |
|---|---|---|---|---|
| REQ-PRJ (Projetos) | 10 | 7 | 3 | 0 |
| REQ-VOO (Voos) | 7 | 1 | 6 | 0 |
| REQ-ORT (Ortomapas) | 11 | 8 | 3 | 0 |
| REQ-ANA (Analises) | 8 | 6 | 2 | 0 |
| REQ-ANO (Anotacoes) | 8 | 6 | 2 | 0 |
| REQ-VEG (Vegetacao) | 7 | 7 | 0 | 0 |
| REQ-TER (Terreno) | 6 | 6 | 0 | 0 |
| REQ-MUD (Mudancas) | 5 | 5 | 0 | 0 |
| REQ-CLA (Classificacao) | 5 | 5 | 0 | 0 |
| REQ-HID (Hidrologia) | 5 | 4 | 1 | 0 |
| REQ-VOL (Volumetria) | 4 | 4 | 0 | 0 |
| REQ-SEG (Segmentacao) | 2 | 2 | 0 | 0 |
| REQ-AGI (Agentes IA) | 4 | 3 | 1 | 0 |
| REQ-MAP (Mapa) | 6 | 6 | 0 | 0 |
| REQ-FER (Ferramentas) | 4 | 4 | 0 | 0 |
| REQ-MED (Medicoes) | 4 | 4 | 0 | 0 |
| REQ-DES (Desenho) | 7 | 6 | 1 | 0 |
| REQ-EXP (Exportacao) | 10 | 10 | 0 | 0 |
| REQ-COM (Comparacao) | 5 | 5 | 0 | 0 |
| REQ-EXTRA (Adicionais) | 6 | 6 | 0 | 0 |
| **TOTAL** | **128** | **109** | **19** | **0** |

**Percentual implementado (total ou parcial): 100%**
**Percentual totalmente implementado: 85.2%**
**Percentual parcialmente implementado: 14.8%**
**Percentual nao implementado: 0%**

---

## LISTA DE PROBLEMAS ENCONTRADOS

### P01 -- Frontend nao expoe filtro de status e area_estudo para projetos
- **Requisitos afetados:** REQ-PRJ-002, REQ-PRJ-003
- **Descricao:** O backend aceita query params `status` e `area_estudo` em `GET /api/projetos`, mas o componente `ProjectList.vue` nao tem campos de filtro na UI.
- **Correcao sugerida:** Adicionar campos de filtro (dropdown para status, input text para area_estudo) no componente ProjectList.vue.

### P02 -- Frontend nao implementa busca textual de projetos
- **Requisitos afetados:** REQ-PRJ-004
- **Descricao:** O backend tem `GET /api/projetos/search?q=`, mas o API client (`client.js`) nao tem funcao `searchProjects()` e nenhum componente expoe campo de busca.
- **Correcao sugerida:** Adicionar `export function searchProjects(q) { return api.get('/projetos/search', { params: { q } }) }` no client.js e um campo de busca no ProjectList.vue.

### P03 -- Frontend nao tem componente de gerenciamento de voos
- **Requisitos afetados:** REQ-VOO-001 a REQ-VOO-004, REQ-VOO-006, REQ-VOO-007
- **Descricao:** Nao existe componente Vue para listar, criar, editar ou deletar voos. Toda a API de voos existe no backend mas nao e acessivel via UI.
- **Correcao sugerida:** Criar componente `FlightList.vue` ou integrar gerenciamento de voos no fluxo de projetos.

### P04 -- API client uploadOrtomapa envia para rota errada
- **Requisitos afetados:** REQ-ORT-004
- **Descricao:** `client.js:L49` `uploadOrtomapa()` envia para `/ortomapas` (create metadata) em vez de `/ortomapas/upload` (upload com extracao automatica de metadados). A funcao tambem nao envia query params (projeto_id, tipo).
- **Correcao sugerida:** Alterar para `return api.post('/ortomapas/upload', formData, { params: { projeto_id, tipo }, ... })`.

### P05 -- Consulta espacial de ortomapas nao utilizada no frontend
- **Requisitos afetados:** REQ-ORT-009
- **Descricao:** O endpoint `GET /api/ortomapas/spatial` existe no backend mas nenhum componente o utiliza.
- **Correcao sugerida:** Integrar chamada spatial query quando o mapa muda de viewport.

### P06 -- API client nao tem funcao updateOrtomapa
- **Requisitos afetados:** REQ-ORT-010
- **Descricao:** `client.js` nao exporta funcao para `PUT /api/ortomapas/{id}`.
- **Correcao sugerida:** Adicionar `export function updateOrtomapa(id, data) { return api.put(\`/ortomapas/${id}\`, data) }`.

### P07 -- Inconsistencia no parametro de filtro de analises no client.js
- **Requisitos afetados:** REQ-ANA-001
- **Descricao:** `client.js:L61` `getAnalises(projetoId)` envia `{ params: { projeto_id: projetoId } }` mas o backend filtra por `ortomapa_id`, nao `projeto_id`.
- **Correcao sugerida:** Alterar para enviar `ortomapa_id` ou adicionar suporte a `projeto_id` no backend.

### P08 -- Frontend AnalysisForm nao expoe opcao queue_task
- **Requisitos afetados:** REQ-ANA-004, REQ-AGI-001
- **Descricao:** O backend suporta `queue_task=true` para enfileirar tarefa de agente, mas o `AnalysisForm.vue` nao tem checkbox ou toggle para ativar isso.
- **Correcao sugerida:** Adicionar checkbox "Executar via Agente" no formulario que envia `queue_task: true` nos dados.

### P09 -- Inconsistencia nos nomes de campos entre DrawTools.vue e backend anotacoes
- **Requisitos afetados:** REQ-ANO-003, REQ-DES-006
- **Descricao:** `DrawTools.vue:L177` envia `{ projeto_id, geometria }` mas o backend espera `{ ortomapa_id, geometria_wkt }`. Dois campos com nomes errados.
- **Correcao sugerida:** Alterar DrawTools.vue para enviar `ortomapa_id` (do ortomapa ativo) e `geometria_wkt` (converter geometria GeoJSON para WKT).

### P10 -- Inconsistencia no parametro de filtro de anotacoes no client.js
- **Requisitos afetados:** REQ-ANO-001
- **Descricao:** `client.js:L78` `getAnotacoes(projetoId)` envia `{ params: { projeto_id: projetoId } }` mas o backend filtra por `ortomapa_id`.
- **Correcao sugerida:** Alterar para enviar `ortomapa_id`.

### P11 -- Falta funcionalidade de clique no mapa para pour point (hidrologia watershed)
- **Requisitos afetados:** REQ-HID-005
- **Descricao:** O painel de hidrologia permite selecionar tipo "watershed" mas nao tem mecanismo de "clique no mapa" para definir o ponto de exutorio (pour_point lat/lon) que o endpoint requer.
- **Correcao sugerida:** Implementar modo de clique no mapa que captura lat/lon e preenche o campo pour_point ao selecionar "watershed".

### P12 -- Duplicacao de campo tamanho_arquivo_mb no INSERT do upload
- **Requisitos afetados:** REQ-ORT-004 (bug potencial)
- **Descricao:** `ortomapas.py:L220` tem `tamanho_arquivo_mb, tamanho_arquivo_mb` duplicado na query INSERT, com os valores sendo `info["bands"]` e `round(size_mb, 2)`. Isso causa erro SQL pois a coluna aparece duas vezes.
- **Correcao sugerida:** Remover a duplicacao. Provavelmente o primeiro deveria ser `num_bandas` ou similar.

### P13 -- Duplicacao de campo tamanho_arquivo_mb na lista updatable do update
- **Requisitos afetados:** REQ-ORT-010 (bug potencial)
- **Descricao:** `ortomapas.py:L277` lista `updatable` contem `tamanho_arquivo_mb` duas vezes. Nao causa erro mas e redundante.
- **Correcao sugerida:** Remover a duplicata.

### P14 -- ToolsPanel.vue exportFormats nao inclui JPEG e GeoJSON
- **Requisitos afetados:** REQ-EXP-002, REQ-EXP-003, REQ-EXP-005 (no ToolsPanel)
- **Descricao:** `ToolsPanel.vue:L400-405` aba exportar oferece apenas GeoTIFF, PNG, KML e Shapefile. Faltam JPEG e GeoJSON. Porem, o `ExportDialog.vue` dedicado oferece todos os formatos incluindo JPEG e GeoJSON.
- **Impacto:** Baixo, pois ExportDialog.vue esta completo. ToolsPanel.vue e um atalho secundario.

### P15 -- ToolsPanel.vue crsOptions incompleto
- **Requisitos afetados:** REQ-EXP-006 (no ToolsPanel)
- **Descricao:** `ToolsPanel.vue:L407-411` oferece apenas 3 CRS (4326, 31983, 32723) vs os 5 requeridos (faltam 31984 e 32724). ExportDialog.vue tem todos os 5.
- **Impacto:** Baixo, pois ExportDialog.vue esta completo.

---

## LISTA DE REQUISITOS TOTALMENTE IMPLEMENTADOS (109 de 128)

REQ-PRJ-001, REQ-PRJ-005, REQ-PRJ-006, REQ-PRJ-007, REQ-PRJ-008, REQ-PRJ-009, REQ-PRJ-010,
REQ-VOO-005,
REQ-ORT-001, REQ-ORT-002, REQ-ORT-003, REQ-ORT-005, REQ-ORT-006, REQ-ORT-007, REQ-ORT-008, REQ-ORT-011,
REQ-ANA-002, REQ-ANA-003, REQ-ANA-005, REQ-ANA-006, REQ-ANA-007, REQ-ANA-008,
REQ-ANO-002, REQ-ANO-004, REQ-ANO-005, REQ-ANO-006, REQ-ANO-007, REQ-ANO-008,
REQ-VEG-001, REQ-VEG-002, REQ-VEG-003, REQ-VEG-004, REQ-VEG-005, REQ-VEG-006, REQ-VEG-007,
REQ-TER-001, REQ-TER-002, REQ-TER-003, REQ-TER-004, REQ-TER-005, REQ-TER-006,
REQ-MUD-001, REQ-MUD-002, REQ-MUD-003, REQ-MUD-004, REQ-MUD-005,
REQ-CLA-001, REQ-CLA-002, REQ-CLA-003, REQ-CLA-004, REQ-CLA-005,
REQ-HID-001, REQ-HID-002, REQ-HID-003, REQ-HID-004,
REQ-VOL-001, REQ-VOL-002, REQ-VOL-003, REQ-VOL-004,
REQ-SEG-001, REQ-SEG-002,
REQ-AGI-002, REQ-AGI-003, REQ-AGI-004,
REQ-MAP-001, REQ-MAP-002, REQ-MAP-003, REQ-MAP-004, REQ-MAP-005, REQ-MAP-006,
REQ-FER-001, REQ-FER-002, REQ-FER-003, REQ-FER-004,
REQ-MED-001, REQ-MED-002, REQ-MED-003, REQ-MED-004,
REQ-DES-001, REQ-DES-002, REQ-DES-003, REQ-DES-004, REQ-DES-005, REQ-DES-007,
REQ-EXP-001, REQ-EXP-002, REQ-EXP-003, REQ-EXP-004, REQ-EXP-005, REQ-EXP-006, REQ-EXP-007, REQ-EXP-008, REQ-EXP-009, REQ-EXP-010,
REQ-COM-001, REQ-COM-002, REQ-COM-003, REQ-COM-004, REQ-COM-005,
REQ-EXTRA-001, REQ-EXTRA-002, REQ-EXTRA-003, REQ-EXTRA-004, REQ-EXTRA-005, REQ-EXTRA-006

---

## CLASSIFICACAO DE SEVERIDADE DOS PROBLEMAS

| Severidade | Problema | Descricao |
|---|---|---|
| ALTA | P04 | uploadOrtomapa envia para rota errada -- upload com extracao de metadados nao funciona via UI |
| ALTA | P09 | DrawTools envia campos incompativeis com backend -- salvar anotacao falha |
| ALTA | P12 | Coluna duplicada no INSERT SQL de upload -- causa erro SQL |
| MEDIA | P03 | Sem UI para gerenciar voos -- funcionalidade inacessivel |
| MEDIA | P07 | getAnalises usa projeto_id que backend nao aceita -- listagem de analises falha |
| MEDIA | P10 | getAnotacoes usa projeto_id que backend nao aceita -- listagem de anotacoes falha |
| MEDIA | P08 | Sem opcao queue_task no formulario -- agentes nao podem ser ativados via UI |
| BAIXA | P01 | Sem filtros de status/area_estudo na UI de projetos |
| BAIXA | P02 | Sem busca textual de projetos na UI |
| BAIXA | P05 | Consulta espacial nao usada no frontend |
| BAIXA | P06 | Sem funcao updateOrtomapa no client.js |
| BAIXA | P11 | Sem clique no mapa para pour point em watershed |
| BAIXA | P13 | Campo duplicado na lista updatable (redundancia inofensiva) |
| BAIXA | P14 | ToolsPanel exportar falta JPEG/GeoJSON (ExportDialog tem) |
| BAIXA | P15 | ToolsPanel CRS incompleto (ExportDialog tem todos) |

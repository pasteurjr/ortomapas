# Revisao de aderencia: requisitos, casos de uso e interface

**Data:** 15/09/2026  
**Fontes:** `docs/analise/casos_de_uso.md`, `docs/analise/especificacao_funcional.md`, `docs/analise/casos_de_uso.html`, componentes Vue e suite Playwright autenticada.

## Veredito executivo

A especificacao funcional descreve 20 casos de uso, mas nao existe um diagrama de casos de uso formal versionado (Mermaid, PlantUML ou Draw.io). O HTML e o MD sao uma especificacao textual detalhada, nao um diagrama.

O backend possui endpoints para quase todos os casos. A aderencia com a **interface navegavel** e menor: 15 UCs estao acessiveis por controles visiveis, 3 estao parciais e 2 possuem componente implementado sem acionador no fluxo principal. Portanto, a matriz anterior, que marcava todos os 20 como implementados, e otimista demais para testes de aceitacao visual.

## Matriz corrigida para testes

| UC | Requisito | Interface observada | API/backend | Classificacao para aceite |
|---|---|---|---|---|
| UC-001 | Criar projeto | Botao Novo + dialog + lista | POST/GET protegidos por JWT | **Aderente** |
| UC-002 | Buscar/filtrar projetos | Filtro local da sidebar funciona; busca global da toolbar nao esta ligada ao store | Busca REST existe | **Parcial** |
| UC-003 | Selecionar projeto/ortomapas | Seletor superior, lista e cards | Listagem e isolamento por usuario | **Aderente** |
| UC-004 | Upload GeoTIFF e visualizar | Nao ha controle de upload GeoTIFF; existe upload de fotos no fluxo de voo | `/api/ortomapas/upload` existe | **Parcial** |
| UC-005 | VARI | Aba Veg, selecao e botao Calcular | Tool real + GeoTIFF | **Aderente** |
| UC-006 | Slope | Aba Terreno | Tool real | **Aderente** |
| UC-007 | Curvas de nivel | Aba Terreno + intervalo | Tool real/GeoJSON | **Aderente** |
| UC-008 | Hillshade | Aba Terreno | Tool real | **Aderente** |
| UC-009 | Mudancas | Aba Mudancas + dois seletores + limiar | Tool real | **Aderente** |
| UC-010 | KMeans/classificacao | Aba Classificacao + classes/algoritmo | Tool real | **Aderente** |
| UC-011 | Drenagem | Aba Hidrologia + limiar/ponto de exutorio | Tool real | **Aderente** |
| UC-012 | Volume | Aba Volume + cota | Tool real | **Aderente** |
| UC-013 | Anotacao poligono | DrawTools com modo poligono e formulario | POST/listagem | **Aderente** |
| UC-014 | Anotacao ponto | DrawTools com modo ponto e formulario | POST/listagem | **Aderente** |
| UC-015 | Medir distancia | `MeasureTools` existe, mas nenhum controle do fluxo principal chama `setMeasureMode('distance')` | Calculo local | **Parcial** |
| UC-016 | Medir area | `MeasureTools` existe, mas nenhum controle do fluxo principal chama `setMeasureMode('area')` | Calculo local | **Parcial** |
| UC-017 | Comparar por swipe | `CompareView` existe, mas nao ha botao navegavel que ative `setCompareMode(true)` | Tile endpoints existem | **Parcial** |
| UC-018 | Exportar | Aba Exp permite camada, formato e CRS | Export REST + download | **Aderente** |
| UC-019 | Registrar voo | Dialog Novo Voo, listagem, exclusao e upload de fotos ODM | CRUD de voos + ODM | **Aderente** |
| UC-020 | Agente IA | Copiloto visivel, memoria por projeto e ferramentas rapidas | LM Studio, tools e threads | **Aderente** |

**Resultado:** 15 aderentes, 5 parciais, 0 totalmente ausentes no nucleo. Os 5 parciais exigem teste especifico e, em parte, ajuste de UX.

## Evidencias de implementacao

### Fluxos aderentes

- `ProjectList.vue`: criacao, filtros locais e selecao.
- `ToolsPanel.vue`: vegetacao, terreno, classificacao, hidrologia, mudancas, volume, recorte e exportacao.
- `DrawTools.vue`: ponto, linha, poligono, retangulo e formulario de anotacao.
- `VoosList.vue`: novo voo, upload de fotos e configuracao da tarefa ODM.
- `OdmTasks.vue`: progresso, importar produtos, qualidade, relatorio, nuvem 3D e superficies.
- `CopilotChat.vue`: prompt, historico por projeto, ferramentas espaciais e camadas persistidas.

### Divergencias que devem virar casos de teste

#### D-01 - Busca global sem efeito visual

`App.vue` mantem `searchQuery` no campo “Buscar...”, mas nao o transmite ao `ProjectList` nem executa `GET /api/projetos/search`. O filtro que funciona e o campo “Filtrar por area...” dentro da sidebar.

**Teste:** digitar um termo exclusivo na barra superior e confirmar se a lista muda. Resultado esperado atual: **falha conhecida**; requisito precisa ser implementado ou removido da especificacao.

#### D-02 - Upload GeoTIFF sem controle de interface

O endpoint `POST /api/ortomapas/upload` existe e extrai metadados, thumbnail e bbox. A interface oferece upload de fotos para ODM em `VoosList.vue`, mas nao oferece seletor de arquivo GeoTIFF ligado ao endpoint de upload de ortomapa.

**Teste:** tentar realizar UC-004 apenas pela interface. Resultado esperado atual: **nao executavel sem Swagger/API**.

#### D-03 - Medicao sem entrada no fluxo principal

`MeasureTools.vue` calcula distancia e area e `MapViewer.vue` desenha os pontos, mas a busca no frontend mostra apenas as chamadas internas do proprio componente. Nao existe botao visivel em `App.vue`, `ToolsPanel.vue` ou `DrawTools.vue` que ative o modo.

**Teste:** localizar um comando “Medir” na tela inicial. Resultado esperado atual: **componente nao alcancavel**.

#### D-04 - Comparacao swipe sem acionador

`CompareView.vue` implementa seletores Antes/Depois e slider, mas `setCompareMode(true)` nao e chamado por nenhum componente navegavel. O botao “Fechar” apenas desativa um modo que nao pode ser iniciado pela UI.

**Teste:** iniciar comparacao pela tela principal. Resultado esperado atual: **modo nao alcancavel**.

#### D-05 - Documento chamado “diagrama” inexistente

Nao foi localizado arquivo de diagrama. Para testes rastreaveis, criar um diagrama formal com atores Usuario, Administrador, Copiloto IA, NodeODM e PostgreSQL/PostGIS, relacionando os 20 UCs e marcando `include`/`extend`.

## Plano de testes de aceitacao

1. Executar os 15 UCs aderentes com Playwright autenticado, validando tela, requisicao, resposta e persistencia.
2. Criar testes negativos para D-01 a D-04, registrando-os como divergencias e nao como “aprovados”.
3. Decidir o requisito de upload: GeoTIFF avulso, fotos de voo ODM ou ambos.
4. Adicionar acionadores visiveis para medir distancia, medir area e iniciar comparacao.
5. Criar o diagrama formal e atualizar a especificacao com a mesma matriz de navegabilidade.
6. Reexecutar a suite; somente depois promover os 5 parciais para aderentes.

## Conclusao

A base implementada e consistente e os 17 testes autenticados existentes comprovam os endpoints e varios fluxos. Entretanto, “endpoint implementado” nao equivale a “caso de uso executavel pela interface”. A matriz acima e a referencia correta para construir os proximos casos de teste de validacao.

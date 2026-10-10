# Relatório visual executado — Guarajuba

Execução Playwright aprovada em `runtime/screenshots/demonstracao_video/20261010T023802Z`. As cenas abaixo são capturas do fluxo executado, não mockups desenhados. O projeto usa produtos sintéticos identificados como demonstração.

## 1. Acesso e projeto

### Login
[Abrir tela de login](../../runtime/screenshots/demonstracao_video/20261010T023802Z/01_login.png)

Preenchimento da conta de teste e entrada no sistema autenticado.

### Painel inicial
[Abrir painel do projeto](../../runtime/screenshots/demonstracao_video/20261010T023802Z/02_painel_inicial.png)

Projeto Guarajuba selecionado, mapa centralizado, barra lateral e painel de dados.

### Novo projeto
[Abrir formulário de novo projeto](../../runtime/screenshots/demonstracao_video/20261010T023802Z/03_novo_projeto.png)

Nome, descrição e área de estudo preenchidos antes do salvamento.

### Projeto criado
[Abrir projeto criado](../../runtime/screenshots/demonstracao_video/20261010T023802Z/04_projeto_criado.png)

Confirmação visual de que o projeto foi persistido e voltou para o cenário Guarajuba.

## 2. Dados, mapa e análises

### Vegetação
[Abrir ferramenta de vegetação](../../runtime/screenshots/demonstracao_video/20261010T023802Z/05_ferramenta_vegetacao.png)

Produto e índice selecionados para cálculo de vegetação.

### Resultado NDVI no mapa
[Abrir mapa NDVI](../../runtime/screenshots/demonstracao_video/20261010T023802Z/05a_mapa_ndvi.png)

Resultado selecionado com camada raster visível e painel de camadas ativo.

### Terreno
[Abrir ferramenta de terreno](../../runtime/screenshots/demonstracao_video/20261010T023802Z/06_ferramenta_terreno.png)

DSM/DTM e tipo de análise de relevo.

### Resultado DSM/terreno
[Abrir mapa de terreno](../../runtime/screenshots/demonstracao_video/20261010T023802Z/05b_mapa_dsm.png)

Camada de terreno selecionada sobre o mapa da área.

### Classificação
[Abrir classificação](../../runtime/screenshots/demonstracao_video/20261010T023802Z/07_ferramenta_classificacao.png)

Algoritmo e número de classes disponíveis.

### Hidrologia
[Abrir hidrologia](../../runtime/screenshots/demonstracao_video/20261010T023802Z/08_ferramenta_hidrologia.png)

DTM, tipo de análise, limiar e captura de ponto de exutório.

### Mudanças
[Abrir ferramenta de mudanças](../../runtime/screenshots/demonstracao_video/20261010T023802Z/09_ferramenta_mudancas.png)

Seleção de camadas antes/depois e limiar.

### Resultado de mudanças
[Abrir mapa de mudanças](../../runtime/screenshots/demonstracao_video/20261010T023802Z/05c_mapa_mudancas.png)

Camada comparativa selecionada no mapa.

### Volume
[Abrir ferramenta de volume](../../runtime/screenshots/demonstracao_video/20261010T023802Z/10_ferramenta_volume.png)

DSM e cota de referência para corte/aterro.

### Resultado de volume
[Abrir mapa de volume](../../runtime/screenshots/demonstracao_video/20261010T023802Z/05d_mapa_volume.png)

Resultado selecionado com a camada correspondente e estatísticas.

### Recorte
[Abrir ferramenta de recorte](../../runtime/screenshots/demonstracao_video/20261010T023802Z/11_ferramenta_recorte.png)

Entrada para desenhar a geometria e recortar o produto.

### Exportação
[Abrir tela de exportação](../../runtime/screenshots/demonstracao_video/20261010T023802Z/12_ferramenta_exportacao.png)

Camada, formato e CRS de saída.

### Geometria desenhada
[Abrir polígono desenhado](../../runtime/screenshots/demonstracao_video/20261010T023802Z/13_geometria_desenhada.png)

Área desenhada no mapa para medições e análises.

## 3. Copiloto

### Pergunta contextual
[Abrir Copiloto](../../runtime/screenshots/demonstracao_video/20261010T023802Z/14_copiloto.png)

Prompt enviado sobre a geometria desenhada. Conferir resposta, ferramentas usadas e camada resultante.

## 4. Missão para Litchi

### AOI, takeoff e waypoints
[Abrir missão com waypoints](../../runtime/screenshots/demonstracao_video/20261010T023802Z/15_missao_waypoints.png)

AOI `data/guarajuba_condominio_paraiso_aoi.geojson`, ponto de decolagem e quatro waypoints.

### Grid fotogramétrico
[Abrir grid](../../runtime/screenshots/demonstracao_video/20261010T023802Z/16_grid_fotogrametrico.png)

Linhas, espaçamento, distância e cobertura calculados.

### Validação
[Abrir validação da missão](../../runtime/screenshots/demonstracao_video/20261010T023802Z/17_validacao_missao.png)

Simulação, pausa e relatório de geometria, altitude, velocidade, sobreposição e autonomia.

### Exportação Litchi
[Abrir exportação Litchi](../../runtime/screenshots/demonstracao_video/20261010T023802Z/18_exportacao_litchi.png)

CSV compatível com Mission Hub, além de KML/GeoJSON.

## 5. ODM e visualização 3D

Estas telas foram capturadas em `runtime/screenshots/demonstracao_video/odm-20261009T214130Z`.

### Pipeline ODM
[Abrir estados ODM](../../runtime/screenshots/demonstracao_video/odm-20261009T214130Z/01_odm_pipeline.png)

Processamento concluído, processamento em andamento e erro recuperável.

### Nuvem de pontos 3D
[Abrir nuvem de pontos](../../runtime/screenshots/demonstracao_video/odm-20261009T214130Z/02_nuvem_pontos_3d.png)

Visualizador Three.js com pontos, elevação, controles de câmera, medição e exportação.

### DSM 3D
[Abrir DSM 3D](../../runtime/screenshots/demonstracao_video/odm-20261009T214130Z/03_dsm_3d.png)

Superfície renderizada, wireframe e enquadramento.

### Diferença DSM-DTM
[Abrir diferença DSM-DTM](../../runtime/screenshots/demonstracao_video/odm-20261009T214130Z/04_diferenca_dsm_dtm.png)

Canvas com escala divergente, mínimo, máximo e média.

### Qualidade ODM
[Abrir avaliação de qualidade](../../runtime/screenshots/demonstracao_video/odm-20261009T214130Z/05_qualidade_odm.png)

Score, nível e recomendação retornados pela API de qualidade.

## 6. Resultado e limites

O roteiro principal terminou com 22 cenas aprovadas. As capturas comprovam a navegação e a visualização das camadas seed. O seed não é um levantamento real: ortomosaico, DSM, DTM, NDVI, nuvem e estados ODM foram preparados para demonstração. Para certificar produção fotogramétrica, é necessário repetir o fluxo com fotos reais de drone e conferir os produtos gerados pelo NodeODM.


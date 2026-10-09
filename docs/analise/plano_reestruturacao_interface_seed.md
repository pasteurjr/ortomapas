# Plano de reestruturação da interface e seed de demonstração

Baseline congelado no commit `3e85770` em 09/10/2026. Este documento define a próxima implementação sem alterar o estado congelado.

## Problemas do baseline

- O mapa, o catálogo de projetos, camadas, voos, ODM e análises aparecem simultaneamente, sem hierarquia de produto.
- A barra lateral esquerda mistura dados, processamentos e resultados.
- A barra lateral direita mistura ferramentas, desenho e copiloto.
- Os visualizadores 3D existem no código, mas não têm uma entrada de navegação claramente visível.
- Não há estados guiados para “sem dados”, “processando”, “concluído”, “erro” e “resultado selecionado”.
- O usuário não consegue entender qual módulo está ativo nem qual ação é a próxima.

## Público principal

1. **Operador de campo**: prepara área, missão, parâmetros e exportação para o aplicativo de voo.
2. **Analista GIS**: carrega ortomapas, DSM/DTM, mede, compara, recorta e exporta.
3. **Gestor de processamento**: envia fotos ao ODM, acompanha fila, importa produtos e avalia qualidade.
4. **Cliente/revisor**: visualiza resultados 2D/3D, relatórios e análises sem editar dados.

## Navegação proposta

### Barra principal

| Módulo | Conteúdo | Ação primária |
|---|---|---|
| Visão geral | resumo do projeto, status dos dados e últimas tarefas | abrir projeto |
| Dados e mapa | ortomapas, camadas, importação, visibilidade e metadados | adicionar dado |
| Processamento ODM | voos, upload de fotos, fila, produtos e qualidade | iniciar processamento |
| Análises | vegetação, terreno, classificação, hidrologia, mudanças e volume | executar análise |
| Missões | AOI, exclusões, takeoff, waypoints, grid, validação e exportação | criar missão |
| Visualização 3D | nuvem de pontos, DSM, DTM, diferença e controles de câmera | abrir produto 3D |
| Copiloto | conversa, contexto do projeto, ferramentas executadas e resultados | perguntar |

### Layout de cada módulo

- **Centro**: mapa ou visualizador principal.
- **Painel esquerdo**: catálogo contextual do módulo ativo.
- **Painel direito**: propriedades e ações do item selecionado.
- **Barra inferior**: coordenadas, escala, CRS, tarefa ativa e mensagens.
- **Breadcrumb**: projeto > módulo > item, sempre visível.

O catálogo não deve listar todos os módulos ao mesmo tempo. A navegação principal escolhe um módulo, e os painéis mostram apenas os dados e ações daquele contexto.

## Estados obrigatórios por módulo

Cada estado abaixo será capturado no roteiro de vídeo:

- vazio, com chamada para ação;
- carregando;
- com dados;
- item selecionado;
- edição aberta;
- processamento em andamento;
- processamento concluído;
- resultado visualizado;
- erro recuperável;
- permissão insuficiente.

## Seed reproduzível de demonstração

O seed será executado por `scripts/seed_demo_guarajuba.py` e deverá ser idempotente por `slug`.

### Dados geográficos

- Projeto: `Guarajuba — Condomínio Paraíso`.
- AOI OSM aproximada, explicitamente marcada como não cadastral.
- Camadas vetoriais OSM: vias, edificações, áreas e pontos de referência.
- Takeoff próximo à portaria localizada no OSM.
- Exclusão sintética sobre uma área sensível para demonstrar bloqueio.

### Produtos raster sintéticos identificados

- `guarajuba_ortho_demo.tif`: ortomosaico RGB sintético com textura baseada no mapa OSM.
- `guarajuba_dsm_demo.tif`: superfície com elevação sintética, edificações e variação costeira.
- `guarajuba_dtm_demo.tif`: terreno interpolado sem edificações.
- `guarajuba_ndvi_demo.tif`: camada derivada sintética para demonstrar a tela de vegetação.

Todos os produtos terão metadados `origem=simulado`, `licenca=demonstracao` e uma tarja visual “DADO SINTÉTICO” para não confundir demonstração com levantamento real.

### Estado ODM simulado

- Voo com 24 fotos sintéticas e EXIF coerente.
- Processamento `concluido`, progresso 100%.
- Produtos associados: ortomosaico, DSM, DTM, nuvem de pontos e relatório de qualidade.
- Uma tarefa adicional `processando`, para demonstrar a fila.
- Uma tarefa adicional `erro`, com mensagem recuperável e botão de tentar novamente.

### Análises semânticas

- NDVI com estatísticas e legenda.
- Declividade com mínimo, máximo e média.
- Diferença DSM–DTM com escala divergente.
- Volume de corte/aterro em polígono.
- Resultado de classificação com classes e áreas.

## Roteiro de validação da nova interface

1. Login e seleção do projeto.
2. Visão geral com cartões de dados e tarefas.
3. Dados e mapa: ligar/desligar camadas, ajustar opacidade, zoom e metadados.
4. ODM: selecionar voo, acompanhar tarefa, importar produtos, avaliar qualidade.
5. Ortomapa: visualizar raster e abrir metadados.
6. DSM/DTM: abrir superfície 3D, wireframe, enquadrar e orbitar.
7. Nuvem de pontos: vistas superior/frontal/lateral, PNG e CSV.
8. Diferença: abrir comparação e ler legenda/estatísticas.
9. Análises: executar cada ferramenta com os rasters seed e mostrar resultado.
10. Desenho/medição: polígono, linha, área, perímetro e recorte.
11. Copiloto: pergunta contextual, ferramentas executadas e camada resultante.
12. Missão: AOI, exclusão, takeoff, grid, edição, simulação, validação e Litchi CSV.
13. Estados de erro e recuperação.
14. Encerramento com catálogo de produtos e exportações.

## Critérios de aceite

- Nenhum módulo deve depender de uma lista global não contextualizada.
- Toda função principal precisa ter uma entrada de menu visível.
- Toda saída precisa aparecer no visualizador ou no painel de resultados.
- O seed deve reconstruir o cenário em uma execução limpa.
- O vídeo deve mostrar resultados, não apenas abas selecionadas.
- Dados reais, OSM e dados sintéticos devem ser identificados separadamente.

## Execução desta etapa

- Seed executado no PostgreSQL/PostGIS existente: projeto `41`, voo `15`, 3 processamentos (concluído, processando e erro), 5 produtos e 4 análises concluídas.
- Arquivos gerados em `data/demo_guarajuba/` são GeoTIFF/LAZ sintéticos e estão marcados como demonstração; não são fotos de drone reais.
- Build do frontend validado com `npm run build`.
- Roteiro Playwright completo aprovado com 18 cenas em `runtime/screenshots/demonstracao_video/20261009T213859Z`.
- Validação dedicada dos viewers ODM aprovada com 5 cenas em `runtime/screenshots/demonstracao_video/odm-20261009T214130Z`: pipeline, nuvem 3D, DSM 3D, diferença DSM–DTM e avaliação de qualidade.
- O storyboard Markdown/PDF foi regenerado a partir da execução aprovada. As abas de análise foram capturadas com seus controles; a execução de análises raster e a visão geral dedicada continuam sendo o próximo lote, não são declaradas como concluídas aqui.

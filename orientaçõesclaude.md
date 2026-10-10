# Orientações para validação do Ortomapas

Este documento orienta uma nova sessão do Claude a executar e visualizar o sistema. A regra principal é **não considerar uma função validada apenas porque existe um botão**: abrir o módulo, carregar dados, executar a ação, verificar a resposta e capturar a tela com o mapa ou visualizador correspondente.

## 1. Ambiente

- Repositório: `/mnt/data1/progpython/ortomapas`
- Banco da aplicação: PostgreSQL/PostGIS existente, `127.0.0.1:5433`, banco `ortomapas`.
- API local: `http://127.0.0.1:5017` durante os testes.
- Frontend local: `http://127.0.0.1:5300`.
- WebODM: `http://127.0.0.1:8020`.
- NodeODM: `http://127.0.0.1:8021`.

Inicialização:

```bash
API_PORT=5017 python -m backend.main
cd frontend
VITE_BACKEND_URL=http://localhost:5017 npm run dev -- --host 0.0.0.0 --port 5300
```

Conta de teste já usada pelos testes E2E:

```text
E-mail: phase1-1791391595@example.test
Senha: fase1-senha-segura
```

## 2. Seed e arquivos de exemplo

Execute o seed idempotente antes da demonstração:

```bash
PYTHONPATH=. python scripts/seed_demo_guarajuba.py
```

O seed cria no PostgreSQL um projeto chamado **Guarajuba - Condomínio Paraíso (Demonstração)**, um voo, processamentos ODM e análises vinculadas.

Arquivos geográficos:

- `data/guarajuba_condominio_paraiso_aoi.geojson`: AOI aproximada do condomínio. É uma área de demonstração, não um limite cadastral.
- `data/guarajuba_osm.osm`: dados OSM baixados para referência cartográfica.
- `data/guarajuba_osm_referencia.geojson`: vias, edificações e elementos OSM convertidos para consulta.
- `data/demo_guarajuba/guarajuba_ortho_demo.tif`: ortomosaico RGB sintético.
- `data/demo_guarajuba/guarajuba_dsm_demo.tif`: modelo digital de superfície sintético.
- `data/demo_guarajuba/guarajuba_dtm_demo.tif`: modelo digital do terreno sintético.
- `data/demo_guarajuba/guarajuba_ndvi_demo.tif`: NDVI sintético.
- `data/demo_guarajuba/guarajuba_nuvem_demo.laz`: nuvem de pontos sintética.

Todos os quatro GeoTIFFs e o LAZ são dados **sintéticos para demonstração**, não fotos reais capturadas por drone. O seed grava essa informação em metadados e observações do banco.

Há também produtos ODM maiores em `data/odm_uploads/`. Não presumir que todo arquivo desse diretório está versionado ou pertence ao cenário Guarajuba; verificar o `log.json` e o relatório ODM antes de usá-los.

## 3. Navegação da interface

A navegação principal é a barra lateral esquerda:

1. **Dados e mapa**: projetos, camadas e ortomapas.
2. **Voos e ODM**: voos, upload de fotos, processamentos, produtos e qualidade.
3. **Análises**: ferramentas espaciais e resultados.
4. **Missões**: AOI, takeoff, waypoints, grid, validação e exportação.
5. **Copiloto**: conversa contextual e ferramentas executadas.

Use o botão de recolher a barra para validar o estado compacto (somente ícones). O mapa deve continuar visível e o módulo ativo deve ter tooltip.

Ao selecionar o projeto Guarajuba, o mapa deve centralizar na região do Condomínio Paraíso. O ortomosaico é adicionado automaticamente como camada inicial. O painel **Camadas** permite visibilidade, opacidade, zoom e remoção.

## 4. Funções implementadas e como visualizar

### Autenticação e projetos

- Login: preencher a conta acima e confirmar que o painel autenticado é exibido.
- Criar projeto: em Dados e mapa, clicar `Novo`, preencher nome, descrição e área de estudo e salvar.
- Selecionar projeto: clicar no projeto Guarajuba e verificar centralização do mapa, camadas e produtos.
- Lista de projetos: usar filtro por área/nome e status.

### Dados e mapa

- Ortomapa: em Camadas/Ortomapas, ativar o botão de visibilidade do ortomosaico. A captura deve mostrar o raster sobre o mapa OSM, não somente o cartão lateral.
- DSM, DTM e NDVI: ativar cada produto individualmente e capturar a legenda/camada visível.
- Camadas: alterar opacidade, ocultar, mostrar, remover e usar zoom para camada.
- Desenho: usar as ferramentas de ponto, linha, polígono e retângulo; guardar a geometria selecionada.
- Medição: desenhar linha/área e verificar distância, perímetro e área no painel de medidas.
- KML/GeoJSON: exportar uma geometria e reabrir o arquivo para conferir a geometria.

### Análises espaciais

No módulo **Análises**, selecionar o produto e executar o botão da ferramenta. A tela de validação deve conter o mapa e a camada gerada/associada, além das estatísticas.

- Vegetação/NDVI: usar `guarajuba_ortho_demo.tif` ou o NDVI seed; executar VARI, TGI, ExG ou GLI; mostrar estatísticas e camada no mapa.
- Terreno: usar DSM/DTM; executar declividade, aspecto, curvas de nível e hillshade; mostrar o raster/linhas no mapa.
- Classificação: executar K-Means ou Random Forest; mostrar classes coloridas e áreas no mapa.
- Hidrologia: usar DTM; executar bacias, drenagem ou TWI; para watershed, capturar o ponto de exutório no mapa antes de executar.
- Mudanças: selecionar duas camadas e mostrar a diferença no mapa com legenda divergente.
- Volume: selecionar DSM e cota de referência; mostrar corte, aterro e área/resultado da geometria.
- Recorte: desenhar o polígono, executar recorte e mostrar o resultado limitado à AOI.
- Exportação: exportar GeoTIFF, PNG, JPEG, KML ou GeoJSON e verificar o arquivo baixado.

Os resultados persistidos do seed aparecem em `AnalysisResults`. Ao clicar em um resultado, a aplicação deve adicionar sua camada de origem/resultado ao mapa e exibir o painel Camadas.

### Voos e ODM

- Novo voo: informar data, drone, altitude, número de fotos, área e GSD.
- Upload: selecionar fotos JPG/TIFF; abrir o diálogo de opções ODM.
- Parâmetros ODM: demonstrar ortofoto rápida, DSM, DTM, nuvem LAZ e opção de modelo 3D.
- Fila: mostrar os três estados seed: `concluido` 100%, `processando` 48% e `erro` 62%.
- Importar produtos: no processamento concluído, clicar `Importar produtos` e conferir produtos associados.
- Qualidade: clicar `Avaliar qualidade`; mostrar score, nível e recomendação.
- Relatório: baixar o relatório ODM quando houver produto de relatório.

### Visualização profissional

- Nuvem de pontos: clicar `Abrir 3D`; validar pontos renderizados, elevação, intensidade, tamanho, opacidade, coloração, grade, eixos, vistas superior/frontal/lateral, medição e exportação PNG/CSV.
- DSM/DTM: clicar `DSM 3D`; validar superfície colorida, wireframe, enquadramento e órbita.
- Diferença DSM-DTM: abrir `Diferença`; validar canvas, escala, mínimo, máximo e média.
- Ortomapa 2D: ativar a camada GeoTIFF e capturar o mapa com a área Guarajuba visível.

### Missões de captura

- Abrir `Planejar missão`.
- Importar `data/guarajuba_condominio_paraiso_aoi.geojson`.
- Marcar takeoff próximo a `-12.6504521, -38.0714399`.
- Adicionar waypoints dentro da AOI.
- Gerar grid fotogramétrico.
- Ajustar altitude, sobreposição frontal/lateral, velocidade, gimbal e intervalo de disparo.
- Simular rota, pausar e validar.
- Exportar CSV Litchi, KML e GeoJSON.
- Capturar a tela da rota, dos waypoints, do grid, da validação e da exportação.

### Copiloto

- Abrir o módulo Copiloto.
- Perguntar: `Calcule a área e o perímetro da geometria desenhada.`
- Perguntar: `Compare DSM e DTM deste projeto.`
- Perguntar: `Qual a declividade média da área selecionada?`
- Verificar resposta, ferramentas usadas, camada criada e persistência da conversa.
- A conversa deve ser testada por usuário/projeto; não usar somente screenshot do campo vazio.

## 5. Testes Playwright existentes

Roteiro principal:

```bash
E2E_EMAIL='phase1-1791391595@example.test' \
E2E_PASSWORD='fase1-senha-segura' \
E2E_PROJECT='Guarajuba - Condomínio Paraíso (Demonstração)' \
FRONTEND_URL=http://127.0.0.1:5300 \
python tests/e2e/playwright/test_roteiro_video_completo.py
```

Viewers ODM:

```bash
python tests/e2e/playwright/test_visualizadores_seed.py
```

O roteiro aprovado mais recente tem 22 cenas em:

`runtime/screenshots/demonstracao_video/20261010T023802Z/`

O PDF/MD do roteiro está em:

- `docs/analise/roteiro_video_demonstracao_ortomapas.pdf`
- `docs/analise/roteiro_video_demonstracao_ortomapas.md`

## 6. Limitações que devem ser reportadas

- Produtos Guarajuba são sintéticos; não apresentá-los como levantamento aéreo real.
- OSM é referência cartográfica e não substitui ortofoto cadastral.
- Uma aba de ferramenta não prova execução: sempre clicar, aguardar resposta, verificar camada/resultado e capturar o mapa.
- Se uma ferramenta retornar somente estatísticas, registrar como limitação e não declarar que gerou mapa.
- Não incluir `data/odm_uploads/` inteiro em commits; pode conter centenas de MB/GB.
- Não alterar credenciais de usuários existentes para facilitar testes.

## 7. Critério para encerrar a validação

Considerar uma função concluída somente quando houver, no mesmo registro de teste:

1. entrada usada;
2. tela antes da execução;
3. ação executada;
4. resposta HTTP ou mensagem de sucesso;
5. mapa/visualizador com resultado;
6. captura de tela identificada;
7. erro ou limitação explicitamente registrados.


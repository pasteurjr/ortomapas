# Plano de Sprint - Planejamento de Missoes de Captura

**Produto:** Ortomapas  
**Data:** 2026-10-07  
**Objetivo:** implementar o editor cartografico de missoes para DJI Mini 3 e preparar uma validacao visual repetivel, com screenshots e video futuro, usando o modelo de interacao do Litchi Hub.

## 1. Resultado esperado

Ao final do sprint, um usuario autenticado deve conseguir:

1. abrir um projeto e criar uma missao;
2. desenhar ou importar uma AOI no mapa;
3. inserir zonas de exclusao e o ponto de decolagem;
4. escolher drone/camera e informar GSD, sobreposicao, altitude e velocidade;
5. gerar uma grid de captura;
6. editar waypoints e parametros no mapa;
7. simular a rota e consultar fotos, tempo, distancia e baterias;
8. executar as validacoes de seguranca e fotogrametria;
9. exportar um pacote canonico e o adaptador homologado;
10. registrar a evidencia da revisao e deixar a execucao pronta para receber fotos e enviar ao ODM.

O primeiro alvo de exportacao e Litchi Hub/Litchi Pilot. Dronelink e Map Pilot Pro entram como adaptadores posteriores, depois de teste real com o Mini 3 e controle compativel.

## 2. Principios de implementacao

- O mapa e a area de trabalho principal; parametros ficam em painel lateral.
- A missao e persistida no PostgreSQL/PostGIS do Ortomapas.
- A geometria canonica nao depende de CSV, KML ou de um aplicativo externo.
- Toda operacao relevante gera versao, auditoria e evidencia.
- Erros bloqueantes aparecem no mapa e no painel; nao ficam escondidos em modal.
- A validacao deve funcionar com dados deterministas, sem depender de internet.
- O teste de navegador deve produzir evidencias que possam ser usadas diretamente em um roteiro de demonstracao.

## 3. Etapas do sprint

### Etapa 0 - Baseline e contrato tecnico

**Tarefas**

- confirmar branch, ambiente, backend, frontend e PostgreSQL/PostGIS;
- revisar rotas e componentes Leaflet existentes;
- criar o contrato JSON `ortomapas.capture-mission/1.0`;
- criar migration/modelos para missao, areas, blocos, waypoints, validacoes e exportacoes;
- definir seeds deterministas para teste.

**Saida:** migration aplicada, endpoint de health, seed reproduzivel e contrato versionado.  
**Validacao:** teste de API cria e recarrega uma missao sem perda de coordenadas.

### Etapa 1 - Editor cartografico

**Tarefas**

- toolbar com selecionar, poligono, linha, exclusao, takeoff, waypoint, desfazer, refazer e limpar;
- desenho e edicao de AOI no Leaflet;
- arraste, insercao e exclusao de vertices;
- importacao de GeoJSON e KML/KMZ;
- camadas de rota, exclusao, takeoff, waypoints e pontos de captura;
- painel de metadados, area, perimetro e coordenadas.

**Saida:** o usuario desenha uma AOI e a salva como versao de rascunho.  
**Validacao Playwright:** `01_projeto_missao.png` ate `05_aoi_salva.png`.

### Etapa 2 - Perfis e parametros de captura

**Tarefas**

- cadastro de drone e camera;
- preset DJI Mini 3;
- campos de sensor, resolucao, focal, GSD, overlap, altitude, velocidade e gimbal;
- referencia AGL/takeoff/AMSL;
- formulas e unidades visiveis;
- atualizacao imediata de footprint, espacamento e intervalo.

**Saida:** perfil selecionado e parametros calculados com origem e unidade.  
**Validacao:** fixture com valores conhecidos e tolerancia numerica definida.

### Etapa 3 - Motor de grid e blocos

**Tarefas**

- grid nadir com orientacao otimizada ou manual;
- double-grid opcional;
- corredor e linha manual;
- recorte na AOI e desvio de zonas de exclusao;
- alternancia de linhas e sentido;
- divisao por bateria;
- contagem de fotos, distancia, tempo e cobertura.

**Saida:** waypoints canonicos ordenados e blocos executaveis.  
**Validacao:** teste geometrico sem navegador e visualizacao da rota no mapa.

### Etapa 4 - Edicao no padrao Litchi Hub

**Tarefas**

- edicao individual e em lote;
- mover, girar, escalar, inverter e centralizar missao;
- numero e setas de sentido;
- selecao de waypoint e painel de propriedades;
- travar/destravar para revisao;
- simulacao com play, pause e waypoint inicial.

**Saida:** interacao equivalente ao modelo do Litchi Hub, sem copiar implementacao ou identidade visual.  
**Validacao Playwright:** roteiro completo com screenshots de cada ferramenta.

### Etapa 5 - Validador de seguranca e fotogrametria

**Tarefas**

- intersecao com exclusoes;
- AOI invalida ou sem cobertura;
- altitude e margem de obstaculos;
- autonomia e reserva de bateria;
- GSD, overlap, intervalo e capacidade da camera;
- conflito Curved Turns com acoes de waypoint;
- limites de distancia, waypoints e blocos;
- checklist operacional e assinatura do revisor.

**Saida:** status `passed`, `warning` ou `blocked`, com regra, geometria e valor observado.  
**Validacao:** fixtures com cenarios aprovado, aviso e bloqueio; cada um deve ter evidencia visual.

### Etapa 6 - Exportacao e adaptadores

**Tarefas**

- JSON canonico, manifesto e SHA-256;
- CSV Litchi e KML 3D;
- relatorio de validacao e checklist;
- endpoint generico `/export/{alvo}`;
- matriz de perdas por formato;
- fixture de round-trip para comparar waypoints exportados/importados;
- esqueleto de adaptadores Dronelink e Map Pilot Pro, sem declarar homologacao antes de voo real.

**Saida:** pacote baixavel e auditavel.  
**Validacao:** arquivos, checksum, CRS, contagem e comparacao de coordenadas.

### Etapa 7 - Execucao, fotos e ODM

**Tarefas**

- registrar execucao e operador;
- importar fotos e logs;
- validar EXIF, hash, horario e coordenada;
- mapa de cobertura real;
- enviar dataset valido ao NodeODM/WebODM;
- vincular ortomosaico, DSM, DTM, nuvem e relatorio ao projeto.

**Saida:** uma missao planejada percorre o ciclo ate os produtos ODM.  
**Validacao:** dados de teste reais do repositorio ou fixture de fotos com EXIF preservado.

### Etapa 8 - Empacotamento da demonstracao

**Tarefas**

- executar o roteiro Playwright completo;
- gerar screenshots em ordem numerada;
- gerar relatorio Markdown e PDF com cada passo, resultado esperado/obtido e alertas;
- gerar video Playwright com `record_video_dir`;
- revisar telas em desktop e tablet;
- corrigir falhas e executar novamente.

**Saida:** pacote de demonstracao pronto para apresentacao ao cliente.

## 4. Dados deterministas de validacao

O teste automatizado deve usar dados estaveis, para que screenshots e comparacoes sejam repetiveis:

| Dado | Valor de teste |
|---|---|
| Projeto | `Demo Planejamento Mini 3` |
| AOI | Poligono WGS84 de quatro vertices em uma area rural de teste |
| Zona de exclusao | Circulo dentro da AOI, para demonstrar desvio e bloqueio |
| Takeoff | Ponto no limite sul da AOI |
| Drone | DJI Mini 3 |
| Camera | Sensor 1/1.3, 8064 x 6048, focal real conforme perfil cadastrado |
| GSD | 1.5 cm/px |
| Overlap | 80% frontal e 70% lateral |
| Altitude | 50 m AGL, com fallback relativo ao takeoff |
| Velocidade | 4 m/s |
| Gimbal | -90 graus |
| Captura | JPEG, exposicao e foco fixos |
| Bateria | 25 minutos uteis, reserva de 25% |

O seed deve criar tres variacoes: `aprovada`, `com_aviso` e `bloqueada_por_exclusao`.

## 5. Roteiro Playwright de validacao

Arquivo planejado: `tests/e2e/playwright/test_planejamento_missoes.py`.

O script deve:

1. iniciar com usuario de teste e projeto seed;
2. abrir a pagina de planejamento;
3. capturar console, erros de pagina, requests falhas e tempos;
4. capturar screenshot apos cada transicao importante;
5. usar `page.screenshot(full_page=False)` para telas de apresentacao e uma captura full page para auditoria;
6. gravar video por teste com `record_video_dir`;
7. salvar um JSON de resultados com passo, seletor, status, timestamp e caminho da evidencia;
8. gerar um relatorio Markdown com imagens relativas;
9. falhar o teste se houver erro bloqueante, console error inesperado ou tela sem mapa;
10. repetir em viewport desktop 1440x900 e tablet 1024x1366.

### Evidencias obrigatorias

| Ordem | Arquivo | O que deve aparecer |
|---:|---|---|
| 01 | `01_projeto_missao.png` | Projeto, missao nova e status rascunho |
| 02 | `02_mapa_vazio.png` | Mapa, toolbar e painel lateral |
| 03 | `03_aoi_desenhada.png` | Poligono, vertices, area e perimetro |
| 04 | `04_exclusao_takeoff.png` | Zona de exclusao e takeoff |
| 05 | `05_parametros_camera.png` | Perfil Mini 3, GSD e camera |
| 06 | `06_grid_gerada.png` | Linhas, setas e pontos de captura |
| 07 | `07_edicao_waypoint.png` | Waypoint selecionado e painel de propriedades |
| 08 | `08_edicao_lote.png` | Alteracao em lote visivel |
| 09 | `09_simulacao_rota.png` | Animacao, distancia, tempo e bloco |
| 10 | `10_validacao_aprovada.png` | Resumo sem erros bloqueantes |
| 11 | `11_validacao_bloqueada.png` | Intersecao destacada e regra bloqueante |
| 12 | `12_exportacao_pacote.png` | Alvo, arquivos, checksum e download |
| 13 | `13_execucao_fotos.png` | Execucao, fotos, EXIF e cobertura |
| 14 | `14_odm_vinculado.png` | Tarefa ODM e produtos vinculados |

Cada screenshot deve ser legivel sem depender do cursor. O script deve ocultar dados sensiveis e registrar a versao da aplicacao no rodape do relatorio.

## 6. Roteiro para video futuro

O video deve seguir a mesma ordem das evidencias, sem cortes que escondam validacoes:

1. Criar projeto e missao;
2. mostrar o mapa e as ferramentas;
3. desenhar AOI;
4. adicionar exclusao e takeoff;
5. configurar Mini 3 e camera;
6. gerar grid;
7. editar waypoint e linhas;
8. executar simulacao;
9. mostrar validacao aprovada;
10. provocar e corrigir um bloqueio;
11. exportar pacote;
12. registrar execucao;
13. importar fotos;
14. disparar ODM e abrir produtos.

O script nao deve depender de gravacao manual. A captura de video sera um artefato adicional do mesmo teste Playwright; os screenshots e o relatorio permanecem a evidencia oficial.

## 7. Criterios de aceite do sprint

- Todas as etapas 0 a 6 concluidas sem erro bloqueante.
- O mapa permanece visivel e interativo em desktop e tablet.
- A AOI, exclusao e rota podem ser editadas sem recarregar a pagina.
- Os numeros apresentados na interface batem com o motor geometrico dentro da tolerancia definida.
- Um caso aprovado e um caso bloqueado sao demonstrados.
- A exportacao produz manifesto, checksum e arquivos esperados.
- O Playwright gera pelo menos 14 screenshots nomeadas, JSON de resultado, Markdown de validacao e video.
- O relatorio identifica claramente implementado, parcial, bloqueado e fora do escopo.
- Falhas encontradas sao corrigidas e o roteiro e executado novamente antes de considerar o sprint concluido.

## 8. Fora do sprint

- controle remoto direto pelo navegador;
- garantia de compatibilidade com qualquer firmware do Mini 3;
- homologacao operacional de Dronelink ou Map Pilot Pro sem voo real;
- autorizacao ANAC/DECEA/SARPAS automatizada;
- processamento GPU ou analise de IA dos produtos ODM.

## 9. Definicao de pronto

O sprint esta pronto quando o roteiro Playwright consegue demonstrar, com dados deterministas e telas legiveis, a criacao, configuracao, geracao, edicao, validacao e exportacao de uma missao. A etapa seguinte e executar o teste com um voo real do Mini 3, importar as fotos e fechar o ciclo com o ODM.

# Sistema de Ortomapas — Recapitulação e Prontidão para Produção

**Data do levantamento:** 2026-09-10
**Base:** memória de sessões anteriores, documentos do repositório, datas de arquivos, histórico git, inspeção do banco e do código-fonte, e testes de SQL executados sobre uma **cópia** do banco (o banco original não foi alterado).

> Os transcripts das sessões anteriores não estão mais disponíveis. A linha do tempo abaixo foi reconstruída por evidências indiretas (datas de arquivos, relatórios, memória) — trechos marcados como *inferido* não têm registro direto.

---

## 1. O que é o sistema

Plataforma web para armazenamento, visualização e análise espacial de ortomosaicos gerados por drone (DJI Mini 3, 248 g), voltada a pesquisa no entorno de Belo Horizonte (Serra do Cipó, Serra da Moeda, Quadrilátero Ferrífero, Brumadinho/Paraopeba, Rio das Velhas, Lagoa Santa).

| Camada | Implementação |
|---|---|
| Backend | FastAPI (porta 8888) — 6 routers: projetos, voos, ortomapas, análises, anotações, tools |
| Ferramentas espaciais | 7 módulos em `backend/tools/` (18 endpoints em `/api/tools/*`): GDAL (clip, reprojeção, merge, curvas de nível, hillshade), índices RGB (VARI, TGI, ExG, GLI), declividade, aspecto, estatísticas zonais, calculadora raster, detecção de mudanças, classificação (KMeans/RF/SVM), hidrologia (bacia, drenagem, TWI), volumetria, diferença de DSM, segmentação |
| Agentes de IA | 5 agentes + orquestrador em `backend/agents/`: vegetação, detecção (YOLOv8), classificação, mudanças, relatórios (Claude/Anthropic API) |
| Frontend | Vue 3 + Vite + Leaflet + PrimeVue + Pinia (porta 5176) — 13 componentes (mapa, camadas, medições, desenho, swipe/comparação, exportação, painel de ferramentas, status de agentes) |
| Banco | MySQL (configurado) com fallback automático para SQLite em `data/ortomapas.db` — **na prática, só SQLite foi usado** (ver seção 4) |
| Infra opcional | `docker-compose.yml` com WebODM (+ NodeODM, Postgres, Redis) e GeoServer |

---

## 2. Linha do tempo

| Data | O que foi feito | Evidência |
|---|---|---|
| **25/03/2026** | Pesquisa de base: operação do Mini 3 para ortomapeamento, Serra do Cipó, guia de configuração (Litchi Pilot + Drone Grid Planner), análise de 19 áreas de interesse perto de BH, limites GeoJSON do PARNA Serra do Cipó e APA Morro da Pedreira | `DJI_Mini3_Orthomapping_Research.md`, `Serra_do_Cipo_Drone_Orthomapping_Research.md`, `configdrone.md`, `ANALISE AREAS.md`, `geojson/` |
| **26–27/03** | Especificação (`ortomapa.md`) e construção do sistema completo (backend, frontend, tools, agentes). Correções: routers sem `with get_connection()`, nomes de coluna divergentes, fallback SQLite com wrapper de cursor. Testes Playwright de UI: 32/32 PASS. Nessa fase ficou definido que testes de UI devem interagir como usuário real (cliques, formulários), e não apenas chamar a API | `testevalidacao/test_ui_completo.py`, `testevalidacao/screenshots/`, memória |
| **28/03** | Validação em equipe de agentes: requisitos → verificação de implementação → validação Playwright → correções → revalidação → relatório de aceite | `testevalidacao/agent_teams/01…06_*.md` |
| **29/03** | Engenharia reversa/documentação: inventário, arquitetura, funcionalidades, especificação funcional, entidades e regras, atores, 20 casos de uso detalhados. Suíte E2E em `tests/e2e/playwright/` | `docs/analise/`, `docs/validacao/relatorio_execucao.md` |
| **29/05** | Validação multi-dataset com 7 datasets públicos reais (ortofoto Trento, Derna pós-enchente, Sentinel-2, Landsat, raster RGB do rasterio, 2 DEMs). 133 combinações; 5 ciclos de *auto research*: de 52 aprovados / 59 reprovados para 100 aprovados / 0 reprovados / 33 skips esperados | `docs/validacao/parecer_final_multi_dataset.md`, `tests/e2e/playwright/test_multi_dataset.py`, `data/downloads/`, `data/analises/multi_*` |
| **11/06** | Limpeza para publicação: credenciais movidas para `.env` (gitignored), `.env.example`, README, commit inicial `7f48002` e push para `github.com/pasteurjr/ortomapas` | `git log` |
| **10/09 (antes desta sessão)** | Build de produção do frontend (`frontend/dist/`, 18:19) e geração de `docs/analise/casos_de_uso.html` (18:46), versão HTML dos 20 casos de uso — **ainda não commitada**. *Inferido*: feito em outra sessão (outro diretório ou claude.ai), sem transcript local | datas de arquivo, `git status` |

---

## 3. Estado atual (10/09/2026)

| Item | Situação |
|---|---|
| Git | `main` sincronizado com `origin/main`. Pendente: `docs/analise/casos_de_uso.html` (não rastreado) |
| Frontend | Rodando em **Vite dev server** na porta 5176 (`0.0.0.0`) |
| Backend | **Parado** (nada escutando em 8888) |
| Portas 8000 e 5173 | Ocupadas por outro projeto (`forge`) — conflitam com a porta 8000 do WebODM no `docker-compose.yml` |
| Containers do projeto | Nenhum rodando (WebODM/GeoServer não estão ativos) |
| Banco SQLite | 69 KB — 47 projetos, 36 voos, 3 ortomapas, **0 análises, 0 anotações, 0 GCPs, 0 comparações temporais, 0 tarefas de agentes**. Quase tudo é resíduo de teste (“Multi-Dataset dem_90m” etc.) |
| Diretório `data/` | 1,5 GB (datasets baixados, resultados de análises de teste, 9 GeoTIFFs em `data/ortomapas/`) |
| Dados reais do Mini 3 | **Nenhum voo real processado.** Só há `serra_moeda_teste*.tif`, que parecem ser de teste |
| MySQL | Host `camerascasa.no-ip.info` **não resolve** (testado com DNS local, 8.8.8.8 e 1.1.1.1) — o hostname no-ip provavelmente expirou |
| Documentos desatualizados | `docs/validacao/divergencias.md` lista divergências do primeiro ciclo, já resolvidas. A numeração dos UCs diverge: nos docs, UC-020 = “Disparar Análise via Agente de IA”; nos testes, UC-020 = “Segmentar Ortomapa” |

---

## 4. MySQL ou SQLite?

**Resposta: tudo o que o sistema gravou até hoje está no SQLite (`data/ortomapas.db`). O MySQL foi configurado, mas não há evidência de que a aplicação tenha operado contra ele — e o código atual nem funcionaria corretamente nele.**

Evidências:

1. **O SQLite contém o histórico completo dos testes**, de março a maio (47 projetos; os últimos criados em 29/05/2026, 20:08).
2. **A memória da sessão de 27/03 já registrava** “DNS resolution intermittent, so system uses SQLite fallback when MySQL unreachable”.
3. **Nenhum relatório de validação cita execução contra MySQL**. O parecer final (`docs/validacao/parecer_final.md`) lista o banco como “SQLite (fallback) / MySQL”.
4. **O host MySQL não resolve hoje**, nem em DNS públicos.
5. **Os dois schemas divergem, e o código segue o SQLite.** `backend/database/schema.sql` (MySQL) usa `created_at`/`updated_at`; o schema SQLite embutido em `connection.py` e os routers usam `criado_em`/`atualizado_em` (15 ocorrências de `criado_em` no código). O MySQL também não tem as colunas `observacoes` (em 4 tabelas) e `data_analise`. Os `INSERT`s dos routers (ex.: upload de ortomapa grava `criado_em`) falhariam no MySQL criado a partir de `schema.sql`.

Ressalva: não consegui acessar o servidor MySQL, então não posso descartar que `schema.sql`/`seed.py` tenham sido executados lá em algum momento. Mas a aplicação, nos testes documentados, rodou sobre SQLite.

**Comportamento do fallback que importa para produção** (`backend/database/connection.py:68-72`): na primeira falha de conexão com o MySQL, o processo muda para SQLite **em silêncio e para sempre** (`_use_sqlite` nunca volta a `False`). Em produção, uma queda breve do MySQL faria o sistema gravar num banco local diferente, sem aviso, até ser reiniciado — dados divididos entre dois bancos.

---

## 5. Problemas encontrados na revisão (não detectados pelos testes)

A validação reportou 100% de aprovação, mas ela não exercitou a criação de análises nem a fila de agentes. Os testes só fazem `GET /api/analises`, e o “UC-020” testado é segmentação, não agentes. Os três SQLs abaixo foram executados numa cópia do banco e **falharam**:

| # | Onde | Erro | Consequência |
|---|---|---|---|
| B1 | `backend/routers/analises.py:103-119` — `POST /api/analises` | `table analises has no column named arquivo_resultado` (a coluna chama-se `resultado_path`) | Criar análise retorna HTTP 500. Por isso a tabela `analises` está vazia |
| B2 | `backend/routers/analises.py:127-144` — enfileirar tarefa | `no such table: tarefas_agente` (a tabela é `tarefas_agentes`; a coluna `referencia_id` também não existe) | Falha **engolida** pelo `except` — o usuário não recebe erro, mas nada entra na fila |
| B3 | `backend/agents/orchestrator.py:58` | `no such column: created_at` | O orquestrador não consegue ler a fila no SQLite |
| B4 | Orquestrador | Nada o inicia (só roda via `python -m …orchestrator`) | Mesmo com B1–B3 corrigidos, as tarefas não seriam processadas sem um serviço dedicado |
| B5 | `backend/routers/ortomapas.py:194` | `res_cm = resolution.x * 100` assume CRS métrico | Para rasters em EPSG:4326 (graus), a resolução gravada fica errada por ordens de grandeza |
| **B6** | `backend/routers/ortomapas.py:363-398` — servidor de tiles `GET /api/ortomapas/{id}/tile/{z}/{x}/{y}.png` | Calcula os limites do tile em **graus** (lon/lat) e os compara com os limites do raster no **CRS nativo** (metros, em UTM ou EPSG:3857), sem reprojetar | **Qualquer ortomosaico que não esteja em EPSG:4326 fica invisível no mapa.** Reproduzi a lógica sobre os 9 GeoTIFFs de `data/ortomapas/`: os 5 datasets públicos (Trento EPSG:25832, Derna EPSG:32634, Sentinel-2 EPSG:32631, rasterio EPSG:32618, Landsat EPSG:3857) geram **tile transparente**. Só aparecem os `serra_moeda_teste*.tif`, em EPSG:4326. Como o WebODM entrega ortomosaicos em UTM, **nenhuma saída real do WebODM apareceria no mapa** |
| B6a | Mesmo trecho, mesmo em EPSG:4326 | Sem reprojeção para Web Mercator, a janela cortada nas bordas é esticada para 256×256, e a normalização min/max é feita **por tile** | Distorção vertical, bordas esticadas e “costuras” de brilho entre tiles vizinhos |

**Os únicos rasters que aparecem no mapa são sintéticos.** Os `serra_moeda_teste*.tif` e o `data/dsm/serra_moeda_dsm.tif` têm 1024×1024 px, extensão de exatamente 0,04°, e o DSM tem desvio-padrão de exatamente 100,0. Foram criados em 26/03, no dia da construção do sistema. São eles os 3 registros da tabela `ortomapas`.

**Conclusão:** o fluxo “Disparar Análise via Agente de IA” nunca funcionou de ponta a ponta. As ferramentas espaciais (`/api/tools/*`), chamadas diretamente pela API com caminhos de arquivo, rodaram nos 7 datasets. Mas **a visualização desses datasets no mapa nunca funcionou** (B6), e nenhum dado real passou pelo fluxo completo da interface (upload → mapa → análise → resultado).

---

## 6. O sistema tem as funcionalidades do WebODM?

**Não.** O sistema é uma camada de **análise e catálogo** que deveria ficar *depois* do WebODM. A integração com o WebODM, prevista na especificação, **não foi implementada**:

- Especificação: `ortomapa.md:77` (“WebODM API — disparo de processamentos”) e `ortomapa.md:447-463` (`processar_webodm()` via API).
- Código: só existem `WEBODM_URL` em `backend/config.py:33` e a coluna `ortomapas.webodm_task_id`. **Não há nenhum cliente da API do WebODM/NodeODM** nem endpoint de envio de fotos.
- Infra: as imagens `opendronemap/*` **nunca foram baixadas** nesta máquina (nenhuma imagem ou volume Docker), e a porta 8000 do WebODM no `docker-compose.yml` está ocupada pelo projeto `forge`.

| Funcionalidade do WebODM | Ortomapas | Observação |
|---|---|---|
| Upload de fotos brutas e processamento fotogramétrico (SfM/MVS pelo ODM) | ❌ | Só aceita GeoTIFF pronto |
| Geração de ortomosaico, DSM e DTM | ❌ | Depende de processar fora |
| Nuvem de pontos (LAZ/PLY) e visualizador 3D (Potree) | ❌ | Nenhum código de nuvem de pontos ou 3D |
| Modelo 3D texturizado (OBJ/glTF) | ❌ | — |
| Relatório de qualidade do processamento (GSD, erro de reconstrução, sobreposição) | ❌ | As colunas `qualidade_processamento` e `erro_rms` existem, mas só são preenchidas à mão |
| GCPs (lista de GCPs, editor de GCP) | ❌ | Há tabela `gcps` e modelo Pydantic, mas nenhum endpoint nem tela |
| Fila, progresso e nós de processamento | ❌ | — |
| Ortomosaico no mapa (tiles) | ⚠️ quebrado | Não funciona em UTM (bug B6), justamente o formato de saída do WebODM |
| Medir distância e área | ✅ | `MeasureTools.vue` (no navegador) |
| Volume | ⚠️ parcial | Só contra uma elevação de referência (`/api/tools/volume`), sem polígono desenhado no mapa |
| Curvas de nível | ✅ | `/api/tools/contours` |
| Índices de vegetação (“Plant Health”) | ✅ só RGB | VARI, TGI, ExG, GLI. Sem NDVI/multiespectral |
| Comparação lado a lado (swipe) | ✅ | `CompareView.vue` (herda o bug B6) |
| Usuários, permissões, compartilhamento | ❌ | Sem nenhuma autenticação |
| API REST com token | ⚠️ | A API existe, mas sem autenticação |

**O que o Ortomapas tem e o WebODM não tem:** catálogo de projetos e voos com metadados de campo, hidrologia (bacia, drenagem, TWI), classificação supervisionada e não supervisionada, detecção de mudanças, segmentação, anotações e agentes de IA (hoje quebrados). Esse é o valor próprio do sistema.

**Recomendação:** não reimplementar a fotogrametria, que é o trabalho do ODM e levou anos para amadurecer. **Integrar:** subir o NodeODM (mais leve, com API simples via `pyodm`) ou o WebODM completo. O backend envia as fotos do voo, acompanha a tarefa, baixa ortomosaico, DSM, DTM e relatório, e cadastra tudo automaticamente, com o `webodm_task_id` e as métricas de qualidade. A máquina aguenta com folga: 20 núcleos, 125 GB de RAM, 3 GPUs NVIDIA de 16 GB (RTX 5080, 5060 Ti, 4060 Ti) e 1,4 TB livres em `/mnt/data1`. A compatibilidade da imagem GPU do ODM com a RTX 5080 (arquitetura Blackwell) precisa ser testada. A imagem só de CPU funciona de qualquer forma.

---

## 7. O que falta para colocar em produção

### P0 — Bloqueantes (segurança e correção)

| # | Item | Detalhe |
|---|---|---|
| 1 | **Autenticação/autorização** | Não existe nenhuma: todos os endpoints, inclusive `DELETE` e upload, estão abertos. Mínimo: login + token (JWT/OAuth2 do FastAPI) e perfis (pesquisador/admin) |
| 2 | **Banco exposto por HTTP** | `backend/main.py:37` monta `data/` inteiro como estático em `/data`: `GET /data/ortomapas.db` baixa o banco, e qualquer GeoTIFF fica público. Servir só `thumbnails/` e `analises/`, ou servir arquivos por endpoint autenticado |
| 3 | **Execução remota de código** | `backend/tools/raster_analysis.py:391` usa `eval(expression, {"__builtins__": {}}, …)` no endpoint `/api/tools/calculator`. Esvaziar `__builtins__` não é sandbox: há técnicas conhecidas para escapar. Trocar por `numexpr` ou por um parser de expressões com whitelist de operadores |
| 4 | **Leitura e escrita arbitrária de arquivos** | `backend/routers/tools.py:106-125`: `_resolve_path` aceita caminhos absolutos, e `output_name` não é sanitizado (`../`). É possível ler qualquer raster do servidor e gravar fora de `data/analises`. Restringir a caminhos dentro de `DATA_DIR` (resolver + checar prefixo) e, de preferência, receber IDs de ortomapa em vez de caminhos |
| 5 | **CORS** | `allow_origins=["*"]` com `allow_credentials=True` (`main.py:28-34`). Restringir ao domínio do frontend |
| 6 | **Senhas padrão** | GeoServer `admin/geoserver` no `docker-compose.yml`. Mover para `.env` |
| 7 | **Corrigir o pipeline de análises/agentes e o servidor de tiles** | Bugs B1–B4 e **B6** da seção 5. Para os tiles: reprojetar com `rio-tiler` (ou `rasterio.vrt.WarpedVRT` para EPSG:3857), usar estatísticas globais para normalizar e, de preferência, gerar COG (Cloud Optimized GeoTIFF) no upload. Tudo com testes que verifiquem pixels não transparentes num raster UTM real |
| 8 | **Definir um único banco e um único schema** | Hoje há dois schemas mantidos à mão e divergentes. Recomendação: **PostgreSQL + PostGIS**, que dá geometria nativa (bbox, anotações WKT, índices espaciais). **Já existe PostGIS nesta máquina**: o container `geoagentica-banco` (imagem `geoagentica/banco:16-3.4`, pela tag PostgreSQL 16 + PostGIS 3.4, porta 5433), mas ele pertence a outro projeto (`geoagentica`). Não há Postgres nativo (serviço `postgresql` inativo, sem `psql`). Opções: (a) criar um banco `ortomapas` nesse servidor, que fica acoplado ao ciclo de vida do outro projeto; (b) **recomendado:** um container `postgis/postgis:16-3.4` próprio no `docker-compose.yml`. Não reutilizar o Postgres interno do WebODM. Em qualquer caso: migrações com Alembic e **remover o fallback silencioso** (falhar com erro claro) |
| 8a | **Integração com WebODM/NodeODM** | Seção 6. Sem ela, o sistema não recebe o produto de um voo real sem passos manuais fora do sistema |

### P1 — Operação

| # | Item | Detalhe |
|---|---|---|
| 9 | Processamento pesado bloqueia a API | Os endpoints de `/api/tools/*` são `async def` e rodam rasterio/sklearn de forma síncrona: um slope num DEM grande trava **todas** as requisições. Mínimo: trocar para `def` (o FastAPI passa a usar threadpool). Ideal: fila (orquestrador como serviço, ou Celery/RQ + Redis) com status consultável |
| 10 | Limites de upload | Não há limite de tamanho, e ortomosaicos reais podem ter vários GB. Definir limite, validar que o arquivo é GeoTIFF, checar espaço em disco |
| 11 | Frontend de produção | Hoje roda o **dev server do Vite** exposto em `0.0.0.0`. Servir `frontend/dist/` com nginx (ou Caddy), com proxy `/api` → 8888 e HTTPS |
| 12 | Empacotamento | Faltam Dockerfile do backend/frontend e serviços no compose. Resolver o conflito da porta 8000 (WebODM vs. projeto `forge`) |
| 13 | Dependências | `requirements.txt` só usa `>=`. Gerar lock com versões fixas. `ultralytics` puxa PyTorch (pesado): avaliar se o agente YOLO entra na primeira versão |
| 14 | Health check real | `/health` não verifica banco, disco nem dependências |
| 15 | Backups | Banco e `data/` (GeoTIFFs). Definir política (ex.: dump diário + rsync/restic) |
| 16 | Logs e monitoramento | Logs estruturados, rotação, alerta de erro. Hoje erros viram `HTTPException(500, str(e))`, que expõe detalhes internos ao cliente |
| 17 | Testes e CI | Faltam testes unitários dos tools (valores conhecidos), testes de API independentes de servidor (TestClient + banco temporário) e CI no GitHub Actions. Os E2E atuais exigem servidores no ar |
| 18 | Limpeza | Remover os 47 projetos de teste e os resultados em `data/analises/`. Separar dados de teste (fixtures) de dados reais |
| 19 | Deprecações | `@app.on_event("startup")` e `datetime.utcnow()`: trocar por `lifespan` e `datetime.now(UTC)` |

### P2 — Validação científica e produto

| # | Item | Detalhe |
|---|---|---|
| 20 | **Voo real do Mini 3 de ponta a ponta** | Planejar (Litchi), voar, processar no WebODM, subir, analisar. Até agora só houve datasets públicos |
| 21 | Acurácia posicional | Fluxo de GCPs (a tabela `gcps` existe, mas não há UI nem uso). Reportar RMSE, que é essencial para publicação |
| 22 | Reprodutibilidade | Registrar parâmetros, versão das bibliotecas e hash dos insumos de cada análise (a tabela `analises` tem esses campos, mas não é populada — bug B1) |
| 23 | Limitações metodológicas explícitas | Índices só RGB (sem NIR, logo sem NDVI), com efeitos de iluminação e BRDF. Documentar isso na UI e nos relatórios |
| 24 | Correção da resolução em CRS geográfico | Bug B5 |
| 25 | Integração com GeoServer | Publicação WMS/WMTS está prevista, mas não foi verificada |
| 26 | Documentação | Atualizar `divergencias.md`, alinhar a numeração dos UCs entre docs e testes, e decidir sobre o `casos_de_uso.html` |

### Ordem sugerida

1. **Segurança mínima** (itens 1–6): sem isso, o sistema não deve ficar exposto nem na rede local.
2. **Banco** (item 8) + **pipeline de análises** (item 7), com testes.
3. **Processamento assíncrono** (item 9) + **empacotamento/deploy** (itens 11–13).
4. **Primeiro voo real** (item 20) como teste de aceitação de verdade.
5. Restante de P1 e P2.

---

## 8. O que valem os relatórios de validação de março/maio

A auditoria completa, UC por UC, foi interrompida para economizar tokens. O que já está comprovado:

| Afirmação dos relatórios | Situação real |
|---|---|
| “100% de aprovação”, “VALIDADO COM ALTA CONFIANÇA” (maio) | **Enganosa.** Os 33 SKIPs ficaram fora do denominador. Os testes validaram sobretudo as **ferramentas chamadas diretamente pela API** com caminhos de arquivo, não o fluxo do usuário na interface |
| UC-020 aprovado | **O teste não é o UC especificado.** Nos testes, UC-020 = “Segmentar Ortomapa”. Na especificação, UC-020 = “Disparar Análise via Agente de IA”, que está quebrado (B1–B4) e nunca foi testado |
| Análises/agentes funcionando | **Falso.** Os testes só fazem `GET /api/analises`. `POST` dá erro 500, e as tabelas `analises` e `tarefas_agentes` estão vazias |
| Visualização de ortomosaicos validada nos 7 datasets | **Falso para os dados reais.** O servidor de tiles não reprojeta (B6). Os datasets públicos ficam transparentes no mapa, e só os rasters sintéticos em EPSG:4326 aparecem |
| Ferramentas espaciais (índices, declividade, hillshade, drenagem, segmentação etc.) | **Provavelmente válidas como cálculo**, porque rodaram sobre dados reais e geraram arquivos em `data/analises/`. A correção numérica contra valores de referência não foi auditada |
| Banco “MySQL / SQLite” | Só SQLite foi usado. O schema do MySQL é incompatível com o código |

**Leitura geral:** o trabalho de março a maio produziu código real e ferramentas de cálculo que funcionam. Mas os relatórios foram escritos em cima de testes que medem “respondeu sem erro”, e não “o usuário consegue fazer o caso de uso com dados reais”. Por isso não detectaram que o mapa não mostra dados reais nem que o fluxo de análises está quebrado. **Esses relatórios não devem ser usados como evidência de que o sistema está pronto.**

## 9. Plano para retomar e finalizar

| Fase | Entrega | Critério de pronto |
|---|---|---|
| **0. Base honesta** | Marcar os relatórios antigos como obsoletos (sem apagar), limpar o banco de teste e commitar este documento | Repositório sem afirmações falsas de “pronto” |
| **1. Núcleo funcionando** | Corrigir o servidor de tiles (B6), o fluxo de análises (B1–B4) e a resolução (B5). Migrar para PostgreSQL + PostGIS com Alembic e remover o fallback | Um GeoTIFF real em UTM aparece no mapa, alinhado com o fundo de satélite; `POST /api/analises` grava e o resultado aparece na UI |
| **2. Testes que provam** | Testes de UI que fazem o caso de uso completo com dados reais e checam o **resultado** (pixels não transparentes, valores de índice em faixa válida, linha gravada no banco). SKIP conta como não testado | Cada UC da especificação tem um teste com o mesmo nome e número |
| **3. Integração ODM** | NodeODM/WebODM em Docker, com envio das fotos pelo sistema, acompanhamento da tarefa e importação automática de ortomosaico, DSM, DTM e relatório | Um voo real do Mini 3 vai das fotos até o mapa sem passos manuais |
| **4. Segurança e deploy** | Autenticação, fechar `/data`, trocar o `eval`, restringir caminhos, CORS, nginx + HTTPS, fila de processamento, backups | Pode ficar exposto na rede |
| **5. Rigor científico** | GCPs e RMSE, registro de parâmetros e versões de cada análise, limitações do RGB documentadas | Resultados publicáveis e reprodutíveis |

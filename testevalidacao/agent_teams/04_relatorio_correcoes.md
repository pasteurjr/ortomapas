# Relatorio de Correcoes

**Data:** 2026-03-28
**Executor:** Agent 4 -- Fixer
**Baseado em:** 02_verificacao_implementacao.md (P01-P15), 03_relatorio_validacao.md

---

## Correcoes Aplicadas

| ID | Severidade | Descricao | Arquivo(s) | Correcao |
|---|---|---|---|---|
| P04 | ALTA | uploadOrtomapa em client.js envia para /ortomapas em vez de /ortomapas/upload | frontend/src/api/client.js | Alterado endpoint de `/ortomapas` para `/ortomapas/upload`. Adicionado suporte a params `projeto_id` e `tipo` via query string, conforme o backend espera. |
| P09 | ALTA | DrawTools.vue envia `projeto_id` e `geometria` mas backend espera `ortomapa_id` e `geometria_wkt` | frontend/src/components/DrawTools.vue | Alterado `projeto_id` para `ortomapa_id` (usa primeiro ortomapa do projeto ativo). Alterado campo `geometria` para `geometria_wkt`. Adicionada validacao de ortomapa disponivel. |
| P12 | ALTA | Coluna `tamanho_arquivo_mb` duplicada no INSERT de upload em ortomapas.py; colunas `crs` e `thumbnail` inexistentes | backend/routers/ortomapas.py | Corrigido INSERT: substituido primeiro `tamanho_arquivo_mb` por `formato` (valor "GeoTIFF"), removida duplicacao. Corrigido `crs` para `sistema_coordenadas` e `thumbnail` para `caminho_thumbnail`, conforme schema do banco. |
| P13 | BAIXA | Campo `tamanho_arquivo_mb` duplicado na lista updatable do PUT | backend/routers/ortomapas.py | Removida duplicata. Corrigido `crs` para `sistema_coordenadas` na lista updatable. |
| P07 | MEDIA | getAnalises em client.js envia `projeto_id` mas backend so aceita `ortomapa_id` | backend/routers/analises.py | Adicionado parametro opcional `projeto_id` ao endpoint `GET /analises` (a tabela analises ja possui coluna projeto_id). Client.js mantido como esta pois agora o backend aceita o filtro. |
| P10 | MEDIA | getAnotacoes em client.js envia `projeto_id` mas backend so aceita `ortomapa_id` | backend/routers/anotacoes.py | Adicionado parametro opcional `projeto_id` ao endpoint `GET /anotacoes` usando subquery `ortomapa_id IN (SELECT id FROM ortomapas WHERE projeto_id = %s)`. Client.js mantido. |
| P08 | MEDIA | AnalysisForm.vue nao tem opcao queue_task para ativar agentes de IA | frontend/src/components/AnalysisForm.vue | Adicionado checkbox "Executar via Agente de IA" com `queue_task` no formulario reativo. Campo enviado no payload de criacao da analise. Estilo visual integrado ao tema escuro. |
| P03 | MEDIA | Sem UI para gerenciamento de voos (flights) | frontend/src/components/VoosList.vue, frontend/src/api/client.js, frontend/src/App.vue | Criado componente VoosList.vue com listagem, criacao e exclusao de voos. Adicionadas funcoes `getVoos`, `getVoo`, `createVoo`, `updateVoo`, `deleteVoo` ao client.js. Componente integrado no App.vue na sidebar esquerda. |
| P01 | BAIXA | Sem filtros de status e area_estudo na UI de projetos | frontend/src/components/ProjectList.vue | Adicionados campo de texto para filtrar por area/nome e dropdown Select para filtrar por status. Listagem agora usa computed `filteredProjects`. |
| P02 | BAIXA | Sem busca textual (search) no client.js para projetos | frontend/src/api/client.js | Adicionada funcao `searchProjects(q)` que chama `GET /projetos/search?q=`. |
| P06 | BAIXA | Sem funcao updateOrtomapa no client.js | frontend/src/api/client.js | Adicionada funcao `updateOrtomapa(id, data)` que chama `PUT /ortomapas/{id}`. |
| P11 | BAIXA | Sem clique no mapa para definir pour point em watershed (hidrologia) | frontend/src/components/ToolsPanel.vue, frontend/src/stores/mapStore.js, frontend/src/components/MapViewer.vue | Adicionados campos lat/lon para pour point no painel de hidrologia (visivel quando tipo=watershed). Botao "Capturar do Mapa" ativa callback no mapStore. MapViewer.vue agora chama `mapStore.handleMapClick()` em cada clique. mapStore ganhou `pourPointCallback`, `setPourPointCallback()` e `handleMapClick()`. |
| P14 | BAIXA | ToolsPanel exportFormats falta JPEG e GeoJSON | frontend/src/components/ToolsPanel.vue | Adicionados `{ label: 'JPEG', value: 'jpeg' }` e `{ label: 'GeoJSON', value: 'geojson' }` ao array exportFormats. |
| P15 | BAIXA | ToolsPanel crsOptions incompleto (faltam EPSG:31984 e EPSG:32724) | frontend/src/components/ToolsPanel.vue | Adicionados `EPSG:31984 (SIRGAS 2000 / UTM 24S)` e `EPSG:32724 (WGS 84 / UTM 24S)` ao array crsOptions. |
| PATH | MEDIA | Inconsistencia de paths: DB armazena com prefixo `data/` mas tools API espera path relativo a `data/` | backend/routers/tools.py | Funcao `_resolve_path()` agora detecta e remove prefixo `data/` antes de juntar com DATA_DIR. Assim funciona tanto para paths com prefixo quanto sem. |

---

## Resumo Quantitativo

| Severidade | Total | Corrigidos |
|---|---|---|
| ALTA | 3 (P04, P09, P12) | 3 |
| MEDIA | 4 (P03, P07, P08, P10) + PATH | 5 |
| BAIXA | 8 (P01, P02, P05, P06, P11, P13, P14, P15) | 7 |
| **TOTAL** | **16** | **15** |

**P05 (consulta espacial no frontend)** nao foi corrigido pois requer decisao de design sobre quando disparar a query (ex: ao mover o mapa). O endpoint backend funciona corretamente e pode ser integrado futuramente.

---

## Arquivos Modificados

1. `frontend/src/api/client.js` -- P02, P03, P04, P06 (funcoes de API)
2. `frontend/src/components/DrawTools.vue` -- P09 (campos de anotacao)
3. `backend/routers/ortomapas.py` -- P12, P13 (SQL INSERT/UPDATE)
4. `backend/routers/analises.py` -- P07 (filtro projeto_id)
5. `backend/routers/anotacoes.py` -- P10 (filtro projeto_id via subquery)
6. `frontend/src/components/AnalysisForm.vue` -- P08 (checkbox queue_task)
7. `backend/routers/tools.py` -- PATH (resolve path com/sem prefixo data/)
8. `frontend/src/components/ToolsPanel.vue` -- P11, P14, P15 (pour point, formatos, CRS)
9. `frontend/src/stores/mapStore.js` -- P11 (pour point callback)
10. `frontend/src/components/MapViewer.vue` -- P11 (click handler)
11. `frontend/src/components/ProjectList.vue` -- P01 (filtros UI)
12. `frontend/src/App.vue` -- P03 (import VoosList)

## Arquivos Criados

1. `frontend/src/components/VoosList.vue` -- P03 (componente de gerenciamento de voos)

# Relatorio de Execucao — Validacao Playwright E2E

**Data:** 2026-09-13 04:43:09

**Backend:** http://localhost:8888

**Frontend:** http://localhost:5176


---

## Resumo

| Total | Aprovados | Reprovados |
|---|---|---|
| **17** | **17** ✅ | **0** ❌ |

Taxa: **100.0%**


---

## Resultado por Caso de Uso


### UC-001: Criar Novo Projeto

**Status:** ✅ **APROVADO**

**Passos executados:**

1. ✅ Estado inicial: 0 projetos existentes
   ![](../runtime/screenshots/UC001_step01_estado_inicial.png)
2. ✅ Projeto criado com ID=23, HTTP 201
3. ✅ Campos validados: nome='UC-001 Teste Automatizado', status='em_andamento'
4. ✅ GET /api/projetos/23 retornou projeto correto
5. ✅ Contagem aumentou de 0 para 1


### UC-002: Buscar e Filtrar Projetos

**Status:** ✅ **APROVADO**

**Passos executados:**

1. ✅ Busca por 'Serra': 1 resultados
2. ✅ Filtro status=planejado: 0 projetos
3. ✅ Filtro status=em_andamento funciona


### UC-003: Selecionar Projeto e Listar Ortomapas

**Status:** ✅ **APROVADO**

**Passos executados:**

1. ✅ Projeto 3 tem 0 ortomapas
2. ✅ Tipos presentes: set()
3. ✅ Frontend carregado, conteudo: 624 chars
   ![](../runtime/screenshots/UC003_step03_sidebar_projetos.png)


### UC-005: Calcular Indice de Vegetacao VARI

**Status:** ✅ **APROVADO**

**Passos executados:**

1. ✅ VARI calculado. Output: e2e_vari.tif
2. ✅ Arquivo existe: 4511 KB
3. ✅ GeoTIFF valido: 1024x1024, CRS=EPSG:4326
4. ✅ Estatisticas: min=-1000000.0, max=118.0, mean=-75.96686188666595
5. ✅ TGI tambem calculado com sucesso
6. ✅ ExG calculado com sucesso
7. ✅ GLI calculado com sucesso. Todos os 4 indices OK.


### UC-006: Calcular Declividade (Slope)

**Status:** ✅ **APROVADO**

**Passos executados:**

1. ✅ Slope calculado: /mnt/data1/progpython/ortomapas/data/analises/e2e_slope.tif
2. ✅ Aspect calculado


### UC-007: Gerar Curvas de Nivel

**Status:** ✅ **APROVADO**

**Passos executados:**

1. ✅ Contornos gerados com intervalo 10m


### UC-008: Gerar Hillshade

**Status:** ✅ **APROVADO**

**Passos executados:**

1. ✅ Hillshade gerado (az=315, alt=45)


### UC-009: Detectar Mudancas Temporais

**Status:** ✅ **APROVADO**

**Passos executados:**

1. ✅ Mudancas detectadas: 3.13% alterado
2. ✅ Validacao: mudanca > 0% confirmada (3.13%)
3. ✅ Arquivo de mudancas gerado: e2e_mudancas.tif


### UC-010: Classificar Uso do Solo (KMeans)

**Status:** ✅ **APROVADO**

**Passos executados:**

1. ✅ Classificacao: 5 clusters gerados
2. ✅ Soma dos clusters: 100.0% (valido)


### UC-011: Extrair Rede de Drenagem

**Status:** ✅ **APROVADO**

**Passos executados:**

1. ✅ Rede de drenagem extraida


### UC-012: Calcular Volume

**Status:** ✅ **APROVADO**

**Passos executados:**

1. ✅ Volume: acima=373,604,498m3, abaixo=1,340,945,479m3
2. ✅ Volume nao-zero confirmado


### UC-013: Criar Anotacao Poligono

**Status:** ✅ **APROVADO**

**Passos executados:**

1. ✅ Anotacao poligono criada
2. ✅ Total anotacoes: 15


### UC-014: Criar Anotacao Ponto

**Status:** ✅ **APROVADO**

**Passos executados:**

1. ✅ Anotacao ponto criada


### UC-017: Comparar Dois Ortomapas

**Status:** ✅ **APROVADO**

**Passos executados:**

1. ✅ Estatisticas de ambos ortomapas obtidas
2. ✅ Banda verde: media1=142.7, media2=140.6, diff=2.0


### UC-019: Registrar Voo de Drone

**Status:** ✅ **APROVADO**

**Passos executados:**

1. ✅ Voo criado ID=10, altitude=50.0m
2. ✅ Voos do projeto 3: 1


### UC-020: Segmentar Ortomapa

**Status:** ✅ **APROVADO**

**Passos executados:**

1. ✅ Segmentacao: 7 clusters


### UC-UI: Validacao da Interface Web

**Status:** ✅ **APROVADO**

**Passos executados:**

1. ✅ Pagina carregada. Titulo: 'Sistema de Ortomapas'
   ![](../runtime/screenshots/UC-UI_step01_pagina_inicial.png)
2. ✅ Mapa Leaflet presente, 30 tiles
   ![](../runtime/screenshots/UC-UI_step02_mapa_leaflet.png)
3. ✅ Zoom In (2 cliques) executado
   ![](../runtime/screenshots/UC-UI_step03_zoom_in.png)
4. ✅ Zero erros no console JS
   ![](../runtime/screenshots/UC-UI_step04_console_check.png)
5. ✅ Screenshot final da interface capturado
   ![](../runtime/screenshots/UC-UI_step05_final_completo.png)


---

## Divergencias

**Nenhuma divergencia encontrada.**


---

## Screenshots Capturados

- `UC-UI_step01_pagina_inicial.png`
- `UC-UI_step02_mapa_leaflet.png`
- `UC-UI_step03_zoom_in.png`
- `UC-UI_step04_console_check.png`
- `UC-UI_step05_final_completo.png`
- `UC001_step01_estado_inicial.png`
- `UC001_step03_erro.png`
- `UC001_step05_erro.png`
- `UC003_step01_erro.png`
- `UC003_step03_sidebar_projetos.png`


*Gerado em 2026-09-13 04:43:09*

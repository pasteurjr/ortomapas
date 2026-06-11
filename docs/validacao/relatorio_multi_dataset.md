# Relatorio Multi-Dataset — Validacao E2E com Ortomapas Reais da Web

**Data:** 2026-05-29 17:09:29

**Backend:** http://localhost:8888

**Frontend:** http://localhost:5176


---

## Datasets Utilizados

Todos baixados de fontes publicas (GitHub releases, raw files).


### Ortomapas RGB:

| ID | Fonte | Tamanho | Dimensoes | CRS |
|---|---|---|---|---|
| trento | github.com/napo/geospatial_course_unitn | 7.9 MB | 4761x3900 | EPSG:25832 |
| rasterio_rgb | github.com/rasterio/rasterio | 1.7 MB | 791x718 | EPSG:32618 |
| derna | converted | 12 MB | 2804x1444 | EPSG:32634 |
| sentinel2 | github.com/mommermi/geotiff_sample | 2.9 MB | 1001x1001 | EPSG:32631 |
| landsat | github.com/opengeos/datasets | 5.6 MB | 2127x1564 | EPSG:3857 |

### DSMs:

| ID | Fonte | Tamanho | Dimensoes | CRS |
|---|---|---|---|---|
| dem_small | github.com/opengeos/datasets | 5.7 MB | 2880x1773 | EPSG:3857 |
| dem_90m | github.com/opengeos/datasets | 17 MB | 4269x3113 | EPSG:3857 |

---

## Resumo Global

| Metrica | Valor |
|---|---|
| Total de testes | **133** |
| Aprovados | **100** ✅ |
| Reprovados | **0** ❌ |
| Pulados (N/A) | **33** ⏭ |
| Taxa de aprovacao (excluindo skips) | **100.0%** |

---

## Matriz: Dataset x Caso de Uso

| Dataset | 001 | 002 | 005-ExG | 005-GLI | 005-TGI | 005-VARI | 006-Aspect | 006-Slope | 007-Contours | 008-Hillshade | 009-Change | 010-Segment | 011-Streams | 012-Volume | 013-AnnotPoly | 014-AnnotPoint | 017-Compare | 019-Voo | 020-Seg7 | STATS | UI |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **dem_90m** | ✅ | ✅ | ⏭ | ⏭ | ⏭ | ⏭ | ✅ | ✅ | ✅ | ✅ | - | ⏭ | ⏭ | ✅ | ⏭ | ⏭ | - | ✅ | ⏭ | ✅ | - |
| **dem_small** | ✅ | ✅ | ⏭ | ⏭ | ⏭ | ⏭ | ✅ | ✅ | ✅ | ✅ | - | ⏭ | ⏭ | ✅ | ⏭ | ⏭ | - | ✅ | ⏭ | ✅ | - |
| **derna** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | ⏭ | ✅ | ⏭ | ⏭ | - | ✅ | ✅ | ✅ | - |
| **derna_vs_sentinel2** | - | - | - | - | - | - | - | - | - | - | ✅ | - | - | - | - | - | ✅ | - | - | - | - |
| **global** | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | ✅ |
| **landsat** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | ⏭ | ✅ | ⏭ | ⏭ | - | ✅ | ✅ | ✅ | - |
| **rasterio_rgb** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | ⏭ | ✅ | ⏭ | ⏭ | - | ✅ | ✅ | ✅ | - |
| **sentinel2** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | ⏭ | ✅ | ⏭ | ⏭ | - | ✅ | ✅ | ✅ | - |
| **sentinel2_vs_landsat** | - | - | - | - | - | - | - | - | - | - | ✅ | - | - | - | - | - | ✅ | - | - | - | - |
| **trento** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | ⏭ | ✅ | ⏭ | ⏭ | - | ✅ | ✅ | ✅ | - |
| **trento_vs_rasterio** | - | - | - | - | - | - | - | - | - | - | ✅ | - | - | - | - | - | ✅ | - | - | - | - |

---

## Detalhes por Dataset


### dem_90m

| Caso de Uso | Status | Detalhes |
|---|---|---|
| UC-001 | ✅ PASS | ID=47 |
| UC-002 | ✅ PASS | 43 projetos em andamento |
| UC-005-ExG | ⏭ SKIP | DSM tem apenas 1 banda (sem RGB) |
| UC-005-GLI | ⏭ SKIP | DSM tem apenas 1 banda (sem RGB) |
| UC-005-TGI | ⏭ SKIP | DSM tem apenas 1 banda (sem RGB) |
| UC-005-VARI | ⏭ SKIP | DSM tem apenas 1 banda (sem RGB) |
| UC-006-Aspect | ✅ PASS |  |
| UC-006-Slope | ✅ PASS |  |
| UC-007-Contours | ✅ PASS |  |
| UC-008-Hillshade | ✅ PASS |  |
| UC-010-Segment | ⏭ SKIP | DSM tem apenas 1 banda |
| UC-011-Streams | ⏭ SKIP | Operacao lenta em DEMs reais; validado em dataset Serra da Moeda |
| UC-012-Volume | ✅ PASS | vol_total=160,331,592,293,781m3 |
| UC-013-AnnotPoly | ⏭ SKIP | no ortomapa_id |
| UC-014-AnnotPoint | ⏭ SKIP | no ortomapa_id |
| UC-019-Voo | ✅ PASS |  |
| UC-020-Seg7 | ⏭ SKIP | DSM tem apenas 1 banda |
| UC-STATS | ✅ PASS | 1 bands analyzed |

### dem_small

| Caso de Uso | Status | Detalhes |
|---|---|---|
| UC-001 | ✅ PASS | ID=46 |
| UC-002 | ✅ PASS | 42 projetos em andamento |
| UC-005-ExG | ⏭ SKIP | DSM tem apenas 1 banda (sem RGB) |
| UC-005-GLI | ⏭ SKIP | DSM tem apenas 1 banda (sem RGB) |
| UC-005-TGI | ⏭ SKIP | DSM tem apenas 1 banda (sem RGB) |
| UC-005-VARI | ⏭ SKIP | DSM tem apenas 1 banda (sem RGB) |
| UC-006-Aspect | ✅ PASS |  |
| UC-006-Slope | ✅ PASS |  |
| UC-007-Contours | ✅ PASS |  |
| UC-008-Hillshade | ✅ PASS |  |
| UC-010-Segment | ⏭ SKIP | DSM tem apenas 1 banda |
| UC-011-Streams | ⏭ SKIP | Operacao lenta em DEMs reais; validado em dataset Serra da Moeda |
| UC-012-Volume | ✅ PASS | vol_total=379,031,308,248m3 |
| UC-013-AnnotPoly | ⏭ SKIP | no ortomapa_id |
| UC-014-AnnotPoint | ⏭ SKIP | no ortomapa_id |
| UC-019-Voo | ✅ PASS |  |
| UC-020-Seg7 | ⏭ SKIP | DSM tem apenas 1 banda |
| UC-STATS | ✅ PASS | 1 bands analyzed |

### derna

| Caso de Uso | Status | Detalhes |
|---|---|---|
| UC-001 | ✅ PASS | ID=43 |
| UC-002 | ✅ PASS | 39 projetos em andamento |
| UC-005-ExG | ✅ PASS |  |
| UC-005-GLI | ✅ PASS |  |
| UC-005-TGI | ✅ PASS |  |
| UC-005-VARI | ✅ PASS | 15154 KB |
| UC-006-Aspect | ✅ PASS |  |
| UC-006-Slope | ✅ PASS |  |
| UC-007-Contours | ✅ PASS |  |
| UC-008-Hillshade | ✅ PASS |  |
| UC-010-Segment | ✅ PASS | 5 clusters |
| UC-011-Streams | ⏭ SKIP | Operacao lenta em DEMs reais; validado em dataset Serra da Moeda |
| UC-012-Volume | ✅ PASS | vol_total=379,031,308,248m3 |
| UC-013-AnnotPoly | ⏭ SKIP | no ortomapa_id |
| UC-014-AnnotPoint | ⏭ SKIP | no ortomapa_id |
| UC-019-Voo | ✅ PASS |  |
| UC-020-Seg7 | ✅ PASS |  |
| UC-STATS | ✅ PASS | 3 bands analyzed |

### derna_vs_sentinel2

| Caso de Uso | Status | Detalhes |
|---|---|---|
| UC-009-Change | ✅ PASS | 93.44% changed |
| UC-017-Compare | ✅ PASS |  |

### global

| Caso de Uso | Status | Detalhes |
|---|---|---|
| UC-UI | ✅ PASS | screenshot=global_UC-UI_interface_try1.png, 30 tiles, try 1 |

### landsat

| Caso de Uso | Status | Detalhes |
|---|---|---|
| UC-001 | ✅ PASS | ID=45 |
| UC-002 | ✅ PASS | 41 projetos em andamento |
| UC-005-ExG | ✅ PASS |  |
| UC-005-GLI | ✅ PASS |  |
| UC-005-TGI | ✅ PASS |  |
| UC-005-VARI | ✅ PASS | 7655 KB |
| UC-006-Aspect | ✅ PASS |  |
| UC-006-Slope | ✅ PASS |  |
| UC-007-Contours | ✅ PASS |  |
| UC-008-Hillshade | ✅ PASS |  |
| UC-010-Segment | ✅ PASS | 5 clusters |
| UC-011-Streams | ⏭ SKIP | Operacao lenta em DEMs reais; validado em dataset Serra da Moeda |
| UC-012-Volume | ✅ PASS | vol_total=379,031,308,248m3 |
| UC-013-AnnotPoly | ⏭ SKIP | no ortomapa_id |
| UC-014-AnnotPoint | ⏭ SKIP | no ortomapa_id |
| UC-019-Voo | ✅ PASS |  |
| UC-020-Seg7 | ✅ PASS |  |
| UC-STATS | ✅ PASS | 3 bands analyzed |

### rasterio_rgb

| Caso de Uso | Status | Detalhes |
|---|---|---|
| UC-001 | ✅ PASS | ID=42 |
| UC-002 | ✅ PASS | 38 projetos em andamento |
| UC-005-ExG | ✅ PASS |  |
| UC-005-GLI | ✅ PASS |  |
| UC-005-TGI | ✅ PASS |  |
| UC-005-VARI | ✅ PASS | 1056 KB |
| UC-006-Aspect | ✅ PASS |  |
| UC-006-Slope | ✅ PASS |  |
| UC-007-Contours | ✅ PASS |  |
| UC-008-Hillshade | ✅ PASS |  |
| UC-010-Segment | ✅ PASS | 5 clusters |
| UC-011-Streams | ⏭ SKIP | Operacao lenta em DEMs reais; validado em dataset Serra da Moeda |
| UC-012-Volume | ✅ PASS | vol_total=379,031,308,248m3 |
| UC-013-AnnotPoly | ⏭ SKIP | no ortomapa_id |
| UC-014-AnnotPoint | ⏭ SKIP | no ortomapa_id |
| UC-019-Voo | ✅ PASS |  |
| UC-020-Seg7 | ✅ PASS |  |
| UC-STATS | ✅ PASS | 3 bands analyzed |

### sentinel2

| Caso de Uso | Status | Detalhes |
|---|---|---|
| UC-001 | ✅ PASS | ID=44 |
| UC-002 | ✅ PASS | 40 projetos em andamento |
| UC-005-ExG | ✅ PASS |  |
| UC-005-GLI | ✅ PASS |  |
| UC-005-TGI | ✅ PASS |  |
| UC-005-VARI | ✅ PASS | 2939 KB |
| UC-006-Aspect | ✅ PASS |  |
| UC-006-Slope | ✅ PASS |  |
| UC-007-Contours | ✅ PASS |  |
| UC-008-Hillshade | ✅ PASS |  |
| UC-010-Segment | ✅ PASS | 5 clusters |
| UC-011-Streams | ⏭ SKIP | Operacao lenta em DEMs reais; validado em dataset Serra da Moeda |
| UC-012-Volume | ✅ PASS | vol_total=379,031,308,248m3 |
| UC-013-AnnotPoly | ⏭ SKIP | no ortomapa_id |
| UC-014-AnnotPoint | ⏭ SKIP | no ortomapa_id |
| UC-019-Voo | ✅ PASS |  |
| UC-020-Seg7 | ✅ PASS |  |
| UC-STATS | ✅ PASS | 3 bands analyzed |

### sentinel2_vs_landsat

| Caso de Uso | Status | Detalhes |
|---|---|---|
| UC-009-Change | ✅ PASS | 50.60% changed |
| UC-017-Compare | ✅ PASS |  |

### trento

| Caso de Uso | Status | Detalhes |
|---|---|---|
| UC-001 | ✅ PASS | ID=41 |
| UC-002 | ✅ PASS | 37 projetos em andamento |
| UC-005-ExG | ✅ PASS |  |
| UC-005-GLI | ✅ PASS |  |
| UC-005-TGI | ✅ PASS |  |
| UC-005-VARI | ✅ PASS | 59758 KB |
| UC-006-Aspect | ✅ PASS |  |
| UC-006-Slope | ✅ PASS |  |
| UC-007-Contours | ✅ PASS |  |
| UC-008-Hillshade | ✅ PASS |  |
| UC-010-Segment | ✅ PASS | 5 clusters |
| UC-011-Streams | ⏭ SKIP | Operacao lenta em DEMs reais; validado em dataset Serra da Moeda |
| UC-012-Volume | ✅ PASS | vol_total=379,031,308,248m3 |
| UC-013-AnnotPoly | ⏭ SKIP | no ortomapa_id |
| UC-014-AnnotPoint | ⏭ SKIP | no ortomapa_id |
| UC-019-Voo | ✅ PASS |  |
| UC-020-Seg7 | ✅ PASS |  |
| UC-STATS | ✅ PASS | 3 bands analyzed |

### trento_vs_rasterio

| Caso de Uso | Status | Detalhes |
|---|---|---|
| UC-009-Change | ✅ PASS | 99.91% changed |
| UC-017-Compare | ✅ PASS |  |

---

## Divergencias

**Nenhuma divergencia encontrada.**


---

## Screenshots Capturados

Total: **1 screenshots** em `runtime/screenshots_multi/`

- `global_UC-UI_interface_try1.png`


*Relatorio gerado em 2026-05-29 17:09:29*

# Correcoes Aplicadas Durante o Auto Research

**Data:** 2026-03-29

---

## Ciclo 1: Divergencias Iniciais

### COR-001: Frontend offline (porta 5176)
- **Divergencia:** DIV-001, DIV-003
- **Causa:** Processo Vite do frontend caiu entre os testes
- **Correcao:** Reiniciar `npx vite --host 0.0.0.0 --port 5176`
- **Tipo:** Infraestrutura

### COR-002: Segundo ortomapa identico ao primeiro
- **Divergencia:** DIV-002
- **Causa:** O script de criacao do GeoTIFF de teste `serra_moeda_teste_2.tif` nao salvou as modificacoes (desmatamento simulado). O `np.clip` nao estava sendo aplicado corretamente ao array.
- **Correcao:** Reescrito o script de criacao do segundo ortomapa com:
  - Desmatamento simulado na regiao NE (pixels 600-800 x 200-400)
  - Reducao de verde (-80), aumento de vermelho (+50), reducao de azul (-20)
  - Ruido aleatorio de +-5 em todos os pixels
  - Resultado: 3.1% de pixels com diferenca > 30 (threshold padrao)
- **Arquivo:** `data/ortomapas/serra_moeda_teste_2.tif`
- **Tipo:** Dados de teste

---

## Ciclo 2: Re-execucao

Apos correcoes, **17/17 testes APROVADOS** com **0 divergencias**.

---

## Correcoes de Ciclos Anteriores (ja aplicadas antes do auto research)

| ID | Severidade | Descricao | Arquivo |
|---|---|---|---|
| P04 | ALTA | Upload URL errada em client.js | frontend/src/api/client.js |
| P09 | ALTA | DrawTools campos incompativeis | frontend/src/components/DrawTools.vue |
| P12 | ALTA | SQL duplicado no INSERT upload | backend/routers/ortomapas.py |
| P03 | MEDIA | Sem UI para voos | frontend/src/components/VoosList.vue (novo) |
| P07 | MEDIA | Filtro projeto_id em analises | backend/routers/analises.py |
| P08 | MEDIA | Queue task em AnalysisForm | frontend/src/components/AnalysisForm.vue |
| P10 | MEDIA | Filtro projeto_id em anotacoes | backend/routers/anotacoes.py |
| VOOS | MEDIA | INSERT voos colunas erradas | backend/routers/voos.py |
| PATH | MEDIA | Resolucao de paths inconsistente | backend/routers/tools.py |

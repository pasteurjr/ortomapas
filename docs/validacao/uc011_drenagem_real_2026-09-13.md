# Validação real UC-011 - Rede de drenagem

**Data:** 13/09/2026  03:09 (America/Sao_Paulo)  
**Caso de uso:** UC-011 - Extrair rede de drenagem a partir de um DTM  
**Resultado:** Aprovado no cenário principal e nos cenários de validação de entrada

## Dados utilizados

- DTM real produzido pelo WebODM/NodeODM: `ortomapas/odm_2_dtm.tif` (produto 6).
- Backend Ortomapas: `POST http://127.0.0.1:8890/api/tools/hydrology/streams`.
- Parâmetros: `threshold=100`, `output_name=real_streams_validation`.
- A chamada foi feita por HTTP contra o serviço em execução, sem dados simulados ou mocks.

## Execução e evidências

1. O backend recebeu o caminho do DTM e o limiar de acumulação.
2. O pipeline executou preenchimento de depressões, direção de fluxo, acumulação e extração.
3. A resposta HTTP foi `200 OK` em aproximadamente **2,0 s**.
4. O arquivo `data/analises/real_streams_validation.geojson` foi criado com **364.943 bytes**.
5. A leitura posterior do arquivo confirmou `FeatureCollection` com **1.173 feições**, todas com geometria `Polygon`.

## Conclusão

O cenário principal de UC-011 está implementado e demonstrado com dados reais de fotogrametria. Os cenários de entrada também foram verificados: DTM inexistente retorna `404 Not Found` e limiares `0` ou negativos retornam `422 Unprocessable Entity`. Permanece como trabalho de validação a captura visual Playwright da camada no mapa e o caso de raster sem dados válidos.

## Cenários alternativos executados

| Cenário | Entrada | Resultado observado |
|---|---|---|
| DTM ausente | `does-not-exist.tif` | HTTP `404` |
| Limiar zero | `threshold=0` | HTTP `422` |
| Limiar negativo | `threshold=-1` | HTTP `422` |

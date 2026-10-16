# Evidências Playwright - Fase 7

**Status:** `passed`
**Projeto:** Guarajuba - Condomínio Paraíso (Demonstração)

| Caso | Resultado | Evidência |
|---|---|---|
| F7-01 - Login, projeto Guarajuba e editor; mapa enquadrado no bbox do projeto | passed | ![F7-01](./01_editor_guarajuba.png) |
| F7-02 - AOI desenhada junto ao Condomínio Paraíso, exclusão, takeoff e parâmetros salvos no PostGIS | passed | ![F7-02](./02_aoi_exclusao_takeoff.png) |
| F7-03 - Grid deriva footprint e espaçamentos dos overlaps; rota contorna exclusao | passed | ![F7-03](./03_cobertura_grid.png) |
| F7-04 - Validador aprova geometrias e verifica autonomia de cada bloco | passed | ![F7-04](./04_validacao_rota.png) |
| F7-05 - Reabertura restaura parâmetros, AOI, exclusão, takeoff e waypoints persistidos | passed | ![F7-05](./05_missao_reaberta.png) |
| F7-06 - Alteração invalida cobertura e exportação; salvar após reabrir preserva a contagem da rota | passed | ![F7-06](./06_cobertura_invalidada.png) |
| F7-07 - API bloqueia validação até regenerar o grid após mudança de altitude | passed | ![F7-07](./07_bloqueio_cobertura_antiga.png) |
| F7-08 - Novo grid é persistido e validado; cobertura deixa de estar obsoleta | passed | ![F7-08](./08_cobertura_recalculada.png) |
| F7-09 - CSV Litchi e KML baixados; contagem CSV comparada à missão persistida | passed | ![F7-09](./09_exportacoes.png) |

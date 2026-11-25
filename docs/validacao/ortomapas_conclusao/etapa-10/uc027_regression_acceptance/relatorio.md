# Etapa 10.7 — Regressão e decisão de aceite da Fase 10

**Data:** 24/11/2026  
**Resultado:** regressão automatizada aprovada nos módulos exercitados; **aceite operacional global retido** por ausência de referências científicas/tolerâncias em UCs específicos.  
**Escopo:** rastreabilidade dos UCs auditados na Fase 10, testes automatizados e revisão das evidências visuais novas.  
**Chamadas ao LLM:** zero.

## Regressão executada

Foram executados 13 módulos de teste que cobrem hidrologia, fila, terreno/AOI, métricas, tiles, mudança, volume, classificação, persistência de produtos e autorização por projeto:

```text
tests/test_hydrology_products.py
tests/test_hydrology_queue_agent.py
tests/test_terrain_tools.py
tests/test_terrain_aoi.py
tests/test_elevation_analysis.py
tests/test_metric_analysis.py
tests/test_raster_tiles.py
tests/test_change_detection.py
tests/test_elevation_change.py
tests/test_volume_aoi.py
tests/test_vegetation_classification.py
tests/test_analysis_products.py
tests/test_project_membership_auth.py
```

**Obtido:** 101 testes passaram em 2,00 s; nenhum falhou. O pytest registrou 230 avisos, principalmente depreciações de APIs Rasterio/Affine e Shapely; eles não causaram falha neste conjunto. O comando exato e a saída estão documentados no manifesto `regression_manifest.json`.

### Esperado versus obtido

| Critério | Esperado | Obtido | Estado |
|---|---|---|---|
| Regressão dos módulos geoespaciais exercitados | Todos os testes selecionados passam | 101 passaram; 0 falharam | Aprovado neste escopo |
| UC-011 visual e persistência | Duas tarefas reais concluídas, mapa/exportações acessíveis, sem erro de browser | #174 rede D8 e #175 bacia concluídas; GeoJSON/KML; 25 tiles HTTP 200; zero page errors | Fluxo funcional aprovado; validação científica parcial |
| UC-026 API e produto real | Indicador sem promessa de acurácia e metadados coerentes com arquivos | API/tela repetidas; ortos/DSM/DTM e LAZ coerentes; nenhum erro JS/console | Auditoria de completude aprovada; acurácia externa parcial |
| UC-009 mudança entre campanhas | Comparação funcional com duas campanhas; não afirmar mudança física sem verdade de campo | Etapa 10.3 preserva o resultado de duas campanhas Aklavik; sem rótulos de campo e controle sazonal | Parcial, sem nova execução destrutiva nesta regressão |
| UC-010 classificação | K-Means RGB reproduzível; não inferir classes sem rótulos | Etapa 10.4 preserva as duas execuções reproduzíveis e o fluxo UI; sem máscara semântica independente | Parcial semanticamente |
| UC-020 fila espacial | Execução persistida e renderizada no escopo documentado | Cobertura funcional de mudança e volume aprovada na etapa 10.2 | Aprovado para o escopo da fila; não significa aceite de qualidade científica |
| UC-024 recuperação NodeODM | Reenvio real e preservação da origem | Etapa 10.1 documenta a tarefa real recuperada e produtos importados | Aprovado no cenário específico; não prova retomada por checkpoint intermediário |
| UC-029 reprocessar/comparar | Linhagem e comparação funcional preservadas | Etapa 9.9 documenta #21/#24 e preservação do original | Aprovado funcionalmente; sem inferência de acurácia de campo |

As telas da execução recente permanecem separadas por caso: [rede de drenagem](../uc011_hydrology/04_drenagem_resultado_mapa.png), [bacia](../uc011_hydrology/05_bacia_resultado_mapa.png), [bloqueio sem exutório](../uc011_hydrology/05_bacia_sem_exutorio_validacao.png) e [completude/limites do ODM](../uc026_accuracy/01_uc026_completude_e_limites.png). A imagem da bacia mostra a camada de elevação em cinza com o recorte azul; isso comprova que o raster aparece no mapa, não que suas bordas coincidam com uma bacia levantada em campo.

## Matriz consolidada após as três etapas

| UC | Conclusão atual | O que a evidência autoriza afirmar | Lacuna que permanece |
|---|---|---|---|
| UC-009 | Parcial | Comparação de duas campanhas independentes, saída e UI funcionam | Rótulos/verdade de campo, limiares quantitativos e controle radiométrico/sazonal |
| UC-010 | Parcial | K-Means RGB determinístico, UI, AOI e raster de saída funcionam | Classes semânticas e métricas contra referência rotulada |
| UC-011 | Parcial | D8, drenagem, bacia, fila, mapa e exportação funcionam | Várias bacias com referência co-localizada, precisão/tolerância pré-definida; benchmark atual não passa integralmente contra 3DHP |
| UC-020 | Aprovado funcionalmente no escopo da fila | Workers e resultados de mudança/volume são persistidos e exibidos | Não estender esta aprovação a LLM/Copiloto ou qualidade científica dos algoritmos |
| UC-024 | Aprovado no cenário exercitado | Recuperação por novo processamento real com fotos preservadas e importação | Retomada intermediária por checkpoint não foi demonstrada |
| UC-026 | Parcial | Completude, metadados e leitura do relatório ODM são coerentes | Checkpoints/GCP independentes, datum/CRS de referência e limites de aceitação |
| UC-029 | Aprovado funcionalmente | Linhagem, reprocessamento e comparação entre versões preservam origem | Não é validação absoluta de acurácia |

A matriz principal foi atualizada em [matriz de rastreabilidade](../../../../analise/matriz_rastreabilidade_ortomapas_fase1.md). O inventário de evidências e os resultados completos da etapa estão no [manifesto](regression_manifest.json).

## Decisão formal

**As três etapas propostas 10.5, 10.6 e 10.7 foram executadas e documentadas.** A regressão automatizada passa para o conjunto selecionado e os fluxos de interface/persistência das etapas 10.5 e 10.6 foram repetidos com dados reais do projeto. Isso não autoriza o aceite operacional global do Ortomapas: UC-009, UC-010, UC-011 e UC-026 continuam parciais para suas afirmações científicas. Não houve ponto de controle independente para erro posicional/vertical; o benchmark hidrológico tem uma única bacia e métricas inferiores ao aceite amplo; classificação/mudança não dispõem de referência rotulada apropriada.

Assim, a **Fase 10 de auditoria está encerrada**, mas o **produto não está certificado para decisões de engenharia, precisão topográfica, mudança física ou classificação semântica**. Para alterar a decisão global, é necessário obter as referências de campo/verdade de terreno e estabelecer os limites de uso antes de reexecutar as métricas. Isso é uma dependência de dados e critérios de aceite, não algo que os 101 testes unitários possam substituir.

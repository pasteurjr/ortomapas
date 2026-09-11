# Requisitos complementares: integração WebODM/NodeODM

## Motivação

Os casos de uso atuais começam com um GeoTIFF pronto (`UC-004`). A integração ODM fecha o fluxo de produção: fotos JPEG/DNG do voo -> processamento fotogramétrico -> ortomosaico, DSM/DTM, nuvem de pontos e relatório -> cadastro e visualização no Ortomapas.

O roadmap já cita WebODM, `webodm_task_id` e `processar_webodm()`, mas a função não está implementada e não há casos de uso para esse ciclo.

## Casos de uso novos

| ID | Caso de uso | Prioridade | Resultado |
|---|---|---:|---|
| UC-021 | Importar fotos de um voo | Alta | Valida formato, preserva EXIF, calcula contagem/tamanho e vincula fotos ao voo/projeto |
| UC-022 | Criar processamento ODM | Alta | Cria tarefa no NodeODM/WebODM com parâmetros, vínculo do voo e identificador externo |
| UC-023 | Acompanhar processamento | Alta | Mostra fila, progresso, etapa, tempo, mensagens e status concluído/erro/cancelado |
| UC-024 | Cancelar ou repetir processamento | Alta | Cancela tarefa ativa ou cria nova tentativa sem perder histórico |
| UC-025 | Importar produtos ODM | Alta | Baixa e registra ortofoto, DSM, DTM, nuvem de pontos e relatório, com metadados raster |
| UC-026 | Validar qualidade do processamento | Alta | Exibe GSD, CRS, extensão, imagens usadas, alertas de alinhamento e métricas do relatório |
| UC-027 | Visualizar produtos derivados | Alta | Exibe ortofoto/DSM/DTM no mapa e permite download; rejeita/normaliza CRS incompatível |
| UC-028 | Visualizar nuvem de pontos 3D | Média | Abre LAZ/PLY em visualizador 3D, com enquadramento e informação de densidade |
| UC-029 | Reprocessar com parâmetros diferentes | Média | Duplica tarefa mantendo origem, parâmetros, versão do ODM e comparação dos resultados |

## Requisitos funcionais

- **ODM-01**: o sistema deve aceitar um diretório ou múltiplas fotos JPG/TIF compatíveis e rejeitar arquivos não-imagem antes do envio.
- **ODM-02**: deve preservar os arquivos originais e o EXIF; registrar hash, nome, tamanho e contagem.
- **ODM-03**: deve enviar a tarefa de forma assíncrona e nunca bloquear a API durante o processamento.
- **ODM-04**: deve persistir `odm_task_id`, endpoint/nó, versão do ODM, parâmetros, timestamps e estado.
- **ODM-05**: deve importar automaticamente os produtos concluídos e criar registros relacionados ao voo/projeto.
- **ODM-06**: deve extrair CRS, bbox, resolução, dimensões, bandas e tamanho com rasterio/GDAL.
- **ODM-07**: deve reprojetar ou gerar tiles em EPSG:3857; ortomosaicos UTM não podem ficar transparentes no mapa.
- **ODM-08**: deve expor download dos produtos e relatório, com limpeza configurável dos temporários.
- **ODM-09**: deve registrar falhas, permitir cancelamento/reprocessamento e evitar duplicação por idempotência.
- **ODM-10**: deve limitar tamanho/quantidade, verificar espaço em disco e informar estimativa de recursos.

## Alterações nos casos existentes

- **UC-003/UC-004**: incluir produtos gerados pelo ODM e estados `aguardando_processamento`, `processando`, `disponivel`, `erro`.
- **UC-019 Registrar Voo**: incluir origem das fotos, diretório/manifesto, câmera, altitude, sobreposição e vínculo com a tarefa ODM.
- **UC-006 a UC-012**: permitir selecionar explicitamente ortofoto, DSM ou DTM importados, validando bandas e CRS.
- **UC-017 Comparar Ortomapas**: comparar produtos de voos distintos somente após normalização de CRS/resolução.
- **UC-020 Agente de IA**: disparar análise somente quando o produto requerido estiver `disponivel`; incluir métricas e relatório ODM no contexto.

## Fora do primeiro incremento

Planejamento de voo, controle do drone, autorização ANAC/DECEA/ICMBio, correção RTK/GCP avançada e processamento GPU são integrações posteriores. O primeiro incremento deve usar NodeODM CPU já validado e um voo real.

## Critério de aceite ponta a ponta

Um voo real do DJI Mini 3 deve ser importado, processado sem intervenção manual no WebODM, ter ortofoto/DSM/DTM e relatório cadastrados, aparecer no mapa reprojetado corretamente, permitir download e alimentar ao menos uma análise espacial existente.

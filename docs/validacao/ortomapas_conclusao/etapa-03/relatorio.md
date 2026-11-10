# Fase 3/8 — Fluxo fotogramétrico ponta a ponta

**Execução:** 10/11/2026<br>
**Estado:** ciclo principal aprovado; fase parcialmente concluída, com cenários de robustez pendentes.<br>
**Aplicação:** projeto temporário isolado, removido após a validação.<br>
**Dados:** conjunto público real `odm_data_aukerman-master` do repositório de teste ODM, licença CC0 1.0. O conjunto não é uma captura do usuário nem da região de Guarajuba.

## Objetivo e resultado

Foi executado no aplicativo o percurso projeto novo → voo → validação/upload das fotografias → tarefa real no NodeODM → acompanhamento → importação do catálogo → reabertura dos produtos e visualização. A tarefa terminou com sucesso; não foi mockada nem substituída por resultado pré-existente.

O upload aceitou 77 fotografias JPEG (77/77 com coordenadas GPS EXIF), total de 542.880.685 bytes. O NodeODM 2.2.4 executou ODM 3.5.6 e marcou a tarefa como concluída após **36,6 minutos**. Seis produtos reais foram importados e seus viewers abriram após um novo login e seleção do projeto.

## Esperado versus obtido

| Verificação | Esperado | Obtido | Resultado |
|---|---|---|---|
| Novo projeto e voo | Registros novos isolados e vinculados | Projeto 86 e voo 32 criados e ligados às fotos | Passou |
| Validação de entrada negativa | Rejeitar formato não aceito sem criar processamento | Arquivo `.txt`: HTTP 400; processamentos antes/depois: 0/0 | Passou |
| Imagens e georreferência | Fotos legíveis, quantidade e GPS coerentes | 77 JPEG aceitos; 77/77 com GPS EXIF; hashes SHA-256 no manifesto | Passou |
| Execução fotogramétrica | NodeODM real conclui sem erro | Tarefa `c53ba032-9fcf-42d9-9b70-e6602508993a`, estado concluído, 100%, 36,6 min | Passou |
| Importação | Orto, DSM, DTM e derivados catalogados uma vez | 6 produtos: GeoTIFF ortomosaico/DSM/DTM, relatório PDF, nuvem LAZ e GLB | Passou |
| Persistência/retomada | Reabrir produtos depois de recarga/login | Após novo login, projeto e catálogo foram reabertos e os produtos visualizados | Passou |
| Ortofoto no mapa | Tiles e cobertura aparecem no mapa | 50 tiles carregados; ortomosaico visível com base cartográfica | Passou |
| Modelo 3D | GLB real renderizado | Estado `loaded`; 264.885 triângulos e 58 materiais/texturas | Passou |
| DSM/DTM 3D | Superfícies não vazias, CRS/unidades e controles funcionais | DSM: 21.197 triângulos; DTM: 21.028; EPSG:32617; exagero vertical e wireframe responderam | Passou |
| Nuvem de pontos | Abrir e informar pontos reais | LAZ aberto; 16.123.377 pontos | Passou |
| Comparação DSM–DTM | Raster de diferença e estatísticas | Canvas 128×102; 10.437 pixels válidos; mín. −12,60 m, média 3,86 m, máx. 41,28 m | Passou |
| Qualidade | Resultado visível vinculado à tarefa | 100%, `BOM`; interface recomenda revisar o relatório ODM | Passou com ressalva semântica abaixo |
| Falha, cancelamento, idempotência e recuperação | Provar que repetição/falha não duplica tarefa e que há retomada segura | Não cobertos nesta execução | Pendente — impede aceite integral da Fase 3 |

### Produtos gerados

| Produto | Arquivo no catálogo | Formato | Tamanho do catálogo |
|---|---|---|---:|
| Ortomosaico | `odm_18_ortomosaico.tif` | GeoTIFF | 88,44 MB |
| DSM | `odm_18_dsm.tif` | GeoTIFF | 59,88 MB |
| DTM | `odm_18_dtm.tif` | GeoTIFF | 70,31 MB |
| Relatório | `odm_18_relatorio.pdf` | PDF | 15,17 MB |
| Nuvem de pontos | `odm_18_nuvem_pontos.laz` | LAZ | 57,60 MB |
| Modelo texturizado | `odm_18_modelo_3d.glb` | GLB | 44,27 MB |

O ortomosaico tem 7.419×5.922 pixels, quatro bandas, `uint8`, EPSG:32617. DSM: 7.419×5.922, `float32`, EPSG:32617, faixa observada de banda 1 de 222,51 a 272,57 m. DTM: 7.419×5.923, `float32`, EPSG:32617, faixa de banda 1 de 216,00 a 262,17 m. As extensões do DSM e DTM diferem poucos centímetros por arredondamento/resolução do raster; isso deve ser considerado ao comparar pixels. A diferença apresentada pelo sistema alinha o DTM ao DSM.

**Interpretação da qualidade:** “100% / BOM” é o indicador operacional calculado pelo catálogo para presença dos produtos principais; não representa erro vertical, acurácia absoluta ou certificação cartográfica. O próprio sistema recomenda conferir o relatório ODM. O resultado não deve ser interpretado como precisão topográfica validada.

## Roteiro executado e telas

Cada imagem é uma captura nova do navegador Playwright nesta execução, exceto 01–14, capturadas no primeiro percurso antes do teste ser interrompido por um seletor incorreto. A tarefa NodeODM continuou e concluiu; o segundo percurso retomou o projeto persistido e repetiu os viewers com seletores corrigidos. Não foram reaproveitadas capturas de uma execução anterior.

### Cena 1 — Aplicativo autenticado

Conta descartável de validação entrou pela tela de login. A credencial foi gerada para esse teste e não é registrada no relatório.

![Login na aplicação](01_aplicativo_logado.png)

### Cena 2 — Preenchimento de projeto novo

Projeto identificado como teste de dataset público, deixando explícito que não representa levantamento em Guarajuba.

![Formulário do projeto](02_novo_projeto_preenchido.png)

### Cena 3 — Projeto criado e vazio

Confirmação visual do projeto novo antes do voo e dos produtos.

![Projeto vazio](03_projeto_novo_vazio.png)

### Cena 4 — Cadastro do voo de teste

O voo foi rotulado como amostra ODM, sem afirmar que foi uma missão de drone feita pelo usuário.

![Formulário do voo](04_novo_voo_preenchido.png)

### Cena 5 — Voo associado ao projeto

Registro do voo novo no painel do projeto.

![Voo cadastrado](05_voo_cadastrado.png)

### Cena 6 — Seleção das fotografias

As 77 imagens foram selecionadas no fluxo visível. A evidência complementar de GPS e hashes está em [manifesto de entrada](manifesto_entrada.csv).

![Fotos selecionadas](06_fotos_selecionadas.png)

### Cena 7 — Rejeição de formato inválido

A chamada negativa com `.txt` recebeu HTTP 400 antes de criar tarefa ou persistir fotos; o formulário não exibiu um falso sucesso.

![Tarefa real enviada após o teste inválido](07_tarefa_nodeodm_enviada.png)

### Cena 8 — Processamento real em andamento

Registro visual da tarefa real no NodeODM. A barra atualiza por marcos; logs do serviço identificaram as etapas de reconstrução.

![Processamento em andamento](08_processamento_em_andamento.png)

### Cena 9 — Marco intermediário

A tarefa ultrapassou o primeiro marco de progresso. O progresso agregado ficou temporariamente constante durante a filtragem de 77 mapas de profundidade e depois avançou.

![Progresso acima de 25 por cento](09_progresso_25.png)

### Cena 10 — Marco de 75 por cento

O processamento avançou pela classificação da nuvem e geração dos produtos raster.

![Progresso acima de 75 por cento](10_progresso_75.png)

### Cena 11 — Conclusão no NodeODM

Estado final do serviço: concluído, 100%. A duração foi medida desde o envio.

![Tarefa concluída](11_processamento_concluido.png)

### Cena 12 — Catálogo importado

Exibição das seis saídas importadas: ortofoto, DSM, DTM, relatório, LAZ e GLB.

![Produtos importados](12_catalogo_produtos_importados.png)

### Cena 13 — Ortomosaico georreferenciado no mapa

O mosaico real foi adicionado ao mapa da aplicação e 50 tiles foram carregados. O rótulo geográfico no fundo confirma que esta amostra é de Aukerman, EUA, e não Guarajuba.

![Ortomosaico sobre mapa base](13_ortomosaico_no_mapa.png)

### Cena 14 — Modelo texturizado 3D

O GLB foi renderizado no WebGL. A cena mostra a reconstrução texturizada do terreno e os indicadores de geometria/material.

![Modelo 3D](14_modelo_texturizado_3d.png)

### Cena 15 — Superfície DSM

O DSM foi aberto como malha 3D contínua, com escala de cores de elevação, CRS EPSG:32617 e 21.197 triângulos. O teste alternou wireframe e exagero vertical 2×; a captura foi feita novamente em superfície sombreada para facilitar leitura.

![DSM 3D](15_dsm_superficie_3d.png)

### Cena 16 — Terreno DTM

O DTM gerado pelo processamento também foi aberto no viewer de terreno, com 21.028 triângulos e os mesmos controles de elevação.

![DTM 3D](16_dtm_terreno_3d.png)

### Cena 17 — Nuvem de pontos

O viewer abriu o LAS/LAZ real e informou 16.123.377 pontos. A ferramenta de nuvem oferece navegação e controles próprios.

![Nuvem de pontos 3D](17_nuvem_pontos_3d.png)

### Cena 18 — Diferença DSM–DTM

O raster compara superfície e terreno com rampa divergente, estatísticas e contagem de pixels válidos. Os valores positivos podem indicar objetos/cobertura acima do terreno; esta amostra e sua resolução não são validação de acurácia de campo.

![Diferença DSM DTM](18_diferenca_dsm_dtm.png)

### Cena 19 — Indicador de qualidade

O painel associado à tarefa mostra 100%/BOM e explicita a recomendação de revisar o relatório ODM.

![Qualidade do processamento](19_qualidade_do_processamento.png)

## Erro encontrado no roteiro e reteste

O primeiro roteiro terminou ao procurar `.dsm-surface-view`; o componente implementado usa `.surface-view`. A aplicação abriu o DSM normalmente depois da correção do seletor. O reteste também corrigiu o seletor do botão “Fechar diferença” (título acessível “Fechar diferenca”) e o botão de qualidade, que é identificado pelo atributo `title`. O script permanente foi ajustado e a execução repetida passou em DSM, DTM, nuvem, diferença e qualidade. **Não foi identificado defeito do visualizador nesta ocorrência; o defeito era no roteiro Playwright.**

## Limites e pendências da Fase 3

- Os cenários de cancelamento, falha de processamento, reenvio/recuperação de tarefa ausente e chave de idempotência não foram exercitados. Não se declara essa fase integralmente aprovada até cobrir esses cenários sem criar processamento duplicado oneroso.
- A leitura do indicador “100%” é somente operacional; precisão vertical requer pontos de controle independentes/relatório ODM e critérios de erro definidos.
- Este ensaio comprova o ciclo com imagens públicas licenciadas. Não comprova captura própria no condomínio Paraíso/Guarajuba nem precisão de campo.
- A diferença DSM–DTM foi visualizada com grade simplificada 128×102. É uma inspeção funcional visual, não substitui análise raster completa para trabalho técnico.

## Limpeza pós-execução

A conta descartável, o projeto de teste, o registro de processamento, a tarefa NodeODM, os seis produtos/arquivos e o diretório de upload foram removidos. A verificação pós-limpeza encontrou zero projeto, usuário e processamento temporários; o UUID não aparece na lista NodeODM. O manifesto preserva o resultado da limpeza, sem e-mail ou credenciais. Foram mantidos neste repositório apenas capturas, manifesto, hashes e documentação.

## Artefatos

- [Manifesto de execução e produtos](manifest.json)
- [Manifesto de hashes SHA-256 das 77 imagens](manifesto_entrada.csv)
- [Roteiro Playwright do ciclo principal](../../../../tests/e2e/playwright/acceptance_odm_novo_projeto.py)
- [Roteiro Playwright retomável para viewers](../../../../tests/e2e/playwright/continue_odm_viewers.py)
- [Rotina de limpeza restrita ao projeto temporário](../../../../scripts/cleanup_odm_acceptance.py)
- [Licença CC0 do dataset](../../../../data/odm_test/odm_data_aukerman-master/license.txt)

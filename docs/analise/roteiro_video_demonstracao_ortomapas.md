# Roteiro de demonstração em vídeo — Ortomapas

Execução Playwright: `20261009T215232Z`  
Status: **passed**  
Duração sugerida: 8 a 12 minutos, com pausas curtas para leitura das telas.

## Objetivo do vídeo

Demonstrar o produto como um operador real: autenticar, selecionar um projeto, criar dados, consultar o mapa, revisar as ferramentas de análise, conversar com o copiloto, planejar uma missão de captura, validar a segurança e exportar a missão para o Mission Hub/Litchi.

## Orientação de gravação

- Gravar em 1440×900 ou 1920×1080, mantendo o cursor visível.
- Narrar somente depois que o resultado visual aparecer; manter cada cena entre 15 e 40 segundos.
- Mostrar o painel lateral inteiro antes de entrar nos detalhes do mapa.
- Na cena Litchi, explicar que o CSV deve ser revisado no Mission Hub e que a validação de voo real depende do drone.
- Usar as capturas abaixo como storyboard e o vídeo WebM da execução como referência de timing.

## Critérios de aceite

1. O login deve bloquear o painel até a autenticação e abrir o projeto após credenciais válidas.
2. O projeto criado deve aparecer na lista e os painéis laterais devem carregar sem erro.
3. Cada aba de ferramentas deve ser acessível e exibir seus controles específicos.
4. O polígono deve aparecer no mapa e ficar disponível para o copiloto/análises.
5. A missão deve conter AOI, takeoff, waypoints, grid, simulação, validação e exportação.
6. As análises raster devem ser executadas somente quando houver ortomapa/DSM/DTM compatível carregado; nesta execução os painéis foram demonstrados, mas o projeto não tinha raster elegível.
7. O roteiro deve terminar somente com status Playwright `passed`.

## Cenas

| Cena | Tela | Ação demonstrada | Narração | Aceite | Evidência |
|---|---|---|---|---|---|
| 01_login | Login | Abrir a aplicação antes da autenticação | Começamos pelo acesso autenticado ao Ortomapas. O sistema exige usuário e senha antes de exibir os projetos e os dados geoespaciais. | Cena capturada sem erro | [01_login.png](runtime/screenshots/demonstracao_video/20261009T215232Z/01_login.png) |
| 02_painel_inicial | Painel do projeto | Selecionar o projeto de demonstração | Após o login, o usuário visualiza o projeto ativo, o mapa, as camadas, os voos, os processamentos ODM, as análises e o copiloto. | Cena capturada sem erro | [02_painel_inicial.png](runtime/screenshots/demonstracao_video/20261009T215232Z/02_painel_inicial.png) |
| 03_novo_projeto | Criação de projeto | Preencher o diálogo Novo Projeto antes de salvar | A criação de projeto registra nome, descrição e área de estudo. Este passo demonstra o cadastro persistido por usuário. | Cena capturada sem erro | [03_novo_projeto.png](runtime/screenshots/demonstracao_video/20261009T215232Z/03_novo_projeto.png) |
| 04_projeto_criado | Projeto criado | Salvar o novo projeto | O novo projeto aparece na lista lateral e pode ser selecionado para concentrar mapas, voos, análises e conversas do copiloto. | Cena capturada sem erro | [04_projeto_criado.png](runtime/screenshots/demonstracao_video/20261009T215232Z/04_projeto_criado.png) |
| 05_ferramenta_vegetacao | Vegetação | Abrir a aba Vegetação | O painel de vegetação permite calcular índices espectrais a partir do ortomapa selecionado. | Cena capturada sem erro | [05_ferramenta_vegetacao.png](runtime/screenshots/demonstracao_video/20261009T215232Z/05_ferramenta_vegetacao.png) |
| 06_ferramenta_terreno | Terreno | Abrir a aba Terreno | O painel de terreno oferece DSM, DTM, declividade, aspecto e curvas de nível. | Cena capturada sem erro | [06_ferramenta_terreno.png](runtime/screenshots/demonstracao_video/20261009T215232Z/06_ferramenta_terreno.png) |
| 07_ferramenta_classificacao | Classificação | Abrir a aba Classificação | A classificação organiza o ortomapa em classes e permite definir áreas de treinamento. | Cena capturada sem erro | [07_ferramenta_classificacao.png](runtime/screenshots/demonstracao_video/20261009T215232Z/07_ferramenta_classificacao.png) |
| 08_ferramenta_hidrologia | Hidrologia | Abrir a aba Hidrologia | A hidrologia executa análises de fluxo, acumulação e bacias a partir do DTM. | Cena capturada sem erro | [08_ferramenta_hidrologia.png](runtime/screenshots/demonstracao_video/20261009T215232Z/08_ferramenta_hidrologia.png) |
| 09_ferramenta_mudancas | Mudanças | Abrir a aba Mudanças | A comparação antes/depois evidencia alterações entre dois ortomapas. | Cena capturada sem erro | [09_ferramenta_mudancas.png](runtime/screenshots/demonstracao_video/20261009T215232Z/09_ferramenta_mudancas.png) |
| 10_ferramenta_volume | Volume | Abrir a aba Volume | A ferramenta de volume calcula corte e aterro dentro de uma geometria. | Cena capturada sem erro | [10_ferramenta_volume.png](runtime/screenshots/demonstracao_video/20261009T215232Z/10_ferramenta_volume.png) |
| 11_ferramenta_recorte | Recorte | Abrir a aba Recorte | O recorte limita o processamento a um polígono desenhado no mapa. | Cena capturada sem erro | [11_ferramenta_recorte.png](runtime/screenshots/demonstracao_video/20261009T215232Z/11_ferramenta_recorte.png) |
| 12_ferramenta_exportacao | Exportação | Abrir a aba Exportação | A exportação permite baixar camadas e resultados para uso externo. | Cena capturada sem erro | [12_ferramenta_exportacao.png](runtime/screenshots/demonstracao_video/20261009T215232Z/12_ferramenta_exportacao.png) |
| 13_geometria_desenhada | Geometria espacial | Desenhar um polígono no mapa | O usuário desenha uma área no mapa. Essa geometria pode alimentar medições, análises espaciais e o copiloto. | Cena capturada sem erro | [13_geometria_desenhada.png](runtime/screenshots/demonstracao_video/20261009T215232Z/13_geometria_desenhada.png) |
| 14_copiloto | Copiloto geoespacial | Enviar uma pergunta de área e perímetro | O copiloto recebe uma solicitação em linguagem natural, preserva a conversa por projeto e executa ferramentas espaciais quando disponíveis. | Cena capturada sem erro | [14_copiloto.png](runtime/screenshots/demonstracao_video/20261009T215232Z/14_copiloto.png) |
| 15_missao_waypoints | Waypoints e rota | Marcar AOI, takeoff e quatro waypoints | O planejador registra a área de interesse, a decolagem e uma sequência de waypoints numerados, com rota desenhada sobre o mapa. | Cena capturada sem erro | [15_missao_waypoints.png](runtime/screenshots/demonstracao_video/20261009T215232Z/15_missao_waypoints.png) |
| 16_grid_fotogrametrico | Grid fotogramétrico | Gerar a cobertura fotogramétrica | O grid calcula linhas, espaçamento, fotos e distância da missão para cobrir a área com sobreposição controlada. | Cena capturada sem erro | [16_grid_fotogrametrico.png](runtime/screenshots/demonstracao_video/20261009T215232Z/16_grid_fotogrametrico.png) |
| 17_validacao_missao | Validação e simulação | Simular, pausar e validar a missão | Antes de exportar, o sistema simula a rota e avalia geometria, altitude, velocidade, gimbal, sobreposição, imagem e autonomia. | Cena capturada sem erro | [17_validacao_missao.png](runtime/screenshots/demonstracao_video/20261009T215232Z/17_validacao_missao.png) |
| 18_exportacao_litchi | Exportação Litchi | Baixar o CSV Litchi | A missão validada pode ser exportada para CSV compatível com o Mission Hub, além de KML e GeoJSON para interoperabilidade. | Cena capturada sem erro | [18_exportacao_litchi.png](runtime/screenshots/demonstracao_video/20261009T215232Z/18_exportacao_litchi.png) |

## Encerramento sugerido

O Ortomapas centraliza o ciclo: projeto, mapa, análise, copiloto, planejamento de voo e exportação. A missão exibida foi validada automaticamente com dados simulados. Antes de uma operação, o operador deve importar o arquivo no aplicativo de voo, confirmar os parâmetros globais e realizar a checagem de segurança em campo.

## Artefatos da execução

- Resultado estruturado: [runtime/screenshots/demonstracao_video/20261009T215232Z/resultado.json](runtime/screenshots/demonstracao_video/20261009T215232Z/resultado.json)
- Vídeo bruto Playwright: consultar a pasta `runtime/screenshots/demonstracao_video/20261009T215232Z/video`.
- Relatórios técnicos: `docs/analise/validacao_fase5_missoes.md` e `docs/analise/validacao_fase6_exportacao.md`.

# Storyboard visual detalhado

Cada bloco abaixo corresponde a uma cena do vídeo. A imagem é a captura real da execução Playwright; o texto imediatamente abaixo orienta o enquadramento e a narração.

## 01_login — Login

![Captura da cena 01_login](../../runtime/screenshots/demonstracao_video/20261009T215232Z/01_login.png)

**Ação executada:** Abrir a aplicação antes da autenticação

**O que mostrar na tela:** destacar a área funcional que comprova esta etapa e manter a informação central visível durante a narração.

**Texto da narração:** Começamos pelo acesso autenticado ao Ortomapas. O sistema exige usuário e senha antes de exibir os projetos e os dados geoespaciais.

**Transição:** aguardar a tela estabilizar e seguir para a próxima cena.

## 02_painel_inicial — Painel do projeto

![Captura da cena 02_painel_inicial](../../runtime/screenshots/demonstracao_video/20261009T215232Z/02_painel_inicial.png)

**Ação executada:** Selecionar o projeto de demonstração

**O que mostrar na tela:** destacar a área funcional que comprova esta etapa e manter a informação central visível durante a narração.

**Texto da narração:** Após o login, o usuário visualiza o projeto ativo, o mapa, as camadas, os voos, os processamentos ODM, as análises e o copiloto.

**Transição:** aguardar a tela estabilizar e seguir para a próxima cena.

## 03_novo_projeto — Criação de projeto

![Captura da cena 03_novo_projeto](../../runtime/screenshots/demonstracao_video/20261009T215232Z/03_novo_projeto.png)

**Ação executada:** Preencher o diálogo Novo Projeto antes de salvar

**O que mostrar na tela:** destacar a área funcional que comprova esta etapa e manter a informação central visível durante a narração.

**Texto da narração:** A criação de projeto registra nome, descrição e área de estudo. Este passo demonstra o cadastro persistido por usuário.

**Transição:** aguardar a tela estabilizar e seguir para a próxima cena.

## 04_projeto_criado — Projeto criado

![Captura da cena 04_projeto_criado](../../runtime/screenshots/demonstracao_video/20261009T215232Z/04_projeto_criado.png)

**Ação executada:** Salvar o novo projeto

**O que mostrar na tela:** destacar a área funcional que comprova esta etapa e manter a informação central visível durante a narração.

**Texto da narração:** O novo projeto aparece na lista lateral e pode ser selecionado para concentrar mapas, voos, análises e conversas do copiloto.

**Transição:** aguardar a tela estabilizar e seguir para a próxima cena.

## 05_ferramenta_vegetacao — Vegetação

![Captura da cena 05_ferramenta_vegetacao](../../runtime/screenshots/demonstracao_video/20261009T215232Z/05_ferramenta_vegetacao.png)

**Ação executada:** Abrir a aba Vegetação

**O que mostrar na tela:** destacar a área funcional que comprova esta etapa e manter a informação central visível durante a narração.

**Texto da narração:** O painel de vegetação permite calcular índices espectrais a partir do ortomapa selecionado.

**Transição:** aguardar a tela estabilizar e seguir para a próxima cena.

## 06_ferramenta_terreno — Terreno

![Captura da cena 06_ferramenta_terreno](../../runtime/screenshots/demonstracao_video/20261009T215232Z/06_ferramenta_terreno.png)

**Ação executada:** Abrir a aba Terreno

**O que mostrar na tela:** destacar a área funcional que comprova esta etapa e manter a informação central visível durante a narração.

**Texto da narração:** O painel de terreno oferece DSM, DTM, declividade, aspecto e curvas de nível.

**Transição:** aguardar a tela estabilizar e seguir para a próxima cena.

## 07_ferramenta_classificacao — Classificação

![Captura da cena 07_ferramenta_classificacao](../../runtime/screenshots/demonstracao_video/20261009T215232Z/07_ferramenta_classificacao.png)

**Ação executada:** Abrir a aba Classificação

**O que mostrar na tela:** destacar a área funcional que comprova esta etapa e manter a informação central visível durante a narração.

**Texto da narração:** A classificação organiza o ortomapa em classes e permite definir áreas de treinamento.

**Transição:** aguardar a tela estabilizar e seguir para a próxima cena.

## 08_ferramenta_hidrologia — Hidrologia

![Captura da cena 08_ferramenta_hidrologia](../../runtime/screenshots/demonstracao_video/20261009T215232Z/08_ferramenta_hidrologia.png)

**Ação executada:** Abrir a aba Hidrologia

**O que mostrar na tela:** destacar a área funcional que comprova esta etapa e manter a informação central visível durante a narração.

**Texto da narração:** A hidrologia executa análises de fluxo, acumulação e bacias a partir do DTM.

**Transição:** aguardar a tela estabilizar e seguir para a próxima cena.

## 09_ferramenta_mudancas — Mudanças

![Captura da cena 09_ferramenta_mudancas](../../runtime/screenshots/demonstracao_video/20261009T215232Z/09_ferramenta_mudancas.png)

**Ação executada:** Abrir a aba Mudanças

**O que mostrar na tela:** destacar a área funcional que comprova esta etapa e manter a informação central visível durante a narração.

**Texto da narração:** A comparação antes/depois evidencia alterações entre dois ortomapas.

**Transição:** aguardar a tela estabilizar e seguir para a próxima cena.

## 10_ferramenta_volume — Volume

![Captura da cena 10_ferramenta_volume](../../runtime/screenshots/demonstracao_video/20261009T215232Z/10_ferramenta_volume.png)

**Ação executada:** Abrir a aba Volume

**O que mostrar na tela:** destacar a área funcional que comprova esta etapa e manter a informação central visível durante a narração.

**Texto da narração:** A ferramenta de volume calcula corte e aterro dentro de uma geometria.

**Transição:** aguardar a tela estabilizar e seguir para a próxima cena.

## 11_ferramenta_recorte — Recorte

![Captura da cena 11_ferramenta_recorte](../../runtime/screenshots/demonstracao_video/20261009T215232Z/11_ferramenta_recorte.png)

**Ação executada:** Abrir a aba Recorte

**O que mostrar na tela:** destacar a área funcional que comprova esta etapa e manter a informação central visível durante a narração.

**Texto da narração:** O recorte limita o processamento a um polígono desenhado no mapa.

**Transição:** aguardar a tela estabilizar e seguir para a próxima cena.

## 12_ferramenta_exportacao — Exportação

![Captura da cena 12_ferramenta_exportacao](../../runtime/screenshots/demonstracao_video/20261009T215232Z/12_ferramenta_exportacao.png)

**Ação executada:** Abrir a aba Exportação

**O que mostrar na tela:** destacar a área funcional que comprova esta etapa e manter a informação central visível durante a narração.

**Texto da narração:** A exportação permite baixar camadas e resultados para uso externo.

**Transição:** aguardar a tela estabilizar e seguir para a próxima cena.

## 13_geometria_desenhada — Geometria espacial

![Captura da cena 13_geometria_desenhada](../../runtime/screenshots/demonstracao_video/20261009T215232Z/13_geometria_desenhada.png)

**Ação executada:** Desenhar um polígono no mapa

**O que mostrar na tela:** destacar a área funcional que comprova esta etapa e manter a informação central visível durante a narração.

**Texto da narração:** O usuário desenha uma área no mapa. Essa geometria pode alimentar medições, análises espaciais e o copiloto.

**Transição:** aguardar a tela estabilizar e seguir para a próxima cena.

## 14_copiloto — Copiloto geoespacial

![Captura da cena 14_copiloto](../../runtime/screenshots/demonstracao_video/20261009T215232Z/14_copiloto.png)

**Ação executada:** Enviar uma pergunta de área e perímetro

**O que mostrar na tela:** destacar a área funcional que comprova esta etapa e manter a informação central visível durante a narração.

**Texto da narração:** O copiloto recebe uma solicitação em linguagem natural, preserva a conversa por projeto e executa ferramentas espaciais quando disponíveis.

**Transição:** aguardar a tela estabilizar e seguir para a próxima cena.

## 15_missao_waypoints — Waypoints e rota

![Captura da cena 15_missao_waypoints](../../runtime/screenshots/demonstracao_video/20261009T215232Z/15_missao_waypoints.png)

**Ação executada:** Marcar AOI, takeoff e quatro waypoints

**O que mostrar na tela:** destacar a área funcional que comprova esta etapa e manter a informação central visível durante a narração.

**Texto da narração:** O planejador registra a área de interesse, a decolagem e uma sequência de waypoints numerados, com rota desenhada sobre o mapa.

**Transição:** aguardar a tela estabilizar e seguir para a próxima cena.

## 16_grid_fotogrametrico — Grid fotogramétrico

![Captura da cena 16_grid_fotogrametrico](../../runtime/screenshots/demonstracao_video/20261009T215232Z/16_grid_fotogrametrico.png)

**Ação executada:** Gerar a cobertura fotogramétrica

**O que mostrar na tela:** destacar a área funcional que comprova esta etapa e manter a informação central visível durante a narração.

**Texto da narração:** O grid calcula linhas, espaçamento, fotos e distância da missão para cobrir a área com sobreposição controlada.

**Transição:** aguardar a tela estabilizar e seguir para a próxima cena.

## 17_validacao_missao — Validação e simulação

![Captura da cena 17_validacao_missao](../../runtime/screenshots/demonstracao_video/20261009T215232Z/17_validacao_missao.png)

**Ação executada:** Simular, pausar e validar a missão

**O que mostrar na tela:** destacar a área funcional que comprova esta etapa e manter a informação central visível durante a narração.

**Texto da narração:** Antes de exportar, o sistema simula a rota e avalia geometria, altitude, velocidade, gimbal, sobreposição, imagem e autonomia.

**Transição:** aguardar a tela estabilizar e seguir para a próxima cena.

## 18_exportacao_litchi — Exportação Litchi

![Captura da cena 18_exportacao_litchi](../../runtime/screenshots/demonstracao_video/20261009T215232Z/18_exportacao_litchi.png)

**Ação executada:** Baixar o CSV Litchi

**O que mostrar na tela:** destacar a área funcional que comprova esta etapa e manter a informação central visível durante a narração.

**Texto da narração:** A missão validada pode ser exportada para CSV compatível com o Mission Hub, além de KML e GeoJSON para interoperabilidade.

**Transição:** aguardar a tela estabilizar e seguir para a próxima cena.

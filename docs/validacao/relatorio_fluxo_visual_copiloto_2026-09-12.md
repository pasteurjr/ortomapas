# Relatorio de validacao visual do Copiloto

**Data:** 12/09/2026  
**Escopo:** login, selecao de projeto, desenho de recorte no Leaflet, acionamento de analise rapida e persistencia da camada.

## Ambiente

- Frontend Vite: `http://127.0.0.1:5302`
- Backend FastAPI: `http://127.0.0.1:8888`
- Banco: PostgreSQL/PostGIS em `127.0.0.1:5433`
- Navegador: Chromium via Playwright, viewport 1600x1000

## Caso validado

O teste cria um usuario e um projeto temporarios, acessa a aplicacao, seleciona o projeto, usa a ferramenta **Recorte 3D** para desenhar uma geometria e verifica se o painel do Copiloto oferece a acao **Medir area e perimetro**. Em seguida, a acao e disparada e a resposta visual e a persistencia sao conferidas pela API.

## Evidencias

### 1. Painel autenticado

![Painel autenticado](evidencias/01-painel-autenticado.png)

**Resultado:** aprovado. A aplicacao abriu apos autenticacao e exibiu mapa, projetos, ferramentas e Copiloto.

### 2. Projeto selecionado

![Projeto selecionado](evidencias/02-projeto-selecionado.png)

**Resultado:** aprovado. O projeto temporario apareceu na lista e foi selecionado.

### 3. Geometria desenhada

![Geometria desenhada](evidencias/03-geometria-desenhada.png)

**Resultado:** aprovado. O retangulo foi finalizado por arraste; o estado `selectedGeometry` foi preenchido e as acoes espaciais apareceram no Copiloto.

### 4. Resposta do Copiloto

![Resposta do Copiloto](evidencias/04-resposta-copiloto.png)

**Resposta observada:** `A area da geometria desenhada no mapa e de aproximadamente 2.813 x 10^-5 km2 e o perimetro e de aproximadamente 0.0212 km. Ferramenta: medir_geometria.`

**Resultado:** aprovado. O backend recebeu a geometria, o modelo selecionou `medir_geometria` e a resposta foi exibida no chat.

## Persistencia

A consulta autenticada a `/api/agents/layers` retornou HTTP 200 e zero camadas, comportamento esperado para `medir_geometria`, que retorna metricas e nao uma nova geometria. O endpoint de persistencia foi validado separadamente com HTTP 201/200/200 (salvar/listar/remover) e e usado para buffers e intersecoes.

## Conclusao

O fluxo visual de autenticacao, selecao de projeto, desenho no mapa, selecao automatica da ferramenta e resposta do Copiloto esta aprovado. Durante a validacao foram corrigidos dois problemas reais: serializacao JSONB das mensagens e nomes de colunas do contexto de voos no PostgreSQL.

## Proxima acao

Executar o mesmo roteiro com uma geometria de buffer ou intersecao para validar tambem a criacao, destaque e persistencia de uma camada espacial retornada pelo Copiloto.

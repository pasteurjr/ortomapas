# Plano de Testes de Aceitacao - Ortomapas

**Versao:** 1.0  
**Data:** 18/09/2026  
**Base normativa:** `docs/analise/casos_de_uso_v2.md` e `docs/analise/especificacao_funcional.md`  
**Automacao prevista:** Playwright Python (Chromium) + requests/API + verificacao PostgreSQL/PostGIS e rasterio/GDAL.

## 1. Objetivo e escopo

Este plano define os dados, pre-condicoes, entradas, passos reproduziveis, resultados de API/banco/arquivos e apresentacao visual esperada para validar os 20 casos de uso. A execucao futura deve usar ambiente isolado de teste, usuario autenticado e evidencias por etapa. Este documento e uma especificacao de testes; nao afirma que todos os testes ja foram executados nem que todos os casos parciais da interface estejam prontos.

Inclui fluxo normal, validacoes negativas essenciais, controle de acesso, persistencia, visualizacao de resultados e integracao ODM. Desempenho em escala, seguranca aprofundada e compatibilidade de navegadores devem ter planos complementares.

## 2. Principios de execucao

1. Nenhum teste destrutivo usa dados ou projetos de producao. Usar banco de teste dedicado, schema/banco efemero ou prefixo `E2E_<run_id>`; nunca apagar por ID fixo.
2. Cada execucao gera `run_id` UUID, email efemero, projeto(s), arquivos de saida e pasta propria `runtime/test-runs/<run_id>/`.
3. Preparacao e limpeza sao idempotentes. A limpeza so remove registros/arquivos criados com o `run_id`; preservar datasets existentes do usuario.
4. Toda acao de tela relevante espera a resposta de rede correspondente e verifica a UI depois; nao basta resposta HTTP isolada para aprovar UC visual.
5. Nunca gravar senha, JWT, token, URL assinada ou dado pessoal nos logs/screenshots. Redigir headers e mascarar campos secretos.
6. Screenshot antes/depois para fluxos visuais, com viewport padrao 1440x900 e uma passada responsiva 390x844 nas telas criticas.
7. Reprovar teste sem esconder falha com retry ilimitado. Retry permitido apenas para carregamento de tiles, com limite e registro da tentativa.
8. Casos parcialmente acessiveis (UC-002, UC-004, UC-015, UC-016, UC-017) devem ser marcados `BLOCKED_UI` ate os acionadores descritos na v2.0 existirem. API positiva pode ser registrada separadamente como `API_PASS`, nunca como aceite visual.

## 3. Ambiente e configuracao

| Item | Valor de teste |
|---|---|
| Frontend | `http://127.0.0.1:5176` (ou URL informada pelo ambiente) |
| API | `http://127.0.0.1:8888` |
| WebODM | `http://127.0.0.1:8020` |
| NodeODM | `http://127.0.0.1:8021` |
| Banco | PostgreSQL/PostGIS de teste; proibido apontar para banco produtivo |
| Browser | Chromium Playwright, viewport desktop + viewport mobile |
| LLM | LM Studio configurado no ambiente; guardar nome/modelo e versao sem segredo |
| Timeouts padrao | UI 15 s; API 30 s; upload 5 min; processamento ODM conforme dataset, limite configuravel |

Configuracao sensivel via variaveis/secret store: `E2E_BASE_URL`, `E2E_API_URL`, `E2E_DATABASE_URL`, `E2E_USER_PASSWORD`, `E2E_NODEODM_URL`, `E2E_LMSTUDIO_URL`. Nao inserir valores reais no repositorio.

## 4. Requisitos e rastreabilidade

| UC | Requisitos funcionais principais |
|---|---|
| UC-001 | EF-PRJ-04 |
| UC-002 | EF-PRJ-01, EF-PRJ-02 |
| UC-003 | EF-PRJ-03, EF-PRJ-07, EF-ORT-01, EF-MAP-01 |
| UC-004 | EF-ORT-04, EF-ORT-01, EF-ORT-07 |
| UC-005 | EF-VEG-01, EF-FER-01 |
| UC-006 | EF-TER-01, EF-FER-01 |
| UC-007 | EF-TER-04, EF-FER-01 |
| UC-008 | EF-TER-03, EF-FER-01 |
| UC-009 | EF-MUD-01, EF-FER-01 |
| UC-010 | EF-CLA-01, EF-FER-01 |
| UC-011 | EF-HID-02, EF-FER-01 |
| UC-012 | EF-VOL-01, EF-FER-01 |
| UC-013/014 | EF-DES-01, EF-ANO-01, EF-ANO-03 |
| UC-015/016 | EF-MED-01, EF-MED-02 |
| UC-017 | EF-COM-01, EF-MAP-01 |
| UC-018 | EF-EXP-01, EF-ANA-04, EF-ANO-06 |
| UC-019 | EF-VOO-01, EF-VOO-03, EF-VOO-05; integracao ODM |
| UC-020 | EF-ANA-03, EF-AGI-01..06; contrato do copiloto definido na v2 |

## 5. Dados de teste e fixtures

### 5.1 Dados sinteticos gerados pelo setup

Gerar por `run_id` (nao commitar saidas):

- Usuario `e2e_<run_id>@example.invalid`, senha aleatoria via secret runtime e perfil `pesquisador` ou perfil dedicado de teste.
- Projeto RGB com coordenadas de teste, descricao, bbox e status `em_andamento`.
- Projeto DEM separado para evitar misturar tipos de produto.
- Um projeto de outro usuario para verificacao de isolamento/permissao.
- GeoTIFF RGB pequeno, georreferenciado, 3 bandas UInt8, CRS metrico projetado e valores conhecidos; dimensao recomendada 256x256 para teste rapido.
- DEM/DSM pequeno, 1 banda Float32, CRS metrico, relevo sintetico conhecido (plano inclinado + depressao controlada), NoData explicito e pixel size conhecido.
- Dois rasters RGB alinhados, mesmo CRS/resolucao/extensao; o segundo altera um retangulo conhecido de pixels para deteccao de mudancas.
- Geometrias conhecidas: ponto dentro do raster; poligono quadrado de 10 m x 10 m em CRS metrico; linha de 3-4-5 m para teste de distancia.
- Arquivo GeoTIFF invalido (bytes/texto renomeados `.tif`), arquivo acima do limite configurado e arquivo fora do CRS aceito para testes negativos.

Metadados e checksums SHA-256 dos fixtures ficam em `runtime/test-runs/<run_id>/manifest.json`. Testes numericos usam tolerancia declarada por algoritmo, nunca comparacao pixel-a-pixel sem justificativa.

### 5.2 Datasets reais locais disponiveis

Preferir inicialmente amostras pequenas existentes no repositorio/maquina e validar licenca/origem antes de distribuir:

| Fixture local | Uso | Checagem no setup |
|---|---|---|
| `data/downloads/rasterio_rgb.tif` | indices/classificacao/segmentacao | bandas >=3, CRS, bounds, dimensoes |
| `data/downloads/trento_orthophoto.tif` | ortofoto RGB alternativa | leitura rasterio, CRS e tamanho |
| `data/downloads/dem_small.tif` | terreno, hidrologia, volume | banda unica, CRS e NoData |
| `data/ortomapas/odm_2_ortomosaico.tif` | produto ODM real | existencia, metadados e permissao de teste |
| `data/ortomapas/odm_2_dsm.tif`, `odm_2_dtm.tif` | terreno/ODM | CRS, dimensoes, bounds |
| `data/odm_test/aukerman.zip` | processamento integral NodeODM | validar integridade ZIP, quantidade de fotos e licenca |
| `data/odm_test/aukerman-results.zip` | importacao de resultado ODM | validar integridade ZIP e assets obrigatorios |

O setup deve procurar cada arquivo, checar `gdalinfo`/rasterio e hash. Se faltar dado, nao assumir que o link conhecido ainda existe. Baixar somente de fonte oficial/licenciada, guardar URL, data, licenca, checksum, tamanho e resposta HTTP no manifesto. Respeitar limites de rede e nao baixar varias centenas de MB automaticamente sem perfil de execucao explicitamente selecionado. Testes diarios usam fixtures sinteticos pequenos; processamento de fotos e job separado de longa duracao.

### 5.3 Dados que nao devem ser utilizados

Nao usar `data/ortomapas.db`, banco de producao, projetos de usuario, `.env`, senhas compartilhadas ou qualquer arquivo sem origem/licenca conhecida como fixture automatica. Nunca assumir IDs fixos (por exemplo projeto 3 ou produto 6).

## 6. Setup/teardown automatizavel

1. Verificar health frontend/API/PostgreSQL/PostGIS; em falha, abortar antes de criar dados.
2. Criar `run_id`; registrar versoes, URLs sem segredo, commit, browser, data/hora e dataset checksums.
3. Registrar usuario efemero pelo endpoint oficial de teste ou fixture aprovada; autenticar pela tela de Login, obter JWT somente em memoria de processo.
4. Criar dois projetos e fixtures via setup API/banco de teste; guardar IDs retornados em `context` do Playwright.
5. Fazer login pela UI para os testes de tela; verificar redirecionamento/estado autenticado.
6. Rodar os casos isolados; garantir namespace por run para caminhos de output.
7. Salvar JSON de resultados, screenshots, videos/traces apenas quando falha, console e resumo de rede redigidos.
8. Teardown: remover entidades e arquivos criados pelo run, confirmar ausencia; jamais excluir dados que nao tenham a etiqueta/run_id.

## 7. Formato de evidencias e estados

Cada caso deve registrar: `case_id`, UC, EF IDs, estado (`PASS`, `FAIL`, `BLOCKED_UI`, `BLOCKED_ENV`, `SKIP`), inicio/fim, browser, IDs dinamicos, fixtures/checksums, passos, asserts, requisicoes relevantes (metodo/rota/status sem token), resultado numerico, screenshots antes/depois e erro completo sanitizado.

Screenshots sugeridos: `CT-xxx_01_estado-inicial.png`, `CT-xxx_02_entrada.png`, `CT-xxx_03_resultado.png`, `CT-xxx_04_persistencia.png`. Anotar as areas relevantes em copia derivada; preservar captura original sem alteracao.

## 8. Casos de teste detalhados

### CT-001 - Criar projeto pela interface (UC-001)

- **Requisitos:** EF-PRJ-04. **Prioridade:** P0. **Tipo:** UI/API/DB.
- **Dados:** usuario E2E autenticado; nome `E2E <run_id> Fazenda`, descricao com texto controlado, area `Area E2E <run_id>`.
- **Passos:** 1) abrir sidebar Projetos; 2) clicar `Novo`; 3) preencher nome/descricao/area; 4) capturar tela do modal preenchido; 5) clicar `Criar` e aguardar POST `/api/projetos`; 6) aguardar modal fechar; 7) verificar item na lista; 8) GET do ID criado e conferir campos; 9) consultar DB de teste para persistencia.
- **Esperado API/DB:** HTTP 201; ID novo, dono conforme regra de autenticacao, status default documentado; exatamente um registro para nome/run_id.
- **Esperado tela:** modal com 3 campos e botoes Cancelar/Criar; apos sucesso modal fecha, projeto aparece com nome/area/status e pode ser selecionado.
- **Playwright:** seletores por role/name preferidos: `getByRole('button',{name:'Novo'})`, `getByRole('dialog')`, labels dos campos. Screenshot antes/depois.
- **Negativos:** nome vazio nao envia requisicao e mostra validacao acessivel; falha API mostra erro e nao cria item fantasma. Nota: comportamento silencioso atual do nome vazio e defeito a registrar.

### CT-002A/B - Busca e filtros (UC-002)

- **Requisitos:** EF-PRJ-01/02. **Prioridade:** P0. **Tipo:** UI/API.
- **Dados:** 3 projetos E2E: nome/area Serra e status `em_andamento`; nome/area diferente `planejado`; registro outro usuario que nao pode vazar.
- **CT-002A filtro sidebar:** autenticar; aguardar lista; preencher `Filtrar por area...` com token exclusivo; selecionar cada status. Esperado: lista e contagem correspondem a intersecao; limpar filtros restaura registros autorizados.
- **CT-002B busca toolbar:** preencher `Buscar...` por nome, descricao e area; verificar chamada `/api/projetos/search?q=...` e resultados na UI. Esperado do requisito: resultados correspondentes e vazios com estado vazio.
- **Esperado tela:** apenas itens correspondentes, sem resultados de outro usuario; filtro/status visivel e estado vazio compreensivel.
- **Estado conhecido:** filtro local da sidebar implementado. Busca superior desconectada na revisao; ate correccao, CT-002B = `BLOCKED_UI`/falha de conformidade, nao PASS.
- **Negativos:** termo vazio nao deve disparar busca invalida; busca sem resultados exibe vazio; status sem resultado nao exibe item residual.

### CT-003 - Selecionar projeto e visualizar produtos (UC-003)

- **Requisitos:** EF-PRJ-03/07, EF-ORT-01, EF-MAP-01/02/03. **P0.**
- **Dados:** projeto RGB com um ortomapa, projeto DEM com DSM/DTM; um usuario sem permissao.
- **Passos:** login; abrir seletor de projeto e selecionar RGB; verificar GET `/api/ortomapas?projeto_id=...`; clicar visibilidade do card; aguardar tiles; alternar OSM/Satellite; mover cursor e zoom; selecionar outro projeto e confirmar troca de cards/camadas.
- **Esperado:** cards pertencem apenas ao projeto escolhido; thumbnail/metadados; tiles PNG 256x256; base map alterna; coordenadas/zoom atualizam; projeto alheio nao aparece.
- **Tela:** mapa central, card e camada efetivamente visiveis, controles de base e status de coordenadas sem sobreposicao.
- **Negativos:** produto sem arquivo mostra erro/estado vazio, sem mapa quebrado; API 403 para projeto alheio; tile inexistente 404 tratado visualmente.

### CT-004A/B - Upload GeoTIFF e visualizacao (UC-004)

- **Requisitos:** EF-ORT-04/01/07. **P0.**
- **Dados:** fixture RGB valido com CRS metrico; GeoTIFF invalido; arquivo grande para limite configurado; projeto de teste.
- **CT-004A API contratual:** enviar `multipart file`, `projeto_id`, `tipo=ortomosaico`, nome; verificar HTTP 201, bounds/CRS/dimensoes/resolucao/thumbnail no retorno e registro no banco.
- **CT-004B UX obrigatorio:** pela interface encontrar acao “Adicionar/Upload GeoTIFF”; selecionar arquivo, projeto/tipo; acompanhar progresso; depois card, thumbnail e tiles no mapa.
- **Esperado tela:** nome e metadados detectados; sucesso confirmado; overlay renderizado no mapa; erro de formato/tamanho explicado sem registro parcial.
- **Estado conhecido:** endpoint existe, controle de upload GeoTIFF na interface ausente. CT-004A pode ser `API_PASS`; CT-004B permanece `BLOCKED_UI` ate entrega.
- **Negativos:** arquivo invalido, projeto inexistente/sem permissao e falha de disco nao deixam arquivo/registro orfaos.

### CT-005 - Indices de vegetacao (UC-005)

- **Requisitos:** EF-VEG-01, EF-FER-01. **P0.** **Dados:** raster RGB controlado e raster de banda unica para erro.
- **Passos UI:** selecionar projeto/produto RGB; aba `Veg`; escolher VARI; executar; aguardar resposta; capturar resultado; localizar camada/registro/arquivo; repetir TGI, ExG, GLI.
- **Esperado:** quatro saidas distintas; raster valido, dimensao/CRS preservados; estatisticas finitas e coerentes com formula/fixture; camada aparece e pode ser ligada/desligada; status de analise atualizado.
- **Tela:** aba selecionada, indice usado, loading e resultado estatistico legiveis; camada no mapa com legenda/contraste quando suportado.
- **Negativos:** raster com menos de 3 bandas deve produzir erro visivel, sem arquivo falso; cancelamento/repeticao nao duplica saidas silenciosamente.

### CT-006 - Declividade e aspecto (UC-006)

- **Requisitos:** EF-TER-01/02. **P1.** **Dados:** DEM de plano inclinado conhecido e NoData controlado.
- **Passos:** aba Terreno, produto DSM/DTM, escolher Slope, executar; repetir Aspect; validar saida pelo GDAL/rasterio e associacao ao projeto.
- **Esperado:** arquivos com mesmo grid/CRS; slope em graus dentro da tolerancia definida; aspect na faixa angular documentada; NoData mantido.
- **Tela:** loading, conclusao, nome de analise/resultado e camada visivel/removivel.
- **Negativos:** produto RGB nao habilita selecao como DEM; NoData excessivo gera aviso/erro, nao valores infinitos.

### CT-007 - Curvas de nivel (UC-007)

- **Requisitos:** EF-TER-04. **P1.** **Dados:** DEM com gradiente conhecido; intervalo 10 m e intervalo invalido 0.
- **Passos:** Terreno -> Curvas; selecionar DEM, intervalo 10; executar; validar GeoJSON/feature count, geometrias LineString e propriedades de elevacao; ligar camada.
- **Esperado:** feicoes nao vazias, elevations com espacamento proximo ao intervalo; CRS documentado; camada aparece no mapa.
- **Negativos:** intervalo <=0 rejeitado com mensagem; DEM plano pode retornar zero feicoes com estado explicativo.

### CT-008 - Hillshade (UC-008)

- **Requisitos:** EF-TER-03. **P1.** **Dados:** DEM conhecido; azimute 315 e altitude 45 (mais limites invalidos).
- **Passos:** selecionar DEM e Hillshade; preencher parametros se expostos; executar; validar raster e camada.
- **Esperado:** saida nao constante para relevo variado, NoData preservado, parametros gravados e imagem visivel.
- **Negativos:** azimute/altitude fora de faixa bloqueados ou normalizados conforme regra explicitada.

### CT-009 - Mudancas entre datas (UC-009)

- **Requisitos:** EF-MUD-01. **P0.** **Dados:** raster A e B alinhados com bloco deliberadamente alterado; um raster desalinhado para negativo.
- **Passos:** aba Mudancas; selecionar Antes/Depois; ajustar limiar; executar; validar percentual conhecido e raster; observar camada/resultado.
- **Esperado:** mudanca maior que zero e aproximadamente a area alterada da fixture; pares/timestamp identificados; resultado reproduzivel dentro de tolerancia.
- **Tela:** dois produtos distintos, slider/limiar, indicador de progresso e resultado com percentual.
- **Negativos:** selecionar mesmo raster gera 0%/aviso; grids/CRS incompatíveis devem reprojetar explicitamente ou recusar com mensagem, nao comparar pixel sem alinhamento.

### CT-010 - Classificacao KMeans (UC-010)

- **Requisitos:** EF-CLA-01. **P0.** **Dados:** RGB sintetico em 3 regioes/classes de cor conhecidas; `k=3` e `k=0` para negativo.
- **Passos:** aba Classificacao; selecionar ortomapa, KMeans e numero de classes; classificar; validar GeoTIFF, contagem de clusters, histograma/proporcoes e camada.
- **Esperado:** tres classes nao vazias (quando fixture permite), proporcoes somam 100% com tolerancia; artefato de saida catalogado.
- **Negativos:** K fora de faixa e raster de uma banda com requisito RGB produzem validacao explicita.

### CT-011 - Hidrologia/rede de drenagem (UC-011)

- **Requisitos:** EF-HID-02 (EF-HID-01 como extensao se watershed for incluida). **P1.** **Dados:** DEM pequeno com talvegue controlado; DEM real `dem_small.tif` ou DTM ODM em job lento separado.
- **Passos:** aba Hidrologia; escolher DTM, `streams`, limiar conhecido; executar; validar GeoJSON/raster; ligar camada e inspecionar geometrias.
- **Esperado:** FeatureCollection/resultado valido, feicoes dentro do bounds, contagem positiva para fixture de talvegue; tempo e limiar registrados.
- **Negativos:** limiar zero/negativo validado; CRS desconhecido/DEM plano gera resultado vazio com explicacao.
- **Performance:** dataset real grande em suite nightly, timeout parametrizado; nunca travar browser sem feedback.

### CT-012 - Volume por cota (UC-012)

- **Requisitos:** EF-VOL-01. **P1.** **Dados:** raster 10x10 com pixel de 1 m e elevacoes conhecidas; cotas que resultem em volumes conhecidos positivo/negativo.
- **Passos:** aba Volume; selecionar DSM; informar cota; calcular; comparar volume e area com calculo analitico da fixture.
- **Esperado:** unidade m3/m2, volume acima/abaixo separado e dentro da tolerancia; nenhum resultado nao finito.
- **Tela:** cota exibida, cards/linhas para volumes e camada se prevista.
- **Negativos:** cota vazia, texto, CRS angular ou pixel size nao metrico deve alertar ou aplicar transformacao correta documentada.

### CT-013 - Anotacao poligonal (UC-013)

- **Requisitos:** EF-DES-01, EF-ANO-03/01. **P0.** **Dados:** ortomapa e poligono quadrado conhecido dentro da extensao; categoria vegetacao, rotulo `E2E poligono <run_id>`.
- **Passos UI:** clicar ferramenta Poligono; desenhar vertices no mapa; preencher categoria/rotulo/descricao; salvar; verificar POST, lista, camada GeoJSON e banco.
- **Esperado:** geometria valida/persistida, centroide/area se calculados coerentes, popup e cor por categoria; apagar no teardown.
- **Negativos:** fechar/cancelar formulario nao cria; geometria invalida ou sem projeto/produto e rejeitada com mensagem.

### CT-014 - Anotacao pontual (UC-014)

- **Requisitos:** EF-DES-01, EF-ANO-03/01. **P0.** **Dados:** ponto conhecido dentro do raster, categoria agua, rotulo unico.
- **Passos:** clicar ferramenta Ponto; clicar coordenada; preencher formulario; salvar; validar API/DB/popup.
- **Esperado:** um ponto na coordenada esperada, marcador/coloracao por categoria e item na lista.
- **Negativos:** cancelar nao salva; tentativa fora da area segue regra de UX documentada.

### CT-015 - Medir distancia (UC-015)

- **Requisitos:** EF-MED-01. **P1.** **Dados:** linha com pontos separados por 3-4-5 m em CRS projetado.
- **Passos planejados:** acionar ferramenta `Medir distancia`; clicar dois ou mais vertices; observar linha/markers e resultado; limpar/cancelar.
- **Esperado:** distancia em metros com arredondamento definido e polyline visivel.
- **Tela atual:** painel `MeasureTools` existe, mas nao possui acionador principal; executar verificacao de navegabilidade como primeiro assert.
- **Status:** `BLOCKED_UI` ate botao visivel ser implementado. Quando existir, executar caso funcional e responsive.

### CT-016 - Medir area (UC-016)

- **Requisitos:** EF-MED-02. **P1.** **Dados:** poligono quadrado 10x10 m em CRS projetado.
- **Passos planejados:** acionar `Medir area`; clicar 3+ vertices; fechar poligono conforme UX; ler area/perimetro; limpar.
- **Esperado:** 100 m2 (ou conversao para ha definida), poligono desenhado e resultado persistente durante modo.
- **Tela atual/status:** mesmo bloqueio de UC-015; `BLOCKED_UI` ate comando ser acessivel.

### CT-017 - Comparacao swipe/lado a lado (UC-017)

- **Requisitos:** EF-COM-01, EF-MAP-01. **P1.** **Dados:** dois ortomapas com mesma extensao/CRS e diferenca visual conhecida.
- **Passos planejados:** acionar comando Comparar; selecionar Antes/Depois; mover slider; alternar Swipe/Lado a Lado; fechar; validar tiles e alinhamento.
- **Esperado tela:** duas imagens com mesma vista/zoom; slider move separador; labels Antes/Depois; fechamento volta ao mapa principal.
- **Estado conhecido:** componente CompareView existe sem acionador na UI; teste deve confirmar nao navegabilidade e reportar `BLOCKED_UI`, nao marcar aprovado.

### CT-018A/B - Exportar camada/produto (UC-018)

- **Requisitos:** EF-EXP-01; EF-ANA-04 e EF-ANO-06 como subfluxos. **P0.** **Dados:** ortomapa e camada GeoJSON da propria execucao; formatos GeoTIFF, PNG, JPEG, KML, GeoJSON e formatos anunciados suportados.
- **Passos:** aba Exp; escolher fonte, formato e CRS; exportar; aguardar download; validar nome/extensao, assinatura do arquivo, CRS/metadados e conteudo; repetir formatos suportados.
- **Esperado tela:** controles coerentes, loading, confirmacao; arquivo baixado e nao vazio. GeoTIFF abre com rasterio; KML/GeoJSON parseiam; CRS solicitado respeitado.
- **Negativos:** fonte inexistente, formato nao suportado e CRS invalido resultam em erro visivel; sem download corrompido.

### CT-019A/B - Voo e processamento ODM (UC-019)

- **Requisitos:** EF-VOO-01/03/05, integracao ODM; parte do upload de imagens. **P0**, perfil separado `odm-smoke` e `odm-full`.
- **CT-019A CRUD leve:** abrir Novo Voo; informar data, drone, altitude, fotos, area, GSD e observacao; criar; conferir lista; excluir apenas o registro E2E.
- **CT-019B ODM smoke:** criar voo; selecionar poucas imagens licenciadas da fixture; upload; configurar opcoes pequenas/fast; iniciar; validar HTTP 202 e UUID; acompanhar progresso; importar quando concluido; validar ortomosaico/DSM/DTM/produtos e viewer.
- **CT-019C falhas:** arquivo `.txt` renomeado JPG, nenhuma imagem, NodeODM indisponivel e voo de outro projeto. Esperado: erro claro, sem produto falso; isolamento e permissao preservados.
- **Esperado tela:** dialog de processamento mostra quantidade, voo e opcoes; status/progresso atualiza; produtos importados; botoes 3D, qualidade, diferenca/relatorio aparecem conforme assets existentes.
- **Dados pesados:** Aukerman integral apenas perfil nightly/manual; primeiro validar checksum, licenca, tamanho e tempo. Reutilizar resultado pronto somente para importacao/viewer; nao declarar que isso testou novo processamento.

### CT-020A/B - Copiloto por projeto (UC-020)

- **Requisitos:** EF-ANA-03, EF-AGI-01..06 e persistencia/contexto definida na especificacao do agente. **P0.** **Dados:** projeto com produto DSM/DTM; geometrias conhecidas; LM Studio e modelo configurados. Fixture de resposta deterministica para smoke; modelo real para acceptance/nightly.
- **CT-020A conversa:** autenticar usuario A; selecionar projeto; enviar prompt de analise; verificar resposta, ferramentas executadas, thread e mensagens persistidas; recarregar; historico retorna.
- **CT-020B espacial:** prompt para area/perimetro de geometria selecionada; comparar resultado com shapely; pedir slope/volume dentro da geometria quando produto adequado existir; verificar camada GeoJSON no mapa e camada persistida.
- **CT-020C isolamento:** usuario B nao acessa thread/camadas de A; mudar projeto troca contexto; prompt sem projeto nao inventa produtos; ferramenta recusada quando input ausente.
- **Esperado tela:** mensagens do usuario/copiloto, loading, nomes de ferramentas executadas, erro compreensivel, camada resultante e historico apos reload.
- **Qualidade da resposta:** validar estrutura/fatos numericos e tool calls; nao usar julgamento subjetivo de texto como unico oracle. Registrar modelo/versao/prompt redigido.
- **Negativos:** LM Studio offline/time-out, resposta malformada, ferramenta falha e contexto de outro usuario; mensagem de erro sem stack trace/segredo.

## 9. Testes transversais obrigatorios

### CT-X01 Login/autenticacao

Credencial correta entra e armazena sessao; senha errada mostra erro sem revelar qual campo; token ausente em rota protegida retorna 401; logout/expiracao encerra sessao; screenshot nao inclui senha/token.

### CT-X02 Autorizacao e isolamento

Usuario A e B; tentativa de GET/PUT/DELETE de IDs cruzados. Esperado 403/404 conforme politica, nenhum vazamento na busca, lista, tiles, analises, threads, fotos e produtos ODM.

### CT-X03 Validacao de formularios

Obrigatorios vazios, formatos invalidos, numeros NaN/fora da faixa, coordenadas invalidas e duplo clique. Verificar mensagem, ausencia de duplicidade e estado do botao/loading.

### CT-X04 Responsividade e acessibilidade funcional

Viewport 390x844: sidebar/painel acessiveis sem sobreposicao, dialogs rolaveis, botoes alcançaveis; teclado Tab/Enter/Escape; labels acessiveis; foco visivel; tooltips para botoes icon-only.

### CT-X05 Recuperacao/rede

API indisponivel antes/depois de enviar; timeout; resposta 500/422; reconectar e atualizar. Sem dados fantasma, controles presos em loading ou perda silenciosa de contexto.

## 10. Sequencia recomendada de automacao

1. `smoke`: health, login, UC-001, UC-003, tiles, console.
2. `functional-ui`: UC-001..003, 005..014, 018..020 que tenham acionador visivel.
3. `api-contract`: UC-004 endpoint, busca endpoint e regras espaciais, mantendo separacao de UI.
4. `blocked-ui`: UC-002B/004B/015/016/017 rodam asserts de navegabilidade e falham controladamente ate entrega dos controles.
5. `negative-security`: CT-X01..X03 e negativos individuais.
6. `nightly-real-data`: datasets reais, ODM smoke/full, LM Studio real, raster grande e relatorios.
7. `teardown-and-audit`: remover apenas fixture do run, validar persistencia esperada antes de limpeza e arquivar manifesto/evidencias.

## 11. Criterios de entrada e saida

**Entrada:** versao/commit registrado; ambiente teste isolado; health verde; fixtures verificadas; credenciais injetadas; NodeODM/LLM marcados como disponiveis ou casos dependentes explicitamente bloqueados.

**Saida:** cada teste tem estado e evidencias; todos os P0 nao bloqueados passam; nenhum vazamento cross-user; arquivos raster/vetoriais validos; falhas com issue e reproducao; bloqueios de interface preservados como bloqueios; teardown auditado. Uma taxa agregada de sucesso nao pode ocultar casos `BLOCKED_UI` ou `SKIP`.

## 12. Artefatos da execucao futura

- `runtime/test-runs/<run_id>/manifest.json`
- `runtime/test-runs/<run_id>/results.json`
- `runtime/test-runs/<run_id>/report.html` e `report.pdf`
- `runtime/test-runs/<run_id>/screenshots/`
- Playwright trace/video apenas em falha, com dados sensiveis redigidos
- Lista de arquivos gerados + checksum + raster metadata
- Resumo com contagem separada `PASS`, `FAIL`, `BLOCKED_UI`, `BLOCKED_ENV`, `SKIP`

## 13. Decisoes que o executor deve respeitar

1. Suite rapida nao inicia processamento fotogrametrico de centenas de imagens.
2. Dados reais baixados precisam de fonte/licenca/checksum registrados; se rede bloqueada, marcar `BLOCKED_ENV` e seguir com fixture sintetica.
3. A interface nao pode ser considerada validada por chamadas diretas de API.
4. Nao modificar os casos de uso nem flexibilizar asserts apenas para obter PASS; divergencia deve ser documentada e encaminhada para correcao.
5. O primeiro ciclo de validacao deve executar este plano sem mutar dados atuais de producao.

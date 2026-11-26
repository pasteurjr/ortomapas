# Plano de correção das lacunas do inventário da interface

- **Data:** 25/11/2026
- **Base:** inventário visual e navegação Playwright de 24/11/2026, projeto #88.
- **Status em 26/11/2026:** Etapas 1–3 de 6 concluídas com evidências visuais; etapas 4–6 pendentes.
**Escopo:** interface web do Ortomapas. Android e simulador de drone ficam fora.

## 1. Objetivo

Corrigir os controles visíveis que não executam ações, consertar o enquadramento contextual do planejador de missões e substituir a inspeção superficial das áreas de análise e do Copiloto por validações funcionais com entradas e resultados reais. Cada etapa deve produzir comparação entre comportamento esperado e observado, capturas Playwright próprias e registro cumulativo de evidências.

O inventário foi uma navegação sem gravações. Portanto, “não demonstrado” abaixo não significa automaticamente “implementado incorretamente”: lacunas observadas no código/UI são defeitos conhecidos; fluxos que não foram executados ficam classificados como pendentes de validação.

## 2. Achados e classificação

| ID | Achado observado | Classificação | Correção/ação necessária | Prioridade |
|---|---|---|---|---|
| I-01 | Subitens da navegação lateral são exibidos como botões, mas vários não têm ação. Em `App.vue`, ações ausentes resultam em `null`. | Defeito funcional e de usabilidade | Ligar cada subitem a um painel/ação existente, ou remover o item até a tela existir. Subitens de seção devem levar ao conteúdo correspondente, com foco/estado ativo acessível. | Alta |
| I-02 | Sino de notificações e engrenagem de configurações aparecem no cabeçalho sem ação associada. | Defeito funcional | Fazer o sino abrir uma lista de tarefas/alertas com estado, data e navegação para o item; fazer a engrenagem abrir preferências reais. Se uma função não tiver escopo aprovado, retirar o controle da interface em vez de manter um botão inerte. | Alta |
| I-03 | `OrtomapCard.vue` emite `delete`, mas o uso em `App.vue` não escuta o evento. O botão de lixeira parece acionável sem excluir. | Defeito funcional | Conectar à operação de exclusão existente, pedir confirmação explícita, mostrar sucesso/erro, atualizar mapa/catálogo e tratar vínculos/uso do produto. Validar autorização no backend; não remover arquivos compartilhados por acidente. | Alta |
| I-04 | Ao abrir o Planejador a partir do projeto “Aukerman”, o mapa aparece em Brasília em vez de enquadrar a área do projeto. | Defeito de contexto espacial | Inicializar o mapa pelo extent do projeto ativo ou da missão carregada; manter um fallback explícito quando o projeto não tiver extent e nunca usar silenciosamente uma cidade sem relação. | Alta |
| I-05 | As capturas das abas de análise mostram formulários, mas não demonstram entrada, execução e produto final. | Lacuna de validação/demonstração | Executar cada análise suportada com dados compatíveis; confrontar produto no mapa, parâmetros, estatísticas, persistência e exportação com resultado esperado. | Alta |
| I-06 | O Copiloto foi capturado sem projeto e sem conversa para evitar persistência; assim, o inventário não prova o fluxo de uso. | Lacuna de validação/demonstração | Com projeto de teste autorizado, criar/retomar conversa, enviar perguntas baseadas em dados existentes, verificar resposta, ferramentas invocadas, isolamento por usuário e persistência após recarga. | Alta |
| I-07 | A navegação recolhida, subitens, cabeçalho e estados responsivos não tiveram validação dedicada de teclado/acessibilidade e retorno visual. | Lacuna de validação | Validar expandir/recolher, foco, nomes acessíveis, tooltips, viewport menor e preservação do mapa/contexto. | Média |
| I-08 | Ao selecionar Missões, o planejador era aberto por cima da área lateral, interceptando cliques nos próprios subitens. | Defeito funcional/usabilidade descoberto na Etapa 1 | Separar seleção da área Missões da abertura do planejador; abrir o planejador pelo CTA ou subitem próprio. | Alta |

## 3. Princípios de execução e segurança dos dados

1. Antes de alterar código, registrar branch/commit e estado do worktree. O worktree atual contém alterações preexistentes não relacionadas; elas devem ser preservadas e não incluídas em commits destas etapas por engano.
2. Usar projeto e conta de teste isolados quando a operação criar ou remover dados. Não excluir o ortomapa #88 nem produtos reais do usuário para testar a lixeira.
3. Para exclusão, verificar a semântica do endpoint/backend e dependências de arquivos, análises e publicações. Usar fixture descartável e comprovar o comportamento após recarga.
4. Capturas devem ser novas, identificadas por ação/resultado e não reutilizadas para representar telas diferentes. Cada imagem precisa de contexto suficiente para reconhecer projeto, ferramenta, parâmetros e saída.
5. Classificar cada validação como aprovada, reprovada ou inconclusiva. Captura de formulário, HTTP 200 ou presença de botão não prova resultado científico.
6. Atualizar o relatório incremental dentro de `docs/validacao/inventario_interface_2026-11-24/` com esperado, obtido, diferença, resultado e links para imagens. Para análises, registrar origem, CRS, parâmetros e limitações dos dados.

## 4. Etapas do plano

### Etapa 1 de 6 — Reproduzir e detalhar os defeitos de navegação e cabeçalho

**Inclui:** I-01, I-02 e baseline de I-07.

**Execução:** reproduzir cada clique com Playwright nas cinco áreas; inventariar todos os subitens; registrar destino esperado e destino atual. Confirmar quais recursos de notificações e preferências já existem no backend/estado. Para cada subitem, ligar a um painel/ação real existente ou removê-lo da navegação até a implementação correspondente. Não inventar funções de produto sem requisito.

**Aceite esperado:** nenhum item de navegação ou cabeçalho aparenta ser clicável sem produzir uma ação compreensível; navegação por clique e teclado indica corretamente a seção ativa; se sino/configurações forem removidos por falta de escopo, a captura comprova sua ausência.

**Evidências:** capturas antes/depois da barra expandida e recolhida; matriz botão → ação → tela/estado; resultado de teclado e viewport compacto.

**Execução em 26/11/2026 — concluída:** os subitens foram ligados aos painéis/ações existentes; o sino abre análises ativas e leva à área de resultados; a engrenagem sem destino foi removida; o menu Missões deixou de abrir automaticamente uma sobreposição que bloqueava seus subitens. Playwright percorreu os cinco espaços, confirmou os destinos, perfil, diálogo de importação e Planejador, verificou teclado e viewport 900×850. `npm run build` passou; `page_errors=[]` e `failed_requests=[]`. Os dados de API eram fixtures no navegador, sem gravação; portanto esta validação aprova navegação e montagem dos painéis, não operações com dados reais. [Relatório e oito capturas](../validacao/inventario_interface_2026-11-24/etapa-01/relatorio.md), [roteiro](../validacao/inventario_interface_2026-11-24/etapa-01/validar_etapa1.py), [resultado JSON](../validacao/inventario_interface_2026-11-24/etapa-01/resultado.json).

**Revisão de telas em 26/11/2026:** duas evidências tinham aparência vazia por problemas distintos. O Planejador foi capturado antes do carregamento assíncrono dos tiles; recapturado após espera, mostrou 30/30 tiles válidos. A fixture do Perfil não respondia a `/api/odm/produtos`, produzindo uma falsa mensagem de falha; após corrigir a resposta para uma lista vazia, o estado apresentado passou a ser “Nenhum DSM / DTM disponível”, coerente com o projeto fixture sem raster de elevação. O roteiro agora espera tiles decodificados antes das capturas de mapa. O gráfico de perfil continua sem ser validado porque não há DSM/DTM de teste neste cenário.

### Etapa 2 de 6 — Corrigir a exclusão de ortomapa de forma segura

**Inclui:** I-03.

**Execução:** rastrear `OrtomapCard` → `App.vue` → cliente API → rota backend → efeitos no catálogo/arquivos. Definir comportamento da exclusão conforme as relações existentes. Conectar o evento, incluir confirmação com nome do item, estados de carregamento/erro/sucesso e atualizar camadas visíveis. Exercitar a ação somente em ortomapa descartável criado para o teste; tentar acesso sem permissão com segunda conta.

**Aceite esperado:** cancelar mantém registro e arquivos; confirmar remove somente o recurso autorizado e o card/camada deixa de aparecer após recarga; erros de dependência ou permissão são explicados e não deixam estado parcial; nenhum dado do projeto #88 é apagado.

**Evidências:** diálogo de confirmação, cancelamento, exclusão confirmada, recarga e conferência API/DB/arquivos, além do teste de autorização.

**Execução em 26/11/2026 — concluída no escopo de UI e guardas da API:** conectei o botão do card ao diálogo de confirmação. A UI explica que a ação remove o registro do catálogo e mantém o arquivo raster; a interface oculta a ação de leitura. A revisão do schema encontrou cascatas de exclusão para análises, anotações, comparações temporais e tarefas de agentes, então a rota agora conta vínculos e responde HTTP 409 quando há histórico dependente, em vez de apagá-lo silenciosamente. Arquivos são mantidos conforme o comportamento existente. Playwright com fixture descartável verificou cancelar (nenhum DELETE), erro (item preservado), sucesso, estado após recarga e usuário sem edição (6/6); nenhum backend ou banco real foi chamado. Dois testes unitários com conexão simulada confirmaram bloqueio 409 sem commit quando há dependências e remoção quando não há vínculos. Build passou. Não foi feita validação de autorização contra banco real; permanece para regressão integrada/ambiente de teste. [Relatório e capturas](../validacao/inventario_interface_2026-11-24/etapa-02/relatorio.md), [roteiro Playwright](../validacao/inventario_interface_2026-11-24/etapa-02/validar_etapa2.cjs), [resultado](../validacao/inventario_interface_2026-11-24/etapa-02/resultado.json), [teste unitário](../../tests/test_ortomapa_delete_guard.py).

### Etapa 3 de 6 — Corrigir contexto geográfico do Planejador de Missão

**Inclui:** I-04.

**Execução:** localizar a origem do centro inicial do Leaflet e a sequência de carregamento do projeto/missão. Derivar o enquadramento do extent da AOI/produtos do projeto; ao abrir missão existente, usar AOI salva. Para projeto sem geometria, mostrar uma ação/aviso para enquadrar manualmente ou escolher local, sem substituir por Brasília implicitamente.

**Aceite esperado:** no projeto Aukerman, o mapa enquadra o extent de Aukerman; ao reabrir missão, AOI e waypoints permanecem no lugar correto; troca de projeto atualiza o contexto sem reaproveitar centro anterior; projeto sem extent apresenta estado vazio explicado.

**Evidências:** capturas para Aukerman, missão reaberta e projeto sem extent; teste numérico de bounds/centro comparado com AOI/GeoJSON persistido.

**Execução em 26/11/2026 — concluída e revisada visualmente:** removido o enquadramento inicial fixo em Brasília. A prioridade agora é (1) bounds válidos do projeto, (2) bounds do ortomapa mais recente, (3) centro cadastrado e (4) visão global com mensagem explícita, sem inventar localização. Ao abrir uma missão, a AOI salva volta a enquadrar o mapa; ao importar ou desenhar AOI, o estado do contexto também é atualizado. Os quatro limites geográficos são validados quanto a presença, faixa e degeneração. O rótulo do contexto fica visível no painel, em uma linha própria.

**Validação:** seis cenários Playwright passaram (0 reprovações), usando Chrome e tiles OSM carregados. O caso Aukerman usou os limites do arquivo local `data/ortomapas/aukerman_dsm_campanha_posterior_1845e1ad.tif` (GeoTIFF, 7.448 × 5.907 px, EPSG:32617); os quatro lados do retângulo UTM foram amostrados em 101 posições com `gdaltransform` para obter o envelope WGS84 usado como referência. O retorno de API foi fixture somente de leitura no navegador, preenchida com a extensão derivada desse arquivo. O cenário de missão também usou fixture, com AOI baseada no recorte controlado local. Um caso adicional com bbox inválido verificou o fallback para centro cadastrado. Não houve gravação ou alteração no banco.

| Caso | Esperado | Obtido | Resultado |
|---|---|---|---|
| Aukerman sem bbox cadastrado | enquadrar extensão do ortomapa/DSM | `project-ortomapa`; bounds visíveis `[41.30042713, -81.75881624, 41.30797098, -81.74551249]`, contendo a extensão do DSM | Aprovado |
| Projeto com bbox | dar precedência ao bbox do projeto | `project-bounds`; extensão Aukerman contida | Aprovado |
| Projeto sem extensão nem centro | não assumir Brasília; mostrar estado explicativo | `world`; centro global e mensagem “Projeto sem extensão espacial; desenhe ou importe uma AOI” | Aprovado |
| Projeto só com centro | centralizar no centro do extent do DSM Aukerman | `project-center`; centro observado (41.30419580, -81.75216248) | Aprovado |
| Bbox inválido | rejeitar e continuar para centro válido | latitude norte 95° rejeitada; contexto `project-center` | Aprovado |
| Reabrir missão | enquadrar AOI salva | `mission-aoi`; AOI salva contida nos bounds exibidos | Aprovado |

Capturas e dados: [relatório ilustrado](../validacao/inventario_interface_2026-11-24/etapa-03/relatorio.md), [resultado JSON](../validacao/inventario_interface_2026-11-24/etapa-03/resultado.json), [script Playwright](../validacao/inventario_interface_2026-11-24/etapa-03/validar_etapa3.cjs). O build de produção passou; permanece um aviso preexistente do Vite sobre o tamanho do bundle (>500 kB), sem falha de compilação.

### Etapa 4 de 6 — Validar as ferramentas de análise da interface

**Inclui:** I-05.

**Execução:** percorrer individualmente Vegetação, Terreno, Classificação, Hidrologia, Mudanças, Volume, Recorte e Exportação. Antes de cada execução, confirmar tipo/bandas/CRS/unidades requeridos. Usar datasets de validação já identificados no repositório e resultados esperados reproduzíveis. Executar pelo formulário/UI, acompanhar fila quando aplicável, abrir resultado no mapa, conferir persistência, parâmetros e exportação.

**Aceite esperado:** para cada ferramenta declarada executável, há entrada compatível, conclusão visível, produto próprio e interpretação/unidades coerentes. Entrada incompatível é bloqueada com mensagem clara. Limitações científicas já registradas (mudança RGB sazonal, classificação sem ground truth, hidrologia sem aceitação operacional, volume sem referência de campo) continuam explícitas e não recebem aprovação indevida.

**Evidências:** uma sequência de capturas própria por análise (formulário preenchido, processamento/estado final, resultado no mapa e painel de valores), manifesto com dados/CRS/parâmetros e comparação esperado × obtido. Se o custo impedir rodar todas em uma sessão, manter a etapa aberta e registrar exatamente quais ferramentas passaram, falharam ou não puderam ser executadas.

### Etapa 5 de 6 — Demonstrar o Copiloto com contexto e persistência

**Inclui:** I-06.

**Execução:** selecionar projeto de teste existente, abrir ou criar conversa, fazer perguntas determinísticas apoiadas em produtos/analises do projeto, inspecionar ferramentas usadas e IDs de resultados, recarregar e retomar a conversa. Repetir com segundo usuário para verificar isolamento. Não chamar modelo externo/local ocupado sem necessidade; registrar provedor/modelo apenas se efetivamente utilizado.

**Aceite esperado:** projeto ativo e dados consultados correspondem à resposta; ferramenta reportada foi realmente executada; conversa persiste e fica isolada por usuário; contexto ausente ou pergunta sem suporte gera resposta explícita de limite, sem inventar estatísticas.

**Evidências:** capturas da conversa, resposta completa, ferramenta/resultado relacionado, recarga/retomada e teste de isolamento; log sanitizado sem segredos.

### Etapa 6 de 6 — Regressão integrada e fechamento do inventário

**Inclui:** I-07 e regressão de I-01–I-06.

**Execução:** repetir a jornada como usuário: login, troca de projeto, navegação por cada item, abrir mapa, abrir Planejador, percorrer análises demonstradas, acessar Copiloto, usar notificações/preferências se aprovadas, e verificar exclusão somente em fixture. Repetir com barra recolhida, teclado e viewport compacto. Comparar todas as capturas com o resultado esperado e atualizar a lista de funcionalidades/limitações.

**Aceite esperado:** zero controles inertes conhecidos; nenhuma regressão nas telas principais; defeitos corrigidos têm teste reproduzível; cada item de análise/Copiloto tem estado de evidência inequívoco. O relatório distingue “interface funciona” de “algoritmo aceito operacionalmente”.

**Evidências:** relatório final com tabela de defeitos, capturas antes/depois referenciadas, execução Playwright, erros de console/rede, respostas esperadas/observadas e pendências científicas mantidas.

## 5. Ordem, dependências e estimativa de validação

```text
Etapa 1 — Navegação/cabeçalho ──┐
Etapa 2 — Exclusão segura ───────┤
Etapa 3 — Contexto de missão ────┼──> Etapa 6 — Regressão integrada/fechamento
Etapa 4 — Análises ──────────────┤
Etapa 5 — Copiloto ──────────────┘
```

As etapas 1–3 são correções de comportamento e podem ser implementadas em sequência; etapas 4–5 dependem de escolher dados/contas de validação sem alterar produção. A etapa 6 só começa depois de as correções e execuções estarem estáveis. O número total é **6 etapas**; uma etapa só conta como concluída quando houver comparação e evidência, não ao terminar o código.

## 6. Estado inicial da matriz

| ID | Estado no início | Etapa de fechamento |
|---|---|---|
| I-01 | **Corrigido e validado**: subitens levam aos destinos da interface | 6 (regressão) |
| I-02 | **Corrigido e validado**: sino abre análises ativas; engrenagem sem função removida | 6 (regressão) |
| I-03 | **Corrigido e validado para UI e proteção contra cascata**; autorização real e dependências em DB real pendem para regressão | 6 |
| I-04 | **Corrigido e validado** com 6 cenários visuais; teste contra API/banco real permanece para regressão integrada | 6 |
| I-05 | Não demonstrado no inventário; status funcional deve ser medido | 4 e 6 |
| I-06 | Não demonstrado por decisão de não persistir conversa durante inventário | 5 e 6 |
| I-07 | Parcialmente validado: teclado, nomes acessíveis, recolhimento e viewport 900×850 passaram; regressão completa segue pendente | 6 |
| I-08 | **Corrigido e validado**: selecionar Missões não cobre mais a navegação; subitem abre o Planejador | 6 (regressão) |

**Próxima etapa:** **Etapa 4 de 6 — validar as ferramentas de análise da interface**, começando por compatibilidade de entrada, formulário e resultado exibido com dados raster locais reproduzíveis.

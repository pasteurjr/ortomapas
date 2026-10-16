# Validação parcial do Copiloto: Fase 8

**Data:** 16/10/2026  
**Estado:** validação integrada aprovada; Fase 8 ainda em andamento
**Escopo desta execução:** continuidade da conversa, isolamento da thread, contexto espacial, recorte por AOI, timeout controlado e exposição das evidências no chat.

## O que mudou

- A interface envia o identificador da conversa junto da pergunta.
- O backend confere que a thread pertence ao usuário autenticado e ao projeto informado. Thread de outro usuário responde `404`; troca de projeto responde `409`.
- O backend recupera as 25 mensagens mais recentes, em ordem cronológica, sem duplicar a mensagem atual que a interface já salvou antes de enviar a pergunta ao modelo.
- O estado da thread guarda contexto espacial usado na análise. Uma geometria selecionada no mapa passa a ser contexto confiável, além do projeto, produtos e voos autorizados já carregados no backend.
- Perguntas de área/perímetro sobre a geometria selecionada executam o motor determinístico `geometry_metrics`; o resultado inclui CRS de cálculo, área em m², perímetro em m e a origem da geometria.
- Declividade, aspecto, hillshade e volume aceitam AOI GeoJSON. A janela do raster é recortada pela geometria reprojetada para o CRS do produto e pixels fora da AOI são mascarados antes das estatísticas. Raster sem CRS, geometria inadequada ou AOI sem pixels suficientes é rejeitada.
- O chat mostra ferramentas executadas e oferece uma seção expansível com resultado, origem e erro. O histórico restaura as evidências armazenadas em `copilot_messages.ferramentas`.
- O modo `Poligono` do painel de desenho agora está ligado ao handler `L.Draw.Polygon`; antes os cliques não produziam uma geometria selecionável. O botão enviar do chat também ganhou nome acessível para automação e tecnologia assistiva.

## Execução integrada real

Em 16/10/2026, às 17:05 BRT, executei o roteiro Playwright contra o frontend `127.0.0.1:18762`, API `127.0.0.1:18761`, PostgreSQL local e LM Studio local. `/health/ready` confirmou `database=true` e `lm_studio=true`; o modelo `qwen2.5-coder-32b-instruct` estava listado em `/v1/models`.

O teste autenticou a conta E2E existente, abriu o projeto **Guarajuba - Condomínio Paraíso (Demonstração)**, desenhou um polígono no mapa e enviou duas perguntas relacionadas. A primeira executou `medir_geometria`: **39.599,67 m²**, perímetro **796,66 m**, CRS de cálculo **EPSG:32724**. A resposta do Qwen apresentou aproximadamente esses valores. A segunda perguntou a unidade da medição anterior; após a correção do contexto histórico, o modelo respondeu **metros quadrados (m²)**. A API autenticada confirmou a thread `102` com quatro mensagens e a evidência `medir_geometria` persistida.

O polígono é uma área de demonstração aproximada sobre o mapa OSM; não é limite cadastral do condomínio, não foi validado em campo e não deve ser usado para decisão fundiária ou voo.

### Capturas

1. Login: ![Tela de login](copiloto_fase8_2026-10-16/live_01_login.png)
2. Projeto selecionado e mapa: ![Projeto Guarajuba no mapa](copiloto_fase8_2026-10-16/live_02_projeto.png)
3. Geometria desenhada e reconhecida pelo copiloto: ![Polígono selecionado](copiloto_fase8_2026-10-16/live_03_geometria_selecionada.png)
4. Resultado calculado e evidências expandidas: ![Medição com resultado](copiloto_fase8_2026-10-16/live_04_medicao_com_evidencia.png)
5. Continuação usando a conversa anterior: ![Retomada do contexto](copiloto_fase8_2026-10-16/live_05_retomada_contexto.png)

Resultado estruturado: [`live_result.json`](copiloto_fase8_2026-10-16/live_result.json). Script reproduzível: [`test_copilot_fase8_live.py`](../../tests/e2e/playwright/test_copilot_fase8_live.py).

## Roteiro de verificação executado

1. Retomada isolada: thread de usuário/projeto simulado, com histórico anterior e pergunta atual já persistida; o adaptador recebeu as mensagens anteriores e não duplicou a atual.
2. Medição isolada: Polygon GeoJSON de teste; `12.333,224 m²` e `444,223 m`, calculados em EPSG:32631.
3. Privacidade isolada: usuário 99 não acessou a thread do usuário 5; resposta `404` antes de qualquer chamada ao LM Studio.
4. Recorte raster: raster sintético 10 x 10 em EPSG:32623; AOI cobre 4 x 4 células. Resultado: 16 pixels válidos, média esperada, resolução de 10 m; 84 pixels externos mascarados.
5. Timeout controlado: três timeouts simulados no cliente LM Studio; o cliente terminou com erro após três tentativas, sem deixar a chamada pendurada.
6. Fluxo integrado: login, desenho de polígono, medição real, pergunta de continuação e leitura autenticada da thread persistida. Nenhum erro JavaScript foi observado.

## Resultado dos testes

- `PYTHONPATH=. pytest -q tests/test_copilot_context.py`: **4 passed**.
- `PYTHONPATH=. pytest -q tests/test_metric_analysis.py`: **9 passed**.
- `PYTHONPATH=. pytest -q tests/test_copilot_context.py tests/test_metric_analysis.py`: **13 passed**, incluindo timeout controlado.
- `FRONTEND_URL=http://127.0.0.1:18762 API_URL=http://127.0.0.1:18761/api python tests/e2e/playwright/test_copilot_fase8_live.py`: **passed**, seis verificações aprovadas e uma verificação de segunda conta ignorada porque a conta não existe; thread 102, quatro mensagens persistidas e nenhuma exceção JavaScript.
- `npm run build`: **aprovado**. O Vite repetiu o aviso já conhecido de chunk JS principal acima de 500 kB.
- `python -m compileall -q backend/routers/agents.py backend/agents/schemas.py`: **aprovado**.
- PostgreSQL e LM Studio locais: `/health/ready` respondeu `ready`, ambos os checks `true`; Qwen configurado presente em `/v1/models`.
- Uma execução ampla que incluía outros testes de integração ficou sem progresso após os testes iniciais; foi interrompida e não é contada como aprovada.

## Limites e pendências

- O fluxo principal foi validado com PostgreSQL e LM Studio reais. O timeout foi testado por simulação do transporte, não por atraso forçado do serviço real.
- O roteiro tentou usar uma segunda conta E2E já existente, mas ela não estava cadastrada; não criei outra conta e marquei esse passo como ignorado. O isolamento entre usuários segue coberto por teste unitário, faltando confirmação integrada com duas contas reais.
- O recorte de derivadas limita estatísticas aos pixels internos da AOI, mas gradientes nas bordas dependem dos vizinhos válidos remanescentes. A resolução de derivadas é amostrada até 512 px no maior lado; volume por AOI é amostrado até 2048 px. Isso é adequado para consulta exploratória e deve ser identificado como amostragem, não levantamento topográfico de precisão.
- Ainda faltam lista/criação/troca de várias conversas na interface (atualmente há uma thread ativa por usuário/projeto/browser), sumarização e memória durável em `copilot_memorias`, aprovação/execução de operações de escrita pelo agente, relatório consolidado PDF e evidência visual do timeout/erro.
- RAG continua deliberadamente fora da Fase 8.

## Conclusão

Esta entrega corrigiu lacunas que o teste real revelou: o handler Leaflet do polígono não estava conectado e a evidência numérica da resposta anterior não era incluída no contexto enviado ao modelo, causando confusão entre m² e hectares. Após as correções, o fluxo visual e real passou, incluindo persistência no PostgreSQL e retomada correta pelo LM Studio. A Fase 8 **não está concluída**: falta gerenciamento de múltiplas conversas e memória durável, teste integrado com duas contas reais, fluxo de escrita/aprovação, timeout visual e relatório consolidado previsto no escopo.

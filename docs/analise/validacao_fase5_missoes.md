# Validação da Fase 5: simulação e segurança da missão

Data da execução: 09/10/2026 05:16 UTC  
Ambiente: backend local + frontend Vite + Chromium headless via Playwright  
Escopo: missão de captura para DJI Mini 3, sem drone físico conectado.

## Objetivo

Verificar se uma missão planejada pode ser analisada antes da exportação para o aplicativo de voo. A validação cobre geometria, parâmetros de voo, sobreposição fotogramétrica, perfil de imagem e autonomia estimada. O objetivo é bloquear configurações claramente inseguras e destacar configurações que exigem revisão.

## Regras implementadas

| Regra | Resultado produzido |
|---|---|
| AOI válida | Aprova geometria válida e não vazia. |
| Mínimo de waypoints | Bloqueia missão com menos de dois pontos. |
| Waypoints na AOI | Bloqueia ponto fora do polígono de interesse. |
| Zonas de exclusão | Bloqueia ponto dentro de uma exclusão. |
| Altitude DJI Mini 3 | Simula faixa operacional de 5 a 120 m. |
| Velocidade | Simula limite de 15 m/s. |
| Gimbal | Avisa quando o ângulo não está entre -90 e 0 graus. |
| Sobreposição | Bloqueia valores abaixo de 60%; avisa abaixo do alvo recomendado. |
| Compatibilidade de imagem | Confere resolução, formato e limite simulado de 48 MP. |
| Autonomia | Estima distância, tempo de voo e reserva de bateria. |

## Cenários sintéticos executados na API

Os cenários foram criados com dados de missão controlados para exercitar os três estados possíveis. Eles não substituem um voo real nem certificam o firmware do drone.

| Cenário | Estado | Bloqueios | Avisos | Verificação |
|---|---:|---:|---:|---|
| Simulado Validação Aprovada | `aprovado` | 0 | 0 | AOI, rota, altitude, velocidade, sobreposição, imagem e autonomia coerentes. |
| Simulado Validação Aviso | `aviso` | 0 | 2 | Parâmetros abaixo do recomendado, mas ainda executáveis após revisão. |
| Simulado Validação Bloqueada | `bloqueado` | 4 | 1 | Pontos/limites incompatíveis com a missão simulada. |

## Roteiro visual Playwright

Relatório bruto: [relatorio.md](../../runtime/screenshots/edicao_waypoints_fase4/20261009T051725Z/relatorio.md)  
Resultado JSON: [resultado.json](../../runtime/screenshots/edicao_waypoints_fase4/20261009T051725Z/resultado.json)

| Etapa | Evidência | O que foi verificado |
|---|---|---|
| Waypoints manuais | [01_waypoints_manuais.png](../../runtime/screenshots/edicao_waypoints_fase4/20261009T051725Z/01_waypoints_manuais.png) | Quatro pontos numerados e rota desenhada no mapa. |
| Seleção | [02_waypoint_selecionado.png](../../runtime/screenshots/edicao_waypoints_fase4/20261009T051725Z/02_waypoint_selecionado.png) | Marcador e linha lateral sincronizados. |
| Arrastar/editar | [03_arrastar_editar.png](../../runtime/screenshots/edicao_waypoints_fase4/20261009T051725Z/03_arrastar_editar.png) | Coordenada alterada por arraste e altitude editada. |
| Operações | [04_operacoes_waypoint.png](../../runtime/screenshots/edicao_waypoints_fase4/20261009T051725Z/04_operacoes_waypoint.png) | Inserir, duplicar e excluir mantiveram a contagem esperada. |
| Simulação pausada | [05_simulacao_pausada.png](../../runtime/screenshots/edicao_waypoints_fase4/20261009T051725Z/05_simulacao_pausada.png) | Marcador de simulação avançou e respondeu a pausa. |
| Persistência | [06_edicoes_salvas.png](../../runtime/screenshots/edicao_waypoints_fase4/20261009T051725Z/06_edicoes_salvas.png) | Edição foi salva e confirmada pelo backend. |
| Relatório na tela | [07_relatorio_validacao.png](../../runtime/screenshots/edicao_waypoints_fase4/20261009T051725Z/07_relatorio_validacao.png) | Estado `bloqueado`, contadores e regras aparecem na interface. |

## Conclusão

O fluxo de pré-validação está funcional e foi demonstrado com dados simulados. A interface não permite interpretar o resultado como autorização automática de voo: um estado `aviso` requer revisão do operador e um estado `bloqueado` deve ser corrigido antes da exportação.

Ainda falta a validação de campo: importar o arquivo no aplicativo compatível com o Mini 3, conferir a aceitação dos parâmetros pelo firmware, executar voo controlado e comparar fotos/telemetria com os limites calculados. Essa etapa depende do drone, controle e aplicativo disponíveis.

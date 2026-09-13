# Validação de auditoria e observabilidade do copiloto

**Data:** 13/09/2026  
**Resultado:** Aprovado

## Execução real

Foi criado um usuário pesquisador de teste e um projeto isolado no PostgreSQL. Em seguida foi enviado o prompt **“Liste os produtos deste projeto”** para `POST /api/agents/ask`.

- Resposta HTTP: `200`.
- Latência observada: aproximadamente **4,2 s**.
- LM Studio respondeu e a ferramenta `listar_produtos` foi executada.
- O projeto sem produtos foi reportado corretamente, sem inventar dados.

## Auditoria persistida

Consulta direta ao PostgreSQL confirmou os eventos:

| Ação | Entidade | Projeto | Dados |
|---|---|---:|---|
| `copilot_ask` | `copilot` | 24 | `prompt_chars=31` |
| `copilot_tools` | `copilot` | 24 | ferramenta `listar_produtos` |

## Conclusão

O fluxo copiloto -> ferramenta -> resposta está rastreável no banco, com latência mensurável e registro das ferramentas executadas. Próxima evolução: expor métricas agregadas (latência, erros e contagem de ferramentas) em endpoint/dashboard operacional.

# Validação de cenários alternativos

**Data:** 14/09/2026  
**Resultado:** Aprovado

## Cenários executados com API e PostgreSQL reais

| Cenário | Resultado esperado | Observado |
|---|---:|---:|
| Projetos sem autenticação | 401 | **401** |
| Token JWT inválido | 401 | **401** |
| Prompt vazio no copiloto | 400 | **400** |
| DTM inexistente | 404 | **404** |
| Limiar hidrológico zero | 422 | **422** |
| Usuário sem acesso ao projeto | 403 | **403** |

Foram usados usuários de teste reais, tokens JWT emitidos pela API e projeto criado no PostgreSQL. Nenhum mock foi utilizado.

## Conclusão

Autenticação, autorização e validação de entradas estão retornando códigos HTTP coerentes e impedindo processamento indevido. O item 4/5 está concluído.

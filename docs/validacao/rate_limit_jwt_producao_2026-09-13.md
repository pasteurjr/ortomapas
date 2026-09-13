# Validação de rate limit e JWT em produção

**Data:** 13/09/2026  
**API:** `http://127.0.0.1:8892`  
**Resultado:** Aprovado

## Rate limit

Foi executada uma rajada controlada de 125 requisições `GET /health` a partir do mesmo IP.

| Status | Quantidade |
|---|---:|
| HTTP `200` | 120 |
| HTTP `429` | 5 |

O middleware bloqueou corretamente as requisições excedentes ao limite de 120 por minuto/IP.

## Segredo JWT

- Com `ENVIRONMENT=production` e segredo de teste forte (mais de 32 caracteres), a API iniciou normalmente.
- Com segredo curto (`AUTH_SECRET=short`), a inicialização foi recusada com `RuntimeError`.

## Conclusão

Os controles de limitação de requisições e tamanho mínimo do segredo JWT estão funcionando. Em produção, o segredo real deve ser fornecido por secret manager ou variável protegida, nunca versionado.

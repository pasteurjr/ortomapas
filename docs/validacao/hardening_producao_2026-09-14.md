# Hardening de produção

**Data:** 14/09/2026  
**Resultado:** Aprovado

## Controles aplicados

- Senha administrativa do Grafana fornecida por `GRAFANA_ADMIN_PASSWORD` externo; Compose falha se ausente.
- Cadastro de usuários do Grafana desativado (`GF_USERS_ALLOW_SIGN_UP=false`).
- Acesso anônimo desativado (`GF_AUTH_ANONYMOUS_ENABLED=false`).
- `AUTH_SECRET` continua exigindo pelo menos 32 caracteres em `ENVIRONMENT=production`.

## Validação real

- `docker compose config --quiet` com senha forte: aprovado.
- `AUTH_SECRET=short` em produção: inicialização rejeitada.
- Grafana `/api/health`: HTTP `200`.
- Grafana `/api/search` sem credenciais: HTTP `401`.

## Operação segura

As credenciais reais devem ser injetadas por secret manager ou ambiente protegido. O arquivo `.env` permanece ignorado pelo Git.

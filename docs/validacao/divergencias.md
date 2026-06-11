# Registro de Divergencias


## DIV-001

- **Caso de Uso:** UC-003
- **Passo:** 3
- **Esperado:** Listar ortomapas do projeto
- **Observado:** Page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:5176/
Call log:
  - navigating to "http://localhost:5176/", waiting until "networkidle"

- **Severidade:** MEDIA
- **Evidencia:** UC003_step03_erro.png

## DIV-002

- **Caso de Uso:** UC-009
- **Passo:** 2
- **Esperado:** Mudancas detectadas
- **Observado:** Nenhuma mudanca detectada (deveria haver)
- **Severidade:** MEDIA

## DIV-003

- **Caso de Uso:** UC-UI
- **Passo:** 1
- **Esperado:** UI funcional
- **Observado:** Page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:5176/
Call log:
  - navigating to "http://localhost:5176/", waiting until "networkidle"

- **Severidade:** ALTA
- **Evidencia:** UC-UI_step01_erro_geral.png
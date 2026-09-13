# Registro de Divergencias

> Reproducao direta autenticada em 13/09/2026 confirmou que os endpoints de projetos, ortomapas e voos respondem corretamente no PostgreSQL real (projeto criado/listado HTTP 200, busca HTTP 200, voo criado HTTP 201). As divergencias abaixo permanecem restritas ao script E2E e ao fluxo visual.


## DIV-001

- **Caso de Uso:** UC-001
- **Passo:** 5
- **Esperado:** Criacao sem erros
- **Observado:** 
- **Severidade:** MEDIA
- **Evidencia:** UC001_step05_erro.png

## DIV-002

- **Caso de Uso:** UC-002
- **Passo:** 1
- **Esperado:** Busca/filtro funcional
- **Observado:** 'method' object is not subscriptable
- **Severidade:** MEDIA

## DIV-003

- **Caso de Uso:** UC-003
- **Passo:** 1
- **Esperado:** Listar ortomapas do projeto
- **Observado:** 
- **Severidade:** MEDIA
- **Evidencia:** UC003_step01_erro.png

## DIV-004

- **Caso de Uso:** UC-019
- **Passo:** 2
- **Esperado:** Voo criado
- **Observado:** 
- **Severidade:** MEDIA

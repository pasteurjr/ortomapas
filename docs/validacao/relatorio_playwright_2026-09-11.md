# Relatório de Validação Playwright

**Data:** 11/09/2026 06:00  
**Frontend:** `http://127.0.0.1:5300`  
**Backend:** `http://127.0.0.1:8888`

## Cenário autenticado

1. Login realizado com usuário administrativo de teste.
2. Token persistido no `localStorage` e página recarregada.
3. Lista de projetos carregada.
4. Painel de ortomapas, voos e análises renderizado.
5. Mapa Leaflet carregado com controles de zoom e escala.
6. Painel de ferramentas de análise renderizado.

**Resultado:** aprovado.

## Verificações complementares

- `GET /health`: `200`, status `healthy`.
- `GET /api/odm/produtos?projeto_id=2`: produtos ODM listados.
- `GET /api/odm/produtos/8/points?max_points=5000`: 16.102.306 pontos totais, 5.001 amostrados.
- `GET /api/odm/produtos/5/surface?max_size=64`: grade DSM `64 x 64`, CRS `EPSG:32617`.

## Observação

A abertura automatizada do modal 3D depende de uma interação específica com a lista de processamentos concluídos. A tela autenticada e os endpoints de produtos foram validados; a próxima validação deve clicar em **Abrir 3D** e **DSM 3D** e verificar o canvas WebGL.

# Matriz de Casos de Uso

**Fonte:** `docs/analise/casos_de_uso.md`  
**Data da revisão:** 12/09/2026

| ID | Caso de uso | Implementação | Validação | Pendência principal |
|---|---|---|---|---|
| UC-001 | Criar novo projeto | Implementado | API e UI observadas | Repetir cenário de validação formal |
| UC-002 | Buscar e filtrar projetos | Implementado | UI existente | Suíte Playwright dedicada |
| UC-003 | Selecionar projeto e visualizar ortomapas | Implementado | UI e API | Suíte Playwright dedicada |
| UC-004 | Upload de GeoTIFF e visualização | Implementado | API/fluxo existente | Testar arquivo inválido e timeout |
| UC-005 | Índice de vegetação VARI | Implementado | Código e endpoint | Validar com raster multibanda real |
| UC-006 | Declividade a partir de DSM | Implementado | API e Playwright aprovados | Avaliar limiar de NoData por projeto |
| UC-007 | Curvas de nível | Implementado | Endpoint disponível | Captura visual e validação de geometria |
| UC-008 | Hillshade | Implementado | API aprovada | Captura visual no mapa |
| UC-009 | Mudanças entre ortomapas | Implementado | Backend existente | Validar com dois ortomapas reais |
| UC-010 | Classificação KMeans | Implementado | Backend existente | Validar resultado visual e métricas |
| UC-011 | Rede de drenagem | Parcialmente implementado | Formulário/endpoint | Validar processamento hidrológico real |
| UC-012 | Volume acima/abaixo de referência | Implementado | API e Copiloto aprovados | Exigir cota explícita em prompts ambíguos |
| UC-013 | Anotação poligonal | Implementado | UI existente | Suíte Playwright dedicada |
| UC-014 | Anotação pontual | Implementado | UI existente | Suíte Playwright dedicada |
| UC-015 | Medir distância | Implementado | Código existente | Validar unidade e arredondamento |
| UC-016 | Medir área | Implementado | Código existente | Validar CRS métrico para áreas oficiais |
| UC-017 | Comparar ortomapas por swipe | Implementado | Código existente | Captura visual dedicada |
| UC-018 | Exportar ortomapa | Implementado | Exportações testadas | Validar metadados CRS nos arquivos |
| UC-019 | Registrar voo de drone | Implementado | API/UI existentes | Validar todos os campos obrigatórios |
| UC-020 | Disparar análise via agente IA | Implementado | Playwright/API aprovados | Completar suíte de intenções e ferramentas |

## Resumo

- **Implementados:** 19
- **Parcialmente implementados:** 1 (UC-011)
- **Pendentes de validação formal:** 16 cenários, principalmente casos alternativos e de exceção.
- **Copiloto:** núcleo operacional implementado; ferramentas de geometria e relevo testadas com LM Studio/Qwen e PostgreSQL reais.

## Critério para considerar pronto

Um caso só será marcado como concluído operacionalmente quando tiver implementação, teste principal, teste de erro e evidência registrada. A matriz deve ser atualizada após cada execução, sem transformar código existente em aprovação automática.

## Próximo lote de fechamento

1. Validar UC-007, UC-009, UC-010 e UC-011 com dados reais.
2. Executar cenários de exceção de UC-004, UC-005 e UC-006.
3. Criar uma suíte Playwright cobrindo os 20 casos e seus fluxos alternativos críticos.

# Plano de Implementação dos Agentes Ortomapas

**Versão:** 1.0  
**Data:** 11/09/2026  
**Status:** aprovado para detalhamento técnico

## 1. Objetivo

Implementar o Ortomapas Copilot com contexto, memória, RAG e ferramentas geoespaciais controladas, usando Qwen 2.5 32B Coder servido pelo LM Studio local.

## 2. Ordem de execução

### Fase 0 — Preparação e contratos

- confirmar modelo exposto em `/v1/models`;
- criar configuração `LLM_BASE_URL`, `LLM_MODEL` e limites de tempo;
- definir schemas JSON de entrada e saída;
- definir catálogo de ferramentas e permissões;
- criar tabela de auditoria de prompts e chamadas.

**Aceite:** uma chamada de teste ao LM Studio retorna JSON validado sem acessar dados reais.

### Fase 1 — Adaptador LM Studio

- implementar cliente OpenAI-compatible;
- suportar `chat/completions` e tool calling;
- validar respostas com Pydantic;
- tratar timeout, modelo indisponível e JSON inválido;
- registrar latência, tokens e erro.

**Aceite:** o backend consegue solicitar uma ferramenta fictícia e interpretar a resposta estruturada.

### Fase 2 — Memória e contexto

- adicionar `thread_id` às tarefas;
- persistir estado do grafo no PostgreSQL;
- criar resumo de conversa por sessão;
- carregar projeto, voo, produto e bbox ativos;
- armazenar decisões e preferências do usuário;
- separar memória estruturada de histórico textual.

**Aceite:** uma conversa interrompida pode ser retomada mantendo projeto, área, ferramentas e resultados anteriores.

### Fase 3 — RAG documental

- habilitar `pgvector` no PostgreSQL;
- criar tabelas de documentos e chunks;
- importar Markdown, PDF, relatórios ODM e manuais;
- gerar embeddings localmente;
- recuperar trechos por projeto, fonte, versão e CRS;
- apresentar referências usadas na resposta.

**Aceite:** o agente responde uma pergunta técnica usando trechos recuperados e informa a fonte, sem usar RAG para calcular pixels ou geometrias.

### Fase 4 — Ferramentas geoespaciais de leitura

- `listar_projetos`;
- `listar_produtos`;
- `consultar_voos`;
- `estatisticas_raster`;
- `estatisticas_laz`;
- `consultar_anotacoes`;
- `consultar_camadas_postgis`.

**Aceite:** o agente responde perguntas somente leitura sobre produtos existentes, com números originados pelas ferramentas.

### Fase 5 — Análises raster, terreno e nuvem

- índices espectrais;
- declividade, aspecto e hillshade;
- recorte raster;
- comparação DSM-DTM;
- volume e perfil altimétrico;
- filtros LAZ e densidade;
- detecção de outliers;
- estatística zonal.

**Aceite:** cada ferramenta gera artefato versionado, métricas, CRS, fonte e limitações.

### Fase 6 — Dados cadastrais e QGIS/OGC

- importação de KML/KMZ, GeoJSON, GeoPackage e Shapefile;
- validação de CRS e licença;
- importação administrativa para PostGIS;
- consultas WFS;
- publicação WMS pelo QGIS Server;
- interseção com propriedades, estradas, rios e limites.

**Aceite:** o usuário consegue perguntar sobre uma área KML e obter interseções reproduzíveis com fonte registrada.

### Fase 7 — Escrita, aprovação e agentes especializados

- implementar nós LangGraph por especialidade;
- solicitar confirmação antes de criar arquivo, anotação ou camada;
- persistir resultados em `analises`, `anotacoes` e `produtos_processamento`;
- permitir retry e retomada;
- registrar auditoria completa.

**Aceite:** nenhuma operação de escrita ocorre sem aprovação explícita e toda execução pode ser auditada.

### Fase 8 — Copiloto e relatório

- interface de chat contextual;
- exibição do plano e ferramentas executadas;
- links para camadas e artefatos;
- respostas com evidências e incertezas;
- relatório consolidado PDF;
- avaliação final de qualidade por IA.

**Aceite:** o usuário faz uma pergunta completa, acompanha o plano, aprova operações, visualiza o resultado e baixa um relatório rastreável.

## 3. Limites do agente

- não executar SQL livre;
- não executar shell;
- não inventar dados ausentes;
- não importar bases externas sem fonte, licença e CRS;
- não escrever no banco sem aprovação;
- não substituir cálculos determinísticos por raciocínio textual;
- não expor dados de outro projeto.

## 4. Critérios globais de qualidade

Cada resposta deverá conter pergunta interpretada, produtos usados, ferramentas, parâmetros, resultado, artefatos, limitações e referências. Prompts, respostas, versões de modelo e hashes de dados deverão ser auditáveis.

## 5. Primeira entrega de desenvolvimento

A primeira implementação será a Fase 0 e a Fase 1: adaptador LM Studio, schemas de ferramentas, teste de tool calling e registro de auditoria. Somente depois serão habilitadas ferramentas que leem ou alteram dados reais.


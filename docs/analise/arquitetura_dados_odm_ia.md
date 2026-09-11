# Arquitetura de dados, ODM e IA

## 1. Diagnostico atual e decisao de arquitetura

### Banco do Ortomapas

O modelo documentado possui oito entidades: `projetos`, `voos`, `ortomapas`, `analises`, `anotacoes`, `gcps`, `comparacoes_temporais` e `tarefas_agentes`. Ele cobre metadados e resultados, mas ainda nao cobre usuarios, arquivos de fotos, tarefas ODM ou auditoria.

Na implementacao legada, o schema MySQL usa `created_at`/`updated_at`, enquanto os routers e o fallback SQLite usam `criado_em`/`atualizado_em`. Essa divergencia confirma que o MySQL nao deve ser o banco-alvo.

**Decisao adotada:** o banco oficial do Ortomapas sera `ortomapas` em PostgreSQL com PostGIS, no servidor PostgreSQL ja existente (`geoagentica-banco`). O banco `webodm` permanece separado no mesmo servidor. O MySQL e o SQLite ficam somente como legado de migracao/teste e nao devem ser usados automaticamente pela aplicacao.

### Banco do WebODM

O banco `webodm` no PostgreSQL/PostGIS e interno ao WebODM: projetos, tarefas, usuarios da interface WebODM, filas e metadados de processamento. O banco `ortomapas` sera outro banco no mesmo PostgreSQL. O Ortomapas nao deve criar chaves estrangeiras para tabelas internas do WebODM.

A integracao deve ser por API:

```text
Ortomapas DB <-> backend Ortomapas <-> NodeODM/WebODM API <-> WebODM DB
```

O Ortomapas guarda a referencia externa (`odm_task_id`, endpoint, parametros, versao, estado e produtos importados). O WebODM executa e administra o processamento. Assim os bancos permanecem independentes, mas os registros ficam correlacionados.

## 2. Modelo de dados alvo

### Usuarios e acesso

Adicionar:

- `usuarios`: id, email unico, nome, senha_hash, perfil (`admin`, `pesquisador`, `leitor`), ativo, ultimo_login, timestamps.
- `projeto_usuarios`: projeto_id, usuario_id, papel (`proprietario`, `editor`, `visualizador`), timestamps.
- `auditoria`: usuario_id, acao, entidade, entidade_id, detalhes JSON, IP, timestamp.

Projetos devem deixar de ter apenas o campo textual `responsavel`; o responsavel principal passa a ser uma relacao com `usuarios`. O campo antigo pode ser mantido durante a migracao.

### Captura e processamento

Adicionar:

- `voo_fotos`: voo_id, caminho, nome_original, hash_sha256, tamanho, mime_type, exif JSON, validacao, timestamps.
- `processamentos_odm`: id local, projeto_id, voo_id, odm_task_id, endpoint, engine, engine_version, parametros JSON, status, progresso, etapa, erro, criado_por, inicio, fim.
- `produtos_processamento`: processamento_id, tipo (`ortomosaico`, `dsm`, `dtm`, `nuvem_pontos`, `malha_3d`, `relatorio`), caminho, formato, tamanho, CRS, bbox, resolucao, largura, altura, bandas, status.
- `metricas_processamento`: processamento_id, imagens_recebidas, imagens_usadas, GSD, erro RMS, pontos, tempo, alertas JSON.

`ortomapas` pode continuar sendo a camada de catalogo para os rasters publicados, mas deve apontar para `produtos_processamento`. Nao e recomendavel criar um registro de ortomapa manualmente antes de existir um produto validado.

### IA

Manter `tarefas_agentes` para analises, mas adicionar:

- `tipo_origem` (`odm`, `raster`, `usuario`);
- `dependencias JSON`;
- `modelo`, `versao_prompt`, `custo`, `confianca` e `revisao_humana`;
- resultado estruturado e trilha de evidencias.

## 3. O que e integrado e o que nao e

### Integrado por API

- Criar tarefa de processamento.
- Enviar fotos e arquivos opcionais de GCP.
- Consultar fila, progresso, etapa e log.
- Cancelar e repetir tarefa.
- Baixar produtos e relatorio.
- Associar tarefa e produtos ao projeto/voo local.

### Mantido no Ortomapas

- Usuarios e permissoes de negocio.
- Projetos, voos e campanhas.
- Catalogo de produtos e historico de processamento.
- Tiles, anotacoes, comparacoes e analises.
- Agentes de IA, relatorios e auditoria.

### Nao fazer

- FK entre o banco Ortomapas e tabelas internas WebODM.
- Duplicar o PostgreSQL do WebODM sem necessidade.
- Fazer o frontend falar diretamente com NodeODM.
- Considerar uma tarefa `concluida` antes de validar e importar os produtos.

## 4. Casos de uso complementares

### Acesso e projetos

- **UC-030 Autenticar usuario**: login, logout, refresh/revogacao de token.
- **UC-031 Administrar usuarios**: criar, bloquear, redefinir senha e atribuir perfil.
- **UC-032 Compartilhar projeto**: adicionar/remover usuario e papel.
- **UC-033 Auditar operacoes**: consultar quem criou, alterou, processou ou excluiu dados.

### ODM

- **UC-021 Importar fotos de voo**.
- **UC-022 Criar processamento ODM**.
- **UC-023 Acompanhar processamento**.
- **UC-024 Cancelar/repetir processamento**.
- **UC-025 Importar e catalogar produtos**.
- **UC-026 Avaliar qualidade e aceitar/rejeitar resultado**.
- **UC-027 Visualizar e baixar produtos**.
- **UC-028 Visualizar nuvem 3D**.
- **UC-029 Reprocessar com parametros diferentes**.

### IA diferencial do Ortomapas

- **UC-034 Assistir configuracao do processamento**: verificar quantidade, EXIF, sobreposicao estimada, CRS e GCP antes do envio.
- **UC-035 Avaliar qualidade automaticamente**: interpretar relatorio ODM, detectar falhas de alinhamento, buracos, GSD inesperado e cobertura insuficiente.
- **UC-036 Recomendar analise**: sugerir slope, vegetacao, hidrologia, classificacao ou mudanca conforme produtos e objetivo do projeto.
- **UC-037 Explicar resultado**: gerar resumo com metricas, mapas utilizados, limitacoes e evidencias; nunca substituir o raster numerico.
- **UC-038 Detectar anomalias**: apontar artefatos, valores fora de faixa e divergencia entre voos.
- **UC-039 Gerar relatorio de campanha**: combinar voo, processamento, qualidade, analises, anotacoes e conclusoes.

## 5. Papel da IA

A IA deve atuar como copiloto verificavel, nao como fonte primaria de medicao. O pipeline deterministico (ODM, GDAL, rasterio e algoritmos numericos) calcula os valores; o agente:

1. valida pre-condicoes e detecta problemas;
2. orquestra tarefas aprovadas;
3. interpreta metricas e resultados;
4. propoe proximos passos;
5. redige relatorios com links para evidencias;
6. solicita aprovacao humana para excluir, publicar ou aceitar um resultado.

Cada conclusao da IA deve registrar modelo, versao, prompt/configuracao, entradas, metricas e nivel de confianca. O agente nao deve inventar coordenadas, precisao ou qualidade ausentes no relatorio ODM.

## 6. Ordem de implementacao

1. Criar o banco `ortomapas` no PostgreSQL/PostGIS existente e aplicar um schema unico.
2. Alterar o backend para PostgreSQL sem fallback silencioso para MySQL/SQLite.
3. Criar migracoes para usuarios, papeis e auditoria.
4. Criar migracoes para processamentos ODM, fotos e produtos.
5. Implementar UC-021 a UC-027 com NodeODM CPU.
6. Corrigir tiles para CRS UTM/EPSG:3857 e validar pixels reais.
7. Executar analises existentes sobre produtos importados.
8. Implementar avaliacao automatica de qualidade (UC-035).
9. Implementar recomendacoes e relatorios de IA com aprovacao humana.
10. Adicionar nuvem 3D, GCP/RTK e reprocessamento avancado.

## 7. Criterio de aceite da arquitetura

Um usuario autenticado cria um projeto, registra um voo, envia fotos, acompanha uma tarefa NodeODM, recebe produtos catalogados, visualiza a ortofoto no mapa, executa uma analise, consulta o parecer de qualidade da IA e consegue auditar todas as operacoes sem consultar diretamente o banco WebODM.

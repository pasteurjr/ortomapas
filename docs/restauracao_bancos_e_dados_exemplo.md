# Restauracao de bancos e dados de exemplo

**Atualizado:** 23/10/2026
**Escopo:** estrutura dos bancos, sem registros de usuarios, projetos, conversas, missoes ou auditoria.

## Banco usado pela aplicacao

O banco ativo do Ortomapas e PostgreSQL com PostGIS. Nesta maquina ele esta disponivel em `127.0.0.1:5433`, banco `ortomapas`. A configuracao `DB_ENGINE=postgres` e a estrutura efetiva foi confirmada no servidor. O dump abaixo e apenas DDL, gerado do PostgreSQL ativo com `pg_dump --schema-only`; nao contem linhas de tabelas.

| Banco | Arquivo de estrutura | Estado |
|---|---|---|
| PostgreSQL/PostGIS | [`backend/database/dumps/ortomapas_postgres_schema_2026-10-23.sql`](../backend/database/dumps/ortomapas_postgres_schema_2026-10-23.sql) | Dump estrutural do banco ativo; restauracao em banco temporario vazio verificada: 29 tabelas publicas, incluindo catalogo do PostGIS. |
| MySQL | [`backend/database/schema.sql`](../backend/database/schema.sql) | DDL legado versionado, 8 tabelas. Nao e dump verificado do MySQL ativo nem equivalente a estrutura atual do PostgreSQL. |

O PostgreSQL tem o schema completo da aplicacao, incluindo as tabelas de usuarios, projetos, ODM, copiloto e missoes. Para recriar o banco atual, prefira o dump PostgreSQL. O arquivo MySQL e mantido por compatibilidade/historico e nao deve ser tratado como backend equivalente.

## Restaurar PostgreSQL

Requisitos: PostgreSQL compativel, extensoes PostGIS e PostGIS Raster disponiveis no servidor e um usuario com permissao para criar banco, schemas e extensoes. Os comandos abaixo criam um banco novo; nao apagam nem sobrescrevem bancos existentes.

```bash
createdb -h 127.0.0.1 -p 5433 -U geo -T template0 ortomapas_recuperado
psql -h 127.0.0.1 -p 5433 -U geo -d ortomapas_recuperado \
  -v ON_ERROR_STOP=1 \
  -f backend/database/dumps/ortomapas_postgres_schema_2026-10-23.sql
```

Se o usuario `geo` nao puder criar as extensoes, uma pessoa administradora deve instala-las no banco novo antes da restauracao:

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_raster;
```

Verifique a estrutura:

```bash
psql -h 127.0.0.1 -p 5433 -U geo -d ortomapas_recuperado -c \
  "SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE';"
```

O numero esperado no servidor usado para gerar o dump e 29, contando `spatial_ref_sys` instalado pelo PostGIS. Depois de conferir e configurar `PGHOST`, `PGPORT`, `PGUSER` e `PGDATABASE` no `.env`, pare a aplicacao antes de direciona-la ao banco restaurado.

Para gerar novamente um dump estrutural a partir de outro servidor, sem expor a senha no comando:

```bash
pg_dump --schema-only --no-owner --no-privileges --no-tablespaces \
  -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" \
  --file=backend/database/dumps/ortomapas_postgres_schema.sql
```

O `pg_dump` solicitara a senha interativamente se necessario. O dump nao inclui dados, objetos grandes externos, imagens nem arquivos de produtos.

## Restaurar ou exportar estrutura MySQL

O arquivo `backend/database/schema.sql` cria o banco `ortomapas` e a estrutura MySQL legada. Para instalar essa estrutura em uma instancia vazia:

```bash
mysql --host=127.0.0.1 --port=3308 --user="$MYSQL_USER" --password \
  < backend/database/schema.sql
```

O cliente solicita a senha; nao a coloque no comando, no `.sql` ou no Git. Esse arquivo contem apenas as 8 tabelas antigas descritas nele. Ele nao recria tabelas atuais do PostgreSQL como `usuarios`, `copilot_threads` e `missoes_*`, portanto nao restaura o backend atual do Ortomapas.

Para obter um dump estrutural real de uma instancia MySQL acessivel, use:

```bash
umask 077
mysqldump --host="$MYSQL_HOST" --port="$MYSQL_PORT" --user="$MYSQL_USER" \
  --password --no-data --routines --triggers --events --databases "$MYSQL_DATABASE" \
  > mysql_schema_only.sql
```

Confirme que o arquivo nao contem `INSERT INTO` antes de arquiva-lo. Para restaurar esse dump em uma instancia vazia:

```bash
mysql --host="$MYSQL_HOST" --port="$MYSQL_PORT" --user="$MYSQL_USER" --password \
  < mysql_schema_only.sql
```

### Estado da verificacao MySQL nesta maquina

O servidor responde na porta `3308`, mas a credencial local configurada para o Ortomapas foi recusada (`Access denied`). O usuario e senha nao foram impressos nem alterados. Por isso nao foi possivel executar `mysqldump` contra o banco ativo; `backend/database/schema.sql` e a unica referencia MySQL versionada e deve ser considerada legada ate ser comparada com uma instancia MySQL autorizada.

## Dados de exemplo ODM

O conjunto de fotos de drone usado na validacao fotogrametrica e o **Aukerman**: 77 fotografias JPG com coordenadas GPS no EXIF. O conjunto original local fica em `data/odm_test/odm_data_aukerman-master/images/`; os ortomosaicos, DSM, DTM, nuvem de pontos e relatorios foram derivados localmente pelo NodeODM e ficam sob `data/odm_test/` e `data/odm_uploads/`. Esses arquivos nao estao dentro do dump SQL e nao sao versionados no Git por causa do tamanho.

Fontes oficiais para baixar o conjunto novamente:

- [Repositorio OpenDroneMap/odm_data_aukerman](https://github.com/OpenDroneMap/odm_data_aukerman) (dataset e fotos originais; licenca CC0 indicada no repositorio).
- [Catalogo oficial OpenDroneMap/ODMdata](https://github.com/OpenDroneMap/ODMdata) (lista Aukerman com 77 imagens e link de acesso ao dataset).

O catalogo indica tamanho aproximado de 543 MB. Para processar novamente, baixe as imagens da fonte, extraia-as no caminho acima e envie-as ao NodeODM/WebODM. Os produtos gerados podem ocupar varios gigabytes; mantenha-os em armazenamento de dados, nao no Git.

## Limites deste procedimento

- Estrutura SQL nao e backup de dados. Usuarios, senhas hash, projetos, conversas, missoes, auditoria e metadados registrados no banco nao sao recuperados por estes arquivos.
- Os arquivos de imagens e produtos raster/3D tambem precisam de backup proprio. O dump nao contem esses arquivos nem os volumes do WebODM/NodeODM.
- Antes de restaurar sobre uma instancia existente, crie um banco separado e confira as tabelas. Nao use `DROP DATABASE` como etapa automatica.

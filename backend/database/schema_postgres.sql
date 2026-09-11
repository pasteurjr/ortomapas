-- Schema oficial do Ortomapas (PostgreSQL + PostGIS)
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_raster;

CREATE TABLE IF NOT EXISTS usuarios (
 id BIGSERIAL PRIMARY KEY, email VARCHAR(320) NOT NULL UNIQUE, nome VARCHAR(255) NOT NULL,
 senha_hash TEXT NOT NULL, perfil VARCHAR(30) NOT NULL DEFAULT 'pesquisador', ativo BOOLEAN NOT NULL DEFAULT TRUE,
 ultimo_login TIMESTAMPTZ, criado_em TIMESTAMPTZ NOT NULL DEFAULT now(), atualizado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS projetos (
 id BIGSERIAL PRIMARY KEY, nome VARCHAR(255) NOT NULL, descricao TEXT, area_estudo VARCHAR(255),
 bbox_norte DOUBLE PRECISION, bbox_sul DOUBLE PRECISION, bbox_leste DOUBLE PRECISION, bbox_oeste DOUBLE PRECISION,
 centro_lat DOUBLE PRECISION, centro_lon DOUBLE PRECISION, objetivo TEXT, responsavel VARCHAR(255),
 data_inicio DATE, data_fim DATE, status VARCHAR(30) NOT NULL DEFAULT 'planejado',
 criado_em TIMESTAMPTZ NOT NULL DEFAULT now(), atualizado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS projeto_usuarios (
 projeto_id BIGINT NOT NULL REFERENCES projetos(id) ON DELETE CASCADE, usuario_id BIGINT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
 papel VARCHAR(30) NOT NULL DEFAULT 'visualizador', criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
 PRIMARY KEY (projeto_id, usuario_id)
);
CREATE TABLE IF NOT EXISTS voos (
 id BIGSERIAL PRIMARY KEY, projeto_id BIGINT NOT NULL REFERENCES projetos(id) ON DELETE CASCADE, data_voo TIMESTAMPTZ NOT NULL,
 local_decolagem_lat DOUBLE PRECISION, local_decolagem_lon DOUBLE PRECISION, altitude_voo_m DOUBLE PRECISION,
 sobreposicao_frontal DOUBLE PRECISION, sobreposicao_lateral DOUBLE PRECISION, velocidade_ms DOUBLE PRECISION,
 num_fotos INTEGER, resolucao_foto VARCHAR(50), formato_foto VARCHAR(20), gsd_cm DOUBLE PRECISION, area_coberta_ha DOUBLE PRECISION,
 num_baterias INTEGER, tipo_bateria VARCHAR(100), condicoes_vento VARCHAR(100), condicoes_ceu VARCHAR(100), temperatura_c DOUBLE PRECISION,
 app_voo VARCHAR(100), missao_csv_path TEXT, fotos_path TEXT, observacoes TEXT,
 criado_em TIMESTAMPTZ NOT NULL DEFAULT now(), atualizado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS processamentos_odm (
 id BIGSERIAL PRIMARY KEY, projeto_id BIGINT NOT NULL REFERENCES projetos(id) ON DELETE CASCADE, voo_id BIGINT NOT NULL REFERENCES voos(id) ON DELETE CASCADE,
 odm_task_id VARCHAR(255) NOT NULL UNIQUE, endpoint TEXT NOT NULL, engine VARCHAR(50), engine_version VARCHAR(50),
 parametros JSONB NOT NULL DEFAULT '{}'::jsonb, status VARCHAR(30) NOT NULL DEFAULT 'pendente', progresso NUMERIC(6,2) DEFAULT 0,
 etapa TEXT, erro TEXT, criado_por BIGINT REFERENCES usuarios(id) ON DELETE SET NULL,
 inicio_em TIMESTAMPTZ, fim_em TIMESTAMPTZ, criado_em TIMESTAMPTZ NOT NULL DEFAULT now(), atualizado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS voo_fotos (
 id BIGSERIAL PRIMARY KEY, voo_id BIGINT NOT NULL REFERENCES voos(id) ON DELETE CASCADE, caminho TEXT NOT NULL,
 nome_original TEXT NOT NULL, hash_sha256 CHAR(64), tamanho_bytes BIGINT, mime_type VARCHAR(100), exif JSONB,
 validacao VARCHAR(30) NOT NULL DEFAULT 'pendente', criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS ortomapas (
 id BIGSERIAL PRIMARY KEY, voo_id BIGINT NOT NULL REFERENCES voos(id) ON DELETE CASCADE, projeto_id BIGINT NOT NULL REFERENCES projetos(id) ON DELETE CASCADE,
 nome VARCHAR(255) NOT NULL, tipo VARCHAR(40) NOT NULL DEFAULT 'ortomosaico', formato VARCHAR(50), resolucao_cm DOUBLE PRECISION,
 largura_px INTEGER, altura_px INTEGER, tamanho_arquivo_mb DOUBLE PRECISION, sistema_coordenadas VARCHAR(100),
 bbox_norte DOUBLE PRECISION, bbox_sul DOUBLE PRECISION, bbox_leste DOUBLE PRECISION, bbox_oeste DOUBLE PRECISION,
 centro_lat DOUBLE PRECISION, centro_lon DOUBLE PRECISION, caminho_arquivo TEXT, caminho_thumbnail TEXT, webodm_task_id VARCHAR(255),
 parametros_processamento JSONB, qualidade_processamento VARCHAR(50), num_fotos_processadas INTEGER, tempo_processamento_min DOUBLE PRECISION,
 erro_rms DOUBLE PRECISION, gcps_utilizados BOOLEAN DEFAULT FALSE, num_gcps INTEGER DEFAULT 0, status VARCHAR(30) DEFAULT 'processando',
 data_processamento TIMESTAMPTZ, observacoes TEXT, criado_em TIMESTAMPTZ NOT NULL DEFAULT now(), atualizado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS produtos_processamento (
 id BIGSERIAL PRIMARY KEY, processamento_id BIGINT NOT NULL REFERENCES processamentos_odm(id) ON DELETE CASCADE, ortomapa_id BIGINT REFERENCES ortomapas(id) ON DELETE SET NULL,
 tipo VARCHAR(40) NOT NULL, caminho TEXT NOT NULL, formato VARCHAR(50), tamanho_arquivo_mb DOUBLE PRECISION,
 crs VARCHAR(100), bbox geometry(Polygon,4326), resolucao DOUBLE PRECISION, largura_px INTEGER, altura_px INTEGER, bandas INTEGER,
 status VARCHAR(30) NOT NULL DEFAULT 'disponivel', criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS analises (
 id BIGSERIAL PRIMARY KEY, ortomapa_id BIGINT NOT NULL REFERENCES ortomapas(id) ON DELETE CASCADE, projeto_id BIGINT NOT NULL REFERENCES projetos(id) ON DELETE CASCADE,
 tipo_analise VARCHAR(80) NOT NULL, nome VARCHAR(255) NOT NULL, descricao TEXT, parametros JSONB, resultado_path TEXT, resultado_thumbnail TEXT,
 resultado_json JSONB, modelo_ia VARCHAR(255), versao_modelo VARCHAR(50), metricas JSONB, agente_ia VARCHAR(255), status VARCHAR(30) DEFAULT 'pendente',
 tempo_processamento_seg DOUBLE PRECISION, data_analise TIMESTAMPTZ, observacoes TEXT, criado_em TIMESTAMPTZ NOT NULL DEFAULT now(), atualizado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS camadas_copiloto (
 id BIGSERIAL PRIMARY KEY, projeto_id BIGINT NOT NULL REFERENCES projetos(id) ON DELETE CASCADE,
 usuario_id BIGINT REFERENCES usuarios(id) ON DELETE SET NULL, nome VARCHAR(255) NOT NULL,
 ferramenta VARCHAR(100) NOT NULL, geojson JSONB NOT NULL, parametros JSONB DEFAULT '{}'::jsonb,
 criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS anotacoes (
 id BIGSERIAL PRIMARY KEY, ortomapa_id BIGINT NOT NULL REFERENCES ortomapas(id) ON DELETE CASCADE, analise_id BIGINT REFERENCES analises(id) ON DELETE SET NULL,
 tipo VARCHAR(30) NOT NULL, categoria VARCHAR(255), rotulo VARCHAR(255), geometria_wkt TEXT, centro_lat DOUBLE PRECISION, centro_lon DOUBLE PRECISION,
 area_m2 DOUBLE PRECISION, atributos JSONB, confianca DOUBLE PRECISION, fonte VARCHAR(30) DEFAULT 'manual', criado_por BIGINT REFERENCES usuarios(id) ON DELETE SET NULL,
 criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS gcps (
 id BIGSERIAL PRIMARY KEY, projeto_id BIGINT NOT NULL REFERENCES projetos(id) ON DELETE CASCADE, voo_id BIGINT REFERENCES voos(id) ON DELETE SET NULL,
 nome VARCHAR(255) NOT NULL, latitude DOUBLE PRECISION NOT NULL, longitude DOUBLE PRECISION NOT NULL, altitude_m DOUBLE PRECISION,
 precisao_horizontal_m DOUBLE PRECISION, precisao_vertical_m DOUBLE PRECISION, metodo_coleta VARCHAR(100), equipamento VARCHAR(255), data_coleta TIMESTAMPTZ,
 observacoes TEXT, criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS comparacoes_temporais (
 id BIGSERIAL PRIMARY KEY, projeto_id BIGINT NOT NULL REFERENCES projetos(id) ON DELETE CASCADE, ortomapa_antes_id BIGINT NOT NULL REFERENCES ortomapas(id) ON DELETE CASCADE,
 ortomapa_depois_id BIGINT NOT NULL REFERENCES ortomapas(id) ON DELETE CASCADE, data_antes TIMESTAMPTZ NOT NULL, data_depois TIMESTAMPTZ NOT NULL,
 tipo_comparacao VARCHAR(50) NOT NULL, resultado_path TEXT, resultado_thumbnail TEXT, estatisticas JSONB, observacoes TEXT, criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS tarefas_agentes (
 id BIGSERIAL PRIMARY KEY, ortomapa_id BIGINT NOT NULL REFERENCES ortomapas(id) ON DELETE CASCADE, tipo_tarefa VARCHAR(255) NOT NULL,
 agente VARCHAR(255) NOT NULL, prioridade INTEGER DEFAULT 5, parametros JSONB, status VARCHAR(30) DEFAULT 'pendente', resultado JSONB, erro_msg TEXT,
 tentativas INTEGER DEFAULT 0, max_tentativas INTEGER DEFAULT 3, inicio_execucao TIMESTAMPTZ, fim_execucao TIMESTAMPTZ, criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS copilot_threads (
 id BIGSERIAL PRIMARY KEY, projeto_id BIGINT REFERENCES projetos(id) ON DELETE CASCADE, usuario_id BIGINT REFERENCES usuarios(id) ON DELETE CASCADE,
 titulo VARCHAR(255), resumo TEXT, estado JSONB NOT NULL DEFAULT '{}'::jsonb, criado_em TIMESTAMPTZ NOT NULL DEFAULT now(), atualizado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS copilot_messages (
 id BIGSERIAL PRIMARY KEY, thread_id BIGINT NOT NULL REFERENCES copilot_threads(id) ON DELETE CASCADE, papel VARCHAR(20) NOT NULL, conteudo TEXT NOT NULL,
 ferramentas JSONB, criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS copilot_memorias (
 id BIGSERIAL PRIMARY KEY, projeto_id BIGINT NOT NULL REFERENCES projetos(id) ON DELETE CASCADE, usuario_id BIGINT REFERENCES usuarios(id) ON DELETE SET NULL,
 chave VARCHAR(255) NOT NULL, valor JSONB NOT NULL, origem VARCHAR(50) DEFAULT 'copiloto', atualizado_em TIMESTAMPTZ NOT NULL DEFAULT now(), UNIQUE(projeto_id, usuario_id, chave)
);
CREATE TABLE IF NOT EXISTS metricas_processamento (
 processamento_id BIGINT PRIMARY KEY REFERENCES processamentos_odm(id) ON DELETE CASCADE, imagens_recebidas INTEGER, imagens_usadas INTEGER,
 gsd_cm DOUBLE PRECISION, erro_rms DOUBLE PRECISION, pontos BIGINT, tempo_segundos DOUBLE PRECISION, alertas JSONB, criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS auditoria (
 id BIGSERIAL PRIMARY KEY, usuario_id BIGINT REFERENCES usuarios(id) ON DELETE SET NULL, acao VARCHAR(80) NOT NULL, entidade VARCHAR(80), entidade_id BIGINT,
 detalhes JSONB, ip INET, criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_projetos_status ON projetos(status);
CREATE INDEX IF NOT EXISTS idx_voos_projeto ON voos(projeto_id);
CREATE INDEX IF NOT EXISTS idx_ortomapas_projeto ON ortomapas(projeto_id);
CREATE INDEX IF NOT EXISTS idx_ortomapas_task ON ortomapas(webodm_task_id);
CREATE INDEX IF NOT EXISTS idx_processamentos_status ON processamentos_odm(status);
CREATE INDEX IF NOT EXISTS idx_produtos_bbox ON produtos_processamento USING GIST(bbox);

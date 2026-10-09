-- Fase 1: contrato e persistencia do planejador de missoes.
-- Executar no PostgreSQL/PostGIS do Ortomapas.

CREATE TABLE IF NOT EXISTS missoes_captura (
    id BIGSERIAL PRIMARY KEY,
    projeto_id BIGINT NOT NULL REFERENCES projetos(id) ON DELETE CASCADE,
    nome VARCHAR(255) NOT NULL,
    descricao TEXT,
    status VARCHAR(30) NOT NULL DEFAULT 'rascunho',
    versao INTEGER NOT NULL DEFAULT 1,
    drone_perfil JSONB NOT NULL DEFAULT '{}'::jsonb,
    camera_perfil JSONB NOT NULL DEFAULT '{}'::jsonb,
    crs VARCHAR(32) NOT NULL DEFAULT 'EPSG:4326',
    takeoff JSONB NOT NULL DEFAULT '{}'::jsonb,
    canonical JSONB NOT NULL DEFAULT '{}'::jsonb,
    criado_por BIGINT REFERENCES usuarios(id) ON DELETE SET NULL,
    revisado_por BIGINT REFERENCES usuarios(id) ON DELETE SET NULL,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS missoes_areas (
    id BIGSERIAL PRIMARY KEY,
    missao_id BIGINT NOT NULL REFERENCES missoes_captura(id) ON DELETE CASCADE,
    tipo VARCHAR(30) NOT NULL,
    nome VARCHAR(255),
    geometria geometry(Geometry,4326) NOT NULL,
    propriedades JSONB NOT NULL DEFAULT '{}'::jsonb,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS missoes_parametros (
    missao_id BIGINT PRIMARY KEY REFERENCES missoes_captura(id) ON DELETE CASCADE,
    gsd_cm_px DOUBLE PRECISION,
    overlap_frontal DOUBLE PRECISION,
    overlap_lateral DOUBLE PRECISION,
    altitude_m DOUBLE PRECISION,
    altitude_referencia VARCHAR(20) NOT NULL DEFAULT 'AGL',
    velocidade_ms DOUBLE PRECISION,
    gimbal_graus DOUBLE PRECISION DEFAULT -90,
    intervalo_segundos DOUBLE PRECISION,
    espacamento_linhas_m DOUBLE PRECISION,
    reserva_bateria_pct DOUBLE PRECISION DEFAULT 25,
    parametros JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS missoes_blocos (
    id BIGSERIAL PRIMARY KEY,
    missao_id BIGINT NOT NULL REFERENCES missoes_captura(id) ON DELETE CASCADE,
    ordem INTEGER NOT NULL,
    nome VARCHAR(80) NOT NULL,
    estimativa_fotos INTEGER,
    distancia_m DOUBLE PRECISION,
    tempo_segundos DOUBLE PRECISION,
    bateria INTEGER,
    status VARCHAR(30) NOT NULL DEFAULT 'rascunho',
    propriedades JSONB NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE(missao_id, ordem)
);

CREATE TABLE IF NOT EXISTS missoes_waypoints (
    id BIGSERIAL PRIMARY KEY,
    missao_id BIGINT NOT NULL REFERENCES missoes_captura(id) ON DELETE CASCADE,
    bloco_id BIGINT REFERENCES missoes_blocos(id) ON DELETE SET NULL,
    ordem INTEGER NOT NULL,
    geometria geometry(Point,4326) NOT NULL,
    altitude_m DOUBLE PRECISION,
    altitude_agl_m DOUBLE PRECISION,
    rumo_graus DOUBLE PRECISION,
    velocidade_ms DOUBLE PRECISION,
    gimbal_graus DOUBLE PRECISION,
    acoes JSONB NOT NULL DEFAULT '[]'::jsonb,
    propriedades JSONB NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE(missao_id, ordem)
);

CREATE TABLE IF NOT EXISTS missoes_validacoes (
    id BIGSERIAL PRIMARY KEY,
    missao_id BIGINT NOT NULL REFERENCES missoes_captura(id) ON DELETE CASCADE,
    regra VARCHAR(80) NOT NULL,
    severidade VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL,
    mensagem TEXT NOT NULL,
    valor_observado JSONB,
    geometria geometry(Geometry,4326),
    executado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS missoes_exportacoes (
    id BIGSERIAL PRIMARY KEY,
    missao_id BIGINT NOT NULL REFERENCES missoes_captura(id) ON DELETE CASCADE,
    alvo VARCHAR(40) NOT NULL,
    formato VARCHAR(40) NOT NULL,
    adaptador_versao VARCHAR(30) NOT NULL,
    checksum_sha256 CHAR(64),
    manifesto JSONB NOT NULL DEFAULT '{}'::jsonb,
    caminho TEXT,
    criado_por BIGINT REFERENCES usuarios(id) ON DELETE SET NULL,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS missoes_execucoes (
    id BIGSERIAL PRIMARY KEY,
    missao_id BIGINT NOT NULL REFERENCES missoes_captura(id) ON DELETE CASCADE,
    voo_id BIGINT REFERENCES voos(id) ON DELETE SET NULL,
    operador_id BIGINT REFERENCES usuarios(id) ON DELETE SET NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'planejada',
    inicio_em TIMESTAMPTZ,
    fim_em TIMESTAMPTZ,
    clima JSONB NOT NULL DEFAULT '{}'::jsonb,
    observacoes TEXT,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS missoes_fotos (
    id BIGSERIAL PRIMARY KEY,
    execucao_id BIGINT NOT NULL REFERENCES missoes_execucoes(id) ON DELETE CASCADE,
    caminho TEXT NOT NULL,
    nome_original TEXT NOT NULL,
    hash_sha256 CHAR(64),
    tamanho_bytes BIGINT,
    exif JSONB,
    validacao VARCHAR(30) NOT NULL DEFAULT 'pendente',
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_missoes_captura_projeto ON missoes_captura(projeto_id, atualizado_em DESC);
CREATE INDEX IF NOT EXISTS idx_missoes_areas_geom ON missoes_areas USING GIST(geometria);
CREATE INDEX IF NOT EXISTS idx_missoes_waypoints_geom ON missoes_waypoints USING GIST(geometria);
CREATE INDEX IF NOT EXISTS idx_missoes_validacoes_missao ON missoes_validacoes(missao_id, executado_em DESC);

-- ============================================================
-- Ortomapas Database Schema
-- Full DDL for the orthomapping system
-- ============================================================

CREATE DATABASE IF NOT EXISTS ortomapas
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE ortomapas;

-- ============================================================
-- 1. PROJETOS
-- ============================================================
CREATE TABLE IF NOT EXISTS projetos (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    nome            VARCHAR(255) NOT NULL,
    descricao       TEXT,
    area_estudo     VARCHAR(255),
    bbox_norte      DECIMAL(10, 6),
    bbox_sul        DECIMAL(10, 6),
    bbox_leste      DECIMAL(10, 6),
    bbox_oeste      DECIMAL(10, 6),
    centro_lat      DECIMAL(10, 6),
    centro_lon      DECIMAL(10, 6),
    objetivo        TEXT,
    responsavel     VARCHAR(255),
    data_inicio     DATE,
    data_fim        DATE,
    status          ENUM('planejado', 'em_andamento', 'concluido', 'cancelado', 'arquivado')
                        NOT NULL DEFAULT 'planejado',
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_projetos_status (status),
    INDEX idx_projetos_responsavel (responsavel),
    INDEX idx_projetos_data_inicio (data_inicio),
    INDEX idx_projetos_centro (centro_lat, centro_lon),
    FULLTEXT INDEX ft_projetos_nome_descricao (nome, descricao),
    FULLTEXT INDEX ft_projetos_objetivo (objetivo)
) ENGINE=InnoDB;

-- ============================================================
-- 2. VOOS
-- ============================================================
CREATE TABLE IF NOT EXISTS voos (
    id                      INT AUTO_INCREMENT PRIMARY KEY,
    projeto_id              INT NOT NULL,
    data_voo                DATETIME NOT NULL,
    local_decolagem_lat     DECIMAL(10, 6),
    local_decolagem_lon     DECIMAL(10, 6),
    altitude_voo_m          DECIMAL(8, 2),
    sobreposicao_frontal    DECIMAL(5, 2),
    sobreposicao_lateral    DECIMAL(5, 2),
    velocidade_ms           DECIMAL(6, 2),
    num_fotos               INT,
    resolucao_foto          VARCHAR(50),
    formato_foto            VARCHAR(20),
    gsd_cm                  DECIMAL(8, 4),
    area_coberta_ha         DECIMAL(10, 4),
    num_baterias            INT,
    tipo_bateria            VARCHAR(100),
    condicoes_vento         VARCHAR(100),
    condicoes_ceu           VARCHAR(100),
    temperatura_c           DECIMAL(5, 2),
    app_voo                 VARCHAR(100),
    missao_csv_path         VARCHAR(500),
    fotos_path              VARCHAR(500),
    observacoes             TEXT,
    created_at              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_voos_projeto FOREIGN KEY (projeto_id)
        REFERENCES projetos(id) ON DELETE CASCADE ON UPDATE CASCADE,

    INDEX idx_voos_projeto_id (projeto_id),
    INDEX idx_voos_data_voo (data_voo),
    INDEX idx_voos_decolagem (local_decolagem_lat, local_decolagem_lon),
    INDEX idx_voos_gsd (gsd_cm),
    FULLTEXT INDEX ft_voos_observacoes (observacoes)
) ENGINE=InnoDB;

-- ============================================================
-- 3. ORTOMAPAS
-- ============================================================
CREATE TABLE IF NOT EXISTS ortomapas (
    id                          INT AUTO_INCREMENT PRIMARY KEY,
    voo_id                      INT NOT NULL,
    projeto_id                  INT NOT NULL,
    nome                        VARCHAR(255) NOT NULL,
    tipo                        ENUM('ortomosaico', 'dsm', 'dtm', 'nuvem_pontos', 'malha_3d')
                                    NOT NULL DEFAULT 'ortomosaico',
    formato                     VARCHAR(50),
    resolucao_cm                DECIMAL(8, 4),
    largura_px                  INT,
    altura_px                   INT,
    tamanho_arquivo_mb          DECIMAL(12, 2),
    sistema_coordenadas         VARCHAR(100),
    bbox_norte                  DECIMAL(10, 6),
    bbox_sul                    DECIMAL(10, 6),
    bbox_leste                  DECIMAL(10, 6),
    bbox_oeste                  DECIMAL(10, 6),
    centro_lat                  DECIMAL(10, 6),
    centro_lon                  DECIMAL(10, 6),
    caminho_arquivo             VARCHAR(500),
    caminho_thumbnail           VARCHAR(500),
    webodm_task_id              VARCHAR(255),
    parametros_processamento    JSON,
    qualidade_processamento     VARCHAR(50),
    num_fotos_processadas       INT,
    tempo_processamento_min     DECIMAL(10, 2),
    erro_rms                    DECIMAL(10, 6),
    gcps_utilizados             BOOLEAN DEFAULT FALSE,
    num_gcps                    INT DEFAULT 0,
    status                      ENUM('pendente', 'processando', 'concluido', 'erro', 'cancelado')
                                    NOT NULL DEFAULT 'pendente',
    data_processamento          DATETIME,
    created_at                  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at                  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_ortomapas_voo FOREIGN KEY (voo_id)
        REFERENCES voos(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_ortomapas_projeto FOREIGN KEY (projeto_id)
        REFERENCES projetos(id) ON DELETE CASCADE ON UPDATE CASCADE,

    INDEX idx_ortomapas_voo_id (voo_id),
    INDEX idx_ortomapas_projeto_id (projeto_id),
    INDEX idx_ortomapas_tipo (tipo),
    INDEX idx_ortomapas_status (status),
    INDEX idx_ortomapas_centro (centro_lat, centro_lon),
    INDEX idx_ortomapas_webodm (webodm_task_id),
    INDEX idx_ortomapas_data_proc (data_processamento),
    FULLTEXT INDEX ft_ortomapas_nome (nome)
) ENGINE=InnoDB;

-- ============================================================
-- 4. ANALISES
-- ============================================================
CREATE TABLE IF NOT EXISTS analises (
    id                      INT AUTO_INCREMENT PRIMARY KEY,
    ortomapa_id             INT NOT NULL,
    projeto_id              INT NOT NULL,
    tipo_analise            ENUM(
                                'indice_vegetacao', 'classificacao_solo', 'deteccao_objetos',
                                'deteccao_mudancas', 'segmentacao', 'volumetria', 'contorno',
                                'perfil_terreno', 'ndvi_rgb', 'personalizada'
                            ) NOT NULL,
    nome                    VARCHAR(255) NOT NULL,
    descricao               TEXT,
    parametros              JSON,
    resultado_path          VARCHAR(500),
    resultado_thumbnail     VARCHAR(500),
    resultado_json          JSON,
    modelo_ia               VARCHAR(255),
    versao_modelo           VARCHAR(50),
    metricas                JSON,
    agente_ia               VARCHAR(255),
    status                  ENUM('pendente', 'em_execucao', 'concluido', 'erro', 'cancelado')
                                NOT NULL DEFAULT 'pendente',
    tempo_processamento_seg DECIMAL(12, 2),
    created_at              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_analises_ortomapa FOREIGN KEY (ortomapa_id)
        REFERENCES ortomapas(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_analises_projeto FOREIGN KEY (projeto_id)
        REFERENCES projetos(id) ON DELETE CASCADE ON UPDATE CASCADE,

    INDEX idx_analises_ortomapa_id (ortomapa_id),
    INDEX idx_analises_projeto_id (projeto_id),
    INDEX idx_analises_tipo (tipo_analise),
    INDEX idx_analises_status (status),
    INDEX idx_analises_agente (agente_ia),
    FULLTEXT INDEX ft_analises_nome_descricao (nome, descricao)
) ENGINE=InnoDB;

-- ============================================================
-- 5. ANOTACOES
-- ============================================================
CREATE TABLE IF NOT EXISTS anotacoes (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    ortomapa_id     INT NOT NULL,
    analise_id      INT,
    tipo            ENUM('ponto', 'linha', 'poligono', 'bbox', 'texto') NOT NULL,
    categoria       VARCHAR(255),
    rotulo          VARCHAR(255),
    geometria_wkt   TEXT,
    centro_lat      DECIMAL(10, 6),
    centro_lon      DECIMAL(10, 6),
    area_m2         DECIMAL(14, 4),
    atributos       JSON,
    confianca       DECIMAL(5, 4),
    fonte           ENUM('manual', 'ia', 'importado') NOT NULL DEFAULT 'manual',
    criado_por      VARCHAR(255),
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_anotacoes_ortomapa FOREIGN KEY (ortomapa_id)
        REFERENCES ortomapas(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_anotacoes_analise FOREIGN KEY (analise_id)
        REFERENCES analises(id) ON DELETE SET NULL ON UPDATE CASCADE,

    INDEX idx_anotacoes_ortomapa_id (ortomapa_id),
    INDEX idx_anotacoes_analise_id (analise_id),
    INDEX idx_anotacoes_tipo (tipo),
    INDEX idx_anotacoes_categoria (categoria),
    INDEX idx_anotacoes_fonte (fonte),
    INDEX idx_anotacoes_centro (centro_lat, centro_lon),
    FULLTEXT INDEX ft_anotacoes_rotulo (rotulo)
) ENGINE=InnoDB;

-- ============================================================
-- 6. GCPS (Ground Control Points)
-- ============================================================
CREATE TABLE IF NOT EXISTS gcps (
    id                      INT AUTO_INCREMENT PRIMARY KEY,
    projeto_id              INT NOT NULL,
    voo_id                  INT,
    nome                    VARCHAR(255) NOT NULL,
    latitude                DECIMAL(10, 6) NOT NULL,
    longitude               DECIMAL(10, 6) NOT NULL,
    altitude_m              DECIMAL(10, 4),
    precisao_horizontal_m   DECIMAL(8, 4),
    precisao_vertical_m     DECIMAL(8, 4),
    metodo_coleta           VARCHAR(100),
    equipamento             VARCHAR(255),
    data_coleta             DATETIME,
    created_at              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_gcps_projeto FOREIGN KEY (projeto_id)
        REFERENCES projetos(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_gcps_voo FOREIGN KEY (voo_id)
        REFERENCES voos(id) ON DELETE SET NULL ON UPDATE CASCADE,

    INDEX idx_gcps_projeto_id (projeto_id),
    INDEX idx_gcps_voo_id (voo_id),
    INDEX idx_gcps_coordenadas (latitude, longitude),
    INDEX idx_gcps_metodo (metodo_coleta)
) ENGINE=InnoDB;

-- ============================================================
-- 7. COMPARACOES TEMPORAIS
-- ============================================================
CREATE TABLE IF NOT EXISTS comparacoes_temporais (
    id                      INT AUTO_INCREMENT PRIMARY KEY,
    projeto_id              INT NOT NULL,
    ortomapa_antes_id       INT NOT NULL,
    ortomapa_depois_id      INT NOT NULL,
    data_antes              DATETIME NOT NULL,
    data_depois             DATETIME NOT NULL,
    tipo_comparacao         ENUM(
                                'diferenca_absoluta', 'diferenca_relativa', 'deteccao_mudancas',
                                'ndvi_temporal', 'volumetria_temporal', 'classificacao_temporal'
                            ) NOT NULL,
    resultado_path          VARCHAR(500),
    resultado_thumbnail     VARCHAR(500),
    estatisticas            JSON,
    created_at              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_comp_projeto FOREIGN KEY (projeto_id)
        REFERENCES projetos(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_comp_ortomapa_antes FOREIGN KEY (ortomapa_antes_id)
        REFERENCES ortomapas(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_comp_ortomapa_depois FOREIGN KEY (ortomapa_depois_id)
        REFERENCES ortomapas(id) ON DELETE CASCADE ON UPDATE CASCADE,

    INDEX idx_comp_projeto_id (projeto_id),
    INDEX idx_comp_antes_id (ortomapa_antes_id),
    INDEX idx_comp_depois_id (ortomapa_depois_id),
    INDEX idx_comp_tipo (tipo_comparacao),
    INDEX idx_comp_datas (data_antes, data_depois)
) ENGINE=InnoDB;

-- ============================================================
-- 8. TAREFAS DE AGENTES
-- ============================================================
CREATE TABLE IF NOT EXISTS tarefas_agentes (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    ortomapa_id         INT NOT NULL,
    tipo_tarefa         VARCHAR(255) NOT NULL,
    agente              VARCHAR(255) NOT NULL,
    prioridade          INT NOT NULL DEFAULT 5,
    parametros          JSON,
    status              ENUM('pendente', 'em_fila', 'em_execucao', 'concluido', 'erro', 'cancelado')
                            NOT NULL DEFAULT 'pendente',
    resultado           JSON,
    erro_msg            TEXT,
    tentativas          INT NOT NULL DEFAULT 0,
    max_tentativas      INT NOT NULL DEFAULT 3,
    inicio_execucao     DATETIME,
    fim_execucao        DATETIME,
    created_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_tarefas_ortomapa FOREIGN KEY (ortomapa_id)
        REFERENCES ortomapas(id) ON DELETE CASCADE ON UPDATE CASCADE,

    INDEX idx_tarefas_ortomapa_id (ortomapa_id),
    INDEX idx_tarefas_status (status),
    INDEX idx_tarefas_agente (agente),
    INDEX idx_tarefas_prioridade (prioridade),
    INDEX idx_tarefas_tipo (tipo_tarefa),
    INDEX idx_tarefas_status_prioridade (status, prioridade),
    FULLTEXT INDEX ft_tarefas_erro (erro_msg)
) ENGINE=InnoDB;

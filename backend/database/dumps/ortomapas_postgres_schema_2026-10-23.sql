--
-- PostgreSQL database dump
--

-- Dumped from database version 16.15 (Debian 16.15-1.pgdg11+2)
-- Dumped by pg_dump version 16.4 (Debian 16.4-1.pgdg110+2)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: postgis; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS postgis WITH SCHEMA public;


--
-- Name: EXTENSION postgis; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION postgis IS 'PostGIS geometry and geography spatial types and functions';


--
-- Name: postgis_raster; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS postgis_raster WITH SCHEMA public;


--
-- Name: EXTENSION postgis_raster; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION postgis_raster IS 'PostGIS raster types and functions';


SET default_table_access_method = heap;

--
-- Name: analises; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.analises (
    id bigint NOT NULL,
    ortomapa_id bigint NOT NULL,
    projeto_id bigint NOT NULL,
    tipo_analise character varying(80) NOT NULL,
    nome character varying(255) NOT NULL,
    descricao text,
    parametros jsonb,
    resultado_path text,
    resultado_thumbnail text,
    resultado_json jsonb,
    modelo_ia character varying(255),
    versao_modelo character varying(50),
    metricas jsonb,
    agente_ia character varying(255),
    status character varying(30) DEFAULT 'pendente'::character varying,
    tempo_processamento_seg double precision,
    data_analise timestamp with time zone,
    observacoes text,
    criado_em timestamp with time zone DEFAULT now() NOT NULL,
    atualizado_em timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: analises_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.analises_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: analises_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.analises_id_seq OWNED BY public.analises.id;


--
-- Name: anotacoes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.anotacoes (
    id bigint NOT NULL,
    ortomapa_id bigint NOT NULL,
    analise_id bigint,
    tipo character varying(30) NOT NULL,
    categoria character varying(255),
    rotulo character varying(255),
    geometria_wkt text,
    centro_lat double precision,
    centro_lon double precision,
    area_m2 double precision,
    atributos jsonb,
    confianca double precision,
    fonte character varying(30) DEFAULT 'manual'::character varying,
    criado_por bigint,
    criado_em timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: anotacoes_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.anotacoes_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: anotacoes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.anotacoes_id_seq OWNED BY public.anotacoes.id;


--
-- Name: auditoria; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.auditoria (
    id bigint NOT NULL,
    usuario_id bigint,
    acao character varying(80) NOT NULL,
    entidade character varying(80),
    entidade_id bigint,
    detalhes jsonb,
    ip inet,
    criado_em timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: auditoria_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.auditoria_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: auditoria_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.auditoria_id_seq OWNED BY public.auditoria.id;


--
-- Name: camadas_copiloto; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.camadas_copiloto (
    id bigint NOT NULL,
    projeto_id bigint NOT NULL,
    usuario_id bigint,
    nome character varying(255) NOT NULL,
    ferramenta character varying(100) NOT NULL,
    geojson jsonb NOT NULL,
    parametros jsonb DEFAULT '{}'::jsonb,
    criado_em timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: camadas_copiloto_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.camadas_copiloto_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: camadas_copiloto_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.camadas_copiloto_id_seq OWNED BY public.camadas_copiloto.id;


--
-- Name: comparacoes_temporais; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.comparacoes_temporais (
    id bigint NOT NULL,
    projeto_id bigint NOT NULL,
    ortomapa_antes_id bigint NOT NULL,
    ortomapa_depois_id bigint NOT NULL,
    data_antes timestamp with time zone NOT NULL,
    data_depois timestamp with time zone NOT NULL,
    tipo_comparacao character varying(50) NOT NULL,
    resultado_path text,
    resultado_thumbnail text,
    estatisticas jsonb,
    observacoes text,
    criado_em timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: comparacoes_temporais_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.comparacoes_temporais_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: comparacoes_temporais_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.comparacoes_temporais_id_seq OWNED BY public.comparacoes_temporais.id;


--
-- Name: copilot_memorias; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.copilot_memorias (
    id bigint NOT NULL,
    projeto_id bigint NOT NULL,
    usuario_id bigint,
    chave character varying(255) NOT NULL,
    valor jsonb NOT NULL,
    origem character varying(50) DEFAULT 'copiloto'::character varying,
    atualizado_em timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: copilot_memorias_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.copilot_memorias_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: copilot_memorias_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.copilot_memorias_id_seq OWNED BY public.copilot_memorias.id;


--
-- Name: copilot_messages; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.copilot_messages (
    id bigint NOT NULL,
    thread_id bigint NOT NULL,
    papel character varying(20) NOT NULL,
    conteudo text NOT NULL,
    ferramentas jsonb,
    criado_em timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: copilot_messages_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.copilot_messages_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: copilot_messages_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.copilot_messages_id_seq OWNED BY public.copilot_messages.id;


--
-- Name: copilot_threads; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.copilot_threads (
    id bigint NOT NULL,
    projeto_id bigint,
    usuario_id bigint,
    titulo character varying(255),
    resumo text,
    estado jsonb DEFAULT '{}'::jsonb NOT NULL,
    criado_em timestamp with time zone DEFAULT now() NOT NULL,
    atualizado_em timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: copilot_threads_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.copilot_threads_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: copilot_threads_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.copilot_threads_id_seq OWNED BY public.copilot_threads.id;


--
-- Name: gcps; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.gcps (
    id bigint NOT NULL,
    projeto_id bigint NOT NULL,
    voo_id bigint,
    nome character varying(255) NOT NULL,
    latitude double precision NOT NULL,
    longitude double precision NOT NULL,
    altitude_m double precision,
    precisao_horizontal_m double precision,
    precisao_vertical_m double precision,
    metodo_coleta character varying(100),
    equipamento character varying(255),
    data_coleta timestamp with time zone,
    observacoes text,
    criado_em timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: gcps_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.gcps_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: gcps_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.gcps_id_seq OWNED BY public.gcps.id;


--
-- Name: metricas_processamento; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.metricas_processamento (
    processamento_id bigint NOT NULL,
    imagens_recebidas integer,
    imagens_usadas integer,
    gsd_cm double precision,
    erro_rms double precision,
    pontos bigint,
    tempo_segundos double precision,
    alertas jsonb,
    criado_em timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: missoes_areas; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.missoes_areas (
    id bigint NOT NULL,
    missao_id bigint NOT NULL,
    tipo character varying(30) NOT NULL,
    nome character varying(255),
    geometria public.geometry(Geometry,4326) NOT NULL,
    propriedades jsonb DEFAULT '{}'::jsonb NOT NULL,
    criado_em timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: missoes_areas_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.missoes_areas_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: missoes_areas_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.missoes_areas_id_seq OWNED BY public.missoes_areas.id;


--
-- Name: missoes_blocos; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.missoes_blocos (
    id bigint NOT NULL,
    missao_id bigint NOT NULL,
    ordem integer NOT NULL,
    nome character varying(80) NOT NULL,
    estimativa_fotos integer,
    distancia_m double precision,
    tempo_segundos double precision,
    bateria integer,
    status character varying(30) DEFAULT 'rascunho'::character varying NOT NULL,
    propriedades jsonb DEFAULT '{}'::jsonb NOT NULL
);


--
-- Name: missoes_blocos_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.missoes_blocos_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: missoes_blocos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.missoes_blocos_id_seq OWNED BY public.missoes_blocos.id;


--
-- Name: missoes_captura; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.missoes_captura (
    id bigint NOT NULL,
    projeto_id bigint NOT NULL,
    nome character varying(255) NOT NULL,
    descricao text,
    status character varying(30) DEFAULT 'rascunho'::character varying NOT NULL,
    versao integer DEFAULT 1 NOT NULL,
    drone_perfil jsonb DEFAULT '{}'::jsonb NOT NULL,
    camera_perfil jsonb DEFAULT '{}'::jsonb NOT NULL,
    crs character varying(32) DEFAULT 'EPSG:4326'::character varying NOT NULL,
    takeoff jsonb DEFAULT '{}'::jsonb NOT NULL,
    canonical jsonb DEFAULT '{}'::jsonb NOT NULL,
    criado_por bigint,
    revisado_por bigint,
    criado_em timestamp with time zone DEFAULT now() NOT NULL,
    atualizado_em timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: missoes_captura_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.missoes_captura_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: missoes_captura_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.missoes_captura_id_seq OWNED BY public.missoes_captura.id;


--
-- Name: missoes_execucoes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.missoes_execucoes (
    id bigint NOT NULL,
    missao_id bigint NOT NULL,
    voo_id bigint,
    operador_id bigint,
    status character varying(30) DEFAULT 'planejada'::character varying NOT NULL,
    inicio_em timestamp with time zone,
    fim_em timestamp with time zone,
    clima jsonb DEFAULT '{}'::jsonb NOT NULL,
    observacoes text,
    criado_em timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: missoes_execucoes_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.missoes_execucoes_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: missoes_execucoes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.missoes_execucoes_id_seq OWNED BY public.missoes_execucoes.id;


--
-- Name: missoes_exportacoes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.missoes_exportacoes (
    id bigint NOT NULL,
    missao_id bigint NOT NULL,
    alvo character varying(40) NOT NULL,
    formato character varying(40) NOT NULL,
    adaptador_versao character varying(30) NOT NULL,
    checksum_sha256 character(64),
    manifesto jsonb DEFAULT '{}'::jsonb NOT NULL,
    caminho text,
    criado_por bigint,
    criado_em timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: missoes_exportacoes_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.missoes_exportacoes_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: missoes_exportacoes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.missoes_exportacoes_id_seq OWNED BY public.missoes_exportacoes.id;


--
-- Name: missoes_fotos; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.missoes_fotos (
    id bigint NOT NULL,
    execucao_id bigint NOT NULL,
    caminho text NOT NULL,
    nome_original text NOT NULL,
    hash_sha256 character(64),
    tamanho_bytes bigint,
    exif jsonb,
    validacao character varying(30) DEFAULT 'pendente'::character varying NOT NULL,
    criado_em timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: missoes_fotos_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.missoes_fotos_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: missoes_fotos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.missoes_fotos_id_seq OWNED BY public.missoes_fotos.id;


--
-- Name: missoes_parametros; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.missoes_parametros (
    missao_id bigint NOT NULL,
    gsd_cm_px double precision,
    overlap_frontal double precision,
    overlap_lateral double precision,
    altitude_m double precision,
    altitude_referencia character varying(20) DEFAULT 'AGL'::character varying NOT NULL,
    velocidade_ms double precision,
    gimbal_graus double precision DEFAULT '-90'::integer,
    intervalo_segundos double precision,
    espacamento_linhas_m double precision,
    reserva_bateria_pct double precision DEFAULT 25,
    parametros jsonb DEFAULT '{}'::jsonb NOT NULL
);


--
-- Name: missoes_validacoes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.missoes_validacoes (
    id bigint NOT NULL,
    missao_id bigint NOT NULL,
    regra character varying(80) NOT NULL,
    severidade character varying(20) NOT NULL,
    status character varying(20) NOT NULL,
    mensagem text NOT NULL,
    valor_observado jsonb,
    geometria public.geometry(Geometry,4326),
    executado_em timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: missoes_validacoes_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.missoes_validacoes_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: missoes_validacoes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.missoes_validacoes_id_seq OWNED BY public.missoes_validacoes.id;


--
-- Name: missoes_waypoints; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.missoes_waypoints (
    id bigint NOT NULL,
    missao_id bigint NOT NULL,
    bloco_id bigint,
    ordem integer NOT NULL,
    geometria public.geometry(Point,4326) NOT NULL,
    altitude_m double precision,
    altitude_agl_m double precision,
    rumo_graus double precision,
    velocidade_ms double precision,
    gimbal_graus double precision,
    acoes jsonb DEFAULT '[]'::jsonb NOT NULL,
    propriedades jsonb DEFAULT '{}'::jsonb NOT NULL
);


--
-- Name: missoes_waypoints_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.missoes_waypoints_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: missoes_waypoints_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.missoes_waypoints_id_seq OWNED BY public.missoes_waypoints.id;


--
-- Name: ortomapas; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ortomapas (
    id bigint NOT NULL,
    voo_id bigint NOT NULL,
    projeto_id bigint NOT NULL,
    nome character varying(255) NOT NULL,
    tipo character varying(40) DEFAULT 'ortomosaico'::character varying NOT NULL,
    formato character varying(50),
    resolucao_cm double precision,
    largura_px integer,
    altura_px integer,
    tamanho_arquivo_mb double precision,
    sistema_coordenadas character varying(100),
    bbox_norte double precision,
    bbox_sul double precision,
    bbox_leste double precision,
    bbox_oeste double precision,
    centro_lat double precision,
    centro_lon double precision,
    caminho_arquivo text,
    caminho_thumbnail text,
    webodm_task_id character varying(255),
    parametros_processamento jsonb,
    qualidade_processamento character varying(50),
    num_fotos_processadas integer,
    tempo_processamento_min double precision,
    erro_rms double precision,
    gcps_utilizados boolean DEFAULT false,
    num_gcps integer DEFAULT 0,
    status character varying(30) DEFAULT 'processando'::character varying,
    data_processamento timestamp with time zone,
    observacoes text,
    criado_em timestamp with time zone DEFAULT now() NOT NULL,
    atualizado_em timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: ortomapas_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.ortomapas_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: ortomapas_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.ortomapas_id_seq OWNED BY public.ortomapas.id;


--
-- Name: processamentos_odm; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.processamentos_odm (
    id bigint NOT NULL,
    projeto_id bigint NOT NULL,
    voo_id bigint NOT NULL,
    odm_task_id character varying(255) NOT NULL,
    endpoint text NOT NULL,
    engine character varying(50),
    engine_version character varying(50),
    parametros jsonb DEFAULT '{}'::jsonb NOT NULL,
    status character varying(30) DEFAULT 'pendente'::character varying NOT NULL,
    progresso numeric(6,2) DEFAULT 0,
    etapa text,
    erro text,
    criado_por bigint,
    inicio_em timestamp with time zone,
    fim_em timestamp with time zone,
    criado_em timestamp with time zone DEFAULT now() NOT NULL,
    atualizado_em timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: processamentos_odm_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.processamentos_odm_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: processamentos_odm_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.processamentos_odm_id_seq OWNED BY public.processamentos_odm.id;


--
-- Name: produtos_processamento; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.produtos_processamento (
    id bigint NOT NULL,
    processamento_id bigint NOT NULL,
    ortomapa_id bigint,
    tipo character varying(40) NOT NULL,
    caminho text NOT NULL,
    formato character varying(50),
    tamanho_arquivo_mb double precision,
    crs character varying(100),
    bbox public.geometry(Polygon,4326),
    resolucao double precision,
    largura_px integer,
    altura_px integer,
    bandas integer,
    status character varying(30) DEFAULT 'disponivel'::character varying NOT NULL,
    criado_em timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: produtos_processamento_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.produtos_processamento_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: produtos_processamento_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.produtos_processamento_id_seq OWNED BY public.produtos_processamento.id;


--
-- Name: projeto_usuarios; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.projeto_usuarios (
    projeto_id bigint NOT NULL,
    usuario_id bigint NOT NULL,
    papel character varying(30) DEFAULT 'visualizador'::character varying NOT NULL,
    criado_em timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: projetos; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.projetos (
    id bigint NOT NULL,
    nome character varying(255) NOT NULL,
    descricao text,
    area_estudo character varying(255),
    bbox_norte double precision,
    bbox_sul double precision,
    bbox_leste double precision,
    bbox_oeste double precision,
    centro_lat double precision,
    centro_lon double precision,
    objetivo text,
    responsavel character varying(255),
    data_inicio date,
    data_fim date,
    status character varying(30) DEFAULT 'planejado'::character varying NOT NULL,
    criado_em timestamp with time zone DEFAULT now() NOT NULL,
    atualizado_em timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: projetos_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.projetos_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: projetos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.projetos_id_seq OWNED BY public.projetos.id;


--
-- Name: tarefas_agentes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tarefas_agentes (
    id bigint NOT NULL,
    ortomapa_id bigint NOT NULL,
    tipo_tarefa character varying(255) NOT NULL,
    agente character varying(255) NOT NULL,
    prioridade integer DEFAULT 5,
    parametros jsonb,
    status character varying(30) DEFAULT 'pendente'::character varying,
    resultado jsonb,
    erro_msg text,
    tentativas integer DEFAULT 0,
    max_tentativas integer DEFAULT 3,
    inicio_execucao timestamp with time zone,
    fim_execucao timestamp with time zone,
    criado_em timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: tarefas_agentes_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tarefas_agentes_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: tarefas_agentes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.tarefas_agentes_id_seq OWNED BY public.tarefas_agentes.id;


--
-- Name: usuarios; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.usuarios (
    id bigint NOT NULL,
    email character varying(320) NOT NULL,
    nome character varying(255) NOT NULL,
    senha_hash text NOT NULL,
    perfil character varying(30) DEFAULT 'pesquisador'::character varying NOT NULL,
    ativo boolean DEFAULT true NOT NULL,
    ultimo_login timestamp with time zone,
    criado_em timestamp with time zone DEFAULT now() NOT NULL,
    atualizado_em timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: usuarios_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.usuarios_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: usuarios_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.usuarios_id_seq OWNED BY public.usuarios.id;


--
-- Name: voo_fotos; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.voo_fotos (
    id bigint NOT NULL,
    voo_id bigint NOT NULL,
    caminho text NOT NULL,
    nome_original text NOT NULL,
    hash_sha256 character(64),
    tamanho_bytes bigint,
    mime_type character varying(100),
    exif jsonb,
    validacao character varying(30) DEFAULT 'pendente'::character varying NOT NULL,
    criado_em timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: voo_fotos_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.voo_fotos_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: voo_fotos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.voo_fotos_id_seq OWNED BY public.voo_fotos.id;


--
-- Name: voos; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.voos (
    id bigint NOT NULL,
    projeto_id bigint NOT NULL,
    data_voo timestamp with time zone NOT NULL,
    local_decolagem_lat double precision,
    local_decolagem_lon double precision,
    altitude_voo_m double precision,
    sobreposicao_frontal double precision,
    sobreposicao_lateral double precision,
    velocidade_ms double precision,
    num_fotos integer,
    resolucao_foto character varying(50),
    formato_foto character varying(20),
    gsd_cm double precision,
    area_coberta_ha double precision,
    num_baterias integer,
    tipo_bateria character varying(100),
    condicoes_vento character varying(100),
    condicoes_ceu character varying(100),
    temperatura_c double precision,
    app_voo character varying(100),
    missao_csv_path text,
    fotos_path text,
    observacoes text,
    criado_em timestamp with time zone DEFAULT now() NOT NULL,
    atualizado_em timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: voos_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.voos_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: voos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.voos_id_seq OWNED BY public.voos.id;


--
-- Name: analises id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.analises ALTER COLUMN id SET DEFAULT nextval('public.analises_id_seq'::regclass);


--
-- Name: anotacoes id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.anotacoes ALTER COLUMN id SET DEFAULT nextval('public.anotacoes_id_seq'::regclass);


--
-- Name: auditoria id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auditoria ALTER COLUMN id SET DEFAULT nextval('public.auditoria_id_seq'::regclass);


--
-- Name: camadas_copiloto id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.camadas_copiloto ALTER COLUMN id SET DEFAULT nextval('public.camadas_copiloto_id_seq'::regclass);


--
-- Name: comparacoes_temporais id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.comparacoes_temporais ALTER COLUMN id SET DEFAULT nextval('public.comparacoes_temporais_id_seq'::regclass);


--
-- Name: copilot_memorias id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.copilot_memorias ALTER COLUMN id SET DEFAULT nextval('public.copilot_memorias_id_seq'::regclass);


--
-- Name: copilot_messages id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.copilot_messages ALTER COLUMN id SET DEFAULT nextval('public.copilot_messages_id_seq'::regclass);


--
-- Name: copilot_threads id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.copilot_threads ALTER COLUMN id SET DEFAULT nextval('public.copilot_threads_id_seq'::regclass);


--
-- Name: gcps id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.gcps ALTER COLUMN id SET DEFAULT nextval('public.gcps_id_seq'::regclass);


--
-- Name: missoes_areas id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.missoes_areas ALTER COLUMN id SET DEFAULT nextval('public.missoes_areas_id_seq'::regclass);


--
-- Name: missoes_blocos id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.missoes_blocos ALTER COLUMN id SET DEFAULT nextval('public.missoes_blocos_id_seq'::regclass);


--
-- Name: missoes_captura id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.missoes_captura ALTER COLUMN id SET DEFAULT nextval('public.missoes_captura_id_seq'::regclass);


--
-- Name: missoes_execucoes id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.missoes_execucoes ALTER COLUMN id SET DEFAULT nextval('public.missoes_execucoes_id_seq'::regclass);


--
-- Name: missoes_exportacoes id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.missoes_exportacoes ALTER COLUMN id SET DEFAULT nextval('public.missoes_exportacoes_id_seq'::regclass);


--
-- Name: missoes_fotos id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.missoes_fotos ALTER COLUMN id SET DEFAULT nextval('public.missoes_fotos_id_seq'::regclass);


--
-- Name: missoes_validacoes id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.missoes_validacoes ALTER COLUMN id SET DEFAULT nextval('public.missoes_validacoes_id_seq'::regclass);


--
-- Name: missoes_waypoints id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.missoes_waypoints ALTER COLUMN id SET DEFAULT nextval('public.missoes_waypoints_id_seq'::regclass);


--
-- Name: ortomapas id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ortomapas ALTER COLUMN id SET DEFAULT nextval('public.ortomapas_id_seq'::regclass);


--
-- Name: processamentos_odm id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.processamentos_odm ALTER COLUMN id SET DEFAULT nextval('public.processamentos_odm_id_seq'::regclass);


--
-- Name: produtos_processamento id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.produtos_processamento ALTER COLUMN id SET DEFAULT nextval('public.produtos_processamento_id_seq'::regclass);


--
-- Name: projetos id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projetos ALTER COLUMN id SET DEFAULT nextval('public.projetos_id_seq'::regclass);


--
-- Name: tarefas_agentes id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tarefas_agentes ALTER COLUMN id SET DEFAULT nextval('public.tarefas_agentes_id_seq'::regclass);


--
-- Name: usuarios id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuarios ALTER COLUMN id SET DEFAULT nextval('public.usuarios_id_seq'::regclass);


--
-- Name: voo_fotos id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.voo_fotos ALTER COLUMN id SET DEFAULT nextval('public.voo_fotos_id_seq'::regclass);


--
-- Name: voos id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.voos ALTER COLUMN id SET DEFAULT nextval('public.voos_id_seq'::regclass);


--
-- Name: analises analises_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.analises
    ADD CONSTRAINT analises_pkey PRIMARY KEY (id);


--
-- Name: anotacoes anotacoes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.anotacoes
    ADD CONSTRAINT anotacoes_pkey PRIMARY KEY (id);


--
-- Name: auditoria auditoria_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auditoria
    ADD CONSTRAINT auditoria_pkey PRIMARY KEY (id);


--
-- Name: camadas_copiloto camadas_copiloto_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.camadas_copiloto
    ADD CONSTRAINT camadas_copiloto_pkey PRIMARY KEY (id);


--
-- Name: comparacoes_temporais comparacoes_temporais_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.comparacoes_temporais
    ADD CONSTRAINT comparacoes_temporais_pkey PRIMARY KEY (id);


--
-- Name: copilot_memorias copilot_memorias_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.copilot_memorias
    ADD CONSTRAINT copilot_memorias_pkey PRIMARY KEY (id);


--
-- Name: copilot_memorias copilot_memorias_projeto_id_usuario_id_chave_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.copilot_memorias
    ADD CONSTRAINT copilot_memorias_projeto_id_usuario_id_chave_key UNIQUE (projeto_id, usuario_id, chave);


--
-- Name: copilot_messages copilot_messages_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.copilot_messages
    ADD CONSTRAINT copilot_messages_pkey PRIMARY KEY (id);


--
-- Name: copilot_threads copilot_threads_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.copilot_threads
    ADD CONSTRAINT copilot_threads_pkey PRIMARY KEY (id);


--
-- Name: gcps gcps_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.gcps
    ADD CONSTRAINT gcps_pkey PRIMARY KEY (id);


--
-- Name: metricas_processamento metricas_processamento_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.metricas_processamento
    ADD CONSTRAINT metricas_processamento_pkey PRIMARY KEY (processamento_id);


--
-- Name: missoes_areas missoes_areas_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.missoes_areas
    ADD CONSTRAINT missoes_areas_pkey PRIMARY KEY (id);


--
-- Name: missoes_blocos missoes_blocos_missao_id_ordem_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.missoes_blocos
    ADD CONSTRAINT missoes_blocos_missao_id_ordem_key UNIQUE (missao_id, ordem);


--
-- Name: missoes_blocos missoes_blocos_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.missoes_blocos
    ADD CONSTRAINT missoes_blocos_pkey PRIMARY KEY (id);


--
-- Name: missoes_captura missoes_captura_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.missoes_captura
    ADD CONSTRAINT missoes_captura_pkey PRIMARY KEY (id);


--
-- Name: missoes_execucoes missoes_execucoes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.missoes_execucoes
    ADD CONSTRAINT missoes_execucoes_pkey PRIMARY KEY (id);


--
-- Name: missoes_exportacoes missoes_exportacoes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.missoes_exportacoes
    ADD CONSTRAINT missoes_exportacoes_pkey PRIMARY KEY (id);


--
-- Name: missoes_fotos missoes_fotos_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.missoes_fotos
    ADD CONSTRAINT missoes_fotos_pkey PRIMARY KEY (id);


--
-- Name: missoes_parametros missoes_parametros_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.missoes_parametros
    ADD CONSTRAINT missoes_parametros_pkey PRIMARY KEY (missao_id);


--
-- Name: missoes_validacoes missoes_validacoes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.missoes_validacoes
    ADD CONSTRAINT missoes_validacoes_pkey PRIMARY KEY (id);


--
-- Name: missoes_waypoints missoes_waypoints_missao_id_ordem_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.missoes_waypoints
    ADD CONSTRAINT missoes_waypoints_missao_id_ordem_key UNIQUE (missao_id, ordem);


--
-- Name: missoes_waypoints missoes_waypoints_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.missoes_waypoints
    ADD CONSTRAINT missoes_waypoints_pkey PRIMARY KEY (id);


--
-- Name: ortomapas ortomapas_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ortomapas
    ADD CONSTRAINT ortomapas_pkey PRIMARY KEY (id);


--
-- Name: processamentos_odm processamentos_odm_odm_task_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.processamentos_odm
    ADD CONSTRAINT processamentos_odm_odm_task_id_key UNIQUE (odm_task_id);


--
-- Name: processamentos_odm processamentos_odm_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.processamentos_odm
    ADD CONSTRAINT processamentos_odm_pkey PRIMARY KEY (id);


--
-- Name: produtos_processamento produtos_processamento_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.produtos_processamento
    ADD CONSTRAINT produtos_processamento_pkey PRIMARY KEY (id);


--
-- Name: projeto_usuarios projeto_usuarios_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projeto_usuarios
    ADD CONSTRAINT projeto_usuarios_pkey PRIMARY KEY (projeto_id, usuario_id);


--
-- Name: projetos projetos_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projetos
    ADD CONSTRAINT projetos_pkey PRIMARY KEY (id);


--
-- Name: tarefas_agentes tarefas_agentes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tarefas_agentes
    ADD CONSTRAINT tarefas_agentes_pkey PRIMARY KEY (id);


--
-- Name: usuarios usuarios_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_email_key UNIQUE (email);


--
-- Name: usuarios usuarios_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_pkey PRIMARY KEY (id);


--
-- Name: voo_fotos voo_fotos_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.voo_fotos
    ADD CONSTRAINT voo_fotos_pkey PRIMARY KEY (id);


--
-- Name: voos voos_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.voos
    ADD CONSTRAINT voos_pkey PRIMARY KEY (id);


--
-- Name: idx_missoes_areas_geom; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_missoes_areas_geom ON public.missoes_areas USING gist (geometria);


--
-- Name: idx_missoes_captura_projeto; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_missoes_captura_projeto ON public.missoes_captura USING btree (projeto_id, atualizado_em DESC);


--
-- Name: idx_missoes_validacoes_missao; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_missoes_validacoes_missao ON public.missoes_validacoes USING btree (missao_id, executado_em DESC);


--
-- Name: idx_missoes_waypoints_geom; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_missoes_waypoints_geom ON public.missoes_waypoints USING gist (geometria);


--
-- Name: idx_ortomapas_projeto; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ortomapas_projeto ON public.ortomapas USING btree (projeto_id);


--
-- Name: idx_ortomapas_task; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ortomapas_task ON public.ortomapas USING btree (webodm_task_id);


--
-- Name: idx_processamentos_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_processamentos_status ON public.processamentos_odm USING btree (status);


--
-- Name: idx_produtos_bbox; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_produtos_bbox ON public.produtos_processamento USING gist (bbox);


--
-- Name: idx_projetos_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_projetos_status ON public.projetos USING btree (status);


--
-- Name: idx_voos_projeto; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_voos_projeto ON public.voos USING btree (projeto_id);


--
-- Name: analises analises_ortomapa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.analises
    ADD CONSTRAINT analises_ortomapa_id_fkey FOREIGN KEY (ortomapa_id) REFERENCES public.ortomapas(id) ON DELETE CASCADE;


--
-- Name: analises analises_projeto_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.analises
    ADD CONSTRAINT analises_projeto_id_fkey FOREIGN KEY (projeto_id) REFERENCES public.projetos(id) ON DELETE CASCADE;


--
-- Name: anotacoes anotacoes_analise_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.anotacoes
    ADD CONSTRAINT anotacoes_analise_id_fkey FOREIGN KEY (analise_id) REFERENCES public.analises(id) ON DELETE SET NULL;


--
-- Name: anotacoes anotacoes_criado_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.anotacoes
    ADD CONSTRAINT anotacoes_criado_por_fkey FOREIGN KEY (criado_por) REFERENCES public.usuarios(id) ON DELETE SET NULL;


--
-- Name: anotacoes anotacoes_ortomapa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.anotacoes
    ADD CONSTRAINT anotacoes_ortomapa_id_fkey FOREIGN KEY (ortomapa_id) REFERENCES public.ortomapas(id) ON DELETE CASCADE;


--
-- Name: auditoria auditoria_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auditoria
    ADD CONSTRAINT auditoria_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id) ON DELETE SET NULL;


--
-- Name: camadas_copiloto camadas_copiloto_projeto_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.camadas_copiloto
    ADD CONSTRAINT camadas_copiloto_projeto_id_fkey FOREIGN KEY (projeto_id) REFERENCES public.projetos(id) ON DELETE CASCADE;


--
-- Name: camadas_copiloto camadas_copiloto_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.camadas_copiloto
    ADD CONSTRAINT camadas_copiloto_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id) ON DELETE SET NULL;


--
-- Name: comparacoes_temporais comparacoes_temporais_ortomapa_antes_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.comparacoes_temporais
    ADD CONSTRAINT comparacoes_temporais_ortomapa_antes_id_fkey FOREIGN KEY (ortomapa_antes_id) REFERENCES public.ortomapas(id) ON DELETE CASCADE;


--
-- Name: comparacoes_temporais comparacoes_temporais_ortomapa_depois_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.comparacoes_temporais
    ADD CONSTRAINT comparacoes_temporais_ortomapa_depois_id_fkey FOREIGN KEY (ortomapa_depois_id) REFERENCES public.ortomapas(id) ON DELETE CASCADE;


--
-- Name: comparacoes_temporais comparacoes_temporais_projeto_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.comparacoes_temporais
    ADD CONSTRAINT comparacoes_temporais_projeto_id_fkey FOREIGN KEY (projeto_id) REFERENCES public.projetos(id) ON DELETE CASCADE;


--
-- Name: copilot_memorias copilot_memorias_projeto_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.copilot_memorias
    ADD CONSTRAINT copilot_memorias_projeto_id_fkey FOREIGN KEY (projeto_id) REFERENCES public.projetos(id) ON DELETE CASCADE;


--
-- Name: copilot_memorias copilot_memorias_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.copilot_memorias
    ADD CONSTRAINT copilot_memorias_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id) ON DELETE SET NULL;


--
-- Name: copilot_messages copilot_messages_thread_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.copilot_messages
    ADD CONSTRAINT copilot_messages_thread_id_fkey FOREIGN KEY (thread_id) REFERENCES public.copilot_threads(id) ON DELETE CASCADE;


--
-- Name: copilot_threads copilot_threads_projeto_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.copilot_threads
    ADD CONSTRAINT copilot_threads_projeto_id_fkey FOREIGN KEY (projeto_id) REFERENCES public.projetos(id) ON DELETE CASCADE;


--
-- Name: copilot_threads copilot_threads_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.copilot_threads
    ADD CONSTRAINT copilot_threads_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id) ON DELETE CASCADE;


--
-- Name: gcps gcps_projeto_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.gcps
    ADD CONSTRAINT gcps_projeto_id_fkey FOREIGN KEY (projeto_id) REFERENCES public.projetos(id) ON DELETE CASCADE;


--
-- Name: gcps gcps_voo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.gcps
    ADD CONSTRAINT gcps_voo_id_fkey FOREIGN KEY (voo_id) REFERENCES public.voos(id) ON DELETE SET NULL;


--
-- Name: metricas_processamento metricas_processamento_processamento_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.metricas_processamento
    ADD CONSTRAINT metricas_processamento_processamento_id_fkey FOREIGN KEY (processamento_id) REFERENCES public.processamentos_odm(id) ON DELETE CASCADE;


--
-- Name: missoes_areas missoes_areas_missao_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.missoes_areas
    ADD CONSTRAINT missoes_areas_missao_id_fkey FOREIGN KEY (missao_id) REFERENCES public.missoes_captura(id) ON DELETE CASCADE;


--
-- Name: missoes_blocos missoes_blocos_missao_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.missoes_blocos
    ADD CONSTRAINT missoes_blocos_missao_id_fkey FOREIGN KEY (missao_id) REFERENCES public.missoes_captura(id) ON DELETE CASCADE;


--
-- Name: missoes_captura missoes_captura_criado_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.missoes_captura
    ADD CONSTRAINT missoes_captura_criado_por_fkey FOREIGN KEY (criado_por) REFERENCES public.usuarios(id) ON DELETE SET NULL;


--
-- Name: missoes_captura missoes_captura_projeto_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.missoes_captura
    ADD CONSTRAINT missoes_captura_projeto_id_fkey FOREIGN KEY (projeto_id) REFERENCES public.projetos(id) ON DELETE CASCADE;


--
-- Name: missoes_captura missoes_captura_revisado_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.missoes_captura
    ADD CONSTRAINT missoes_captura_revisado_por_fkey FOREIGN KEY (revisado_por) REFERENCES public.usuarios(id) ON DELETE SET NULL;


--
-- Name: missoes_execucoes missoes_execucoes_missao_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.missoes_execucoes
    ADD CONSTRAINT missoes_execucoes_missao_id_fkey FOREIGN KEY (missao_id) REFERENCES public.missoes_captura(id) ON DELETE CASCADE;


--
-- Name: missoes_execucoes missoes_execucoes_operador_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.missoes_execucoes
    ADD CONSTRAINT missoes_execucoes_operador_id_fkey FOREIGN KEY (operador_id) REFERENCES public.usuarios(id) ON DELETE SET NULL;


--
-- Name: missoes_execucoes missoes_execucoes_voo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.missoes_execucoes
    ADD CONSTRAINT missoes_execucoes_voo_id_fkey FOREIGN KEY (voo_id) REFERENCES public.voos(id) ON DELETE SET NULL;


--
-- Name: missoes_exportacoes missoes_exportacoes_criado_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.missoes_exportacoes
    ADD CONSTRAINT missoes_exportacoes_criado_por_fkey FOREIGN KEY (criado_por) REFERENCES public.usuarios(id) ON DELETE SET NULL;


--
-- Name: missoes_exportacoes missoes_exportacoes_missao_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.missoes_exportacoes
    ADD CONSTRAINT missoes_exportacoes_missao_id_fkey FOREIGN KEY (missao_id) REFERENCES public.missoes_captura(id) ON DELETE CASCADE;


--
-- Name: missoes_fotos missoes_fotos_execucao_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.missoes_fotos
    ADD CONSTRAINT missoes_fotos_execucao_id_fkey FOREIGN KEY (execucao_id) REFERENCES public.missoes_execucoes(id) ON DELETE CASCADE;


--
-- Name: missoes_parametros missoes_parametros_missao_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.missoes_parametros
    ADD CONSTRAINT missoes_parametros_missao_id_fkey FOREIGN KEY (missao_id) REFERENCES public.missoes_captura(id) ON DELETE CASCADE;


--
-- Name: missoes_validacoes missoes_validacoes_missao_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.missoes_validacoes
    ADD CONSTRAINT missoes_validacoes_missao_id_fkey FOREIGN KEY (missao_id) REFERENCES public.missoes_captura(id) ON DELETE CASCADE;


--
-- Name: missoes_waypoints missoes_waypoints_bloco_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.missoes_waypoints
    ADD CONSTRAINT missoes_waypoints_bloco_id_fkey FOREIGN KEY (bloco_id) REFERENCES public.missoes_blocos(id) ON DELETE SET NULL;


--
-- Name: missoes_waypoints missoes_waypoints_missao_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.missoes_waypoints
    ADD CONSTRAINT missoes_waypoints_missao_id_fkey FOREIGN KEY (missao_id) REFERENCES public.missoes_captura(id) ON DELETE CASCADE;


--
-- Name: ortomapas ortomapas_projeto_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ortomapas
    ADD CONSTRAINT ortomapas_projeto_id_fkey FOREIGN KEY (projeto_id) REFERENCES public.projetos(id) ON DELETE CASCADE;


--
-- Name: ortomapas ortomapas_voo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ortomapas
    ADD CONSTRAINT ortomapas_voo_id_fkey FOREIGN KEY (voo_id) REFERENCES public.voos(id) ON DELETE CASCADE;


--
-- Name: processamentos_odm processamentos_odm_criado_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.processamentos_odm
    ADD CONSTRAINT processamentos_odm_criado_por_fkey FOREIGN KEY (criado_por) REFERENCES public.usuarios(id) ON DELETE SET NULL;


--
-- Name: processamentos_odm processamentos_odm_projeto_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.processamentos_odm
    ADD CONSTRAINT processamentos_odm_projeto_id_fkey FOREIGN KEY (projeto_id) REFERENCES public.projetos(id) ON DELETE CASCADE;


--
-- Name: processamentos_odm processamentos_odm_voo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.processamentos_odm
    ADD CONSTRAINT processamentos_odm_voo_id_fkey FOREIGN KEY (voo_id) REFERENCES public.voos(id) ON DELETE CASCADE;


--
-- Name: produtos_processamento produtos_processamento_ortomapa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.produtos_processamento
    ADD CONSTRAINT produtos_processamento_ortomapa_id_fkey FOREIGN KEY (ortomapa_id) REFERENCES public.ortomapas(id) ON DELETE SET NULL;


--
-- Name: produtos_processamento produtos_processamento_processamento_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.produtos_processamento
    ADD CONSTRAINT produtos_processamento_processamento_id_fkey FOREIGN KEY (processamento_id) REFERENCES public.processamentos_odm(id) ON DELETE CASCADE;


--
-- Name: projeto_usuarios projeto_usuarios_projeto_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projeto_usuarios
    ADD CONSTRAINT projeto_usuarios_projeto_id_fkey FOREIGN KEY (projeto_id) REFERENCES public.projetos(id) ON DELETE CASCADE;


--
-- Name: projeto_usuarios projeto_usuarios_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projeto_usuarios
    ADD CONSTRAINT projeto_usuarios_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id) ON DELETE CASCADE;


--
-- Name: tarefas_agentes tarefas_agentes_ortomapa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tarefas_agentes
    ADD CONSTRAINT tarefas_agentes_ortomapa_id_fkey FOREIGN KEY (ortomapa_id) REFERENCES public.ortomapas(id) ON DELETE CASCADE;


--
-- Name: voo_fotos voo_fotos_voo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.voo_fotos
    ADD CONSTRAINT voo_fotos_voo_id_fkey FOREIGN KEY (voo_id) REFERENCES public.voos(id) ON DELETE CASCADE;


--
-- Name: voos voos_projeto_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.voos
    ADD CONSTRAINT voos_projeto_id_fkey FOREIGN KEY (projeto_id) REFERENCES public.projetos(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

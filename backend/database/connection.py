"""
MySQL connection pool and database helpers for the ortomapas system.

Uses mysql.connector.pooling for efficient connection management.
"""

import os
import logging
from pathlib import Path
from contextlib import contextmanager
from typing import Any, Optional

import mysql.connector
import psycopg2
from psycopg2 import pool as pg_pool
from psycopg2.extras import RealDictCursor
from mysql.connector import pooling, Error as MySQLError

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")
except ImportError:
    pass

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "ortomapas"),
    "charset": "utf8mb4",
    "collation": "utf8mb4_unicode_ci",
    "autocommit": True,
    "use_pure": True,
}
DB_ENGINE = os.getenv("DB_ENGINE", "postgres").lower()
PG_CONFIG = {
    "host": os.getenv("PGHOST", os.getenv("DB_HOST", "localhost")),
    "port": int(os.getenv("PGPORT", os.getenv("DB_PORT", "5433"))),
    "user": os.getenv("PGUSER", os.getenv("DB_USER", "geo")),
    "password": os.getenv("PGPASSWORD") or os.getenv("GEOAGENTICA_DB_PASSWORD") or os.getenv("DB_PASSWORD", ""),
    "dbname": os.getenv("PGDATABASE", os.getenv("DB_NAME", "ortomapas")),
}

POOL_NAME = "ortomapas_pool"
POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))

# ---------------------------------------------------------------------------
# Connection pool (lazy initialised)
# ---------------------------------------------------------------------------
_pool: Optional[pooling.MySQLConnectionPool] = None
_pg_pool: Optional[pg_pool.ThreadedConnectionPool] = None


_use_sqlite = False
_sqlite_conn = None


class _PGConnWrapper:
    """Adapt psycopg2 to the cursor(dictionary=True) API used by routers."""
    def __init__(self, conn):
        self._conn = conn

    def cursor(self, dictionary=False):
        return self._conn.cursor(cursor_factory=RealDictCursor if dictionary else None)

    def commit(self):
        return self._conn.commit()

    def rollback(self):
        return self._conn.rollback()

    def is_connected(self):
        return self._conn.closed == 0


def _get_pool():
    """Return the shared connection pool, creating it on first call.
    Falls back to SQLite if MySQL is unreachable."""
    global _pool, _use_sqlite
    if DB_ENGINE == "postgres":
        global _pg_pool
        if _pg_pool is None:
            logger.info("Creating PostgreSQL pool -> %s:%s/%s", PG_CONFIG["host"], PG_CONFIG["port"], PG_CONFIG["dbname"])
            _pg_pool = pg_pool.ThreadedConnectionPool(1, POOL_SIZE, **PG_CONFIG)
        return _pg_pool
    if _use_sqlite:
        return None
    if _pool is None:
        try:
            logger.info(
                "Creating MySQL connection pool '%s' (size=%d) -> %s:%s/%s",
                POOL_NAME,
                POOL_SIZE,
                DB_CONFIG["host"],
                DB_CONFIG["port"],
                DB_CONFIG["database"],
            )
            _pool = pooling.MySQLConnectionPool(
                pool_name=POOL_NAME,
                pool_size=POOL_SIZE,
                pool_reset_session=True,
                **DB_CONFIG,
            )
        except Exception as e:
            logger.warning("MySQL unavailable (%s), falling back to SQLite", e)
            _use_sqlite = True
            _init_sqlite()
            return None
    return _pool


def reset_pool() -> None:
    """Tear down the current pool so the next call creates a fresh one."""
    global _pool, _pg_pool
    _pool = None
    if _pg_pool is not None:
        _pg_pool.closeall()
        _pg_pool = None
    logger.info("Connection pool reset.")


# ---------------------------------------------------------------------------
# Context manager
# ---------------------------------------------------------------------------
def _init_sqlite():
    """Initialize SQLite fallback database."""
    global _sqlite_conn
    import sqlite3
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "ortomapas.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    _sqlite_conn = sqlite3.connect(db_path, check_same_thread=False)
    _sqlite_conn.row_factory = sqlite3.Row
    _sqlite_conn.execute("PRAGMA journal_mode=WAL")
    # Create tables (simplified SQLite schema)
    _sqlite_conn.executescript("""
        CREATE TABLE IF NOT EXISTS projetos (
            id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL, descricao TEXT,
            area_estudo TEXT, bbox_norte REAL, bbox_sul REAL, bbox_leste REAL, bbox_oeste REAL,
            centro_lat REAL, centro_lon REAL, objetivo TEXT, responsavel TEXT,
            data_inicio TEXT, data_fim TEXT, status TEXT DEFAULT 'planejado',
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP, atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS voos (
            id INTEGER PRIMARY KEY AUTOINCREMENT, projeto_id INTEGER, data_voo TEXT,
            local_decolagem_lat REAL, local_decolagem_lon REAL, altitude_voo_m REAL,
            sobreposicao_frontal REAL, sobreposicao_lateral REAL, velocidade_ms REAL,
            num_fotos INTEGER, resolucao_foto TEXT, formato_foto TEXT, gsd_cm REAL,
            area_coberta_ha REAL, num_baterias INTEGER, tipo_bateria TEXT,
            condicoes_vento TEXT, condicoes_ceu TEXT, temperatura_c REAL,
            app_voo TEXT, missao_csv_path TEXT, fotos_path TEXT, observacoes TEXT,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS ortomapas (
            id INTEGER PRIMARY KEY AUTOINCREMENT, voo_id INTEGER, projeto_id INTEGER,
            nome TEXT NOT NULL, tipo TEXT, formato TEXT, resolucao_cm REAL,
            largura_px INTEGER, altura_px INTEGER, tamanho_arquivo_mb REAL,
            sistema_coordenadas TEXT, bbox_norte REAL, bbox_sul REAL, bbox_leste REAL, bbox_oeste REAL,
            centro_lat REAL, centro_lon REAL, caminho_arquivo TEXT, caminho_thumbnail TEXT,
            webodm_task_id TEXT, parametros_processamento TEXT, qualidade_processamento TEXT,
            num_fotos_processadas INTEGER, tempo_processamento_min INTEGER, erro_rms REAL,
            gcps_utilizados INTEGER DEFAULT 0, num_gcps INTEGER DEFAULT 0,
            status TEXT DEFAULT 'processando', data_processamento TEXT, observacoes TEXT,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP, atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS analises (
            id INTEGER PRIMARY KEY AUTOINCREMENT, ortomapa_id INTEGER, projeto_id INTEGER,
            tipo_analise TEXT, nome TEXT, descricao TEXT, parametros TEXT,
            resultado_path TEXT, resultado_thumbnail TEXT, resultado_json TEXT,
            modelo_ia TEXT, versao_modelo TEXT, metricas TEXT, agente_ia TEXT,
            status TEXT DEFAULT 'em_fila', tempo_processamento_seg INTEGER,
            data_analise TEXT, observacoes TEXT, criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS anotacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT, ortomapa_id INTEGER, analise_id INTEGER,
            tipo TEXT, categoria TEXT, rotulo TEXT, geometria_wkt TEXT,
            centro_lat REAL, centro_lon REAL, area_m2 REAL, atributos TEXT,
            confianca REAL, fonte TEXT DEFAULT 'manual', criado_por TEXT,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS gcps (
            id INTEGER PRIMARY KEY AUTOINCREMENT, projeto_id INTEGER, voo_id INTEGER,
            nome TEXT, latitude REAL, longitude REAL, altitude_m REAL,
            precisao_horizontal_m REAL, precisao_vertical_m REAL,
            metodo_coleta TEXT, equipamento TEXT, data_coleta TEXT, observacoes TEXT,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS comparacoes_temporais (
            id INTEGER PRIMARY KEY AUTOINCREMENT, projeto_id INTEGER,
            ortomapa_antes_id INTEGER, ortomapa_depois_id INTEGER,
            data_antes TEXT, data_depois TEXT, tipo_comparacao TEXT,
            resultado_path TEXT, resultado_thumbnail TEXT, estatisticas TEXT,
            observacoes TEXT, criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS tarefas_agentes (
            id INTEGER PRIMARY KEY AUTOINCREMENT, ortomapa_id INTEGER,
            tipo_tarefa TEXT, agente TEXT, prioridade INTEGER DEFAULT 5,
            parametros TEXT, status TEXT DEFAULT 'pendente', resultado TEXT,
            erro_msg TEXT, tentativas INTEGER DEFAULT 0, max_tentativas INTEGER DEFAULT 3,
            inicio_execucao TEXT, fim_execucao TEXT,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
    """)
    _sqlite_conn.commit()
    logger.info("SQLite fallback initialized at %s", db_path)


class _SQLiteCursorWrapper:
    """Wraps SQLite cursor to behave like mysql.connector cursor(dictionary=True)."""
    def __init__(self, conn):
        self._conn = conn
        self._cursor = conn.cursor()
        self.lastrowid = None
        self.rowcount = 0

    def execute(self, query, params=None):
        # Adapt MySQL-style %s placeholders to SQLite ?
        q = query.replace("%s", "?")
        # Remove MySQL-specific syntax
        q = q.replace("FOR UPDATE SKIP LOCKED", "")
        if params:
            self._cursor.execute(q, params)
        else:
            self._cursor.execute(q)
        self.lastrowid = self._cursor.lastrowid
        self.rowcount = self._cursor.rowcount
        return self._cursor

    def fetchone(self):
        row = self._cursor.fetchone()
        if row is None:
            return None
        return dict(row)

    def fetchall(self):
        return [dict(r) for r in self._cursor.fetchall()]

    def close(self):
        self._cursor.close()


class _SQLiteConnWrapper:
    """Wraps SQLite connection to behave like mysql.connector connection."""
    def __init__(self, conn):
        self._conn = conn

    def cursor(self, dictionary=False):
        return _SQLiteCursorWrapper(self._conn)

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def is_connected(self):
        return True

    def close(self):
        pass  # Don't actually close the shared SQLite connection


@contextmanager
def get_connection():
    """
    Yield a connection from the pool.
    Falls back to SQLite wrapper if MySQL is unavailable.
    """
    global _use_sqlite, _sqlite_conn
    pool = _get_pool()
    if DB_ENGINE == "postgres":
        conn = pool.getconn()
        try:
            yield _PGConnWrapper(conn)
        except Exception:
            conn.rollback()
            raise
        finally:
            pool.putconn(conn)
        return
    if _use_sqlite:
        yield _SQLiteConnWrapper(_sqlite_conn)
        return

    conn = pool.get_connection()
    try:
        yield conn
    except MySQLError:
        if conn.is_connected():
            conn.rollback()
        raise
    finally:
        if conn.is_connected():
            conn.close()


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------
def execute_query(
    sql: str,
    params: Optional[tuple] = None,
    *,
    dictionary: bool = True,
    fetch_one: bool = False,
    commit: bool = False,
) -> Any:
    """
    Execute a single SQL statement and return results.

    Parameters
    ----------
    sql : str
        SQL statement (may contain ``%s`` placeholders).
    params : tuple, optional
        Parameters to bind.
    dictionary : bool
        If True, rows are returned as dicts.
    fetch_one : bool
        If True, return only the first row (or None).
    commit : bool
        If True, explicitly commit after execution.

    Returns
    -------
    For SELECT: list[dict] or dict/None (if fetch_one).
    For INSERT: the lastrowid.
    For UPDATE/DELETE: the rowcount.
    """
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=dictionary)
        try:
            cursor.execute(sql, params)

            if sql.strip().upper().startswith("SELECT") or sql.strip().upper().startswith("SHOW"):
                rows = cursor.fetchall()
                return rows[0] if fetch_one and rows else (rows[0] if fetch_one else rows)

            if commit:
                conn.commit()

            # INSERT -> return last id; UPDATE/DELETE -> return rowcount
            if sql.strip().upper().startswith("INSERT"):
                return cursor.lastrowid
            return cursor.rowcount
        finally:
            cursor.close()


def execute_many(
    sql: str,
    data: list[tuple],
    *,
    commit: bool = True,
) -> int:
    """
    Execute a parameterised statement for each item in *data*.

    Returns the total rowcount.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.executemany(sql, data)
            if commit:
                conn.commit()
            return cursor.rowcount
        finally:
            cursor.close()


# ---------------------------------------------------------------------------
# Schema initialisation
# ---------------------------------------------------------------------------
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def init_database(schema_path: Optional[str] = None) -> None:
    """
    Read *schema.sql* and execute every statement to bootstrap the database.

    The function connects **without** selecting a database first so that the
    ``CREATE DATABASE`` / ``USE`` statements in the SQL file take effect.
    """
    path = Path(schema_path) if schema_path else SCHEMA_PATH
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {path}")

    sql_text = path.read_text(encoding="utf-8")

    # Build a one-off connection without the database selected
    init_config = {k: v for k, v in DB_CONFIG.items() if k != "database"}
    conn = mysql.connector.connect(**init_config)
    cursor = conn.cursor()

    logger.info("Initialising database from %s ...", path)

    try:
        # Split on semicolons, filtering empty fragments
        statements = [s.strip() for s in sql_text.split(";") if s.strip()]
        for stmt in statements:
            try:
                cursor.execute(stmt)
            except MySQLError as exc:
                logger.warning("Statement skipped (%s): %.120s", exc.msg, stmt)
        conn.commit()
        logger.info("Database initialisation complete (%d statements).", len(statements))
    finally:
        cursor.close()
        conn.close()


# ---------------------------------------------------------------------------
# Quick smoke test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_database()
    rows = execute_query("SELECT COUNT(*) AS total FROM projetos")
    print(f"projetos rows: {rows}")

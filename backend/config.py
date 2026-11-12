# Centralized configuration
# Credenciais sao lidas de variaveis de ambiente — ver .env.example
import os

# Carregar .env automaticamente se python-dotenv estiver disponivel
try:
    from dotenv import dotenv_values, load_dotenv
    _env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    if os.path.exists(_env_path):
        _local_env = dotenv_values(_env_path)
        load_dotenv(_env_path)
        _provider = (os.getenv("LLM_PROVIDER") or _local_env.get("LLM_PROVIDER") or "").strip().lower()
        _inherited_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
        _local_key = (_local_env.get("ANTHROPIC_API_KEY") or "").strip()
        # A placeholder exported from a shell profile must not shadow the real
        # key configured in this application's ignored, permission-restricted .env.
        _is_obvious_placeholder = (
            len(_inherited_key) < 50
            or _inherited_key.startswith("<")
            or "example" in _inherited_key.lower()
            or "placeholder" in _inherited_key.lower()
        )
        if _provider == "anthropic" and _local_key and _is_obvious_placeholder:
            os.environ["ANTHROPIC_API_KEY"] = _local_key
except ImportError:
    pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
ORTOMAPAS_DIR = os.path.join(DATA_DIR, "ortomapas")
DSM_DIR = os.path.join(DATA_DIR, "dsm")
DTM_DIR = os.path.join(DATA_DIR, "dtm")
ANALISES_DIR = os.path.join(DATA_DIR, "analises")
THUMBNAILS_DIR = os.path.join(DATA_DIR, "thumbnails")
UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")
EXPORTS_DIR = os.path.join(DATA_DIR, "exports")
GEOJSON_DIR = os.path.join(BASE_DIR, "geojson")

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "ortomapas"),
}

# NodeODM is the processing API; WebODM remains available as the UI.
NODEODM_URL = os.getenv("NODEODM_URL", "http://localhost:8021").rstrip("/")
WEBODM_URL = os.getenv("WEBODM_URL", "http://localhost:8020").rstrip("/")
AUTH_SECRET = os.getenv("AUTH_SECRET", "change-me-in-production")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()
if ENVIRONMENT in {"production", "prod"} and len(AUTH_SECRET) < 32:
    raise RuntimeError("AUTH_SECRET deve ter pelo menos 32 caracteres em producao")
GEOSERVER_URL = os.getenv("GEOSERVER_URL", "http://localhost:8080/geoserver")
GEOSERVER_ADMIN_USER = os.getenv("GEOSERVER_ADMIN_USER", "admin")
GEOSERVER_ADMIN_PASSWORD = os.getenv("GEOSERVER_ADMIN_PASSWORD", "geoserver")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://127.0.0.1:1234/v1")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "lmstudio").strip().lower()
LLM_MODEL = os.getenv(
    "LLM_MODEL",
    "claude-sonnet-5-5" if LLM_PROVIDER == "anthropic" else "qwen/qwen3.8-27b",
)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
LLM_MAX_OUTPUT_TOKENS = int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "1024"))
LLM_MAX_INPUT_CHARS = int(os.getenv("LLM_MAX_INPUT_CHARS", "24000"))
LLM_MAX_CALLS_PER_TURN = int(os.getenv("LLM_MAX_CALLS_PER_TURN", "6"))
OTEL_ENABLED = os.getenv("OTEL_ENABLED", "0").lower() in {"1", "true", "yes"}
OTEL_SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "ortomapas-api")
OTEL_EXPORTER_OTLP_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://127.0.0.1:4317")
OTEL_OTLP_ENABLED = os.getenv("OTEL_OTLP_ENABLED", "0").lower() in {"1", "true", "yes"}
AGENT_WORKER_ENABLED = os.getenv("AGENT_WORKER_ENABLED", "1").lower() in {"1", "true", "yes"}
AGENT_WORKER_POLL_SECONDS = max(1, int(os.getenv("AGENT_WORKER_POLL_SECONDS", "5")))

API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8888"))

# Ensure directories exist
for d in [DATA_DIR, ORTOMAPAS_DIR, DSM_DIR, DTM_DIR, ANALISES_DIR, THUMBNAILS_DIR, UPLOADS_DIR, EXPORTS_DIR, GEOJSON_DIR]:
    os.makedirs(d, exist_ok=True)

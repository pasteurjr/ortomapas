# Centralized configuration
# Credenciais sao lidas de variaveis de ambiente — ver .env.example
import os

# Carregar .env automaticamente se python-dotenv estiver disponivel
try:
    from dotenv import load_dotenv
    _env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    if os.path.exists(_env_path):
        load_dotenv(_env_path)
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
GEOSERVER_URL = os.getenv("GEOSERVER_URL", "http://localhost:8080/geoserver")

API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8888"))

# Ensure directories exist
for d in [DATA_DIR, ORTOMAPAS_DIR, DSM_DIR, DTM_DIR, ANALISES_DIR, THUMBNAILS_DIR, UPLOADS_DIR, EXPORTS_DIR, GEOJSON_DIR]:
    os.makedirs(d, exist_ok=True)

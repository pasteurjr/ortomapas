"""
Main FastAPI application for the Sistema de Ortomapas.
"""

import logging
import time
from threading import Lock
from collections import defaultdict, deque
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.staticfiles import StaticFiles

from backend.config import DATA_DIR, API_HOST, API_PORT, OTEL_ENABLED, OTEL_SERVICE_NAME, OTEL_EXPORTER_OTLP_ENDPOINT, OTEL_OTLP_ENABLED
from backend.routers import projetos, voos, ortomapas, analises, anotacoes, tools, odm, auth, agents, copilot

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

_metrics = {"requests_total": 0, "errors_total": 0, "latency_ms_total": 0.0, "by_status": {}}
_metrics_lock = Lock()

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, limit=120, window=60):
        super().__init__(app); self.limit=limit; self.window=window; self.hits=defaultdict(deque)
    async def dispatch(self, request, call_next):
        key=request.client.host if request.client else 'unknown'; now=time.monotonic(); q=self.hits[key]
        while q and now-q[0] > self.window: q.popleft()
        if len(q) >= self.limit:
            from fastapi.responses import JSONResponse
            with _metrics_lock:
                _metrics["requests_total"] += 1
                _metrics["errors_total"] += 1
                _metrics["by_status"]["429"] = _metrics["by_status"].get("429", 0) + 1
            return JSONResponse({'detail':'Limite de requisicoes excedido'}, status_code=429, headers={'Retry-After':str(self.window)})
        q.append(now)
        started = time.perf_counter()
        response = await call_next(request)
        elapsed = (time.perf_counter() - started) * 1000
        with _metrics_lock:
            _metrics["requests_total"] += 1
            _metrics["latency_ms_total"] += elapsed
            status = str(response.status_code)
            _metrics["by_status"][status] = _metrics["by_status"].get(status, 0) + 1
            if response.status_code >= 500:
                _metrics["errors_total"] += 1
        return response

app = FastAPI(
    title="Sistema de Ortomapas",
    description="API para gerenciamento de ortomapas, voos, analises e anotacoes geoespaciais.",
    version="1.0.0",
)

if OTEL_ENABLED:
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        provider = TracerProvider(resource=Resource.create({"service.name": OTEL_SERVICE_NAME}))
        # Console exporter is deterministic for local validation; deployments can
        # replace it with OTLP by configuring a collector endpoint.
        if OTEL_OTLP_ENABLED:
            provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=OTEL_EXPORTER_OTLP_ENDPOINT, insecure=True)))
        else:
            provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
        trace.set_tracer_provider(provider)
        FastAPIInstrumentor.instrument_app(app)
        logger.info("OpenTelemetry habilitado para %s (endpoint=%s)", OTEL_SERVICE_NAME, OTEL_EXPORTER_OTLP_ENDPOINT)
    except ImportError as exc:
        logger.warning("OpenTelemetry solicitado, mas dependencias ausentes: %s", exc)

# CORS middleware — allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)

# Mount static files from data/ at /data
app.mount("/data", StaticFiles(directory=DATA_DIR), name="data")

# Include routers
app.include_router(projetos.router, prefix="/api", tags=["Projetos"])
app.include_router(voos.router, prefix="/api", tags=["Voos"])
app.include_router(ortomapas.router, prefix="/api", tags=["Ortomapas"])
app.include_router(analises.router, prefix="/api", tags=["Analises"])
app.include_router(anotacoes.router, prefix="/api", tags=["Anotacoes"])
app.include_router(tools.router, prefix="/api", tags=["Tools"])
app.include_router(odm.router, prefix="/api", tags=["ODM"])
app.include_router(auth.router, prefix="/api", tags=["Auth"])
app.include_router(agents.router, prefix="/api", tags=["Agents"])
app.include_router(copilot.router, prefix="/api", tags=["Copilot"])


@app.on_event("startup")
async def startup_event():
    logger.info("Sistema de Ortomapas API iniciando...")
    logger.info(f"Data directory: {DATA_DIR}")
    logger.info("API pronta para receber requisicoes.")


@app.get("/", tags=["Root"])
async def root():
    """Return system information."""
    return {
        "sistema": "Sistema de Ortomapas",
        "versao": "1.0.0",
        "status": "online",
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "api": "/api",
            "data": "/data",
        },
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
    }

@app.get("/health/ready", tags=["Health"])
async def readiness_check():
    checks = {'database': False, 'lm_studio': False}
    try:
        from backend.database.connection import get_connection
        with get_connection() as conn:
            cur=conn.cursor(); cur.execute('SELECT 1'); checks['database']=True
    except Exception: pass
    try:
        from backend.agents.llm_client import LMStudioClient
        checks['lm_studio']=bool(LMStudioClient().models().get('data'))
    except Exception: pass
    return {'status':'ready' if all(checks.values()) else 'degraded', 'checks':checks, 'timestamp':datetime.utcnow().isoformat()}

@app.get("/health/metrics", tags=["Health"])
async def metrics():
    """Return process-local request metrics for operational monitoring."""
    with _metrics_lock:
        total = _metrics["requests_total"]
        return {
            "requests_total": total,
            "errors_total": _metrics["errors_total"],
            "average_latency_ms": round(_metrics["latency_ms_total"] / total, 2) if total else 0.0,
            "by_status": dict(_metrics["by_status"]),
            "timestamp": datetime.utcnow().isoformat(),
        }

@app.get("/metrics", include_in_schema=False)
async def prometheus_metrics():
    """Expose basic counters in Prometheus text exposition format."""
    with _metrics_lock:
        total = _metrics["requests_total"]
        errors = _metrics["errors_total"]
        latency = _metrics["latency_ms_total"]
        statuses = dict(_metrics["by_status"])
    lines = [
        "# HELP ortomapas_http_requests_total Total HTTP requests.",
        "# TYPE ortomapas_http_requests_total counter",
        f"ortomapas_http_requests_total {total}",
        "# HELP ortomapas_http_errors_total Total HTTP 5xx and rate-limit errors.",
        "# TYPE ortomapas_http_errors_total counter",
        f"ortomapas_http_errors_total {errors}",
        "# HELP ortomapas_http_latency_ms_total Cumulative request latency in milliseconds.",
        "# TYPE ortomapas_http_latency_ms_total counter",
        f"ortomapas_http_latency_ms_total {latency:.3f}",
    ]
    for status, count in sorted(statuses.items()):
        lines.append(f'ortomapas_http_responses_total{{status="{status}"}} {count}')
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse("\n".join(lines) + "\n", media_type="text/plain; version=0.0.4")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host=API_HOST, port=API_PORT, reload=True)

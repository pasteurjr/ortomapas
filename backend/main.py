"""
Main FastAPI application for the Sistema de Ortomapas.
"""

import logging
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.config import DATA_DIR, API_HOST, API_PORT
from backend.routers import projetos, voos, ortomapas, analises, anotacoes, tools, odm, auth

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Sistema de Ortomapas",
    description="API para gerenciamento de ortomapas, voos, analises e anotacoes geoespaciais.",
    version="1.0.0",
)

# CORS middleware — allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host=API_HOST, port=API_PORT, reload=True)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import os
import sys
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
log = logging.getLogger(__name__)

from src.backend.routes import Routes
from src.backend.database.InitializeConnectionWithDatabase import initialize_app
from src.api.routes.api_v1_routes import router as api_v1_router

# Initialize FastAPI app
app = FastAPI(
    title="Queto System - C2M (Cyber Crisis Management)",
    description="Sistema de IA para Gerenciamento Inteligente de Crises Cibernéticas",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Initialize database
#initialize_app()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
# Legacy routes (backward compatibility)
app.include_router(Routes.router, prefix="")

# New REST API v1 routes
app.include_router(api_v1_router)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    log.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    log.info("═" * 80)
    log.info("🚀 Queto System (C2M) iniciando...")
    log.info("═" * 80)
    log.info("✓ FastAPI configurado")
    log.info("✓ Banco de dados inicializado")
    log.info("✓ Rotas registradas")
    log.info("═" * 80)

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    log.info("🛑 Queto System desligando...")
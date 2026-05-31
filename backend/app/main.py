import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import settings
from backend.app.routes import agent, media, files, settings as settings_route, company

# Setup structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    description="Modular AI Agent base built with FastAPI, LangGraph, and safe local file editing capabilities.",
    version="1.0.0",
    debug=settings.DEBUG
)

# Configure CORS so the frontend Vite server can fetch APIs
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For local development convenience. Can restrict to settings in production.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Register routes under /api
app.include_router(agent.router, prefix="/api")
app.include_router(media.router, prefix="/api")
app.include_router(files.router, prefix="/api")
app.include_router(settings_route.router, prefix="/api")
app.include_router(company.router, prefix="/api")

@app.get("/")
async def root():
    """Root server status endpoint."""
    return {
        "status": "online",
        "app_name": settings.APP_NAME,
        "active_provider": settings.ACTIVE_PROVIDER
    }

@app.on_event("startup")
async def startup_event():
    logger.info("=========================================")
    logger.info(f"Starting {settings.APP_NAME}...")
    logger.info(f"Host: {settings.HOST}, Port: {settings.PORT}")
    logger.info(f"Workspace Root: {settings.FILE_WORKSPACE_ROOT}")
    logger.info(f"Default Provider: {settings.ACTIVE_PROVIDER}")
    logger.info("=========================================")

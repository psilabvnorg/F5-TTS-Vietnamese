"""
F5-TTS Vietnamese API - Main Application
FastAPI application with preloaded model and modern architecture
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.core.config import settings
from app.core.events import startup_event, shutdown_event
from app.core.logging import logger
from app.api.v1 import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup
    await startup_event()
    yield
    # Shutdown
    await shutdown_event()


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOW_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)


# Mount static files if directory exists
if settings.STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(settings.STATIC_DIR)), name="static")
    logger.info(f"Mounted static files from {settings.STATIC_DIR}")

# Mount output directory for generated audio files
if settings.OUTPUT_DIR.exists():
    app.mount("/output", StaticFiles(directory=str(settings.OUTPUT_DIR)), name="output")
    logger.info(f"Mounted output files from {settings.OUTPUT_DIR}")
else:
    settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    app.mount("/output", StaticFiles(directory=str(settings.OUTPUT_DIR)), name="output")
    logger.info(f"Created and mounted output directory at {settings.OUTPUT_DIR}")


# Include API router
app.include_router(api_router)


# Root endpoint - serve index.html
@app.get("/", include_in_schema=False)
async def root():
    """Serve the main application page"""
    return FileResponse(settings.STATIC_DIR / "index.html")


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting {settings.APP_NAME} v{settings.VERSION}")
    logger.info(f"Server: http://{settings.HOST}:{settings.PORT}")
    logger.info(f"Docs: http://{settings.HOST}:{settings.PORT}/docs")
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower()
    )

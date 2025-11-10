"""Main FastAPI application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.background_worker import start_background_worker, stop_background_worker
from app.config import settings
from app.db import create_db_and_tables
from app.routers import alarms, analytics, recommendations, turbines
from app.schemas import HealthCheck


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.

    Creates database tables on startup and starts background worker.
    """
    # Startup: Create database tables
    create_db_and_tables()
    
    # Start background worker for snoozed alarms
    await start_background_worker()
    
    yield
    
    # Shutdown: Stop background worker
    stop_background_worker()


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="FastAPI backend for wind turbine fault management and orchestration",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(turbines.router, prefix=settings.API_V1_PREFIX)
app.include_router(alarms.router, prefix=settings.API_V1_PREFIX)
app.include_router(recommendations.router, prefix=settings.API_V1_PREFIX)
app.include_router(analytics.router, prefix=settings.API_V1_PREFIX)


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "Wind Fault Orchestrator API",
        "version": settings.VERSION,
        "docs": "/docs",
        "health": f"{settings.API_V1_PREFIX}/health",
    }


@app.get(f"{settings.API_V1_PREFIX}/health", response_model=HealthCheck)
def health_check():
    """
    Health check endpoint.

    Returns the status of the API and database connection.
    """
    database_status = "connected"

    # Test database connection
    try:
        from app.db import engine

        with engine.connect() as conn:
            conn.execute("SELECT 1")
    except Exception as e:
        database_status = f"error: {str(e)}"

    return HealthCheck(
        status="healthy" if database_status == "connected" else "unhealthy",
        version=settings.VERSION,
        database=database_status,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )


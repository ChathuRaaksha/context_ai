"""
AI-Powered Bug Detection & Self-Healing System
Main FastAPI application entry point.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import db_instance
from app.api.monitoring import router as monitoring_router, set_services
from app.services.bug_detection_service import BugDetectionService
from app.services.self_healing_service import SelfHealingService
from app.services.github_service import GitHubService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Service instances
bug_detection_service: BugDetectionService
self_healing_service: SelfHealingService
github_service: GitHubService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.

    Args:
        app: FastAPI application instance
    """
    # Startup
    logger.info("Starting AI-Powered Bug Detection & Self-Healing System")

    try:
        # Initialize database
        await db_instance.connect_db()
        logger.info("Database connected successfully")

        # Initialize services
        global bug_detection_service, self_healing_service, github_service

        bug_detection_service = BugDetectionService()
        await bug_detection_service.initialize()
        logger.info("Bug detection service initialized")

        self_healing_service = SelfHealingService()
        await self_healing_service.initialize()
        logger.info("Self-healing service initialized")

        github_service = GitHubService()
        if github_service.is_configured():
            logger.info("GitHub integration configured")
        else:
            logger.info("GitHub integration not configured (optional)")

        # Set services in monitoring router
        set_services(bug_detection_service, self_healing_service, github_service)

        logger.info(f"Application started successfully on port {settings.PORT}")
        logger.info(f"Environment: {settings.ENV}")
        logger.info(f"AI Model: {settings.AI_MODEL}")

    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down AI-Powered Bug Detection & Self-Healing System")

    try:
        await db_instance.close_db()
        logger.info("Database connection closed")

    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Create FastAPI application
app = FastAPI(
    title="AI-Powered Bug Detection & Self-Healing System",
    description="""
    # AI-Powered Bug Detection & Self-Healing System

    An intelligent system that combines Grafana monitoring with AI-powered bug detection and automated self-healing.

    ## Features

    - **AI-Powered Analysis**: Uses Claude 3.5 Sonnet for intelligent log analysis
    - **Automatic Bug Detection**: Detects bugs from logs and Grafana alerts
    - **Self-Healing**: Automatically attempts to heal detected bugs based on risk level
    - **GitHub Integration**: Creates issues for bugs that require manual intervention
    - **Health Monitoring**: Tracks service health scores and metrics
    - **Dashboard Statistics**: Provides real-time insights into system health

    ## Authentication

    API endpoints support optional authentication via:
    - Bearer token in Authorization header
    - X-API-Key header
    - api_key query parameter

    ## Grafana Integration

    Configure Grafana to send webhooks to `/api/v1/grafana/webhook` for automatic bug detection and healing.
    """,
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(monitoring_router)


@app.get("/", tags=["root"])
async def root():
    """
    Root endpoint with API information.

    Returns:
        dict: API information and available endpoints
    """
    return {
        "name": "AI-Powered Bug Detection & Self-Healing System",
        "version": "2.0.0",
        "status": "running",
        "environment": settings.ENV,
        "ai_model": settings.AI_MODEL,
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "api": "/api/v1"
        },
        "features": {
            "bug_detection": True,
            "self_healing": True,
            "github_integration": github_service.is_configured() if github_service else False,
            "grafana_webhook": True
        }
    }


@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint for monitoring.

    Returns:
        dict: Health status of the application
    """
    try:
        # Check database connection
        db = db_instance.get_db()
        await db.command("ping")

        return {
            "status": "healthy",
            "database": "connected",
            "services": {
                "bug_detection": bug_detection_service is not None,
                "self_healing": self_healing_service is not None,
                "github": github_service.is_configured() if github_service else False
            }
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@app.get("/api/v1/status", tags=["monitoring"])
async def api_status():
    """
    API status endpoint with detailed service information.

    Returns:
        dict: Detailed API status
    """
    return {
        "api_version": "v1",
        "status": "operational",
        "environment": settings.ENV,
        "configuration": {
            "ai_model": settings.AI_MODEL,
            "ai_temperature": settings.AI_TEMPERATURE,
            "auto_heal_low_risk": settings.AUTO_HEAL_LOW_RISK,
            "auto_heal_medium_risk": settings.AUTO_HEAL_MEDIUM_RISK,
            "auto_heal_high_risk": settings.AUTO_HEAL_HIGH_RISK
        },
        "integrations": {
            "openrouter": bool(settings.OPENROUTER_API_KEY),
            "github": github_service.is_configured() if github_service else False,
            "mongodb": True
        }
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.ENV == "development",
        log_level="info"
    )

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import db
from app.api.contexts import router as contexts_router
from app.api.tools import router as tools_router
from app.services.context_service import context_service
from app.services.tool_service import tool_service

app = FastAPI(
    title="Context Management System",
    description="AI-Powered Context Management System for Documentation and Infrastructure",
    version="1.0.0"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(contexts_router, prefix="/api")
app.include_router(tools_router, prefix="/api")

@app.on_event("startup")
async def startup_event():
    """Initialize connections and create indexes on startup."""
    # Initialize database connection
    await db.connect_db()
    
    # Initialize services
    await context_service.initialize()
    await tool_service.initialize()
    
    # Create text index for search functionality
    collection = db.get_db().contexts
    await collection.create_index([
        ("content", "text"),
        ("tags", "text"),
        ("metadata", "text")
    ])
    
    # Create indexes for common queries
    await collection.create_index("content_type")
    await collection.create_index("tags")
    await collection.create_index([
        ("quality_metrics.completeness", 1),
        ("quality_metrics.accuracy", 1),
        ("quality_metrics.relevance", 1),
        ("quality_metrics.clarity", 1)
    ])

    # Create indexes for tool collections
    tools_collection = db.get_db().tools
    await tools_collection.create_index("id", unique=True)
    await tools_collection.create_index([("metadata.name", 1)])
    await tools_collection.create_index([("capabilities", 1)])
    
    instances_collection = db.get_db().tool_instances
    await instances_collection.create_index([("tool_id", 1), ("context_id", 1)], unique=True)
    await instances_collection.create_index([("context_id", 1)])
    await instances_collection.create_index([("status", 1)])

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up connections on shutdown."""
    await db.close_db()

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Context Management System API",
        "version": "1.0.0",
        "status": "running",
        "features": [
            "Context Management",
            "Tool Integration",
            "Quality Assessment",
            "Automatic Tool Discovery"
        ],
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }

# Error handling
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    return {
        "error": str(exc),
        "type": exc.__class__.__name__,
        "path": request.url.path
    }

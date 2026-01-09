"""
EquiShard FastAPI Query Layer

This is the READ side of the CQRS architecture.
Handles all data retrieval and aggregation for frontend charts/dashboards.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.v1 import analytics, store


# Create FastAPI app
app = FastAPI(
    title="EquiShard Query API",
    description="Read-optimized API for charts, dashboards, and data retrieval",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check
@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "equishard-query-api"}


# Include routers
app.include_router(
    analytics.router,
    prefix="/api/v1/analytics",
    tags=["Analytics"]
)

app.include_router(
    store.router,
    prefix="/api/v1/store",
    tags=["Store"]
)

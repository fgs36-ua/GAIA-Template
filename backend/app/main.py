# [Feature: Infrastructure] [Story: Backend Setup] [Ticket: NM-ADMIN-001-DB-T01]
"""
FastAPI Application Entry Point

Mounts all routers and configures middleware.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.presentation.api import health
from app.presentation.api import news

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="GAIA Template Backend API",
    version="1.0.0",
    openapi_url="/api/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
# [Feature: Infrastructure] [Story: Backend Setup] [Ticket: NM-ADMIN-001-DB-T01]
app.include_router(health.router, prefix="/api", tags=["health"])

# [Feature: News Management] [Story: NM-ADMIN-001] [Ticket: NM-ADMIN-001-BE-T01]
app.include_router(news.router, prefix="/api", tags=["news"])

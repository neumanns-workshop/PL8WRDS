"""
PL8WRDS FastAPI Application Main Module.

This module sets up the FastAPI application with comprehensive monitoring,
error handling, and dependency injection.
"""

import logging
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import get_settings
from .core.container import create_container
from .core.error_handlers import setup_error_handlers
from .monitoring import (
    CriticalErrorHandler,
    MetricsMiddleware,
    ObservabilityMiddleware,
    PerformanceMiddleware,
    RateLimitingMiddleware,
    SecurityMiddleware,
    get_metrics_manager,
    instrument_fastapi_app,
    setup_logging,
    setup_tracing,
)
from .routers import (
    combinations,
    corpus,
    dataset,
    dictionary,
    metrics,
    monitoring,
    prediction,
    scoring,
    solver,
)

# Initialize structured logging before anything else
setup_logging()

from .monitoring.logger import get_logger
logger = get_logger(__name__)

# Create dependency injection container
container = create_container()

# Get settings
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    # Startup
    logger.info("Application startup...", 
               service_name=settings.monitoring.service_name,
               service_version=settings.monitoring.service_version)
    
    try:
        # Initialize tracing
        setup_tracing()
        logger.info("Distributed tracing initialized")
        
        # Initialize metrics system
        metrics = get_metrics_manager()
        logger.info("Metrics system initialized")
        
        # Initialize the prediction service (load ML model)
        prediction_service = container.prediction_service()
        await prediction_service.initialize()
        logger.info("Prediction service initialized successfully")
        
    except Exception as e:
        CriticalErrorHandler.handle_startup_error(e, "application_startup")
        logger.error(f"Critical startup failure: {e}")
        # Don't prevent startup for non-critical failures
    
    logger.info("Application startup completed")
    
    yield
    
    # Shutdown
    logger.info("Application shutdown...")
    
    try:
        # Cleanup monitoring resources
        metrics.update_system_metrics()  # Final metrics update
        logger.info("Monitoring cleanup completed")
    except Exception as e:
        logger.error(f"Error during shutdown cleanup: {e}")
    
    logger.info("Application shutdown completed")


app = FastAPI(
    title=settings.app.app_name,
    description=settings.app.app_description,
    version=settings.app.app_version,
    lifespan=lifespan,
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
    openapi_url="/openapi.json" if settings.is_development else None,
)

# Set container for the FastAPI app
app.container = container

# Setup error handlers
setup_error_handlers(app)

# Setup CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.is_development else ["https://pl8wrds.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Setup tracing for FastAPI
instrument_fastapi_app(app)

# Add monitoring middleware (order matters - add in reverse order of execution)
if settings.monitoring.enable_rate_limiting:
    app.add_middleware(RateLimitingMiddleware)

if settings.monitoring.enable_security_monitoring:
    app.add_middleware(SecurityMiddleware)

if settings.monitoring.enable_performance_monitoring:
    app.add_middleware(PerformanceMiddleware)

if settings.monitoring.enable_prometheus_metrics:
    app.add_middleware(MetricsMiddleware)

# Always add observability middleware last (executes first)
app.add_middleware(ObservabilityMiddleware)

# Include routers
app.include_router(monitoring.router)  # Add monitoring router first
app.include_router(solver.router)
app.include_router(scoring.router)
app.include_router(metrics.router)
app.include_router(dataset.router)
app.include_router(corpus.router)
app.include_router(combinations.router)
app.include_router(dictionary.router)
app.include_router(prediction.router)


@app.get("/", include_in_schema=False)
async def read_root() -> Dict[str, Any]:
    """Root endpoint with API information.
    
    Returns:
        API information including version and available endpoints.
    """
    response = {
        "message": "Welcome to PL8WRDS API",
        "version": settings.app.app_version,
        "status": "running",
        "environment": "development" if settings.is_development else "production",
    }
    
    if settings.is_development:
        response.update({
            "docs": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json",
        })
    
    return response


@app.get("/health", include_in_schema=False)
async def health_check() -> Dict[str, Any]:
    """Health check endpoint for load balancers and monitoring.
    
    Returns:
        Health status information.
    """
    return {
        "status": "healthy",
        "version": settings.app.app_version,
        "environment": "development" if settings.is_development else "production",
        "timestamp": None,  # Will be added by middleware
        "uptime": None,     # Will be added by health monitoring
    }

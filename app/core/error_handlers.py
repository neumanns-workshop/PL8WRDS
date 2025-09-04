"""
Global error handlers for FastAPI application.

This module provides centralized error handling for the PL8WRDS API,
ensuring consistent error responses and proper logging of exceptions.
"""

from __future__ import annotations

import traceback
from typing import Any, Dict, Union

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from ..monitoring.logger import get_logger
from .exceptions import (
    AuthenticationError,
    AuthorizationError,
    CacheError,
    ConfigurationError,
    DatabaseError,
    ExternalServiceError,
    ModelError,
    PL8WRDSException,
    RateLimitExceededError,
    ResourceNotFoundError,
    ServiceError,
    ValidationError,
)

logger = get_logger(__name__)


def create_error_response(
    status_code: int,
    error_code: str,
    message: str,
    details: Dict[str, Any] | None = None,
    request_id: str | None = None,
) -> JSONResponse:
    """Create a standardized error response.
    
    Args:
        status_code: HTTP status code
        error_code: Application-specific error code
        message: Human-readable error message
        details: Additional error details
        request_id: Request ID for tracing
        
    Returns:
        JSONResponse with standardized error format
    """
    error_response = {
        "error": {
            "code": error_code,
            "message": message,
            "timestamp": None,  # Will be set by middleware
        }
    }
    
    if details:
        error_response["error"]["details"] = details
        
    if request_id:
        error_response["error"]["request_id"] = request_id
        
    return JSONResponse(
        status_code=status_code,
        content=error_response,
        headers={"Content-Type": "application/json"},
    )


async def pl8wrds_exception_handler(request: Request, exc: PL8WRDSException) -> JSONResponse:
    """Handle custom PL8WRDS exceptions.
    
    Args:
        request: FastAPI request object
        exc: PL8WRDS exception instance
        
    Returns:
        JSONResponse with error details
    """
    logger.error(
        f"PL8WRDS exception: {exc.error_code}",
        error=exc.error_code,
        message=exc.message,
        context=exc.context,
        path=request.url.path,
        method=request.method,
        exc_info=True,
    )
    
    # Map exception types to HTTP status codes
    status_code_map = {
        ValidationError: status.HTTP_400_BAD_REQUEST,
        ResourceNotFoundError: status.HTTP_404_NOT_FOUND,
        AuthenticationError: status.HTTP_401_UNAUTHORIZED,
        AuthorizationError: status.HTTP_403_FORBIDDEN,
        RateLimitExceededError: status.HTTP_429_TOO_MANY_REQUESTS,
        ConfigurationError: status.HTTP_500_INTERNAL_SERVER_ERROR,
        ServiceError: status.HTTP_500_INTERNAL_SERVER_ERROR,
        ExternalServiceError: status.HTTP_502_BAD_GATEWAY,
        CacheError: status.HTTP_503_SERVICE_UNAVAILABLE,
        DatabaseError: status.HTTP_503_SERVICE_UNAVAILABLE,
        ModelError: status.HTTP_500_INTERNAL_SERVER_ERROR,
    }
    
    status_code = status_code_map.get(type(exc), status.HTTP_500_INTERNAL_SERVER_ERROR)
    request_id = getattr(request.state, "request_id", None)
    
    return create_error_response(
        status_code=status_code,
        error_code=exc.error_code,
        message=exc.message,
        details=exc.context if exc.context else None,
        request_id=request_id,
    )


async def validation_exception_handler(
    request: Request, exc: PydanticValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors.
    
    Args:
        request: FastAPI request object
        exc: Pydantic validation exception
        
    Returns:
        JSONResponse with validation error details
    """
    logger.warning(
        "Validation error",
        path=request.url.path,
        method=request.method,
        errors=exc.errors(),
    )
    
    request_id = getattr(request.state, "request_id", None)
    
    return create_error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error_code="VALIDATION_ERROR",
        message="Input validation failed",
        details={"validation_errors": exc.errors()},
        request_id=request_id,
    )


async def http_exception_handler(
    request: Request, exc: Union[HTTPException, StarletteHTTPException]
) -> JSONResponse:
    """Handle HTTP exceptions.
    
    Args:
        request: FastAPI request object
        exc: HTTP exception
        
    Returns:
        JSONResponse with error details
    """
    logger.warning(
        f"HTTP exception: {exc.status_code}",
        status_code=exc.status_code,
        detail=exc.detail,
        path=request.url.path,
        method=request.method,
    )
    
    request_id = getattr(request.state, "request_id", None)
    
    return create_error_response(
        status_code=exc.status_code,
        error_code="HTTP_ERROR",
        message=str(exc.detail) if exc.detail else "HTTP error occurred",
        request_id=request_id,
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions.
    
    Args:
        request: FastAPI request object
        exc: Unexpected exception
        
    Returns:
        JSONResponse with generic error message
    """
    logger.critical(
        f"Unhandled exception: {type(exc).__name__}",
        error=str(exc),
        path=request.url.path,
        method=request.method,
        traceback=traceback.format_exc(),
        exc_info=True,
    )
    
    request_id = getattr(request.state, "request_id", None)
    
    return create_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code="INTERNAL_ERROR",
        message="An unexpected error occurred",
        request_id=request_id,
    )


def setup_error_handlers(app: Any) -> None:
    """Set up error handlers for the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    # Custom exception handlers
    app.add_exception_handler(PL8WRDSException, pl8wrds_exception_handler)
    app.add_exception_handler(PydanticValidationError, validation_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
    
    logger.info("Error handlers configured successfully")

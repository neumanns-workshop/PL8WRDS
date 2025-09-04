"""
Custom exception classes for PL8WRDS application.

This module provides a hierarchy of custom exceptions that provide
more specific error handling and better error messages throughout
the application.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


class PL8WRDSException(Exception):
    """Base exception class for all PL8WRDS-specific errors.
    
    This is the base class for all custom exceptions in the PL8WRDS
    application. It provides common functionality for error handling
    and logging.
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the exception.
        
        Args:
            message: Human-readable error message
            error_code: Optional error code for programmatic handling
            context: Optional context information for debugging
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.context = context or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for serialization."""
        return {
            "error": self.error_code,
            "message": self.message,
            "context": self.context,
        }


class ValidationError(PL8WRDSException):
    """Raised when input validation fails."""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize validation error.
        
        Args:
            message: Error message
            field: Field name that failed validation
            value: Invalid value that caused the error
            **kwargs: Additional context
        """
        context = kwargs.copy()
        if field:
            context["field"] = field
        if value is not None:
            context["value"] = str(value)

        super().__init__(message, error_code="VALIDATION_ERROR", context=context)


class ConfigurationError(PL8WRDSException):
    """Raised when there's a configuration problem."""

    def __init__(self, message: str, setting: Optional[str] = None, **kwargs: Any) -> None:
        """Initialize configuration error.
        
        Args:
            message: Error message
            setting: Name of the problematic setting
            **kwargs: Additional context
        """
        context = kwargs.copy()
        if setting:
            context["setting"] = setting

        super().__init__(message, error_code="CONFIGURATION_ERROR", context=context)


class ServiceError(PL8WRDSException):
    """Raised when a service operation fails."""

    def __init__(
        self,
        message: str,
        service: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize service error.
        
        Args:
            message: Error message
            service: Name of the service that failed
            operation: Operation that failed
            **kwargs: Additional context
        """
        context = kwargs.copy()
        if service:
            context["service"] = service
        if operation:
            context["operation"] = operation

        super().__init__(message, error_code="SERVICE_ERROR", context=context)


class ResourceNotFoundError(PL8WRDSException):
    """Raised when a requested resource is not found."""

    def __init__(
        self,
        message: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize resource not found error.
        
        Args:
            message: Error message
            resource_type: Type of resource that wasn't found
            resource_id: ID of the resource that wasn't found
            **kwargs: Additional context
        """
        context = kwargs.copy()
        if resource_type:
            context["resource_type"] = resource_type
        if resource_id:
            context["resource_id"] = resource_id

        super().__init__(message, error_code="RESOURCE_NOT_FOUND", context=context)


class ExternalServiceError(PL8WRDSException):
    """Raised when an external service call fails."""

    def __init__(
        self,
        message: str,
        service_name: Optional[str] = None,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize external service error.
        
        Args:
            message: Error message
            service_name: Name of the external service
            status_code: HTTP status code if applicable
            response_body: Response body for debugging
            **kwargs: Additional context
        """
        context = kwargs.copy()
        if service_name:
            context["service_name"] = service_name
        if status_code:
            context["status_code"] = status_code
        if response_body:
            context["response_body"] = response_body

        super().__init__(message, error_code="EXTERNAL_SERVICE_ERROR", context=context)


class CacheError(PL8WRDSException):
    """Raised when cache operations fail."""

    def __init__(
        self,
        message: str,
        cache_key: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize cache error.
        
        Args:
            message: Error message
            cache_key: Cache key involved in the operation
            operation: Cache operation that failed (get, set, delete, etc.)
            **kwargs: Additional context
        """
        context = kwargs.copy()
        if cache_key:
            context["cache_key"] = cache_key
        if operation:
            context["operation"] = operation

        super().__init__(message, error_code="CACHE_ERROR", context=context)


class DatabaseError(PL8WRDSException):
    """Raised when database operations fail."""

    def __init__(
        self,
        message: str,
        table: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize database error.
        
        Args:
            message: Error message
            table: Database table involved
            operation: Database operation that failed
            **kwargs: Additional context
        """
        context = kwargs.copy()
        if table:
            context["table"] = table
        if operation:
            context["operation"] = operation

        super().__init__(message, error_code="DATABASE_ERROR", context=context)


class ModelError(PL8WRDSException):
    """Raised when ML model operations fail."""

    def __init__(
        self,
        message: str,
        model_name: Optional[str] = None,
        model_version: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize model error.
        
        Args:
            message: Error message
            model_name: Name of the model that failed
            model_version: Version of the model
            **kwargs: Additional context
        """
        context = kwargs.copy()
        if model_name:
            context["model_name"] = model_name
        if model_version:
            context["model_version"] = model_version

        super().__init__(message, error_code="MODEL_ERROR", context=context)


class AuthenticationError(PL8WRDSException):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed", **kwargs: Any) -> None:
        """Initialize authentication error.
        
        Args:
            message: Error message
            **kwargs: Additional context
        """
        super().__init__(message, error_code="AUTHENTICATION_ERROR", context=kwargs)


class AuthorizationError(PL8WRDSException):
    """Raised when authorization fails."""

    def __init__(
        self,
        message: str = "Access denied",
        required_permission: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize authorization error.
        
        Args:
            message: Error message
            required_permission: Permission that was required
            **kwargs: Additional context
        """
        context = kwargs.copy()
        if required_permission:
            context["required_permission"] = required_permission

        super().__init__(message, error_code="AUTHORIZATION_ERROR", context=context)


class RateLimitExceededError(PL8WRDSException):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        limit: Optional[int] = None,
        window: Optional[int] = None,
        retry_after: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize rate limit error.
        
        Args:
            message: Error message
            limit: Rate limit that was exceeded
            window: Time window for the rate limit
            retry_after: Seconds until the rate limit resets
            **kwargs: Additional context
        """
        context = kwargs.copy()
        if limit:
            context["limit"] = limit
        if window:
            context["window"] = window
        if retry_after:
            context["retry_after"] = retry_after

        super().__init__(message, error_code="RATE_LIMIT_EXCEEDED", context=context)

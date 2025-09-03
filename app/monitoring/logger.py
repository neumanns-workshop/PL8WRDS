"""
Structured logging implementation with correlation IDs and contextual information.
"""

import json
import logging
import sys
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Union
import structlog

from ..core.config import get_settings

# Context variables for request-scoped data
correlation_id_var: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar('user_id', default=None)
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
session_id_var: ContextVar[Optional[str]] = ContextVar('session_id', default=None)

settings = get_settings()


class CorrelationIDProcessor:
    """Processor to add correlation ID to log records."""
    
    def __call__(self, logger, name, event_dict):
        correlation_id = correlation_id_var.get()
        if correlation_id:
            event_dict['correlation_id'] = correlation_id
        
        request_id = request_id_var.get()
        if request_id:
            event_dict['request_id'] = request_id
        
        user_id = user_id_var.get() 
        if user_id:
            event_dict['user_id'] = user_id
        
        session_id = session_id_var.get()
        if session_id:
            event_dict['session_id'] = session_id
        
        return event_dict


class ServiceContextProcessor:
    """Processor to add service context information."""
    
    def __call__(self, logger, name, event_dict):
        event_dict.update({
            'service_name': settings.monitoring.service_name,
            'service_version': settings.monitoring.service_version,
            'environment': 'development' if settings.is_development else 'production',
            'timestamp': datetime.now(timezone.utc).isoformat(),
        })
        return event_dict


class CustomJSONRenderer:
    """Custom JSON renderer for structured logs."""
    
    def __call__(self, logger, name, event_dict):
        # Extract the main message
        message = event_dict.pop('event', '')
        
        # Build the log record
        log_record = {
            'timestamp': event_dict.pop('timestamp', datetime.now(timezone.utc).isoformat()),
            'level': event_dict.pop('level', 'INFO'),
            'logger': name,
            'message': message,
            'service_name': event_dict.pop('service_name', settings.monitoring.service_name),
            'service_version': event_dict.pop('service_version', settings.monitoring.service_version),
            'environment': event_dict.pop('environment', 'development' if settings.is_development else 'production')
        }
        
        # Add correlation and request context
        if 'correlation_id' in event_dict:
            log_record['correlation_id'] = event_dict.pop('correlation_id')
        if 'request_id' in event_dict:
            log_record['request_id'] = event_dict.pop('request_id')
        if 'user_id' in event_dict:
            log_record['user_id'] = event_dict.pop('user_id')
        if 'session_id' in event_dict:
            log_record['session_id'] = event_dict.pop('session_id')
        
        # Add any remaining fields as extra context
        if event_dict:
            log_record['extra'] = event_dict
        
        return json.dumps(log_record, ensure_ascii=False, default=str)


def setup_logging() -> None:
    """Configure structured logging for the application."""
    
    # Configure structlog
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        ServiceContextProcessor(),
        CorrelationIDProcessor(),
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    
    if settings.monitoring.log_format == "json":
        processors.append(CustomJSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        context_class=dict,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(message)s'))
    
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, settings.monitoring.log_level.upper()))


def get_logger(name: str = None) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    if name is None:
        import inspect
        frame = inspect.currentframe().f_back
        name = frame.f_globals.get('__name__', 'unknown')
    
    return structlog.get_logger(name)


def set_correlation_id(correlation_id: str = None) -> str:
    """Set correlation ID for the current context."""
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())
    correlation_id_var.set(correlation_id)
    return correlation_id


def get_correlation_id() -> Optional[str]:
    """Get the current correlation ID."""
    return correlation_id_var.get()


def set_request_id(request_id: str = None) -> str:
    """Set request ID for the current context."""
    if request_id is None:
        request_id = str(uuid.uuid4())
    request_id_var.set(request_id)
    return request_id


def get_request_id() -> Optional[str]:
    """Get the current request ID."""
    return request_id_var.get()


def set_user_id(user_id: str) -> None:
    """Set user ID for the current context."""
    user_id_var.set(user_id)


def get_user_id() -> Optional[str]:
    """Get the current user ID."""
    return user_id_var.get()


def set_session_id(session_id: str) -> None:
    """Set session ID for the current context."""
    session_id_var.set(session_id)


def get_session_id() -> Optional[str]:
    """Get the current session ID."""
    return session_id_var.get()


class LoggerMixin:
    """Mixin class to provide structured logging to any class."""
    
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.logger = get_logger(f"{cls.__module__}.{cls.__name__}")
    
    @property
    def logger(self) -> structlog.BoundLogger:
        """Get the logger for this class."""
        if not hasattr(self, '_logger'):
            self._logger = get_logger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        return self._logger


def log_function_call(func_name: str, args: tuple = None, kwargs: dict = None, 
                     duration: float = None, result: Any = None, error: Exception = None):
    """Log function call details."""
    logger = get_logger("function_calls")
    
    log_data = {
        'function': func_name,
        'event_type': 'function_call'
    }
    
    if args:
        log_data['args_count'] = len(args)
    
    if kwargs:
        log_data['kwargs_keys'] = list(kwargs.keys())
    
    if duration is not None:
        log_data['duration_ms'] = round(duration * 1000, 2)
    
    if error:
        log_data['error'] = str(error)
        log_data['error_type'] = error.__class__.__name__
        logger.error("Function call failed", **log_data)
    else:
        if result is not None:
            log_data['result_type'] = type(result).__name__
        logger.info("Function call completed", **log_data)


def log_service_event(service: str, event_type: str, details: Dict[str, Any] = None):
    """Log service-specific events."""
    logger = get_logger("service_events")
    
    log_data = {
        'service': service,
        'event_type': event_type
    }
    
    if details:
        log_data.update(details)
    
    logger.info(f"Service event: {event_type}", **log_data)


def log_business_metric(metric_name: str, value: Union[int, float], 
                       tags: Dict[str, Any] = None, unit: str = None):
    """Log business metrics for monitoring."""
    logger = get_logger("business_metrics")
    
    log_data = {
        'metric_name': metric_name,
        'metric_value': value,
        'event_type': 'business_metric'
    }
    
    if tags:
        log_data['tags'] = tags
    
    if unit:
        log_data['unit'] = unit
    
    logger.info(f"Business metric: {metric_name}", **log_data)


def log_security_event(event_type: str, severity: str, details: Dict[str, Any] = None):
    """Log security-related events."""
    logger = get_logger("security")
    
    log_data = {
        'event_type': 'security_event',
        'security_event_type': event_type,
        'severity': severity
    }
    
    if details:
        log_data.update(details)
    
    if severity in ['high', 'critical']:
        logger.error(f"Security event: {event_type}", **log_data)
    else:
        logger.warning(f"Security event: {event_type}", **log_data)


def log_performance_event(operation: str, duration: float, success: bool = True, 
                         details: Dict[str, Any] = None):
    """Log performance-related events."""
    logger = get_logger("performance")
    
    log_data = {
        'event_type': 'performance',
        'operation': operation,
        'duration_ms': round(duration * 1000, 2),
        'success': success
    }
    
    if details:
        log_data.update(details)
    
    if duration > settings.monitoring.slow_request_threshold:
        logger.warning(f"Slow operation detected: {operation}", **log_data)
    else:
        logger.info(f"Performance event: {operation}", **log_data)
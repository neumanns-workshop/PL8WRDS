"""
Monitoring and observability package for PL8WRDS API.

This package provides:
- Structured logging with correlation IDs
- Prometheus metrics collection
- Health checks and dependency monitoring
- Distributed tracing with OpenTelemetry
- Error tracking and aggregation
- Performance monitoring
- Alerting and notifications
- Security monitoring
"""

from .logger import get_logger, setup_logging
from .metrics import MetricsManager, get_metrics_manager
from .health import HealthManager, get_health_manager
from .tracing import setup_tracing, get_tracer, instrument_fastapi_app
from .middleware import (
    ObservabilityMiddleware,
    MetricsMiddleware,
    PerformanceMiddleware,
    SecurityMiddleware,
    RateLimitingMiddleware
)
from .alerting import AlertManager, get_alert_manager
from .errors import CriticalErrorHandler

__all__ = [
    "get_logger",
    "setup_logging",
    "MetricsManager",
    "get_metrics_manager", 
    "HealthManager",
    "get_health_manager",
    "setup_tracing",
    "get_tracer",
    "instrument_fastapi_app",
    "ObservabilityMiddleware",
    "MetricsMiddleware", 
    "PerformanceMiddleware",
    "SecurityMiddleware",
    "RateLimitingMiddleware",
    "AlertManager",
    "get_alert_manager",
    "CriticalErrorHandler"
]
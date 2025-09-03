"""
OpenTelemetry distributed tracing configuration and utilities.
"""

import functools
from typing import Any, Dict, Optional, Callable
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.trace import Status, StatusCode
from opentelemetry.util.http import get_excluded_urls

from ..core.config import get_settings
from .logger import get_logger, get_correlation_id, get_request_id

settings = get_settings()
logger = get_logger(__name__)

# Global tracer instance
_tracer: Optional[trace.Tracer] = None


def setup_tracing() -> None:
    """Configure OpenTelemetry tracing."""
    if not settings.monitoring.enable_tracing:
        logger.info("Tracing is disabled")
        return
    
    try:
        # Create resource
        resource = Resource.create({
            SERVICE_NAME: settings.monitoring.service_name,
            SERVICE_VERSION: settings.monitoring.service_version,
            "environment": "development" if settings.is_development else "production"
        })
        
        # Create tracer provider
        tracer_provider = TracerProvider(resource=resource)
        
        # Create Jaeger exporter
        jaeger_exporter = JaegerExporter(
            endpoint=settings.monitoring.jaeger_endpoint,
        )
        
        # Create batch span processor
        span_processor = BatchSpanProcessor(jaeger_exporter)
        tracer_provider.add_span_processor(span_processor)
        
        # Set the global tracer provider
        trace.set_tracer_provider(tracer_provider)
        
        # Configure sampling
        # Note: This is a simplified approach. In production, you might want
        # to use more sophisticated sampling strategies
        
        logger.info("OpenTelemetry tracing configured successfully")
        
        # Instrument FastAPI automatically
        _setup_auto_instrumentation()
        
    except Exception as e:
        logger.error(f"Failed to setup tracing: {e}")


def _setup_auto_instrumentation() -> None:
    """Set up automatic instrumentation for common libraries."""
    try:
        # Instrument FastAPI
        # This will be done when the FastAPI app is created
        
        # Instrument HTTPX (for external HTTP calls)
        HTTPXClientInstrumentor().instrument()
        
        # Instrument logging
        LoggingInstrumentor().instrument(set_logging_format=True)
        
        logger.info("Auto-instrumentation configured")
        
    except Exception as e:
        logger.error(f"Failed to setup auto-instrumentation: {e}")


def get_tracer() -> trace.Tracer:
    """Get the application tracer."""
    global _tracer
    if _tracer is None:
        _tracer = trace.get_tracer(
            instrumenting_module_name=__name__,
            instrumenting_library_version=settings.monitoring.service_version
        )
    return _tracer


def instrument_fastapi_app(app):
    """Instrument FastAPI application with tracing."""
    if not settings.monitoring.enable_tracing:
        return
    
    try:
        # Exclude health check endpoints from tracing to reduce noise
        excluded_urls = [
            "http://localhost/health",
            "http://localhost/metrics",
            "http://localhost/ping"
        ]
        
        FastAPIInstrumentor.instrument_app(
            app,
            excluded_urls=get_excluded_urls(excluded_urls)
        )
        
        logger.info("FastAPI app instrumented with tracing")
        
    except Exception as e:
        logger.error(f"Failed to instrument FastAPI app: {e}")


class TracingMixin:
    """Mixin class to add tracing capabilities to any class."""
    
    @property
    def tracer(self) -> trace.Tracer:
        """Get the tracer for this class."""
        return get_tracer()
    
    def create_span(self, name: str, **attributes) -> trace.Span:
        """Create a new span with class context."""
        span_name = f"{self.__class__.__name__}.{name}"
        span = self.tracer.start_span(span_name)
        
        # Add common attributes
        span.set_attribute("service.name", settings.monitoring.service_name)
        span.set_attribute("service.version", settings.monitoring.service_version)
        span.set_attribute("class.name", self.__class__.__name__)
        
        # Add correlation IDs if available
        correlation_id = get_correlation_id()
        if correlation_id:
            span.set_attribute("correlation.id", correlation_id)
        
        request_id = get_request_id()
        if request_id:
            span.set_attribute("request.id", request_id)
        
        # Add custom attributes
        for key, value in attributes.items():
            span.set_attribute(key, str(value))
        
        return span


def trace_function(
    name: Optional[str] = None,
    attributes: Optional[Dict[str, Any]] = None,
    record_exception: bool = True
):
    """Decorator to trace function calls."""
    def decorator(func: Callable) -> Callable:
        span_name = name or f"{func.__module__}.{func.__name__}"
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracer = get_tracer()
            
            with tracer.start_as_current_span(span_name) as span:
                # Add function information
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)
                
                # Add correlation context
                correlation_id = get_correlation_id()
                if correlation_id:
                    span.set_attribute("correlation.id", correlation_id)
                
                request_id = get_request_id()
                if request_id:
                    span.set_attribute("request.id", request_id)
                
                # Add custom attributes
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, str(value))
                
                # Add arguments information (be careful with sensitive data)
                if args:
                    span.set_attribute("function.args.count", len(args))
                
                if kwargs:
                    span.set_attribute("function.kwargs.count", len(kwargs))
                    # Only add non-sensitive kwargs
                    safe_kwargs = {
                        k: v for k, v in kwargs.items() 
                        if k not in ['password', 'token', 'secret', 'key']
                        and len(str(v)) < 100  # Avoid large values
                    }
                    for k, v in safe_kwargs.items():
                        span.set_attribute(f"function.kwargs.{k}", str(v))
                
                try:
                    result = await func(*args, **kwargs)
                    
                    # Record successful execution
                    span.set_status(Status(StatusCode.OK))
                    
                    # Add result information if appropriate
                    if result is not None:
                        span.set_attribute("function.result.type", type(result).__name__)
                        
                        # For dict results, add some metadata
                        if isinstance(result, dict):
                            span.set_attribute("function.result.keys.count", len(result))
                            
                        # For list results, add length
                        elif isinstance(result, list):
                            span.set_attribute("function.result.length", len(result))
                    
                    return result
                    
                except Exception as e:
                    # Record error
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.set_attribute("error.type", e.__class__.__name__)
                    span.set_attribute("error.message", str(e))
                    
                    if record_exception:
                        span.record_exception(e)
                    
                    raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            tracer = get_tracer()
            
            with tracer.start_as_current_span(span_name) as span:
                # Add function information
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)
                
                # Add correlation context
                correlation_id = get_correlation_id()
                if correlation_id:
                    span.set_attribute("correlation.id", correlation_id)
                
                request_id = get_request_id()
                if request_id:
                    span.set_attribute("request.id", request_id)
                
                # Add custom attributes
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, str(value))
                
                # Add arguments information
                if args:
                    span.set_attribute("function.args.count", len(args))
                
                if kwargs:
                    span.set_attribute("function.kwargs.count", len(kwargs))
                    safe_kwargs = {
                        k: v for k, v in kwargs.items() 
                        if k not in ['password', 'token', 'secret', 'key']
                        and len(str(v)) < 100
                    }
                    for k, v in safe_kwargs.items():
                        span.set_attribute(f"function.kwargs.{k}", str(v))
                
                try:
                    result = func(*args, **kwargs)
                    
                    # Record successful execution
                    span.set_status(Status(StatusCode.OK))
                    
                    # Add result information
                    if result is not None:
                        span.set_attribute("function.result.type", type(result).__name__)
                        
                        if isinstance(result, dict):
                            span.set_attribute("function.result.keys.count", len(result))
                        elif isinstance(result, list):
                            span.set_attribute("function.result.length", len(result))
                    
                    return result
                    
                except Exception as e:
                    # Record error
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.set_attribute("error.type", e.__class__.__name__)
                    span.set_attribute("error.message", str(e))
                    
                    if record_exception:
                        span.record_exception(e)
                    
                    raise
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def trace_business_operation(operation_name: str, **attributes):
    """Decorator specifically for tracing business operations."""
    def decorator(func: Callable) -> Callable:
        return trace_function(
            name=f"business.{operation_name}",
            attributes={
                "operation.type": "business",
                "operation.name": operation_name,
                **attributes
            }
        )(func)
    
    return decorator


def trace_external_call(service_name: str, **attributes):
    """Decorator for tracing external service calls."""
    def decorator(func: Callable) -> Callable:
        return trace_function(
            name=f"external.{service_name}",
            attributes={
                "operation.type": "external_call",
                "external.service": service_name,
                **attributes
            }
        )(func)
    
    return decorator


def trace_db_operation(operation_type: str, **attributes):
    """Decorator for tracing database operations."""
    def decorator(func: Callable) -> Callable:
        return trace_function(
            name=f"db.{operation_type}",
            attributes={
                "operation.type": "database",
                "db.operation": operation_type,
                **attributes
            }
        )(func)
    
    return decorator


def add_span_attributes(**attributes):
    """Add attributes to the current span."""
    current_span = trace.get_current_span()
    if current_span is not None:
        for key, value in attributes.items():
            current_span.set_attribute(key, str(value))


def add_span_event(name: str, **attributes):
    """Add an event to the current span."""
    current_span = trace.get_current_span()
    if current_span is not None:
        current_span.add_event(name, attributes)


def set_span_error(error: Exception):
    """Mark the current span as having an error."""
    current_span = trace.get_current_span()
    if current_span is not None:
        current_span.set_status(Status(StatusCode.ERROR, str(error)))
        current_span.set_attribute("error.type", error.__class__.__name__)
        current_span.set_attribute("error.message", str(error))
        current_span.record_exception(error)


class TracedOperation:
    """Context manager for tracing operations."""
    
    def __init__(self, name: str, **attributes):
        self.name = name
        self.attributes = attributes
        self.tracer = get_tracer()
        self.span = None
    
    def __enter__(self):
        self.span = self.tracer.start_span(self.name)
        
        # Add correlation context
        correlation_id = get_correlation_id()
        if correlation_id:
            self.span.set_attribute("correlation.id", correlation_id)
        
        request_id = get_request_id()
        if request_id:
            self.span.set_attribute("request.id", request_id)
        
        # Add custom attributes
        for key, value in self.attributes.items():
            self.span.set_attribute(key, str(value))
        
        return self.span
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.span:
            if exc_type is not None:
                self.span.set_status(Status(StatusCode.ERROR, str(exc_val)))
                self.span.set_attribute("error.type", exc_type.__name__)
                self.span.set_attribute("error.message", str(exc_val))
                self.span.record_exception(exc_val)
            else:
                self.span.set_status(Status(StatusCode.OK))
            
            self.span.end()


# Utility functions for common tracing patterns
def trace_word_scoring(model_type: str):
    """Trace word scoring operations."""
    return trace_business_operation(
        "word_scoring",
        model_type=model_type,
        component="scoring"
    )


def trace_ml_prediction():
    """Trace ML prediction operations."""
    return trace_business_operation(
        "ml_prediction",
        component="prediction_service"
    )


def trace_llm_request(model_name: str):
    """Trace LLM API requests."""
    return trace_external_call(
        "ollama",
        model_name=model_name,
        component="ollama_client"
    )


def trace_feature_extraction():
    """Trace feature extraction operations."""
    return trace_business_operation(
        "feature_extraction",
        component="feature_service"
    )


def trace_solver_operation():
    """Trace word solver operations."""
    return trace_business_operation(
        "word_solving", 
        component="solver_service"
    )
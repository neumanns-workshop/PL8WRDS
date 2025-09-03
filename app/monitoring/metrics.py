"""
Prometheus metrics collection and management.
"""

import time
from functools import wraps
from typing import Any, Dict, List, Optional, Union
from prometheus_client import (
    Counter, Histogram, Gauge, Summary, Info,
    CollectorRegistry, CONTENT_TYPE_LATEST, generate_latest
)
import psutil
from contextvars import ContextVar

from ..core.config import get_settings
from .logger import get_logger, log_business_metric

settings = get_settings()
logger = get_logger(__name__)

# Global registry for metrics
registry = CollectorRegistry()

# Context variable for tracking current operation
current_operation_var: ContextVar[Optional[str]] = ContextVar('current_operation', default=None)


class MetricsManager:
    """Centralized metrics management for the PL8WRDS API."""
    
    def __init__(self):
        self.prefix = settings.monitoring.prometheus_prefix
        self._setup_default_metrics()
        self._setup_business_metrics()
        self._setup_performance_metrics()
        
    def _setup_default_metrics(self):
        """Set up default application metrics."""
        
        # HTTP request metrics
        self.http_requests_total = Counter(
            f'{self.prefix}_http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status_code'],
            registry=registry
        )
        
        self.http_request_duration = Histogram(
            f'{self.prefix}_http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'endpoint'],
            buckets=[0.001, 0.01, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0],
            registry=registry
        )
        
        self.http_requests_in_progress = Gauge(
            f'{self.prefix}_http_requests_in_progress',
            'Number of HTTP requests currently being processed',
            ['method', 'endpoint'],
            registry=registry
        )
        
        # Application metrics
        self.app_info = Info(
            f'{self.prefix}_app_info',
            'Application information',
            registry=registry
        )
        self.app_info.info({
            'version': settings.app.app_version,
            'environment': 'development' if settings.is_development else 'production',
            'service_name': settings.monitoring.service_name
        })
        
        self.app_start_time = Gauge(
            f'{self.prefix}_app_start_time_seconds',
            'Unix timestamp when the application started',
            registry=registry
        )
        self.app_start_time.set_to_current_time()
        
        # System metrics
        self.system_cpu_usage = Gauge(
            f'{self.prefix}_system_cpu_usage_percent',
            'CPU usage percentage',
            registry=registry
        )
        
        self.system_memory_usage = Gauge(
            f'{self.prefix}_system_memory_usage_bytes',
            'Memory usage in bytes',
            ['type'],  # 'used', 'available', 'total'
            registry=registry
        )
        
        self.system_disk_usage = Gauge(
            f'{self.prefix}_system_disk_usage_bytes',
            'Disk usage in bytes',
            ['type'],  # 'used', 'free', 'total'
            registry=registry
        )
        
    def _setup_business_metrics(self):
        """Set up business-specific metrics."""
        
        # Word scoring metrics
        self.word_scores_generated = Counter(
            f'{self.prefix}_word_scores_generated_total',
            'Total number of word scores generated',
            ['model_type'],  # 'ml_prediction', 'llm_scoring'
            registry=registry
        )
        
        self.word_scoring_duration = Histogram(
            f'{self.prefix}_word_scoring_duration_seconds',
            'Time taken to score words',
            ['model_type'],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
            registry=registry
        )
        
        self.ml_model_predictions = Counter(
            f'{self.prefix}_ml_model_predictions_total',
            'Total ML model predictions made',
            ['model_version', 'success'],
            registry=registry
        )
        
        self.ml_model_accuracy = Gauge(
            f'{self.prefix}_ml_model_accuracy',
            'Current ML model accuracy score',
            registry=registry
        )
        
        # LLM scoring metrics
        self.llm_requests = Counter(
            f'{self.prefix}_llm_requests_total',
            'Total LLM requests',
            ['model_name', 'status'],
            registry=registry
        )
        
        self.llm_request_duration = Histogram(
            f'{self.prefix}_llm_request_duration_seconds',
            'LLM request duration',
            ['model_name'],
            buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0],
            registry=registry
        )
        
        # Cache metrics
        self.cache_operations = Counter(
            f'{self.prefix}_cache_operations_total',
            'Cache operations',
            ['operation', 'status'],  # hit/miss, success/error
            registry=registry
        )
        
        self.cache_size = Gauge(
            f'{self.prefix}_cache_size_bytes',
            'Size of various caches',
            ['cache_type'],
            registry=registry
        )
        
        # Solver service metrics
        self.word_discoveries = Counter(
            f'{self.prefix}_word_discoveries_total',
            'Words discovered for license plates',
            registry=registry
        )
        
        self.solver_duration = Histogram(
            f'{self.prefix}_solver_duration_seconds',
            'Time taken to find words for plates',
            buckets=[0.001, 0.01, 0.1, 0.5, 1.0, 2.0],
            registry=registry
        )
        
    def _setup_performance_metrics(self):
        """Set up performance monitoring metrics."""
        
        # Error metrics
        self.errors_total = Counter(
            f'{self.prefix}_errors_total',
            'Total errors by type',
            ['error_type', 'severity', 'component'],
            registry=registry
        )
        
        self.exceptions_total = Counter(
            f'{self.prefix}_exceptions_total',
            'Total exceptions',
            ['exception_type', 'endpoint'],
            registry=registry
        )
        
        # Database metrics (future use)
        self.db_connections_active = Gauge(
            f'{self.prefix}_db_connections_active',
            'Active database connections',
            registry=registry
        )
        
        self.db_query_duration = Histogram(
            f'{self.prefix}_db_query_duration_seconds',
            'Database query duration',
            ['operation'],
            buckets=[0.001, 0.01, 0.1, 0.5, 1.0, 5.0],
            registry=registry
        )
        
        # Health check metrics
        self.health_check_status = Gauge(
            f'{self.prefix}_health_check_status',
            'Health check status (1=healthy, 0=unhealthy)',
            ['service'],
            registry=registry
        )
        
        self.health_check_duration = Histogram(
            f'{self.prefix}_health_check_duration_seconds',
            'Health check duration',
            ['service'],
            registry=registry
        )
        
    def update_system_metrics(self):
        """Update system resource metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.system_cpu_usage.set(cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.system_memory_usage.labels(type='used').set(memory.used)
            self.system_memory_usage.labels(type='available').set(memory.available)
            self.system_memory_usage.labels(type='total').set(memory.total)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            self.system_disk_usage.labels(type='used').set(disk.used)
            self.system_disk_usage.labels(type='free').set(disk.free)
            self.system_disk_usage.labels(type='total').set(disk.total)
            
        except Exception as e:
            logger.error("Failed to update system metrics", error=str(e))
    
    def record_http_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record HTTP request metrics."""
        self.http_requests_total.labels(
            method=method, 
            endpoint=endpoint, 
            status_code=str(status_code)
        ).inc()
        
        self.http_request_duration.labels(
            method=method, 
            endpoint=endpoint
        ).observe(duration)
    
    def start_http_request(self, method: str, endpoint: str):
        """Mark the start of an HTTP request."""
        self.http_requests_in_progress.labels(
            method=method, 
            endpoint=endpoint
        ).inc()
    
    def end_http_request(self, method: str, endpoint: str):
        """Mark the end of an HTTP request."""
        self.http_requests_in_progress.labels(
            method=method, 
            endpoint=endpoint
        ).dec()
    
    def record_word_score(self, model_type: str, duration: float, success: bool = True):
        """Record word scoring metrics."""
        if success:
            self.word_scores_generated.labels(model_type=model_type).inc()
        
        self.word_scoring_duration.labels(model_type=model_type).observe(duration)
        
        # Also log as business metric
        log_business_metric(
            'word_score_generated',
            1,
            tags={'model_type': model_type, 'success': success},
            unit='count'
        )
    
    def record_ml_prediction(self, model_version: str, success: bool, duration: float = None):
        """Record ML model prediction metrics."""
        self.ml_model_predictions.labels(
            model_version=model_version,
            success=str(success)
        ).inc()
        
        if duration:
            self.word_scoring_duration.labels(model_type='ml_prediction').observe(duration)
    
    def record_llm_request(self, model_name: str, status: str, duration: float):
        """Record LLM request metrics."""
        self.llm_requests.labels(
            model_name=model_name,
            status=status
        ).inc()
        
        self.llm_request_duration.labels(model_name=model_name).observe(duration)
    
    def record_cache_operation(self, operation: str, status: str):
        """Record cache operation metrics."""
        self.cache_operations.labels(
            operation=operation,
            status=status
        ).inc()
    
    def record_error(self, error_type: str, severity: str, component: str):
        """Record error metrics."""
        self.errors_total.labels(
            error_type=error_type,
            severity=severity,
            component=component
        ).inc()
    
    def record_exception(self, exception_type: str, endpoint: str):
        """Record exception metrics."""
        self.exceptions_total.labels(
            exception_type=exception_type,
            endpoint=endpoint
        ).inc()
    
    def record_health_check(self, service: str, is_healthy: bool, duration: float):
        """Record health check metrics."""
        self.health_check_status.labels(service=service).set(1 if is_healthy else 0)
        self.health_check_duration.labels(service=service).observe(duration)
    
    def get_metrics_text(self) -> str:
        """Get metrics in Prometheus text format."""
        return generate_latest(registry).decode('utf-8')
    
    def get_metrics_content_type(self) -> str:
        """Get the content type for metrics endpoint."""
        return CONTENT_TYPE_LATEST


# Global metrics manager instance
_metrics_manager: Optional[MetricsManager] = None


def get_metrics_manager() -> MetricsManager:
    """Get the global metrics manager instance."""
    global _metrics_manager
    if _metrics_manager is None:
        _metrics_manager = MetricsManager()
    return _metrics_manager


def track_operation(operation_name: str):
    """Decorator to track operation metrics."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            metrics = get_metrics_manager()
            start_time = time.time()
            current_operation_var.set(operation_name)
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Record success metrics based on operation type
                if 'score' in operation_name.lower():
                    metrics.record_word_score('ml_prediction', duration, success=True)
                elif 'llm' in operation_name.lower():
                    metrics.record_llm_request('unknown', 'success', duration)
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                metrics.record_error(
                    error_type=e.__class__.__name__,
                    severity='error',
                    component=operation_name
                )
                raise
            finally:
                current_operation_var.set(None)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            metrics = get_metrics_manager()
            start_time = time.time()
            current_operation_var.set(operation_name)
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Record success metrics based on operation type
                if 'score' in operation_name.lower():
                    metrics.record_word_score('ml_prediction', duration, success=True)
                elif 'llm' in operation_name.lower():
                    metrics.record_llm_request('unknown', 'success', duration)
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                metrics.record_error(
                    error_type=e.__class__.__name__,
                    severity='error', 
                    component=operation_name
                )
                raise
            finally:
                current_operation_var.set(None)
        
        # Return appropriate wrapper based on whether function is async
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def record_business_event(event_name: str, value: Union[int, float] = 1, 
                         labels: Dict[str, str] = None):
    """Record a business event metric."""
    metrics = get_metrics_manager()
    
    # Map common business events to specific metrics
    if event_name == 'word_discovered':
        metrics.word_discoveries.inc()
    elif event_name == 'cache_hit':
        metrics.record_cache_operation('get', 'hit')
    elif event_name == 'cache_miss':
        metrics.record_cache_operation('get', 'miss')
    
    # Also log as structured event
    log_business_metric(event_name, value, tags=labels)
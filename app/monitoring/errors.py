"""
Error tracking and aggregation system with Sentry integration.
"""

import functools
import inspect
import traceback
from collections import defaultdict, Counter
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Union, Callable
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.httpx import HttpxIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

from ..core.config import get_settings
from .logger import get_logger, get_correlation_id, get_request_id, get_user_id
from .metrics import get_metrics_manager
from .alerting import get_alert_manager, AlertSeverity

settings = get_settings()
logger = get_logger(__name__)


class ErrorTracker:
    """Track and aggregate application errors."""
    
    def __init__(self):
        self.error_counts = Counter()
        self.error_details = defaultdict(list)
        self.error_trends = defaultdict(list)
        self.max_error_history = 1000
        self.setup_sentry()
    
    def setup_sentry(self):
        """Initialize Sentry error tracking if enabled."""
        if not settings.monitoring.enable_sentry or not settings.monitoring.sentry_dsn:
            logger.info("Sentry error tracking is disabled")
            return
        
        try:
            sentry_sdk.init(
                dsn=settings.monitoring.sentry_dsn,
                environment=settings.monitoring.sentry_environment,
                sample_rate=settings.monitoring.sentry_sample_rate,
                traces_sample_rate=settings.monitoring.sentry_traces_sample_rate,
                integrations=[
                    FastApiIntegration(auto_instrumenting=True),
                    HttpxIntegration(),
                    LoggingIntegration(
                        level=None,        # Capture info and above as breadcrumbs
                        event_level=40,    # Send no events from log statements
                    ),
                ],
                before_send=self._before_send_sentry,
                max_breadcrumbs=50,
                attach_stacktrace=True,
                send_default_pii=False
            )
            
            logger.info("Sentry error tracking initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Sentry: {e}")
    
    def _before_send_sentry(self, event, hint):
        """Process Sentry events before sending."""
        # Add custom context
        if event:
            # Add correlation context
            correlation_id = get_correlation_id()
            if correlation_id:
                event.setdefault('extra', {})['correlation_id'] = correlation_id
            
            request_id = get_request_id()
            if request_id:
                event.setdefault('extra', {})['request_id'] = request_id
            
            user_id = get_user_id()
            if user_id:
                event.setdefault('user', {})['id'] = user_id
            
            # Add service context
            event.setdefault('tags', {}).update({
                'service_name': settings.monitoring.service_name,
                'service_version': settings.monitoring.service_version,
                'environment': 'development' if settings.is_development else 'production'
            })
        
        return event
    
    def record_error(self, 
                    error: Exception,
                    context: Optional[Dict[str, Any]] = None,
                    severity: str = "error",
                    component: str = "unknown",
                    user_id: Optional[str] = None,
                    correlation_id: Optional[str] = None) -> str:
        """Record an error with context."""
        
        # Generate error ID
        error_id = f"{component}_{int(datetime.now(timezone.utc).timestamp())}_{hash(str(error)) % 10000}"
        
        # Create error record
        error_record = {
            'id': error_id,
            'error_type': error.__class__.__name__,
            'error_message': str(error),
            'component': component,
            'severity': severity,
            'timestamp': datetime.now(timezone.utc),
            'user_id': user_id or get_user_id(),
            'correlation_id': correlation_id or get_correlation_id(),
            'request_id': get_request_id(),
            'context': context or {},
            'traceback': traceback.format_exc(),
            'stack_info': self._get_stack_info()
        }
        
        # Update counters
        error_key = f"{error.__class__.__name__}:{component}"
        self.error_counts[error_key] += 1
        
        # Store error details
        self.error_details[error_key].append(error_record)
        
        # Trim history if too large
        if len(self.error_details[error_key]) > self.max_error_history:
            self.error_details[error_key] = self.error_details[error_key][-self.max_error_history:]
        
        # Update trends
        now = datetime.now(timezone.utc)
        self.error_trends[error_key].append(now)
        
        # Clean old trend data (keep last 24 hours)
        cutoff_time = now - timedelta(hours=24)
        self.error_trends[error_key] = [
            t for t in self.error_trends[error_key] if t > cutoff_time
        ]
        
        # Record metrics
        metrics = get_metrics_manager()
        metrics.record_error(
            error_type=error.__class__.__name__,
            severity=severity,
            component=component
        )
        
        # Log error
        logger.error(
            f"Error recorded: {error.__class__.__name__}",
            error_id=error_id,
            error_message=str(error),
            component=component,
            severity=severity,
            context=context
        )
        
        # Send to Sentry if enabled
        if settings.monitoring.enable_sentry:
            with sentry_sdk.push_scope() as scope:
                scope.set_tag("component", component)
                scope.set_tag("severity", severity)
                scope.set_extra("error_id", error_id)
                
                if context:
                    for key, value in context.items():
                        scope.set_extra(key, value)
                
                if correlation_id:
                    scope.set_extra("correlation_id", correlation_id)
                
                sentry_sdk.capture_exception(error)
        
        # Check for alert conditions
        self._check_error_alerts(error_key, error_record)
        
        return error_id
    
    def _get_stack_info(self) -> List[Dict[str, Any]]:
        """Get simplified stack information."""
        stack = inspect.stack()
        stack_info = []
        
        for frame_info in stack[2:]:  # Skip current and calling frame
            stack_info.append({
                'filename': frame_info.filename,
                'function': frame_info.function,
                'lineno': frame_info.lineno,
                'code': frame_info.code_context[0].strip() if frame_info.code_context else None
            })
        
        return stack_info
    
    def _check_error_alerts(self, error_key: str, error_record: Dict[str, Any]):
        """Check if error conditions warrant alerts."""
        import asyncio
        
        # High frequency errors
        recent_errors = len([
            t for t in self.error_trends[error_key]
            if t > datetime.now(timezone.utc) - timedelta(minutes=5)
        ])
        
        if recent_errors >= 10:  # 10 errors in 5 minutes
            alert_manager = get_alert_manager()
            asyncio.create_task(alert_manager.create_alert(
                title=f"High Error Rate: {error_record['error_type']}",
                description=f"Component '{error_record['component']}' has generated {recent_errors} errors in the last 5 minutes",
                severity=AlertSeverity.HIGH,
                component=error_record['component'],
                metadata={
                    'error_type': error_record['error_type'],
                    'error_count': recent_errors,
                    'time_window': '5_minutes'
                },
                correlation_id=error_record['correlation_id']
            ))
        
        # Critical errors
        if error_record['severity'] == 'critical':
            alert_manager = get_alert_manager()
            asyncio.create_task(alert_manager.create_alert(
                title=f"Critical Error: {error_record['error_type']}",
                description=f"Critical error in component '{error_record['component']}': {error_record['error_message']}",
                severity=AlertSeverity.CRITICAL,
                component=error_record['component'],
                metadata={
                    'error_type': error_record['error_type'],
                    'error_message': error_record['error_message'],
                    'error_id': error_record['id']
                },
                correlation_id=error_record['correlation_id']
            ))
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of error statistics."""
        now = datetime.now(timezone.utc)
        
        # Calculate time-based statistics
        last_hour_errors = 0
        last_24h_errors = 0
        
        for error_key, timestamps in self.error_trends.items():
            last_hour_errors += len([t for t in timestamps if t > now - timedelta(hours=1)])
            last_24h_errors += len([t for t in timestamps if t > now - timedelta(hours=24)])
        
        # Top errors
        top_errors = self.error_counts.most_common(10)
        
        # Error rate trends
        hourly_errors = defaultdict(int)
        for timestamps in self.error_trends.values():
            for timestamp in timestamps:
                hour_key = timestamp.replace(minute=0, second=0, microsecond=0)
                hourly_errors[hour_key] += 1
        
        return {
            'total_errors': sum(self.error_counts.values()),
            'unique_error_types': len(self.error_counts),
            'last_hour_errors': last_hour_errors,
            'last_24h_errors': last_24h_errors,
            'top_errors': [{'error_key': key, 'count': count} for key, count in top_errors],
            'hourly_trends': {
                k.isoformat(): v for k, v in 
                sorted(hourly_errors.items(), key=lambda x: x[0])[-24:]  # Last 24 hours
            }
        }
    
    def get_error_details(self, error_key: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get detailed error records for a specific error type."""
        if error_key not in self.error_details:
            return []
        
        # Return most recent errors
        errors = self.error_details[error_key][-limit:]
        
        # Convert timestamps to ISO format for JSON serialization
        for error in errors:
            if isinstance(error['timestamp'], datetime):
                error['timestamp'] = error['timestamp'].isoformat()
        
        return errors
    
    def clear_old_errors(self, days: int = 7):
        """Clear error records older than specified days."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(days=days)
        
        for error_key in list(self.error_details.keys()):
            self.error_details[error_key] = [
                error for error in self.error_details[error_key]
                if error['timestamp'] > cutoff_time
            ]
            
            # Remove empty keys
            if not self.error_details[error_key]:
                del self.error_details[error_key]
                del self.error_counts[error_key]
        
        logger.info(f"Cleared error records older than {days} days")


def track_errors(
    component: str = None,
    severity: str = "error",
    capture_context: bool = True,
    reraise: bool = True
):
    """Decorator to automatically track errors from function calls."""
    def decorator(func: Callable) -> Callable:
        component_name = component or f"{func.__module__}.{func.__name__}"
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                context = {}
                if capture_context:
                    context.update({
                        'function_name': func.__name__,
                        'function_module': func.__module__,
                        'args_count': len(args),
                        'kwargs_keys': list(kwargs.keys()) if kwargs else []
                    })
                    
                    # Add safe argument values (avoid sensitive data)
                    safe_kwargs = {
                        k: v for k, v in kwargs.items()
                        if k not in ['password', 'token', 'secret', 'key', 'auth']
                        and len(str(v)) < 200
                    }
                    if safe_kwargs:
                        context['safe_kwargs'] = safe_kwargs
                
                error_tracker.record_error(
                    error=e,
                    context=context,
                    severity=severity,
                    component=component_name
                )
                
                if reraise:
                    raise
                
                return None
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                context = {}
                if capture_context:
                    context.update({
                        'function_name': func.__name__,
                        'function_module': func.__module__,
                        'args_count': len(args),
                        'kwargs_keys': list(kwargs.keys()) if kwargs else []
                    })
                    
                    safe_kwargs = {
                        k: v for k, v in kwargs.items()
                        if k not in ['password', 'token', 'secret', 'key', 'auth']
                        and len(str(v)) < 200
                    }
                    if safe_kwargs:
                        context['safe_kwargs'] = safe_kwargs
                
                error_tracker.record_error(
                    error=e,
                    context=context,
                    severity=severity,
                    component=component_name
                )
                
                if reraise:
                    raise
                
                return None
        
        # Return appropriate wrapper
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def record_error(error: Exception, 
                context: Optional[Dict[str, Any]] = None,
                severity: str = "error",
                component: str = "unknown") -> str:
    """Convenience function to record errors."""
    return error_tracker.record_error(
        error=error,
        context=context,
        severity=severity,
        component=component
    )


def with_error_context(**context_kwargs):
    """Context manager to add error tracking context."""
    class ErrorContext:
        def __enter__(self):
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            if exc_type is not None:
                error_tracker.record_error(
                    error=exc_val,
                    context=context_kwargs,
                    component=context_kwargs.get('component', 'unknown')
                )
            return False  # Don't suppress the exception
    
    return ErrorContext()


class CriticalErrorHandler:
    """Handler for critical system errors that require immediate attention."""
    
    @staticmethod
    def handle_startup_error(error: Exception, component: str):
        """Handle critical startup errors."""
        error_id = error_tracker.record_error(
            error=error,
            severity="critical",
            component=component,
            context={'phase': 'startup'}
        )
        
        logger.critical(
            f"Critical startup error in {component}",
            error_id=error_id,
            error_type=error.__class__.__name__,
            error_message=str(error)
        )
    
    @staticmethod
    def handle_service_failure(error: Exception, service: str):
        """Handle critical service failures."""
        error_id = error_tracker.record_error(
            error=error,
            severity="critical",
            component=service,
            context={'failure_type': 'service_failure'}
        )
        
        logger.critical(
            f"Critical service failure: {service}",
            error_id=error_id,
            error_type=error.__class__.__name__,
            error_message=str(error)
        )
    
    @staticmethod
    def handle_data_corruption(error: Exception, data_type: str):
        """Handle data corruption errors."""
        error_id = error_tracker.record_error(
            error=error,
            severity="critical",
            component="data_integrity",
            context={
                'corruption_type': data_type,
                'failure_type': 'data_corruption'
            }
        )
        
        logger.critical(
            f"Data corruption detected: {data_type}",
            error_id=error_id,
            error_type=error.__class__.__name__,
            error_message=str(error)
        )


# Global error tracker instance
error_tracker = ErrorTracker()


def get_error_tracker() -> ErrorTracker:
    """Get the global error tracker instance."""
    return error_tracker
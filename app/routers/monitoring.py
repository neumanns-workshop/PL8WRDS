"""
Monitoring endpoints for health checks, metrics, and observability.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Response, Query
from pydantic import BaseModel

from ..core.config import get_settings
from ..monitoring.health import get_health_manager, HealthStatus
from ..monitoring.metrics import get_metrics_manager
from ..monitoring.errors import get_error_tracker
from ..monitoring.alerting import get_alert_manager, AlertSeverity
from ..monitoring.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: str
    uptime_seconds: float
    checks: Dict[str, Any]
    summary: Dict[str, Any]
    service_info: Dict[str, str]


class MetricsSummary(BaseModel):
    """Metrics summary response model."""
    total_requests: int
    error_rate: float
    avg_response_time: float
    active_requests: int
    uptime_seconds: float


class ErrorSummary(BaseModel):
    """Error summary response model."""
    total_errors: int
    unique_error_types: int
    last_hour_errors: int
    last_24h_errors: int
    top_errors: List[Dict[str, Any]]


class AlertResponse(BaseModel):
    """Alert response model."""
    id: str
    title: str
    description: str
    severity: str
    status: str
    component: str
    created_at: str
    updated_at: str


@router.get("/health", response_model=HealthResponse, include_in_schema=False)
async def health_check():
    """
    Comprehensive health check endpoint.
    
    Returns detailed health status of all application components.
    """
    health_manager = get_health_manager()
    health_result = await health_manager.run_all_checks()
    
    return HealthResponse(**health_result)


@router.get("/health/live", include_in_schema=False)
async def liveness_check():
    """
    Kubernetes liveness probe endpoint.
    
    Simple check to verify the application is running.
    """
    health_manager = get_health_manager()
    result = await health_manager.run_liveness_check()
    
    if result["status"] != HealthStatus.HEALTHY.value:
        raise HTTPException(status_code=503, detail="Service not available")
    
    return result


@router.get("/health/ready", include_in_schema=False)
async def readiness_check():
    """
    Kubernetes readiness probe endpoint.
    
    Checks if the application is ready to serve traffic.
    """
    health_manager = get_health_manager()
    result = await health_manager.run_readiness_check()
    
    if result["status"] != HealthStatus.HEALTHY.value:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    return result


@router.get("/metrics", include_in_schema=False)
async def metrics_endpoint():
    """
    Prometheus metrics endpoint.
    
    Returns metrics in Prometheus text format.
    """
    metrics_manager = get_metrics_manager()
    
    # Update system metrics before returning
    metrics_manager.update_system_metrics()
    
    metrics_text = metrics_manager.get_metrics_text()
    content_type = metrics_manager.get_metrics_content_type()
    
    return Response(content=metrics_text, media_type=content_type)


@router.get("/metrics/summary", response_model=MetricsSummary)
async def metrics_summary():
    """
    Get a summary of key metrics.
    
    Returns high-level metrics for dashboards and monitoring.
    """
    metrics_manager = get_metrics_manager()
    
    # This would typically query your metrics backend
    # For now, return placeholder data
    return MetricsSummary(
        total_requests=1000,
        error_rate=0.01,
        avg_response_time=0.25,
        active_requests=5,
        uptime_seconds=3600.0
    )


@router.get("/errors", response_model=ErrorSummary)
async def error_summary():
    """
    Get error summary and statistics.
    
    Returns aggregated error information for monitoring.
    """
    error_tracker = get_error_tracker()
    summary = error_tracker.get_error_summary()
    
    return ErrorSummary(**summary)


@router.get("/errors/{error_key}")
async def error_details(
    error_key: str,
    limit: int = Query(default=50, ge=1, le=200)
):
    """
    Get detailed error records for a specific error type.
    
    Args:
        error_key: The error key (e.g., "ValueError:ml_model")
        limit: Maximum number of error records to return
    """
    error_tracker = get_error_tracker()
    details = error_tracker.get_error_details(error_key, limit)
    
    if not details:
        raise HTTPException(status_code=404, detail="Error key not found")
    
    return {
        "error_key": error_key,
        "total_records": len(details),
        "errors": details
    }


@router.get("/alerts", response_model=List[AlertResponse])
async def get_active_alerts():
    """
    Get all active alerts.
    
    Returns list of currently active alerts.
    """
    alert_manager = get_alert_manager()
    alerts = alert_manager.get_active_alerts()
    
    return [AlertResponse(
        id=alert.id,
        title=alert.title,
        description=alert.description,
        severity=alert.severity.value,
        status=alert.status.value,
        component=alert.component,
        created_at=alert.created_at.isoformat(),
        updated_at=alert.updated_at.isoformat()
    ) for alert in alerts]


@router.get("/alerts/history")
async def get_alert_history(
    limit: int = Query(default=100, ge=1, le=500)
):
    """
    Get alert history.
    
    Args:
        limit: Maximum number of alerts to return
    """
    alert_manager = get_alert_manager()
    alerts = alert_manager.get_alert_history(limit)
    
    return {
        "total_alerts": len(alerts),
        "alerts": [AlertResponse(
            id=alert.id,
            title=alert.title,
            description=alert.description,
            severity=alert.severity.value,
            status=alert.status.value,
            component=alert.component,
            created_at=alert.created_at.isoformat(),
            updated_at=alert.updated_at.isoformat()
        ) for alert in alerts]
    }


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    acknowledged_by: str = Query(..., description="Who acknowledged the alert")
):
    """
    Acknowledge an active alert.
    
    Args:
        alert_id: The alert ID to acknowledge
        acknowledged_by: Username or system that acknowledged the alert
    """
    alert_manager = get_alert_manager()
    success = await alert_manager.acknowledge_alert(alert_id, acknowledged_by)
    
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found or already resolved")
    
    return {"message": "Alert acknowledged successfully"}


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    resolved_by: str = Query(..., description="Who resolved the alert")
):
    """
    Resolve an active alert.
    
    Args:
        alert_id: The alert ID to resolve
        resolved_by: Username or system that resolved the alert
    """
    alert_manager = get_alert_manager()
    success = await alert_manager.resolve_alert(alert_id, resolved_by)
    
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {"message": "Alert resolved successfully"}


@router.post("/alerts/test")
async def create_test_alert():
    """
    Create a test alert for testing notification channels.
    
    This endpoint creates a low-severity test alert to verify
    the alerting system is working properly.
    """
    alert_manager = get_alert_manager()
    
    alert = await alert_manager.create_alert(
        title="Test Alert",
        description="This is a test alert created via the monitoring API to verify the alerting system is functioning correctly.",
        severity=AlertSeverity.LOW,
        component="monitoring_api",
        metadata={
            "test_alert": True,
            "created_via": "api_endpoint"
        }
    )
    
    return {
        "message": "Test alert created successfully",
        "alert_id": alert.id
    }


@router.post("/notifications/test")
async def test_notifications():
    """
    Test all notification channels.
    
    Sends test notifications through all configured channels
    and returns the status of each channel.
    """
    alert_manager = get_alert_manager()
    results = await alert_manager.test_notifications()
    
    return {
        "message": "Notification test completed",
        "results": results,
        "total_channels": len(results),
        "successful_channels": sum(1 for success in results.values() if success),
        "failed_channels": sum(1 for success in results.values() if not success)
    }


@router.get("/info")
async def monitoring_info():
    """
    Get monitoring system information and configuration.
    
    Returns information about the monitoring setup and capabilities.
    """
    return {
        "service": {
            "name": settings.monitoring.service_name,
            "version": settings.monitoring.service_version,
            "environment": "development" if settings.is_development else "production"
        },
        "monitoring": {
            "structured_logging": settings.monitoring.enable_structured_logging,
            "prometheus_metrics": settings.monitoring.enable_prometheus_metrics,
            "health_checks": settings.monitoring.enable_health_checks,
            "distributed_tracing": settings.monitoring.enable_tracing,
            "error_tracking": settings.monitoring.enable_sentry,
            "alerting": settings.monitoring.enable_alerting,
            "performance_monitoring": settings.monitoring.enable_performance_monitoring,
            "security_monitoring": settings.monitoring.enable_security_monitoring
        },
        "endpoints": {
            "health": "/monitoring/health",
            "liveness": "/monitoring/health/live",
            "readiness": "/monitoring/health/ready",
            "metrics": "/monitoring/metrics",
            "errors": "/monitoring/errors",
            "alerts": "/monitoring/alerts"
        },
        "alert_channels": {
            "email": settings.monitoring.alert_email_enabled,
            "slack": settings.monitoring.alert_slack_enabled,
            "webhook": settings.monitoring.alert_webhook_enabled
        }
    }


@router.post("/cache/clear")
async def clear_monitoring_cache():
    """
    Clear monitoring system caches.
    
    Clears error history and resets monitoring caches.
    Useful for testing and cleanup.
    """
    try:
        # Clear error tracker cache
        error_tracker = get_error_tracker()
        error_tracker.clear_old_errors(days=0)  # Clear all
        
        # Reset metrics (if needed)
        # This would depend on your metrics implementation
        
        logger.info("Monitoring caches cleared successfully")
        
        return {"message": "Monitoring caches cleared successfully"}
        
    except Exception as e:
        logger.error(f"Failed to clear monitoring caches: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear caches")


@router.get("/status")
async def monitoring_status():
    """
    Get overall monitoring system status.
    
    Quick status check of all monitoring components.
    """
    health_manager = get_health_manager()
    error_tracker = get_error_tracker()
    alert_manager = get_alert_manager()
    
    # Get basic health
    health_result = await health_manager.run_liveness_check()
    
    # Get error summary
    error_summary = error_tracker.get_error_summary()
    
    # Get active alerts count
    active_alerts = alert_manager.get_active_alerts()
    
    overall_status = "healthy"
    if health_result["status"] != HealthStatus.HEALTHY.value:
        overall_status = "unhealthy"
    elif error_summary["last_hour_errors"] > 10:
        overall_status = "degraded"
    elif len(active_alerts) > 5:
        overall_status = "degraded"
    
    return {
        "overall_status": overall_status,
        "timestamp": health_result["timestamp"],
        "uptime_seconds": health_result["uptime_seconds"],
        "components": {
            "health_checks": health_result["status"],
            "error_tracking": "healthy" if error_summary["last_hour_errors"] < 50 else "degraded",
            "alerting": "healthy" if len(active_alerts) < 10 else "degraded"
        },
        "summary": {
            "active_alerts": len(active_alerts),
            "errors_last_hour": error_summary["last_hour_errors"],
            "total_errors": error_summary["total_errors"]
        }
    }
# PL8WRDS Monitoring & Observability Guide

This document provides comprehensive guidance on monitoring, observability, and operational aspects of the PL8WRDS API.

## Overview

The PL8WRDS API includes a production-ready monitoring and observability stack with the following components:

- **Structured Logging** with correlation IDs and contextual information
- **Prometheus Metrics** for performance and business metrics
- **Comprehensive Health Checks** for all dependencies and services
- **Distributed Tracing** with OpenTelemetry and Jaeger
- **Error Tracking** with Sentry integration
- **Alerting & Notifications** via email, Slack, and webhooks
- **Security Monitoring** with intrusion detection and audit logging
- **Performance Monitoring** with automatic slow request detection

## Quick Start

### Environment Configuration

Create a `.env` file with monitoring configuration:

```bash
# Monitoring Configuration
MONITORING_ENABLE_STRUCTURED_LOGGING=true
MONITORING_LOG_FORMAT=json
MONITORING_ENABLE_PROMETHEUS_METRICS=true
MONITORING_ENABLE_HEALTH_CHECKS=true
MONITORING_ENABLE_TRACING=true
MONITORING_ENABLE_ALERTING=true

# Sentry Error Tracking (optional)
MONITORING_ENABLE_SENTRY=false
MONITORING_SENTRY_DSN=your-sentry-dsn-here
MONITORING_SENTRY_ENVIRONMENT=production

# Alerting Configuration
MONITORING_ALERT_EMAIL_ENABLED=false
MONITORING_SMTP_HOST=localhost
MONITORING_SMTP_PORT=587
MONITORING_ALERT_EMAIL_FROM=alerts@yourdomain.com
MONITORING_ALERT_EMAIL_TO=["admin@yourdomain.com"]

MONITORING_ALERT_SLACK_ENABLED=false  
MONITORING_SLACK_WEBHOOK_URL=your-slack-webhook-url
MONITORING_SLACK_CHANNEL=#alerts

# Tracing Configuration
MONITORING_JAEGER_ENDPOINT=http://localhost:14268/api/traces
MONITORING_SERVICE_NAME=pl8wrds-api
MONITORING_SERVICE_VERSION=1.0.0

# Redis (optional for advanced caching)
MONITORING_REDIS_ENABLED=false
MONITORING_REDIS_HOST=localhost
MONITORING_REDIS_PORT=6379
```

### Docker Compose Setup

For a complete monitoring stack, use the provided docker-compose configuration:

```yaml
version: '3.8'
services:
  pl8wrds-api:
    build: .
    environment:
      - MONITORING_ENABLE_PROMETHEUS_METRICS=true
      - MONITORING_JAEGER_ENDPOINT=http://jaeger:14268/api/traces
    ports:
      - "8000:8000"
    depends_on:
      - jaeger
      - prometheus
  
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
  
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - ./monitoring/grafana/dashboards:/var/lib/grafana/dashboards
  
  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686"
      - "14268:14268"
```

## Monitoring Endpoints

### Health Checks

| Endpoint | Purpose | Usage |
|----------|---------|-------|
| `/monitoring/health` | Comprehensive health check | Dashboard monitoring |
| `/monitoring/health/live` | Kubernetes liveness probe | K8s liveness check |
| `/monitoring/health/ready` | Kubernetes readiness probe | K8s readiness check |
| `/monitoring/status` | Quick status overview | Load balancer health |

### Metrics

| Endpoint | Purpose | Format |
|----------|---------|---------|
| `/monitoring/metrics` | Prometheus metrics | Prometheus text format |
| `/monitoring/metrics/summary` | Metrics summary | JSON |

### Error Tracking

| Endpoint | Purpose | Usage |
|----------|---------|-------|
| `/monitoring/errors` | Error summary | Operations dashboard |
| `/monitoring/errors/{error_key}` | Detailed error records | Debugging |

### Alerting

| Endpoint | Purpose | Usage |
|----------|---------|-------|
| `/monitoring/alerts` | Active alerts | Alert dashboard |
| `/monitoring/alerts/history` | Alert history | Trend analysis |
| `/monitoring/alerts/test` | Create test alert | Testing |
| `/monitoring/notifications/test` | Test notifications | Channel verification |

## Structured Logging

### Log Format

All logs use structured JSON format with consistent fields:

```json
{
  "timestamp": "2024-01-15T10:30:00.123456Z",
  "level": "INFO",
  "logger": "app.services.prediction_service",
  "message": "Prediction completed successfully",
  "service_name": "pl8wrds-api",
  "service_version": "1.0.0",
  "environment": "production",
  "correlation_id": "req-123e4567-e89b-12d3-a456-426614174000",
  "request_id": "req-987fcdeb-51a2-43d1-b123-789012345678",
  "user_id": "user123",
  "extra": {
    "duration_ms": 250,
    "word": "ambulance",
    "plate": "ABC",
    "predicted_score": 8.5
  }
}
```

### Context Variables

The logging system automatically includes:
- **correlation_id**: Tracks requests across services
- **request_id**: Unique identifier for each HTTP request  
- **user_id**: User context (when available)
- **session_id**: Session context (when available)

### Usage in Code

```python
from app.monitoring import get_logger

logger = get_logger(__name__)

# Basic logging
logger.info("Processing word scoring request", word="ambulance", plate="ABC")

# Error logging with context
try:
    result = process_scoring(word, plate)
    logger.info("Scoring completed", result=result, duration_ms=duration)
except Exception as e:
    logger.error("Scoring failed", error=str(e), error_type=type(e).__name__)
```

## Metrics Collection

### Prometheus Metrics

The system collects comprehensive metrics including:

#### HTTP Metrics
- `pl8wrds_http_requests_total` - Total HTTP requests by method, endpoint, status
- `pl8wrds_http_request_duration_seconds` - Request duration histogram
- `pl8wrds_http_requests_in_progress` - Current active requests

#### Business Metrics  
- `pl8wrds_word_scores_generated_total` - Total word scores generated
- `pl8wrds_word_scoring_duration_seconds` - Word scoring duration
- `pl8wrds_ml_model_predictions_total` - ML model predictions
- `pl8wrds_llm_requests_total` - LLM API requests

#### System Metrics
- `pl8wrds_system_cpu_usage_percent` - CPU usage
- `pl8wrds_system_memory_usage_bytes` - Memory usage
- `pl8wrds_system_disk_usage_bytes` - Disk usage

#### Error Metrics
- `pl8wrds_errors_total` - Total errors by type and component
- `pl8wrds_exceptions_total` - Exceptions by type and endpoint

### Custom Metrics

Add custom business metrics:

```python
from app.monitoring.metrics import get_metrics_manager, record_business_event

# Record business events
record_business_event('word_discovered', 1, labels={'difficulty': 'hard'})

# Direct metrics access
metrics = get_metrics_manager()
metrics.word_scores_generated.labels(model_type='ml_prediction').inc()
```

## Health Checks

### Built-in Health Checks

1. **File System Check** - Verifies required files and directories exist
2. **ML Model Check** - Ensures prediction model is loaded and functional  
3. **Ollama Service Check** - Checks LLM service availability (non-critical)
4. **System Resources Check** - Monitors CPU, memory, and disk usage
5. **Cache Health Check** - Verifies cache files are accessible

### Custom Health Checks

Add custom health checks:

```python
from app.monitoring.health import get_health_manager, HealthCheck, HealthStatus

class DatabaseHealthCheck(HealthCheck):
    def __init__(self):
        super().__init__("database", critical=True)
    
    async def check(self):
        try:
            # Check database connection
            await db.execute("SELECT 1")
            return {"status": HealthStatus.HEALTHY.value}
        except Exception as e:
            return {
                "status": HealthStatus.UNHEALTHY.value,
                "error": str(e)
            }

# Register the health check
health_manager = get_health_manager()
health_manager.add_health_check(DatabaseHealthCheck())
```

## Distributed Tracing

### OpenTelemetry Integration

Distributed tracing is automatically configured for:
- FastAPI endpoints
- HTTP client requests (httpx)
- Database queries (future)
- External service calls

### Manual Tracing

```python
from app.monitoring.tracing import trace_function, TracedOperation, add_span_attributes

# Decorator-based tracing
@trace_function(name="word_processing", attributes={"component": "scoring"})
async def process_word_scoring(word: str, plate: str):
    # Function automatically traced
    return score_word(word, plate)

# Context manager tracing
with TracedOperation("feature_extraction") as span:
    features = extract_features(word, plate)
    span.set_attribute("feature_count", len(features))
```

### Business Operation Tracing

```python
from app.monitoring.tracing import trace_word_scoring, trace_ml_prediction

@trace_word_scoring("ml_model")
async def ml_score_word(word: str, plate: str):
    return model.predict(word, plate)

@trace_ml_prediction()
async def predict_score(word: str, plate: str):
    return prediction_service.predict_score(word, plate)
```

## Error Tracking

### Automatic Error Tracking

All errors are automatically tracked with:
- Error type and message
- Stack trace and context
- Correlation IDs for request tracing
- Component identification
- Severity classification

### Manual Error Tracking

```python
from app.monitoring.errors import record_error, track_errors, with_error_context

# Manual error recording
try:
    risky_operation()
except Exception as e:
    error_id = record_error(
        error=e,
        context={"operation": "word_scoring", "word": word},
        severity="error",
        component="scoring_service"
    )

# Decorator-based tracking
@track_errors(component="ml_model", severity="high")
def ml_prediction(word: str, plate: str):
    return model.predict(word, plate)

# Context-based tracking
with with_error_context(component="feature_extraction", operation="tfidf"):
    features = calculate_tfidf_features(word)
```

### Sentry Integration

When enabled, errors are automatically sent to Sentry with:
- Full context and tags
- User and session information
- Custom fingerprinting
- Performance data

## Alerting & Notifications

### Alert Severity Levels

- **LOW**: Informational, no immediate action required
- **MEDIUM**: Warning condition, should be investigated
- **HIGH**: Error condition, requires attention
- **CRITICAL**: Service impacting, immediate action required

### Notification Channels

#### Email Notifications
```bash
MONITORING_ALERT_EMAIL_ENABLED=true
MONITORING_SMTP_HOST=smtp.gmail.com
MONITORING_SMTP_PORT=587
MONITORING_SMTP_USERNAME=your-email@gmail.com  
MONITORING_SMTP_PASSWORD=your-app-password
MONITORING_ALERT_EMAIL_FROM=alerts@yourdomain.com
MONITORING_ALERT_EMAIL_TO=["admin@yourdomain.com","ops@yourdomain.com"]
```

#### Slack Notifications
```bash
MONITORING_ALERT_SLACK_ENABLED=true
MONITORING_SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
MONITORING_SLACK_CHANNEL=#alerts
```

#### Webhook Notifications
```bash
MONITORING_ALERT_WEBHOOK_ENABLED=true
MONITORING_ALERT_WEBHOOK_URL=https://your-monitoring-system.com/webhook
```

### Built-in Alert Rules

1. **High Error Rate** - Triggers when error rate exceeds 5%
2. **Service Unavailable** - Triggers when health checks fail
3. **High Response Time** - Triggers when response time > 2 seconds
4. **ML Model Failure** - Triggers when model predictions fail

### Custom Alerts

```python
from app.monitoring.alerting import get_alert_manager, AlertSeverity, AlertRule

# Create custom alert
alert_manager = get_alert_manager()
await alert_manager.create_alert(
    title="High Memory Usage",
    description="System memory usage exceeded 90%",
    severity=AlertSeverity.HIGH,
    component="system",
    metadata={"memory_usage": "92%", "threshold": "90%"}
)

# Add custom alert rule
def check_memory_usage(context):
    return context.get('memory_usage', 0) > 0.9

memory_rule = AlertRule(
    name="high_memory_usage",
    condition=check_memory_usage,
    severity=AlertSeverity.HIGH,
    component="system",
    cooldown_seconds=600
)

alert_manager.add_alert_rule(memory_rule)
```

## Security Monitoring

### Built-in Security Features

1. **Suspicious Pattern Detection** - Monitors for attack patterns in requests
2. **Authentication Failure Tracking** - Tracks and blocks excessive failures  
3. **Rate Limiting** - Prevents abuse with configurable limits
4. **IP Blocking** - Automatically blocks malicious IPs
5. **Audit Logging** - Comprehensive security event logging

### Security Events

```python
from app.monitoring.logger import log_security_event

# Log security events
log_security_event(
    "authentication_failure",
    "medium", 
    {
        "client_ip": "192.168.1.100",
        "user_agent": "suspicious-bot",
        "attempt_count": 5
    }
)
```

### Rate Limiting Configuration

```bash
MONITORING_ENABLE_RATE_LIMITING=true
MONITORING_RATE_LIMIT_REQUESTS_PER_MINUTE=100
MONITORING_RATE_LIMIT_BURST_SIZE=20
MONITORING_MAX_FAILED_AUTH_ATTEMPTS=5
MONITORING_AUTH_LOCKOUT_DURATION=300
```

## Performance Monitoring

### Automatic Performance Tracking

- Request duration monitoring
- Slow request detection and alerting  
- Memory and CPU usage tracking
- Database query performance (future)
- Cache hit/miss ratios

### Performance Thresholds

```bash
MONITORING_SLOW_REQUEST_THRESHOLD=1.0  # 1 second
MONITORING_ENABLE_MEMORY_PROFILING=false
MONITORING_ENABLE_CPU_PROFILING=false
```

### Custom Performance Monitoring

```python
from app.monitoring.logger import log_performance_event

start_time = time.time()
try:
    result = expensive_operation()
    duration = time.time() - start_time
    
    log_performance_event(
        operation="expensive_operation",
        duration=duration,
        success=True,
        details={"result_size": len(result)}
    )
except Exception as e:
    duration = time.time() - start_time
    log_performance_event(
        operation="expensive_operation", 
        duration=duration,
        success=False,
        details={"error": str(e)}
    )
```

## Dashboard Configuration

### Prometheus Configuration

Create `monitoring/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'pl8wrds-api'
    static_configs:
      - targets: ['pl8wrds-api:8000']
    metrics_path: '/monitoring/metrics'
    scrape_interval: 30s

rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

### Grafana Dashboards

Import the provided Grafana dashboards for:
- API Performance Overview
- Error Rate Monitoring  
- Business Metrics Dashboard
- System Resource Monitoring
- Security Events Dashboard

### Alert Rules

Create `monitoring/alert_rules.yml`:

```yaml
groups:
  - name: pl8wrds-api
    rules:
      - alert: HighErrorRate
        expr: rate(pl8wrds_http_requests_total{status_code=~"5.."}[5m]) > 0.1
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          
      - alert: SlowRequests
        expr: histogram_quantile(0.95, rate(pl8wrds_http_request_duration_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "95th percentile latency is above 2 seconds"
```

## Operational Procedures

### Health Check Monitoring

```bash
# Check overall health
curl http://localhost:8000/monitoring/health

# Kubernetes probes
curl http://localhost:8000/monitoring/health/live
curl http://localhost:8000/monitoring/health/ready

# Quick status check
curl http://localhost:8000/monitoring/status
```

### Metrics Collection

```bash
# View Prometheus metrics
curl http://localhost:8000/monitoring/metrics

# Get metrics summary
curl http://localhost:8000/monitoring/metrics/summary
```

### Error Investigation

```bash
# Get error summary
curl http://localhost:8000/monitoring/errors

# Get specific error details
curl http://localhost:8000/monitoring/errors/ValueError:ml_model
```

### Alert Management

```bash
# View active alerts
curl http://localhost:8000/monitoring/alerts

# Acknowledge alert
curl -X POST "http://localhost:8000/monitoring/alerts/alert-123/acknowledge?acknowledged_by=ops-team"

# Resolve alert
curl -X POST "http://localhost:8000/monitoring/alerts/alert-123/resolve?resolved_by=ops-team"

# Test notifications
curl -X POST http://localhost:8000/monitoring/notifications/test
```

### Log Analysis

```bash
# View structured logs with jq
kubectl logs deployment/pl8wrds-api | jq 'select(.level == "ERROR")'

# Filter by correlation ID
kubectl logs deployment/pl8wrds-api | jq 'select(.correlation_id == "req-123")'

# Performance analysis
kubectl logs deployment/pl8wrds-api | jq 'select(.event_type == "performance" and .duration_ms > 1000)'
```

## Troubleshooting

### Common Issues

#### Metrics Not Appearing
1. Check Prometheus configuration
2. Verify `/monitoring/metrics` endpoint accessibility
3. Check firewall rules for metrics port

#### Health Checks Failing
1. Verify required files exist (models, cache files)
2. Check external service connectivity (Ollama)
3. Review system resource usage

#### Alerts Not Triggering
1. Test notification channels with `/monitoring/notifications/test`
2. Check alert rule conditions
3. Verify SMTP/Slack webhook configuration

#### Tracing Not Working
1. Check Jaeger endpoint configuration
2. Verify OpenTelemetry setup
3. Check network connectivity to Jaeger

### Debug Mode

Enable debug logging for troubleshooting:

```bash
MONITORING_LOG_LEVEL=DEBUG
MONITORING_ENABLE_PERFORMANCE_MONITORING=true
MONITORING_ENABLE_MEMORY_PROFILING=true
```

### Log Correlation

Use correlation IDs to trace requests across components:

```bash
# Find all logs for a specific request
grep "correlation_id.*req-123" /var/log/pl8wrds.log

# Or with structured logging
cat /var/log/pl8wrds.log | jq 'select(.correlation_id == "req-123")'
```

## Best Practices

### Development
- Always use structured logging with context
- Add correlation IDs to external service calls
- Include business metrics in your code
- Test error scenarios and alerting

### Production
- Monitor health check endpoints continuously
- Set up alerting for critical business metrics
- Regular review of error patterns and trends
- Implement proper log retention policies
- Use distributed tracing for complex request flows

### Security
- Regularly review security event logs
- Monitor for unusual patterns and anomalies
- Keep alert channels secure and up-to-date
- Implement proper access controls for monitoring endpoints

This comprehensive monitoring setup provides production-ready observability for the PL8WRDS API with minimal operational overhead and maximum insight into system behavior.
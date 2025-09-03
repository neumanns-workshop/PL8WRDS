"""
Observability middleware for FastAPI application.
"""

import time
import uuid
from typing import Callable, Dict, Any, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR
import json

from ..core.config import get_settings
from .logger import (
    get_logger, 
    set_correlation_id, 
    set_request_id,
    set_user_id,
    set_session_id,
    log_security_event,
    log_performance_event
)
from .metrics import get_metrics_manager, record_business_event

settings = get_settings()
logger = get_logger(__name__)


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """
    Core observability middleware that adds correlation IDs, 
    request tracking, and basic observability features.
    """
    
    def __init__(self, app, enable_request_logging: bool = True):
        super().__init__(app)
        self.enable_request_logging = enable_request_logging
        self.metrics = get_metrics_manager()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate or extract correlation ID
        correlation_id = (
            request.headers.get("x-correlation-id") or 
            request.headers.get("x-request-id") or
            str(uuid.uuid4())
        )
        set_correlation_id(correlation_id)
        
        # Generate request ID
        request_id = str(uuid.uuid4())
        set_request_id(request_id)
        
        # Extract user context if available
        user_id = request.headers.get("x-user-id")
        if user_id:
            set_user_id(user_id)
        
        session_id = request.headers.get("x-session-id")
        if session_id:
            set_session_id(session_id)
        
        # Add to request state for other middleware
        request.state.correlation_id = correlation_id
        request.state.request_id = request_id
        request.state.start_time = time.time()
        
        # Get endpoint info
        endpoint = self._get_endpoint_name(request)
        method = request.method
        
        # Log request start
        if self.enable_request_logging:
            logger.info(
                "Request started",
                method=method,
                endpoint=endpoint,
                user_agent=request.headers.get("user-agent"),
                client_ip=self._get_client_ip(request),
                query_params=dict(request.query_params) if request.query_params else None
            )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - request.state.start_time
            
            # Add headers to response
            response.headers["x-correlation-id"] = correlation_id
            response.headers["x-request-id"] = request_id
            response.headers["x-response-time"] = str(round(duration * 1000, 2))
            
            # Log request completion
            if self.enable_request_logging:
                logger.info(
                    "Request completed",
                    method=method,
                    endpoint=endpoint,
                    status_code=response.status_code,
                    duration_ms=round(duration * 1000, 2),
                    content_length=response.headers.get("content-length")
                )
            
            return response
            
        except Exception as e:
            # Calculate duration for failed request
            duration = time.time() - request.state.start_time
            
            # Log error
            logger.error(
                "Request failed",
                method=method,
                endpoint=endpoint,
                error=str(e),
                error_type=e.__class__.__name__,
                duration_ms=round(duration * 1000, 2)
            )
            
            # Create error response
            error_response = Response(
                content=json.dumps({
                    "error": "Internal Server Error",
                    "correlation_id": correlation_id,
                    "request_id": request_id
                }),
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                headers={
                    "content-type": "application/json",
                    "x-correlation-id": correlation_id,
                    "x-request-id": request_id
                }
            )
            
            return error_response
    
    def _get_endpoint_name(self, request: Request) -> str:
        """Extract endpoint name from request."""
        if hasattr(request, "scope") and "route" in request.scope:
            route = request.scope["route"]
            if hasattr(route, "path"):
                return route.path
        return request.url.path
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request headers."""
        # Check common headers for client IP
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fall back to client address
        if hasattr(request.client, "host"):
            return request.client.host
        
        return "unknown"


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware for collecting HTTP metrics."""
    
    def __init__(self, app):
        super().__init__(app)
        self.metrics = get_metrics_manager()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get endpoint and method
        endpoint = self._get_endpoint_pattern(request)
        method = request.method
        
        # Record request start
        self.metrics.start_http_request(method, endpoint)
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Calculate duration and record metrics
            duration = time.time() - start_time
            status_code = response.status_code
            
            self.metrics.record_http_request(method, endpoint, status_code, duration)
            
            return response
            
        except Exception as e:
            # Record error metrics
            duration = time.time() - start_time
            self.metrics.record_http_request(method, endpoint, 500, duration)
            self.metrics.record_exception(e.__class__.__name__, endpoint)
            raise
        
        finally:
            # Always decrement in-progress counter
            self.metrics.end_http_request(method, endpoint)
    
    def _get_endpoint_pattern(self, request: Request) -> str:
        """Get endpoint pattern for metrics (to avoid high cardinality)."""
        if hasattr(request, "scope") and "route" in request.scope:
            route = request.scope["route"]
            if hasattr(route, "path_regex"):
                # Return the pattern instead of actual path
                return getattr(route, "path", request.url.path)
        
        # Simplify dynamic paths to reduce metric cardinality
        path = request.url.path
        
        # Replace common dynamic segments
        import re
        path = re.sub(r'/\d+', '/{id}', path)  # Replace numeric IDs
        path = re.sub(r'/[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}', '/{uuid}', path)  # Replace UUIDs
        
        return path


class PerformanceMiddleware(BaseHTTPMiddleware):
    """Middleware for performance monitoring and alerting."""
    
    def __init__(self, app, slow_threshold: float = None):
        super().__init__(app)
        self.slow_threshold = slow_threshold or settings.monitoring.slow_request_threshold
        self.metrics = get_metrics_manager()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        endpoint = self._get_endpoint_name(request)
        method = request.method
        start_time = time.time()
        
        # Add performance context to request
        request.state.performance_start = start_time
        
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            
            # Log performance event
            log_performance_event(
                operation=f"{method} {endpoint}",
                duration=duration,
                success=True,
                details={
                    "status_code": response.status_code,
                    "content_length": response.headers.get("content-length")
                }
            )
            
            # Check for slow requests
            if duration > self.slow_threshold:
                logger.warning(
                    "Slow request detected",
                    method=method,
                    endpoint=endpoint,
                    duration_ms=round(duration * 1000, 2),
                    threshold_ms=round(self.slow_threshold * 1000, 2),
                    status_code=response.status_code
                )
                
                # Record slow request metric
                record_business_event(
                    'slow_request',
                    1,
                    labels={
                        'endpoint': endpoint,
                        'method': method,
                        'duration_bucket': self._get_duration_bucket(duration)
                    }
                )
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            
            # Log performance event for failed request
            log_performance_event(
                operation=f"{method} {endpoint}",
                duration=duration,
                success=False,
                details={
                    "error": str(e),
                    "error_type": e.__class__.__name__
                }
            )
            
            raise
    
    def _get_endpoint_name(self, request: Request) -> str:
        """Extract endpoint name from request."""
        if hasattr(request, "scope") and "route" in request.scope:
            route = request.scope["route"]
            if hasattr(route, "path"):
                return route.path
        return request.url.path
    
    def _get_duration_bucket(self, duration: float) -> str:
        """Get duration bucket for categorization."""
        if duration < 1.0:
            return "fast"
        elif duration < 5.0:
            return "medium"
        elif duration < 10.0:
            return "slow"
        else:
            return "very_slow"


class SecurityMiddleware(BaseHTTPMiddleware):
    """Middleware for security monitoring and protection."""
    
    def __init__(self, app):
        super().__init__(app)
        self.failed_attempts: Dict[str, Dict[str, Any]] = {}  # client_ip -> {count, last_attempt}
        self.blocked_ips: set = set()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = self._get_client_ip(request)
        endpoint = request.url.path
        method = request.method
        
        # Check if IP is blocked
        if client_ip in self.blocked_ips:
            log_security_event(
                "blocked_ip_access_attempt",
                "high",
                {
                    "client_ip": client_ip,
                    "endpoint": endpoint,
                    "method": method,
                    "user_agent": request.headers.get("user-agent")
                }
            )
            
            return Response(
                content=json.dumps({"error": "Access denied"}),
                status_code=403,
                headers={"content-type": "application/json"}
            )
        
        # Monitor for suspicious patterns
        self._check_suspicious_patterns(request, client_ip)
        
        try:
            response = await call_next(request)
            
            # Monitor authentication failures
            if response.status_code == 401:
                self._handle_auth_failure(client_ip, endpoint)
            elif response.status_code == 403:
                log_security_event(
                    "authorization_failure",
                    "medium",
                    {
                        "client_ip": client_ip,
                        "endpoint": endpoint,
                        "method": method
                    }
                )
            
            return response
            
        except Exception as e:
            # Log security-relevant exceptions
            if "auth" in str(e).lower() or "permission" in str(e).lower():
                log_security_event(
                    "security_exception",
                    "high",
                    {
                        "client_ip": client_ip,
                        "endpoint": endpoint,
                        "error": str(e),
                        "error_type": e.__class__.__name__
                    }
                )
            
            raise
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request."""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        if hasattr(request.client, "host"):
            return request.client.host
        
        return "unknown"
    
    def _check_suspicious_patterns(self, request: Request, client_ip: str):
        """Check for suspicious request patterns."""
        path = request.url.path.lower()
        user_agent = request.headers.get("user-agent", "").lower()
        
        # Common attack patterns
        suspicious_paths = [
            "admin", "wp-admin", "phpmyadmin", ".env", "config",
            "sql", "script", "eval", "exec", "system", "cmd"
        ]
        
        suspicious_user_agents = [
            "sqlmap", "nmap", "nikto", "burp", "owasp", "scanner"
        ]
        
        # Check path for suspicious patterns
        for pattern in suspicious_paths:
            if pattern in path:
                log_security_event(
                    "suspicious_path_access",
                    "medium",
                    {
                        "client_ip": client_ip,
                        "path": request.url.path,
                        "pattern": pattern,
                        "user_agent": user_agent
                    }
                )
                break
        
        # Check user agent for suspicious patterns
        for pattern in suspicious_user_agents:
            if pattern in user_agent:
                log_security_event(
                    "suspicious_user_agent",
                    "high",
                    {
                        "client_ip": client_ip,
                        "user_agent": request.headers.get("user-agent"),
                        "path": request.url.path,
                        "pattern": pattern
                    }
                )
                break
        
        # Check for potential injection attempts in query parameters
        query_string = str(request.url.query).lower()
        injection_patterns = ["'", "union", "select", "drop", "insert", "script", "<", ">"]
        
        for pattern in injection_patterns:
            if pattern in query_string:
                log_security_event(
                    "potential_injection_attempt",
                    "high",
                    {
                        "client_ip": client_ip,
                        "path": request.url.path,
                        "query_string": str(request.url.query),
                        "pattern": pattern
                    }
                )
                break
    
    def _handle_auth_failure(self, client_ip: str, endpoint: str):
        """Handle authentication failure and track attempts."""
        now = time.time()
        
        if client_ip not in self.failed_attempts:
            self.failed_attempts[client_ip] = {"count": 0, "last_attempt": now}
        
        self.failed_attempts[client_ip]["count"] += 1
        self.failed_attempts[client_ip]["last_attempt"] = now
        
        attempt_count = self.failed_attempts[client_ip]["count"]
        
        log_security_event(
            "authentication_failure",
            "medium",
            {
                "client_ip": client_ip,
                "endpoint": endpoint,
                "attempt_count": attempt_count
            }
        )
        
        # Block IP if too many failures
        if attempt_count >= settings.monitoring.max_failed_auth_attempts:
            self.blocked_ips.add(client_ip)
            
            log_security_event(
                "ip_blocked_excessive_auth_failures",
                "critical",
                {
                    "client_ip": client_ip,
                    "total_attempts": attempt_count,
                    "lockout_duration": settings.monitoring.auth_lockout_duration
                }
            )
            
            # Schedule IP unblocking (in a real implementation, this would use a task queue)
            import asyncio
            asyncio.create_task(self._unblock_ip_after_timeout(client_ip))
    
    async def _unblock_ip_after_timeout(self, client_ip: str):
        """Unblock IP after timeout period."""
        await asyncio.sleep(settings.monitoring.auth_lockout_duration)
        
        if client_ip in self.blocked_ips:
            self.blocked_ips.remove(client_ip)
            
            log_security_event(
                "ip_unblocked",
                "low",
                {
                    "client_ip": client_ip,
                    "reason": "timeout_expired"
                }
            )
        
        # Clean up failed attempts
        if client_ip in self.failed_attempts:
            del self.failed_attempts[client_ip]


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware."""
    
    def __init__(self, app, requests_per_minute: int = None, burst_size: int = None):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute or settings.monitoring.rate_limit_requests_per_minute
        self.burst_size = burst_size or settings.monitoring.rate_limit_burst_size
        self.client_requests: Dict[str, List[float]] = {}  # client_ip -> [timestamps]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not settings.monitoring.enable_rate_limiting:
            return await call_next(request)
        
        client_ip = self._get_client_ip(request)
        
        # Skip rate limiting for localhost/development
        if client_ip in ['127.0.0.1', '::1', 'localhost'] or settings.environment == 'development':
            return await call_next(request)
            
        now = time.time()
        
        # Clean old requests
        self._cleanup_old_requests(client_ip, now)
        
        # Check rate limit
        if self._is_rate_limited(client_ip, now):
            log_security_event(
                "rate_limit_exceeded",
                "medium",
                {
                    "client_ip": client_ip,
                    "requests_per_minute": len(self.client_requests.get(client_ip, [])),
                    "limit": self.requests_per_minute,
                    "endpoint": request.url.path
                }
            )
            
            return Response(
                content=json.dumps({
                    "error": "Rate limit exceeded",
                    "retry_after": 60
                }),
                status_code=429,
                headers={
                    "content-type": "application/json",
                    "retry-after": "60"
                }
            )
        
        # Record request
        if client_ip not in self.client_requests:
            self.client_requests[client_ip] = []
        self.client_requests[client_ip].append(now)
        
        return await call_next(request)
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request."""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        if hasattr(request.client, "host"):
            return request.client.host
        
        return "unknown"
    
    def _cleanup_old_requests(self, client_ip: str, now: float):
        """Remove requests older than 1 minute."""
        if client_ip in self.client_requests:
            cutoff_time = now - 60  # 1 minute ago
            self.client_requests[client_ip] = [
                ts for ts in self.client_requests[client_ip] if ts > cutoff_time
            ]
    
    def _is_rate_limited(self, client_ip: str, now: float) -> bool:
        """Check if client has exceeded rate limit."""
        if client_ip not in self.client_requests:
            return False
        
        recent_requests = len(self.client_requests[client_ip])
        return recent_requests >= self.requests_per_minute
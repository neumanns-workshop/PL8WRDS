"""
Comprehensive health check system for monitoring service dependencies.
"""

import asyncio
import os
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
import httpx
import psutil

from ..core.config import get_settings
from .logger import get_logger
from .metrics import get_metrics_manager

settings = get_settings()
logger = get_logger(__name__)


class HealthStatus(Enum):
    """Health check status enumeration."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy" 
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


class HealthCheck(ABC):
    """Abstract base class for health checks."""
    
    def __init__(self, name: str, critical: bool = True, timeout: float = 5.0):
        self.name = name
        self.critical = critical  # If True, failure marks overall service as unhealthy
        self.timeout = timeout
        self.last_check_time: Optional[datetime] = None
        self.last_status: HealthStatus = HealthStatus.UNKNOWN
        self.last_error: Optional[str] = None
        self.check_count = 0
        self.failure_count = 0
    
    @abstractmethod
    async def check(self) -> Dict[str, Any]:
        """Perform the health check. Should return status details."""
        pass
    
    async def run_check(self) -> Dict[str, Any]:
        """Run the health check with timeout and error handling."""
        start_time = time.time()
        self.check_count += 1
        
        try:
            # Run check with timeout
            result = await asyncio.wait_for(self.check(), timeout=self.timeout)
            
            # Determine status from result
            if result.get('status') == HealthStatus.HEALTHY.value:
                self.last_status = HealthStatus.HEALTHY
                self.last_error = None
            elif result.get('status') == HealthStatus.DEGRADED.value:
                self.last_status = HealthStatus.DEGRADED
                self.last_error = result.get('error')
            else:
                self.last_status = HealthStatus.UNHEALTHY
                self.last_error = result.get('error', 'Unknown error')
                self.failure_count += 1
                
        except asyncio.TimeoutError:
            self.last_status = HealthStatus.UNHEALTHY
            self.last_error = f"Health check timed out after {self.timeout}s"
            self.failure_count += 1
            result = {
                'status': HealthStatus.UNHEALTHY.value,
                'error': self.last_error
            }
        except Exception as e:
            self.last_status = HealthStatus.UNHEALTHY
            self.last_error = str(e)
            self.failure_count += 1
            result = {
                'status': HealthStatus.UNHEALTHY.value,
                'error': self.last_error
            }
        
        duration = time.time() - start_time
        self.last_check_time = datetime.now(timezone.utc)
        
        # Record metrics
        metrics = get_metrics_manager()
        metrics.record_health_check(
            service=self.name,
            is_healthy=(self.last_status == HealthStatus.HEALTHY),
            duration=duration
        )
        
        # Add metadata to result
        result.update({
            'name': self.name,
            'critical': self.critical,
            'duration_ms': round(duration * 1000, 2),
            'last_check_time': self.last_check_time.isoformat(),
            'check_count': self.check_count,
            'failure_count': self.failure_count,
            'failure_rate': self.failure_count / self.check_count if self.check_count > 0 else 0
        })
        
        return result


class FileSystemHealthCheck(HealthCheck):
    """Health check for required files and directories."""
    
    def __init__(self, paths: List[str], **kwargs):
        super().__init__("filesystem", **kwargs)
        self.paths = paths
    
    async def check(self) -> Dict[str, Any]:
        """Check if required files and directories exist."""
        missing_paths = []
        accessible_paths = []
        
        for path_str in self.paths:
            path = Path(path_str)
            if not path.exists():
                missing_paths.append(str(path))
            elif not os.access(path, os.R_OK):
                missing_paths.append(f"{path} (not readable)")
            else:
                accessible_paths.append(str(path))
        
        if missing_paths:
            return {
                'status': HealthStatus.UNHEALTHY.value,
                'error': f"Missing or inaccessible paths: {', '.join(missing_paths)}",
                'missing_paths': missing_paths,
                'accessible_paths': accessible_paths
            }
        
        return {
            'status': HealthStatus.HEALTHY.value,
            'accessible_paths': accessible_paths
        }


class ModelHealthCheck(HealthCheck):
    """Health check for ML model availability."""
    
    def __init__(self, **kwargs):
        super().__init__("ml_model", **kwargs)
    
    async def check(self) -> Dict[str, Any]:
        """Check if ML model is loaded and functional."""
        try:
            from ..services.prediction_service import prediction_service
            
            if not prediction_service._is_initialized:
                return {
                    'status': HealthStatus.UNHEALTHY.value,
                    'error': 'Prediction service not initialized'
                }
            
            # Try a simple prediction to verify model is working
            test_result = prediction_service.predict_score("test", "ABC")
            
            if 'predicted_score' not in test_result:
                return {
                    'status': HealthStatus.DEGRADED.value,
                    'error': 'Model prediction missing score field'
                }
            
            return {
                'status': HealthStatus.HEALTHY.value,
                'model_path': prediction_service.model_path,
                'feature_count': len(prediction_service.feature_names),
                'test_prediction': test_result['predicted_score']
            }
            
        except Exception as e:
            return {
                'status': HealthStatus.UNHEALTHY.value,
                'error': f"Model check failed: {str(e)}"
            }


class OllamaHealthCheck(HealthCheck):
    """Health check for Ollama service."""
    
    def __init__(self, **kwargs):
        super().__init__("ollama", critical=False, **kwargs)
    
    async def check(self) -> Dict[str, Any]:
        """Check Ollama service availability."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.ollama.base_url}/api/tags",
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    models_data = response.json()
                    available_models = [model['name'] for model in models_data.get('models', [])]
                    
                    # Check if any of our required models are available
                    required_models = set(settings.default_models)
                    available_required = required_models.intersection(set(available_models))
                    
                    if not available_required and required_models:
                        return {
                            'status': HealthStatus.DEGRADED.value,
                            'error': f"Required models not available: {required_models - available_required}",
                            'available_models': available_models,
                            'required_models': list(required_models)
                        }
                    
                    return {
                        'status': HealthStatus.HEALTHY.value,
                        'available_models': available_models,
                        'required_models_available': list(available_required)
                    }
                else:
                    return {
                        'status': HealthStatus.UNHEALTHY.value,
                        'error': f"Ollama returned status {response.status_code}"
                    }
                    
        except httpx.ConnectError:
            return {
                'status': HealthStatus.UNHEALTHY.value,
                'error': "Cannot connect to Ollama service"
            }
        except Exception as e:
            return {
                'status': HealthStatus.UNHEALTHY.value,
                'error': f"Ollama check failed: {str(e)}"
            }


class SystemResourceHealthCheck(HealthCheck):
    """Health check for system resources."""
    
    def __init__(self, 
                 max_cpu_percent: float = 90.0, 
                 max_memory_percent: float = 90.0,
                 max_disk_percent: float = 95.0,
                 **kwargs):
        super().__init__("system_resources", critical=False, **kwargs)
        self.max_cpu_percent = max_cpu_percent
        self.max_memory_percent = max_memory_percent
        self.max_disk_percent = max_disk_percent
    
    async def check(self) -> Dict[str, Any]:
        """Check system resource usage."""
        try:
            # Get CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Get memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Get disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # Determine status
            warnings = []
            if cpu_percent > self.max_cpu_percent:
                warnings.append(f"High CPU usage: {cpu_percent:.1f}%")
            if memory_percent > self.max_memory_percent:
                warnings.append(f"High memory usage: {memory_percent:.1f}%")
            if disk_percent > self.max_disk_percent:
                warnings.append(f"High disk usage: {disk_percent:.1f}%")
            
            status = HealthStatus.HEALTHY.value
            if warnings:
                status = HealthStatus.DEGRADED.value if len(warnings) <= 2 else HealthStatus.UNHEALTHY.value
            
            return {
                'status': status,
                'warnings': warnings if warnings else None,
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'disk_percent': disk_percent,
                'memory_available_gb': round(memory.available / (1024**3), 2),
                'disk_free_gb': round(disk.free / (1024**3), 2)
            }
            
        except Exception as e:
            return {
                'status': HealthStatus.UNHEALTHY.value,
                'error': f"System resource check failed: {str(e)}"
            }


class CacheHealthCheck(HealthCheck):
    """Health check for cache systems."""
    
    def __init__(self, **kwargs):
        super().__init__("cache", critical=False, **kwargs)
    
    async def check(self) -> Dict[str, Any]:
        """Check cache system health."""
        try:
            cache_files = [
                settings.app.get_absolute_path("cache/corpus_features.json"),
                settings.app.get_absolute_path("cache/corpus_stats.json")
            ]
            
            existing_caches = []
            missing_caches = []
            cache_sizes = {}
            
            for cache_file in cache_files:
                if cache_file.value and Path(cache_file.value).exists():
                    existing_caches.append(cache_file.value)
                    cache_sizes[cache_file.value] = Path(cache_file.value).stat().st_size
                else:
                    missing_caches.append(cache_file.value)
            
            # If no caches exist, this is a problem for predictions
            if not existing_caches:
                return {
                    'status': HealthStatus.UNHEALTHY.value,
                    'error': 'No cache files found - predictions may not work',
                    'missing_caches': missing_caches
                }
            
            # If some caches are missing, degraded but functional
            if missing_caches:
                return {
                    'status': HealthStatus.DEGRADED.value,
                    'warning': f'Some cache files missing: {missing_caches}',
                    'existing_caches': existing_caches,
                    'cache_sizes_mb': {k: round(v / (1024*1024), 2) for k, v in cache_sizes.items()}
                }
            
            return {
                'status': HealthStatus.HEALTHY.value,
                'existing_caches': existing_caches,
                'cache_sizes_mb': {k: round(v / (1024*1024), 2) for k, v in cache_sizes.items()}
            }
            
        except Exception as e:
            return {
                'status': HealthStatus.UNHEALTHY.value,
                'error': f"Cache check failed: {str(e)}"
            }


class HealthManager:
    """Manages all health checks for the application."""
    
    def __init__(self):
        self.checks: List[HealthCheck] = []
        self.last_overall_status: HealthStatus = HealthStatus.UNKNOWN
        self.startup_time = datetime.now(timezone.utc)
        self._setup_health_checks()
    
    def _setup_health_checks(self):
        """Set up all health checks."""
        
        # File system health check
        required_paths = [
            settings.app.data_directory_path.value,
            settings.app.cache_directory_path.value,
            settings.app.models_directory_path.value
        ]
        self.checks.append(FileSystemHealthCheck(required_paths))
        
        # ML Model health check
        self.checks.append(ModelHealthCheck())
        
        # Ollama health check (non-critical)
        self.checks.append(OllamaHealthCheck())
        
        # System resources health check
        self.checks.append(SystemResourceHealthCheck())
        
        # Cache health check
        self.checks.append(CacheHealthCheck())
    
    def add_health_check(self, health_check: HealthCheck):
        """Add a custom health check."""
        self.checks.append(health_check)
    
    async def run_all_checks(self) -> Dict[str, Any]:
        """Run all health checks and return comprehensive status."""
        start_time = time.time()
        
        # Run all checks concurrently
        check_tasks = [check.run_check() for check in self.checks]
        check_results = await asyncio.gather(*check_tasks, return_exceptions=True)
        
        # Process results
        results = {}
        critical_failures = 0
        total_failures = 0
        
        for i, result in enumerate(check_results):
            check = self.checks[i]
            
            if isinstance(result, Exception):
                # Handle exceptions that occurred during check execution
                result = {
                    'name': check.name,
                    'status': HealthStatus.UNHEALTHY.value,
                    'error': f"Check execution failed: {str(result)}",
                    'critical': check.critical,
                    'duration_ms': 0,
                    'last_check_time': datetime.now(timezone.utc).isoformat()
                }
            
            results[check.name] = result
            
            # Count failures
            if result['status'] != HealthStatus.HEALTHY.value:
                total_failures += 1
                if check.critical:
                    critical_failures += 1
        
        # Determine overall status
        if critical_failures > 0:
            overall_status = HealthStatus.UNHEALTHY
        elif total_failures > 0:
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY
        
        self.last_overall_status = overall_status
        
        # Calculate uptime
        uptime_seconds = (datetime.now(timezone.utc) - self.startup_time).total_seconds()
        
        duration = time.time() - start_time
        
        # Record overall health metric
        metrics = get_metrics_manager()
        metrics.record_health_check(
            service="overall",
            is_healthy=(overall_status == HealthStatus.HEALTHY),
            duration=duration
        )
        
        return {
            'status': overall_status.value,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'uptime_seconds': round(uptime_seconds, 2),
            'duration_ms': round(duration * 1000, 2),
            'checks': results,
            'summary': {
                'total_checks': len(self.checks),
                'healthy_checks': len(self.checks) - total_failures,
                'failed_checks': total_failures,
                'critical_failures': critical_failures
            },
            'service_info': {
                'name': settings.monitoring.service_name,
                'version': settings.monitoring.service_version,
                'environment': 'development' if settings.is_development else 'production'
            }
        }
    
    async def run_readiness_check(self) -> Dict[str, Any]:
        """Run readiness check (critical components only)."""
        critical_checks = [check for check in self.checks if check.critical]
        
        if not critical_checks:
            return {
                'status': HealthStatus.HEALTHY.value,
                'message': 'No critical checks configured'
            }
        
        check_tasks = [check.run_check() for check in critical_checks]
        results = await asyncio.gather(*check_tasks, return_exceptions=True)
        
        failures = 0
        for i, result in enumerate(results):
            if isinstance(result, Exception) or result.get('status') != HealthStatus.HEALTHY.value:
                failures += 1
        
        status = HealthStatus.HEALTHY if failures == 0 else HealthStatus.UNHEALTHY
        
        return {
            'status': status.value,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'critical_checks_passed': len(critical_checks) - failures,
            'total_critical_checks': len(critical_checks)
        }
    
    async def run_liveness_check(self) -> Dict[str, Any]:
        """Run liveness check (basic application health)."""
        return {
            'status': HealthStatus.HEALTHY.value,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'uptime_seconds': round((datetime.now(timezone.utc) - self.startup_time).total_seconds(), 2),
            'service': settings.monitoring.service_name
        }


# Global health manager instance
_health_manager: Optional[HealthManager] = None


def get_health_manager() -> HealthManager:
    """Get the global health manager instance."""
    global _health_manager
    if _health_manager is None:
        _health_manager = HealthManager()
    return _health_manager
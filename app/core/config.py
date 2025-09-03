"""
Application configuration using Pydantic settings.
"""

import os
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import validator
from pydantic_settings import BaseSettings

from ..domain.value_objects import FilePath, DirectoryPath


class AppSettings(BaseSettings):
    """Application configuration settings."""
    
    # Application metadata
    app_name: str = "PL8WRDS API"
    app_description: str = "License plate word game API with AI scoring"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # API settings
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    api_workers: int = 1
    api_reload: bool = True
    
    # File paths
    project_root: str = ""
    data_directory: str = "data"
    cache_directory: str = "cache"
    models_directory: str = "models"
    
    # Data files
    words_file: str = "words_with_freqs.json"
    plates_file: str = "plates.txt"
    
    # Model files
    ridge_model_file: str = "word_scoring_ridge_v3.joblib"
    
    # Cache settings
    enable_caching: bool = True
    cache_ttl_seconds: int = 3600  # 1 hour
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # External services
    ollama_base_url: str = "http://localhost:11434"
    ollama_timeout: int = 30
    
    # Scoring configuration
    default_models: List[str] = ["granite", "mistral", "deepseek"]
    max_scoring_sessions: int = 10
    scoring_cache_size: int = 10000
    
    # Feature extraction
    use_full_corpus: bool = True
    feature_cache_enabled: bool = True
    tfidf_max_features: int = 10000
    ngram_range_start: int = 2
    ngram_range_end: int = 4
    
    class Config:
        env_file = ".env"
        env_prefix = "PL8WRDS_"
        case_sensitive = False
    
    @validator("project_root", pre=True, always=True)
    def set_project_root(cls, v):
        if not v:
            # Auto-detect project root (directory containing this config file)
            current_file = Path(__file__)
            project_root = current_file.parent.parent.parent
            return str(project_root.absolute())
        return v
    
    @property
    def project_root_path(self) -> DirectoryPath:
        """Get project root as DirectoryPath."""
        return DirectoryPath(self.project_root)
    
    @property
    def data_directory_path(self) -> DirectoryPath:
        """Get data directory as DirectoryPath."""
        return DirectoryPath(os.path.join(self.project_root, self.data_directory))
    
    @property
    def cache_directory_path(self) -> DirectoryPath:
        """Get cache directory as DirectoryPath."""
        return DirectoryPath(os.path.join(self.project_root, self.cache_directory))
    
    @property
    def models_directory_path(self) -> DirectoryPath:
        """Get models directory as DirectoryPath."""
        return DirectoryPath(os.path.join(self.project_root, self.models_directory))
    
    @property
    def words_file_path(self) -> FilePath:
        """Get words file path."""
        return self.data_directory_path.join(self.words_file)
    
    @property
    def plates_file_path(self) -> FilePath:
        """Get plates file path."""
        return self.data_directory_path.join(self.plates_file)
    
    @property
    def ridge_model_file_path(self) -> FilePath:
        """Get Ridge model file path."""
        return self.models_directory_path.join(self.ridge_model_file)
    
    def get_absolute_path(self, relative_path: str) -> FilePath:
        """Convert relative path to absolute path from project root."""
        absolute_path = os.path.join(self.project_root, relative_path)
        return FilePath(absolute_path)
    
    def ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        directories = [
            self.data_directory_path,
            self.cache_directory_path,
            self.models_directory_path
        ]
        
        for directory in directories:
            Path(directory.value).mkdir(parents=True, exist_ok=True)


class OllamaSettings(BaseSettings):
    """Ollama-specific configuration."""
    
    base_url: str = "http://localhost:11434"
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    
    # Available models configuration
    available_models: List[str] = [
        "granite",
        "mistral",
        "deepseek",
        "llama2",
        "codellama"
    ]
    
    # Model auto-download settings
    auto_download_models: bool = True
    download_timeout: int = 300  # 5 minutes
    
    class Config:
        env_file = ".env"
        env_prefix = "OLLAMA_"


class DatabaseSettings(BaseSettings):
    """Database configuration (for future database integration)."""
    
    # SQLite settings (for development)
    sqlite_file: str = "pl8wrds.db"
    
    # PostgreSQL settings (for production)
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "pl8wrds"
    postgres_user: str = "pl8wrds"
    postgres_password: str = ""
    
    # Connection settings
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    
    class Config:
        env_file = ".env"
        env_prefix = "DB_"
    
    @property
    def sqlite_file_path(self) -> FilePath:
        """Get SQLite file path."""
        return FilePath(self.sqlite_file)
    
    @property
    def postgres_url(self) -> str:
        """Get PostgreSQL connection URL."""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"


class MonitoringSettings(BaseSettings):
    """Monitoring and observability configuration."""
    
    # Logging configuration
    enable_structured_logging: bool = True
    log_level: str = "INFO"
    log_format: str = "json"  # json or text
    enable_correlation_ids: bool = True
    
    # Metrics configuration
    enable_prometheus_metrics: bool = True
    prometheus_prefix: str = "pl8wrds"
    metrics_port: int = 9090
    enable_custom_metrics: bool = True
    
    # Health check configuration
    enable_health_checks: bool = True
    health_check_interval: int = 30  # seconds
    dependency_timeout: int = 5  # seconds
    enable_detailed_health: bool = True
    
    # Tracing configuration
    enable_tracing: bool = True
    jaeger_endpoint: str = "http://localhost:14268/api/traces"
    trace_sample_rate: float = 0.1
    service_name: str = "pl8wrds-api"
    service_version: str = "1.0.0"
    
    # Error tracking configuration
    enable_sentry: bool = False
    sentry_dsn: str = ""
    sentry_environment: str = "development"
    sentry_sample_rate: float = 1.0
    sentry_traces_sample_rate: float = 0.1
    
    # Performance monitoring
    enable_performance_monitoring: bool = True
    slow_request_threshold: float = 1.0  # seconds
    enable_memory_profiling: bool = False
    enable_cpu_profiling: bool = False
    
    # Alerting configuration
    enable_alerting: bool = True
    alert_email_enabled: bool = False
    alert_slack_enabled: bool = False
    alert_webhook_enabled: bool = False
    
    # Email alerting
    smtp_host: str = "localhost"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True
    alert_email_from: str = ""
    alert_email_to: List[str] = []
    
    # Slack alerting
    slack_webhook_url: str = ""
    slack_channel: str = "#alerts"
    
    # Webhook alerting
    alert_webhook_url: str = ""
    alert_webhook_timeout: int = 10
    
    # Redis configuration for caching and pub/sub
    redis_enabled: bool = False
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""
    redis_ssl: bool = False
    
    # Circuit breaker configuration
    enable_circuit_breakers: bool = True
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_recovery_timeout: int = 60
    circuit_breaker_expected_exception: str = "Exception"
    
    # Rate limiting
    enable_rate_limiting: bool = True
    rate_limit_requests_per_minute: int = 100
    rate_limit_burst_size: int = 20
    
    # Security monitoring
    enable_security_monitoring: bool = True
    max_failed_auth_attempts: int = 5
    auth_lockout_duration: int = 300  # seconds
    enable_audit_logging: bool = True
    
    class Config:
        env_file = ".env"
        env_prefix = "MONITORING_"
        case_sensitive = False
    
    @property
    def redis_url(self) -> str:
        """Get Redis connection URL."""
        protocol = "rediss" if self.redis_ssl else "redis"
        if self.redis_password:
            return f"{protocol}://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"{protocol}://{self.redis_host}:{self.redis_port}/{self.redis_db}"


class Settings:
    """Combined settings container."""
    
    def __init__(self):
        self.app = AppSettings()
        self.ollama = OllamaSettings()
        self.database = DatabaseSettings()
        self.monitoring = MonitoringSettings()
        
        # Ensure required directories exist
        self.app.ensure_directories()
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.app.debug or self.app.api_reload
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return not self.is_development


@lru_cache()
def get_settings() -> Settings:
    """Get application settings (cached)."""
    return Settings()


# Global settings instance
settings = get_settings()
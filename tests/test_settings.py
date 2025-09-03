"""
Test-specific settings and configuration.
"""

from pydantic import Field
from app.core.config import Settings


class TestSettings(Settings):
    """Test-specific settings that override default settings."""
    
    class AppSettings:
        app_name: str = "PL8WRDS Test API"
        app_description: str = "Test environment for PL8WRDS"
        app_version: str = "0.1.0-test"
        project_root: str = "/tmp/test_pl8wrds"
        
        # Test-specific paths
        words_file_path: str = "/tmp/test_words.json"
        ridge_model_file_path: str = "/tmp/test_model.joblib"
        cache_dir_path: str = "/tmp/test_cache"
        
        # Disable external services by default in tests
        enable_ollama: bool = False
        enable_prediction_service: bool = False
    
    class DatabaseSettings:
        # Use in-memory or test-specific database settings
        database_url: str = "sqlite:///:memory:"
        echo_sql: bool = False  # Disable SQL logging in tests
    
    class CacheSettings:
        enable_cache: bool = True
        cache_ttl: int = 300  # 5 minutes for tests
        max_cache_size: int = 100  # Smaller cache for tests
    
    class LoggingSettings:
        log_level: str = "WARNING"  # Reduce noise in test output
        log_format: str = "%(levelname)s: %(message)s"
        enable_file_logging: bool = False
    
    # Override default settings
    app = AppSettings()
    database = DatabaseSettings()
    cache = CacheSettings()
    logging = LoggingSettings()
    
    # Test-specific flags
    is_testing: bool = True
    is_development: bool = False
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Ensure test-specific configurations
        self.app.enable_ollama = False
        self.app.enable_prediction_service = False
        self.is_testing = True


def get_test_settings() -> TestSettings:
    """Get test-specific settings."""
    return TestSettings()
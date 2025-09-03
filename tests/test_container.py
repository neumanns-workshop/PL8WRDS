"""
Test-specific dependency injection container.
"""

from dependency_injector import containers, providers

from app.core.container import Container
from tests.mocks.external_services import (
    MockLLMClient, MockWordSolver, MockFeatureExtractor,
    MockModelPredictor, MockCombinationGenerator, MockCacheManager
)
from tests.mocks.repositories import (
    InMemoryWordRepository, InMemoryScoringRepository, InMemoryCorpusRepository
)
from tests.test_settings import get_test_settings


class TestContainer(Container):
    """Test-specific dependency injection container with mocks."""
    
    def __init__(self):
        super().__init__()
        
        # Override settings with test settings
        self.settings.override(providers.Singleton(get_test_settings))
        
        # Override repositories with in-memory implementations
        self.word_repository.override(
            providers.Singleton(InMemoryWordRepository)
        )
        
        self.scoring_repository.override(
            providers.Singleton(InMemoryScoringRepository)
        )
        
        self.corpus_repository.override(
            providers.Singleton(InMemoryCorpusRepository)
        )
        
        # Override external services with mocks
        self.llm_client.override(
            providers.Singleton(MockLLMClient)
        )
        
        self.word_solver.override(
            providers.Singleton(
                MockWordSolver,
                word_repository=self.word_repository
            )
        )
        
        self.feature_extractor.override(
            providers.Singleton(MockFeatureExtractor)
        )
        
        self.model_predictor.override(
            providers.Singleton(MockModelPredictor)
        )
        
        self.combination_generator.override(
            providers.Singleton(MockCombinationGenerator)
        )
        
        self.cache_manager.override(
            providers.Singleton(MockCacheManager)
        )


def create_test_container() -> TestContainer:
    """Create a test container with all mocks configured."""
    container = TestContainer()
    
    # Wire the container for dependency injection
    container.wire(modules=[
        "app.application.services",
        "app.routers.prediction",
        "app.routers.scoring", 
        "app.routers.solver",
        "app.routers.corpus",
        "app.routers.combinations",
        "app.routers.dictionary",
        "app.routers.dataset",
        "app.routers.metrics"
    ])
    
    return container


def create_test_container_with_real_services() -> TestContainer:
    """Create a test container that uses real services but test repositories."""
    container = TestContainer()
    
    # Keep mock repositories but remove service mocks
    # This allows testing with real service logic but controlled data
    container.llm_client.reset_last_overriding()
    container.word_solver.reset_last_overriding()
    container.feature_extractor.reset_last_overriding()
    container.model_predictor.reset_last_overriding()
    container.combination_generator.reset_last_overriding()
    container.cache_manager.reset_last_overriding()
    
    # Re-wire with real implementations
    from app.infrastructure.external_services import (
        OllamaLLMClient, SimpleWordSolver, SimpleFeatureExtractor,
        JoblibModelPredictor, SimpleCombinationGenerator, MemoryCacheManager
    )
    
    container.llm_client.override(
        providers.Singleton(
            OllamaLLMClient,
            settings=container.settings
        )
    )
    
    container.word_solver.override(
        providers.Singleton(
            SimpleWordSolver,
            word_repository=container.word_repository
        )
    )
    
    container.feature_extractor.override(
        providers.Singleton(
            SimpleFeatureExtractor,
            word_repository=container.word_repository
        )
    )
    
    container.model_predictor.override(
        providers.Singleton(
            JoblibModelPredictor,
            settings=container.settings
        )
    )
    
    container.combination_generator.override(
        providers.Singleton(SimpleCombinationGenerator)
    )
    
    container.cache_manager.override(
        providers.Singleton(MemoryCacheManager)
    )
    
    return container


def create_integration_test_container() -> TestContainer:
    """Create a container for integration tests with minimal mocking."""
    container = create_test_container_with_real_services()
    
    # For integration tests, we might want to use real file-based repositories
    # but with test data directories
    from app.infrastructure.repositories import (
        JsonWordRepository, JsonScoringRepository, JsonCorpusRepository
    )
    from app.domain.value_objects import FilePath, DirectoryPath
    
    # Override with file-based repositories using test paths
    test_settings = get_test_settings()
    
    container.word_repository.override(
        providers.Singleton(
            JsonWordRepository,
            data_file_path=FilePath(test_settings.app.words_file_path)
        )
    )
    
    container.scoring_repository.override(
        providers.Singleton(
            JsonScoringRepository,
            cache_dir=DirectoryPath(test_settings.app.cache_dir_path)
        )
    )
    
    container.corpus_repository.override(
        providers.Singleton(
            JsonCorpusRepository,
            cache_dir=DirectoryPath(test_settings.app.cache_dir_path)
        )
    )
    
    return container
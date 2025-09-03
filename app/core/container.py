"""
Dependency injection container configuration.
"""

from dependency_injector import containers, providers
from dependency_injector.wiring import Provide, inject

from .config import Settings, get_settings
from ..infrastructure.repositories import (
    JsonWordRepository, JsonScoringRepository, JsonCorpusRepository
)
from ..infrastructure.external_services import (
    OllamaLLMClient, SimpleWordSolver, SimpleCombinationGenerator,
    JoblibModelPredictor, MemoryCacheManager, SimpleFeatureExtractor
)
from ..application.services import (
    WordScoringService, WordDiscoveryService, CorpusManagementService,
    PredictionService
)


class Container(containers.DeclarativeContainer):
    """Dependency injection container."""
    
    # Configuration
    config = providers.Singleton(get_settings)
    
    # Repositories
    word_repository = providers.Singleton(
        JsonWordRepository,
        data_file_path=config.provided.app.words_file_path
    )
    
    scoring_repository = providers.Singleton(
        JsonScoringRepository,
        cache_dir=config.provided.app.cache_directory_path
    )
    
    corpus_repository = providers.Singleton(
        JsonCorpusRepository,
        cache_dir=config.provided.app.cache_directory_path
    )
    
    # External Services
    llm_client = providers.Singleton(
        OllamaLLMClient,
        settings=config
    )
    
    word_solver = providers.Singleton(
        SimpleWordSolver,
        word_repository=word_repository
    )
    
    combination_generator = providers.Singleton(
        SimpleCombinationGenerator
    )
    
    model_predictor = providers.Singleton(
        JoblibModelPredictor,
        settings=config
    )
    
    cache_manager = providers.Singleton(
        MemoryCacheManager
    )
    
    feature_extractor = providers.Singleton(
        SimpleFeatureExtractor,
        word_repository=word_repository
    )
    
    # Application Services
    word_scoring_service = providers.Singleton(
        WordScoringService,
        word_repository=word_repository,
        scoring_repository=scoring_repository,
        llm_client=llm_client,
        model_predictor=model_predictor
    )
    
    word_discovery_service = providers.Singleton(
        WordDiscoveryService,
        word_repository=word_repository,
        word_solver=word_solver
    )
    
    corpus_management_service = providers.Singleton(
        CorpusManagementService,
        corpus_repository=corpus_repository,
        feature_extractor=feature_extractor,
        cache_manager=cache_manager
    )
    
    prediction_service = providers.Singleton(
        PredictionService,
        word_repository=word_repository,
        model_predictor=model_predictor,
        feature_extractor=feature_extractor
    )


def create_container() -> Container:
    """Create and configure the dependency injection container."""
    container = Container()
    container.wire(modules=[
        "app.application.services",
        "app.routers.prediction",
        "app.routers.scoring", 
        "app.routers.corpus",
        "app.routers.solver",
        "app.routers.dataset",
        "app.routers.dictionary",
        "app.routers.combinations",
        "app.routers.metrics"
    ])
    return container
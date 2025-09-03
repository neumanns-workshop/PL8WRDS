"""
Application services - Coordinate use cases and provide high-level API.
"""

import logging
from typing import List, Optional, Dict, Any
from dependency_injector.wiring import Provide, inject

from .use_cases import (
    ScoreWordUseCase, PredictWordScoreUseCase, FindWordsForPlateUseCase,
    CreateScoringSessionUseCase, ManageCorpusUseCase, CheckSystemHealthUseCase
)
from .interfaces import (
    LLMClient, ModelPredictor, WordSolver, CombinationGenerator,
    FeatureExtractor, CacheManager
)
from ..domain.entities import (
    WordScore, ScoringSession, CorpusStatistics, CorpusFeatures,
    ScoringSystemStatus
)
from ..domain.value_objects import (
    Word, LicensePlate, ModelName, Score, SessionId
)
from ..infrastructure.repositories import (
    WordRepository, ScoringRepository, CorpusRepository
)

logger = logging.getLogger(__name__)


class WordScoringService:
    """Application service for word scoring operations."""
    
    @inject
    def __init__(self,
                 word_repository: WordRepository = Provide["word_repository"],
                 scoring_repository: ScoringRepository = Provide["scoring_repository"],
                 llm_client: LLMClient = None,  # Will be injected when implemented
                 model_predictor: ModelPredictor = None):  # Will be injected when implemented
        self.word_repository = word_repository
        self.scoring_repository = scoring_repository
        self.llm_client = llm_client
        self.model_predictor = model_predictor
    
    async def score_word(self, 
                        word_str: str, 
                        plate_str: str, 
                        model_names: List[str]) -> WordScore:
        """Score a word against a license plate using multiple models."""
        
        # Convert to domain objects
        word = Word(word_str)
        plate = LicensePlate(plate_str)
        models = [ModelName(name) for name in model_names]
        
        # Create and execute use case
        use_case = ScoreWordUseCase(
            self.llm_client,
            self.scoring_repository,
            self.word_repository
        )
        
        return await use_case.execute(word, plate, models)
    
    async def predict_score(self, word_str: str, plate_str: str) -> float:
        """Predict a score using the ML model."""
        
        # Convert to domain objects
        word = Word(word_str)
        plate = LicensePlate(plate_str)
        
        # Create and execute use case
        use_case = PredictWordScoreUseCase(
            self.model_predictor,
            None,  # Will be injected when implemented
            self.word_repository
        )
        
        score = await use_case.execute(word, plate)
        return score.value
    
    async def create_scoring_session(self,
                                   num_plates: int,
                                   words_per_plate: int,
                                   plate_length: int,
                                   model_names: List[str]) -> ScoringSession:
        """Create and execute a scoring session."""
        
        models = [ModelName(name) for name in model_names]
        
        # Create and execute use case
        use_case = CreateScoringSessionUseCase(
            self.llm_client,
            None,  # WordSolver - will be injected when implemented
            None,  # CombinationGenerator - will be injected when implemented
            self.scoring_repository,
            self.word_repository
        )
        
        return await use_case.execute(num_plates, words_per_plate, plate_length, models)
    
    async def get_session(self, session_id: str) -> Optional[ScoringSession]:
        """Get a scoring session by ID."""
        session_id_obj = SessionId(session_id)
        return await self.scoring_repository.get_session(session_id_obj)
    
    async def check_system_health(self, model_names: List[str]) -> ScoringSystemStatus:
        """Check the health of the scoring system."""
        
        models = [ModelName(name) for name in model_names]
        
        use_case = CheckSystemHealthUseCase(
            self.llm_client,
            self.model_predictor
        )
        
        return await use_case.execute(models)


class WordDiscoveryService:
    """Application service for word discovery operations."""
    
    @inject
    def __init__(self,
                 word_repository: WordRepository = Provide["word_repository"],
                 word_solver: WordSolver = None):  # Will be injected when implemented
        self.word_repository = word_repository
        self.word_solver = word_solver
    
    async def find_words_for_plate(self, 
                                  plate_str: str, 
                                  strategy: str = "subsequence",
                                  limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Find words that match a license plate."""
        
        plate = LicensePlate(plate_str)
        
        use_case = FindWordsForPlateUseCase(self.word_solver)
        matches = await use_case.execute(plate, strategy, limit)
        
        # Convert to API format
        return [
            {
                "word": match[0].value,
                "frequency": match[1]
            }
            for match in matches
        ]
    
    async def get_word_frequency(self, word_str: str) -> Optional[int]:
        """Get the frequency of a word."""
        word = Word(word_str)
        frequency = await self.word_repository.get_word_frequency(word)
        return frequency.value if frequency else None


class CorpusManagementService:
    """Application service for corpus management operations."""
    
    @inject
    def __init__(self,
                 corpus_repository: CorpusRepository = Provide["corpus_repository"],
                 feature_extractor: FeatureExtractor = None,  # Will be injected when implemented
                 cache_manager: Optional[CacheManager] = None):
        self.corpus_repository = corpus_repository
        self.feature_extractor = feature_extractor
        self.cache_manager = cache_manager
    
    async def get_corpus_statistics(self, force_rebuild: bool = False) -> Dict[str, Any]:
        """Get corpus statistics."""
        
        use_case = ManageCorpusUseCase(
            self.feature_extractor,
            self.corpus_repository,
            self.cache_manager
        )
        
        stats = await use_case.get_corpus_statistics(force_rebuild)
        
        # Convert to API format
        return {
            "total_plates": stats.total_plates,
            "total_unique_words": stats.total_unique_words,
            "dataset_words": stats.dataset_words,
            "plate_word_counts": stats.plate_word_counts,
            "word_frequency_distribution": stats.word_frequency_distribution,
            "generated_at": stats.generated_at.isoformat()
        }
    
    async def get_corpus_features(self, force_rebuild: bool = False) -> Dict[str, Any]:
        """Get corpus features."""
        
        use_case = ManageCorpusUseCase(
            self.feature_extractor,
            self.corpus_repository,
            self.cache_manager
        )
        
        features = await use_case.get_corpus_features(force_rebuild)
        
        # Convert to API format
        return {
            "features": features.features,
            "metadata": features.metadata,
            "generated_at": features.generated_at.isoformat()
        }
    
    async def get_cache_info(self) -> Dict[str, Any]:
        """Get information about cache status."""
        # TODO: Implement cache info retrieval
        return {
            "cached": False,
            "cache_file_exists": False,
            "cache_file_size_bytes": 0,
            "last_updated": None,
            "cache_file_path": None
        }


class PredictionService:
    """Application service for ML prediction operations."""
    
    @inject
    def __init__(self,
                 word_repository: WordRepository = Provide["word_repository"],
                 model_predictor: ModelPredictor = None,  # Will be injected when implemented
                 feature_extractor: FeatureExtractor = None):
        self.word_repository = word_repository
        self.model_predictor = model_predictor
        self.feature_extractor = feature_extractor
    
    async def predict_score(self, word_str: str, plate_str: str) -> Dict[str, Any]:
        """Predict a score for a word-plate combination."""
        
        word = Word(word_str)
        plate = LicensePlate(plate_str)
        
        use_case = PredictWordScoreUseCase(
            self.model_predictor,
            self.feature_extractor,
            self.word_repository
        )
        
        score = await use_case.execute(word, plate)
        
        return {
            "word": word_str,
            "plate": plate_str,
            "predicted_score": score.value,
            "model": "ridge_regression"
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if the prediction service is healthy."""
        
        try:
            is_loaded = await self.model_predictor.is_model_loaded()
            return {
                "status": "healthy" if is_loaded else "model_not_loaded",
                "model_loaded": is_loaded
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "model_loaded": False
            }
    
    async def initialize(self):
        """Initialize the prediction service (load model)."""
        if self.model_predictor and not await self.model_predictor.is_model_loaded():
            await self.model_predictor.load_model()
            logger.info("Prediction model loaded successfully")
    
    async def get_feature_importance(self, top_k: int = 20) -> Dict[str, Any]:
        """Get feature importance from the trained model."""
        if not self.model_predictor:
            raise RuntimeError("Model predictor not available")
        
        # For now, delegate to model predictor
        # This method should be added to the ModelPredictor interface
        if hasattr(self.model_predictor, 'get_feature_importance'):
            return await self.model_predictor.get_feature_importance(top_k)
        else:
            raise NotImplementedError("Feature importance not implemented in model predictor")
    
    async def explain_prediction(self, word_str: str, plate_str: str, top_k: int = 10) -> Dict[str, Any]:
        """Explain a specific prediction by showing feature contributions."""
        if not self.model_predictor:
            raise RuntimeError("Model predictor not available")
        
        word = Word(word_str)
        plate = LicensePlate(plate_str)
        
        # For now, delegate to model predictor
        # This method should be added to the ModelPredictor interface
        if hasattr(self.model_predictor, 'explain_prediction'):
            return await self.model_predictor.explain_prediction(word, plate, top_k)
        else:
            raise NotImplementedError("Prediction explanation not implemented in model predictor")
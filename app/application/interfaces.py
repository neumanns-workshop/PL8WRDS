"""
Application layer interfaces - Abstractions for external services.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from ..domain.entities import (
    WordScore, IndividualScore, ScoringSession, ModelAvailability,
    ScoringSystemStatus, CorpusStatistics, CorpusFeatures
)
from ..domain.value_objects import (
    Word, LicensePlate, ModelName, Score, SessionId,
    Reasoning
)


class LLMClient(ABC):
    """Abstract interface for Language Model clients."""
    
    @abstractmethod
    async def generate_score(self, 
                           word: Word, 
                           plate: LicensePlate, 
                           model: ModelName) -> IndividualScore:
        """Generate a score for a word-plate combination."""
        pass
    
    @abstractmethod
    async def check_model_availability(self, model: ModelName) -> ModelAvailability:
        """Check if a model is available."""
        pass
    
    @abstractmethod
    async def is_service_healthy(self) -> bool:
        """Check if the LLM service is healthy."""
        pass


class FeatureExtractor(ABC):
    """Abstract interface for feature extraction."""
    
    @abstractmethod
    async def extract_features(self, word: Word, plate: LicensePlate) -> Dict[str, Any]:
        """Extract features for a word-plate combination."""
        pass
    
    @abstractmethod
    async def build_corpus_statistics(self) -> CorpusStatistics:
        """Build comprehensive corpus statistics."""
        pass
    
    @abstractmethod
    async def build_corpus_features(self) -> CorpusFeatures:
        """Build pre-computed features for all word-plate combinations."""
        pass


class ModelPredictor(ABC):
    """Abstract interface for ML model predictions."""
    
    @abstractmethod
    async def predict_score(self, word: Word, plate: LicensePlate) -> Score:
        """Predict a score using the trained model."""
        pass
    
    @abstractmethod
    async def is_model_loaded(self) -> bool:
        """Check if the prediction model is loaded."""
        pass
    
    @abstractmethod
    async def load_model(self) -> None:
        """Load the prediction model."""
        pass
    
    @abstractmethod
    async def get_feature_importance(self, top_k: int = 20) -> Dict[str, Any]:
        """Get feature importance from the trained model."""
        pass
    
    @abstractmethod
    async def explain_prediction(self, word: Word, plate: LicensePlate, top_k: int = 10) -> Dict[str, Any]:
        """Explain a specific prediction by showing feature contributions."""
        pass


class WordSolver(ABC):
    """Abstract interface for word solving algorithms."""
    
    @abstractmethod
    async def find_matching_words(self, 
                                plate: LicensePlate, 
                                strategy: str = "subsequence") -> List[tuple[Word, int]]:
        """Find words that match a license plate pattern."""
        pass
    
    @abstractmethod
    async def get_random_words_for_plate(self, 
                                       plate: LicensePlate, 
                                       count: int = 5,
                                       strategy: str = "frequency_weighted") -> List[Word]:
        """Get random words that match a plate using different sampling strategies."""
        pass


class CombinationGenerator(ABC):
    """Abstract interface for generating license plate combinations."""
    
    @abstractmethod
    async def generate_combinations(self, 
                                  character_set: str,
                                  length: int,
                                  count: int) -> List[LicensePlate]:
        """Generate random license plate combinations."""
        pass


class CacheManager(ABC):
    """Abstract interface for cache management."""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache."""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete value from cache."""
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """Clear all cache."""
        pass
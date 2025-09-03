"""
Mock implementations for external services used in testing.
"""

from typing import Dict, List, Optional, Any, Tuple
from unittest.mock import AsyncMock
import random

from app.application.interfaces import (
    LLMClient, FeatureExtractor, ModelPredictor, WordSolver,
    CombinationGenerator, CacheManager
)
from app.domain.entities import (
    IndividualScore, ModelAvailability, CorpusStatistics, CorpusFeatures
)
from app.domain.value_objects import (
    Word, LicensePlate, ModelName, Score, Reasoning, Frequency
)


class MockLLMClient(LLMClient):
    """Mock LLM client for testing."""
    
    def __init__(self, available_models: Optional[List[str]] = None, healthy: bool = True):
        self.available_models = available_models or ["granite", "mistral", "deepseek"]
        self.healthy = healthy
        self.generation_delay = 0  # Simulate processing delay in seconds
        self.call_count = 0
        
    async def generate_score(self, word: Word, plate: LicensePlate, model: ModelName) -> IndividualScore:
        """Generate a predictable mock score."""
        self.call_count += 1
        
        if not self.healthy:
            raise RuntimeError("LLM service is unhealthy")
        
        if model.value not in self.available_models:
            raise ValueError(f"Model {model.value} not available")
        
        # Generate deterministic but varied scores based on word and plate
        base_score = hash(f"{word.value}:{plate.value}") % 80 + 10  # 10-90
        model_offset = hash(model.value) % 20 - 10  # -10 to +10 offset per model
        final_score = max(0, min(100, base_score + model_offset))
        
        reasoning_templates = [
            f"The word '{word.value}' matches '{plate.value}' with good creativity.",
            f"'{word.value}' represents '{plate.value}' in an interesting way.",
            f"Strong connection between '{word.value}' and '{plate.value}'.",
            f"'{word.value}' is a clever interpretation of '{plate.value}'.",
        ]
        
        reasoning_text = random.choice(reasoning_templates)
        
        return IndividualScore(
            model=model,
            score=Score(final_score),
            reasoning=Reasoning(reasoning_text)
        )
    
    async def check_model_availability(self, model: ModelName) -> ModelAvailability:
        """Check mock model availability."""
        available = model.value in self.available_models and self.healthy
        error_message = None if available else "Model not available in mock"
        
        return ModelAvailability(
            model=model,
            available=available,
            error_message=error_message
        )
    
    async def is_service_healthy(self) -> bool:
        """Check mock service health."""
        return self.healthy
    
    def set_unhealthy(self):
        """Make the mock service unhealthy."""
        self.healthy = False
    
    def set_healthy(self):
        """Make the mock service healthy."""
        self.healthy = True
    
    def add_model(self, model_name: str):
        """Add a model to available models."""
        if model_name not in self.available_models:
            self.available_models.append(model_name)
    
    def remove_model(self, model_name: str):
        """Remove a model from available models."""
        if model_name in self.available_models:
            self.available_models.remove(model_name)


class MockWordSolver(WordSolver):
    """Mock word solver for testing."""
    
    def __init__(self, word_data: Optional[Dict[str, int]] = None):
        # Default test data
        self.word_data = word_data or {
            "ambulance": 5000,
            "albatross": 3000,
            "abstract": 4000,
            "beach": 2500,
            "cabin": 2000,  # Doesn't match ABC
            "cat": 8000,    # Doesn't match ABC
            "dog": 6000,    # Matches D**
            "elephant": 1500, # Matches E**
        }
        
    async def find_matching_words(self, plate: LicensePlate, strategy: str = "subsequence") -> List[tuple[Word, int]]:
        """Find mock matching words."""
        matches = []
        
        for word_str, frequency in self.word_data.items():
            word = Word(word_str)
            if word.matches_plate(plate):
                matches.append((word, frequency))
        
        # Sort by frequency (descending)
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches
    
    async def get_random_words_for_plate(self, 
                                       plate: LicensePlate,
                                       count: int = 5,
                                       strategy: str = "frequency_weighted") -> List[Word]:
        """Get random mock words."""
        matches = await self.find_matching_words(plate)
        
        if not matches:
            return []
        
        if strategy == "uniform":
            words = [word for word, freq in matches]
            selected = random.sample(words, min(count, len(words)))
        elif strategy == "frequency_weighted":
            words, frequencies = zip(*matches) if matches else ([], [])
            if not words:
                return []
            
            selected = []
            words_list = list(words)
            freq_list = list(frequencies)
            
            for _ in range(min(count, len(words_list))):
                if not words_list:
                    break
                chosen_idx = random.choices(range(len(words_list)), weights=freq_list, k=1)[0]
                selected.append(words_list[chosen_idx])
                words_list.pop(chosen_idx)
                freq_list.pop(chosen_idx)
        else:
            # Default to first N words
            selected = [word for word, freq in matches[:count]]
        
        return selected
    
    def add_word(self, word: str, frequency: int):
        """Add a word to mock data."""
        self.word_data[word] = frequency
    
    def remove_word(self, word: str):
        """Remove a word from mock data."""
        if word in self.word_data:
            del self.word_data[word]


class MockFeatureExtractor(FeatureExtractor):
    """Mock feature extractor for testing."""
    
    def __init__(self):
        self.extraction_count = 0
        
    async def extract_features(self, word: Word, plate: LicensePlate) -> Dict[str, Any]:
        """Extract mock features."""
        self.extraction_count += 1
        
        return {
            "word_length": len(word),
            "plate_length": len(plate),
            "word_frequency": hash(word.value) % 10000 + 1000,  # 1000-11000
            "character_overlap": len(set(word.value.lower()) & set(plate.value.lower())),
            "vowel_ratio": len([c for c in word.value.lower() if c in 'aeiou']) / len(word),
            "consonant_ratio": 1 - (len([c for c in word.value.lower() if c in 'aeiou']) / len(word)),
            "position_entropy": hash(f"{word.value}:{plate.value}") % 100 / 100 * 3,  # 0-3
            "tfidf_score": hash(f"tfidf_{word.value}") % 100 / 100,  # 0-1
            "ngram_features": {
                "bigram_count": max(0, len(word) - 1),
                "trigram_count": max(0, len(word) - 2)
            },
            "word": word.value,
            "plate": plate.value
        }
    
    async def build_corpus_statistics(self) -> CorpusStatistics:
        """Build mock corpus statistics."""
        return CorpusStatistics(
            total_plates=100,
            total_unique_words=5000,
            dataset_words=["ambulance", "beach", "cat", "dog", "elephant"] * 20,  # 100 words
            plate_word_counts={
                "ABC": 25,
                "DEF": 30,
                "GHI": 20,
                "JKL": 15,
                "MNO": 10
            },
            word_frequency_distribution={
                "very_rare": 500,     # < 1000
                "rare": 1000,        # 1000-5000  
                "common": 2000,      # 5000-10000
                "very_common": 1500  # > 10000
            }
        )
    
    async def build_corpus_features(self) -> CorpusFeatures:
        """Build mock corpus features."""
        # Generate sample features for common word-plate combinations
        sample_combinations = [
            ("ambulance", "abc"),
            ("beach", "bch"), 
            ("cat", "cat"),
            ("dog", "dg"),
            ("elephant", "elh")
        ]
        
        features = {}
        for word_str, plate_str in sample_combinations:
            word = Word(word_str)
            plate = LicensePlate(plate_str)
            key = f"{word.value}:{plate.value}"
            
            mock_features = await self.extract_features(word, plate)
            features[key] = mock_features
        
        return CorpusFeatures(
            features=features,
            metadata={
                "total_features": len(features),
                "feature_types": ["word_length", "plate_length", "word_frequency", "character_overlap", "vowel_ratio"],
                "extraction_method": "mock",
                "version": "1.0"
            }
        )


class MockModelPredictor(ModelPredictor):
    """Mock model predictor for testing."""
    
    def __init__(self):
        self.model_loaded = False
        self.prediction_count = 0
        
    async def predict_score(self, word: Word, plate: LicensePlate) -> Score:
        """Predict mock score."""
        if not self.model_loaded:
            raise RuntimeError("Model not loaded")
        
        self.prediction_count += 1
        
        # Generate deterministic but realistic scores
        base_score = hash(f"{word.value}:{plate.value}") % 70 + 15  # 15-85
        
        # Add some factors to make it more realistic
        word_length_factor = min(5, max(-5, (len(word) - 6) * 2))  # Favor 6-letter words
        plate_complexity = len(set(plate.value))  # More unique letters = harder
        
        final_score = base_score + word_length_factor - plate_complexity
        final_score = max(0, min(100, final_score))
        
        return Score(final_score)
    
    async def is_model_loaded(self) -> bool:
        """Check if mock model is loaded."""
        return self.model_loaded
    
    async def load_model(self) -> None:
        """Load mock model."""
        self.model_loaded = True
    
    def unload_model(self):
        """Unload mock model."""
        self.model_loaded = False


class MockCombinationGenerator(CombinationGenerator):
    """Mock combination generator for testing."""
    
    async def generate_combinations(self,
                                  character_set: str,
                                  length: int,
                                  count: int) -> List[LicensePlate]:
        """Generate mock combinations."""
        combinations = []
        
        # Generate deterministic but varied combinations
        for i in range(count):
            combo = ""
            for j in range(length):
                char_index = (i * length + j) % len(character_set)
                combo += character_set[char_index]
            
            combinations.append(LicensePlate(combo))
        
        return combinations


class MockCacheManager(CacheManager):
    """Mock cache manager for testing."""
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self.get_count = 0
        self.set_count = 0
        
    async def get(self, key: str) -> Optional[Any]:
        """Get from mock cache."""
        self.get_count += 1
        return self._cache.get(key)
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set in mock cache."""
        self.set_count += 1
        self._cache[key] = value
    
    async def delete(self, key: str) -> None:
        """Delete from mock cache."""
        self._cache.pop(key, None)
    
    async def clear(self) -> None:
        """Clear mock cache."""
        self._cache.clear()
    
    def get_cache_size(self) -> int:
        """Get cache size."""
        return len(self._cache)
    
    def get_all_keys(self) -> List[str]:
        """Get all cache keys."""
        return list(self._cache.keys())


# Factory functions for creating pre-configured mocks

def create_healthy_llm_client() -> MockLLMClient:
    """Create a healthy LLM client mock."""
    return MockLLMClient(
        available_models=["granite", "mistral", "deepseek"],
        healthy=True
    )

def create_unhealthy_llm_client() -> MockLLMClient:
    """Create an unhealthy LLM client mock."""
    return MockLLMClient(
        available_models=["granite", "mistral", "deepseek"],
        healthy=False
    )

def create_limited_llm_client() -> MockLLMClient:
    """Create an LLM client mock with limited models."""
    return MockLLMClient(
        available_models=["granite"],  # Only one model
        healthy=True
    )

def create_populated_word_solver() -> MockWordSolver:
    """Create a word solver mock with comprehensive test data."""
    word_data = {
        # ABC matches
        "ambulance": 5000,
        "albatross": 3000,
        "abstract": 4000,
        "about": 8000,
        
        # DEF matches  
        "defeat": 3500,
        "defend": 4200,
        "define": 5500,
        
        # GHI matches
        "garage": 2800,
        "graphics": 3200,
        
        # Non-matches for ABC
        "cabin": 2000,  # CBA order
        "cat": 8000,    # Missing letters
        "xyz": 100,     # No overlap
        
        # Single letter matches
        "a": 10000,
        "about": 8000,  # Duplicate, will overwrite
    }
    
    return MockWordSolver(word_data)

def create_loaded_model_predictor() -> MockModelPredictor:
    """Create a model predictor mock with loaded model."""
    predictor = MockModelPredictor()
    predictor.model_loaded = True
    return predictor

def create_unloaded_model_predictor() -> MockModelPredictor:
    """Create a model predictor mock without loaded model."""
    return MockModelPredictor()  # model_loaded defaults to False
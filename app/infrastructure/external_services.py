"""
Concrete implementations of external service interfaces.
"""

import json
import logging
import random
import statistics
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

from ..application.interfaces import (
    LLMClient, FeatureExtractor, ModelPredictor, WordSolver, 
    CombinationGenerator, CacheManager
)
from ..domain.entities import (
    IndividualScore, ModelAvailability, CorpusStatistics, CorpusFeatures
)
from ..domain.value_objects import (
    Word, LicensePlate, ModelName, Score, Reasoning, Frequency
)
from ..core.config import Settings

logger = logging.getLogger(__name__)


class OllamaLLMClient(LLMClient):
    """Ollama-based LLM client implementation."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.ollama_client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Ollama client safely."""
        try:
            # Import ollama_client from project root without sys.path manipulation
            # This is a safer approach than the current implementation
            project_root = Path(self.settings.app.project_root)
            ollama_client_path = project_root / "ollama_client.py"
            
            if ollama_client_path.exists():
                import importlib.util
                spec = importlib.util.spec_from_file_location("ollama_client", ollama_client_path)
                ollama_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(ollama_module)
                
                self.ollama_client = ollama_module.OllamaClient()
                self.check_ollama_health = ollama_module.check_ollama_health
                self.check_model_available = ollama_module.check_model_available
                self.auto_setup_model = ollama_module.auto_setup_model
                
                logger.info("Ollama client initialized successfully")
            else:
                logger.warning("ollama_client.py not found, LLM features will be disabled")
                
        except Exception as e:
            logger.error(f"Failed to initialize Ollama client: {e}")
            self.ollama_client = None
    
    async def generate_score(self, word: Word, plate: LicensePlate, model: ModelName) -> IndividualScore:
        """Generate a score for a word-plate combination."""
        if not self.ollama_client:
            # Return a mock score if Ollama is not available
            return IndividualScore(
                model=model,
                score=Score(50.0),  # Default middle score
                reasoning=Reasoning("Ollama service not available")
            )
        
        try:
            # Create the scoring prompt
            prompt = f"""
            Score the following word for how well it represents the license plate combination.
            
            License Plate: {plate.value}
            Word: {word.value}
            
            Consider:
            1. Cleverness (how creative/witty is the connection?)
            2. Difficulty (how hard was it to find this word?)
            3. Satisfaction (how satisfying is it when you discover this word?)
            4. Word Quality (is it a good/common English word?)
            
            Provide a score from 0-100 and brief reasoning.
            
            Format your response as JSON with 'score' and 'reasoning' fields.
            """
            
            # Use the Ollama client to generate response
            response = self.ollama_client.generate_response(
                model=model.value,
                prompt=prompt,
                response_model=None  # We'll parse JSON manually
            )
            
            # Parse the response
            if hasattr(response, 'score') and hasattr(response, 'reasoning'):
                score_value = float(response.score)
                reasoning_text = response.reasoning
            else:
                # Try to parse as JSON string
                try:
                    parsed = json.loads(str(response))
                    score_value = float(parsed['score'])
                    reasoning_text = parsed['reasoning']
                except (json.JSONDecodeError, KeyError):
                    # Fallback to default values
                    score_value = 50.0
                    reasoning_text = "Unable to parse LLM response"
            
            return IndividualScore(
                model=model,
                score=Score(score_value),
                reasoning=Reasoning(reasoning_text)
            )
            
        except Exception as e:
            logger.error(f"Failed to generate score with {model.value}: {e}")
            return IndividualScore(
                model=model,
                score=Score(0.0),
                reasoning=Reasoning(f"Error: {str(e)}")
            )
    
    async def check_model_availability(self, model: ModelName) -> ModelAvailability:
        """Check if a model is available."""
        if not self.ollama_client or not hasattr(self, 'check_model_available'):
            return ModelAvailability(
                model=model,
                available=False,
                error_message="Ollama client not initialized"
            )
        
        try:
            available = self.check_model_available(model.value)
            return ModelAvailability(model=model, available=available)
        except Exception as e:
            return ModelAvailability(
                model=model,
                available=False,
                error_message=str(e)
            )
    
    async def is_service_healthy(self) -> bool:
        """Check if the LLM service is healthy."""
        if not self.ollama_client or not hasattr(self, 'check_ollama_health'):
            return False
        
        try:
            return self.check_ollama_health()
        except Exception:
            return False


class SimpleWordSolver(WordSolver):
    """Simple implementation of word solver."""
    
    def __init__(self, word_repository):
        self.word_repository = word_repository
    
    async def find_matching_words(self, plate: LicensePlate, strategy: str = "subsequence") -> List[tuple[Word, int]]:
        """Find words that match a license plate pattern."""
        all_words = await self.word_repository.get_all_words()
        
        matches = []
        for word, frequency in all_words.items():
            # Filter out very short words (single letters, abbreviations)
            if len(word.value) >= 3 and word.matches_plate(plate):
                matches.append((word, frequency.value))
        
        # Sort by frequency (descending)
        matches.sort(key=lambda x: x[1], reverse=True)
        
        return matches
    
    async def get_random_words_for_plate(self, 
                                       plate: LicensePlate, 
                                       count: int = 5,
                                       strategy: str = "frequency_weighted") -> List[Word]:
        """Get random words that match a plate using different sampling strategies."""
        matches = await self.find_matching_words(plate)
        
        if not matches:
            return []
        
        if strategy == "uniform":
            words = [word for word, freq in matches]
            selected = random.sample(words, min(count, len(words)))
        elif strategy == "frequency_weighted":
            words, frequencies = zip(*matches)
            selected = []
            words_list = list(words)
            freq_list = list(frequencies)
            
            for _ in range(min(count, len(words_list))):
                chosen_idx = random.choices(range(len(words_list)), weights=freq_list, k=1)[0]
                selected.append(words_list[chosen_idx])
                words_list.pop(chosen_idx)
                freq_list.pop(chosen_idx)
        else:
            # Default to first N words
            selected = [word for word, freq in matches[:count]]
        
        return selected


class SimpleCombinationGenerator(CombinationGenerator):
    """Simple implementation of combination generator."""
    
    async def generate_combinations(self, 
                                  character_set: str,
                                  length: int,
                                  count: int) -> List[LicensePlate]:
        """Generate random license plate combinations."""
        combinations = []
        
        for _ in range(count):
            combo = ''.join(random.choice(character_set) for _ in range(length))
            combinations.append(LicensePlate(combo))
        
        return combinations


class JoblibModelPredictor(ModelPredictor):
    """Joblib-based model predictor implementation."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.model = None
        self.feature_extractor = None
    
    async def is_model_loaded(self) -> bool:
        """Check if the prediction model is loaded."""
        return self.model is not None
    
    async def load_model(self) -> None:
        """Load the prediction model."""
        try:
            import joblib
            model_path = self.settings.app.ridge_model_file_path.value
            
            if Path(model_path).exists():
                model_data = joblib.load(model_path)
                
                # Handle different model file formats
                if isinstance(model_data, dict):
                    # New format with model, feature_names, and training_info
                    self.model = model_data.get('model')
                    self.feature_names = model_data.get('feature_names', [])
                    self.training_info = model_data.get('training_info', {})
                    logger.info(f"Loaded model with {len(self.feature_names)} features from {model_path}")
                else:
                    # Legacy format - direct model object
                    self.model = model_data
                    self.feature_names = []
                    self.training_info = {}
                    logger.info(f"Loaded legacy model from {model_path}")
                    
            else:
                logger.warning(f"Model file not found: {model_path}")
                
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    async def predict_score(self, word: Word, plate: LicensePlate) -> Score:
        """Predict a score using the trained model."""
        if not self.model:
            raise RuntimeError("Model not loaded")
        
        # For now, return a mock prediction
        # In a real implementation, this would extract features and use the model
        mock_score = hash(f"{word.value}:{plate.value}") % 100
        return Score(float(mock_score))
    
    async def get_feature_importance(self, top_k: int = 20) -> Dict[str, Any]:
        """Get feature importance from the trained model."""
        if not self.model:
            raise RuntimeError("Model not loaded")
        
        # Get feature names and coefficients from the Ridge model
        if not hasattr(self, 'feature_names') or not self.feature_names:
            # If feature names not available, create generic names based on model structure
            if hasattr(self.model, 'steps') and len(self.model.steps) > 0:
                # Pipeline - get the final estimator
                final_estimator = self.model.steps[-1][1]
                if hasattr(final_estimator, 'coef_'):
                    feature_names = [f"feature_{i}" for i in range(len(final_estimator.coef_))]
                else:
                    raise RuntimeError("Final estimator does not have coefficients")
            elif hasattr(self.model, 'coef_'):
                # Direct model
                feature_names = [f"feature_{i}" for i in range(len(self.model.coef_))]
            else:
                raise RuntimeError("Model structure not recognized")
        else:
            feature_names = self.feature_names
            
        # Get coefficients from the model (handle Pipeline vs direct model)
        if hasattr(self.model, 'steps') and len(self.model.steps) > 0:
            # Pipeline - get coefficients from the final estimator (Ridge)
            final_estimator = self.model.steps[-1][1]
            coefficients = final_estimator.coef_
            intercept = getattr(final_estimator, 'intercept_', 0.0)
        else:
            # Direct model
            coefficients = self.model.coef_
            intercept = getattr(self.model, 'intercept_', 0.0)
            
        abs_coefficients = abs(coefficients)
        
        # Create feature importance list
        feature_importance = []
        for i, (name, coef, abs_coef) in enumerate(zip(feature_names, coefficients, abs_coefficients)):
            feature_importance.append({
                "name": name,
                "importance": float(abs_coef),
                "coefficient": float(coef),
                "rank": i + 1
            })
        
        # Sort by absolute importance
        feature_importance.sort(key=lambda x: x["importance"], reverse=True)
        
        # Update ranks after sorting
        for i, feature in enumerate(feature_importance):
            feature["rank"] = i + 1
            
        return {
            "total_features": len(feature_importance),
            "top_features": feature_importance[:top_k],
            "model_info": {
                "model_type": "Ridge Regression", 
                "total_coefficients": len(coefficients),
                "model_path": str(self.settings.app.ridge_model_file_path),
                "intercept": float(intercept)
            }
        }
    
    async def explain_prediction(self, word: Word, plate: LicensePlate, top_k: int = 10) -> Dict[str, Any]:
        """Explain a specific prediction by showing feature contributions."""
        if not self.model:
            raise RuntimeError("Model not loaded")
        
        # This is a simplified implementation
        # TODO: Integrate with proper feature extraction service
        
        # Get coefficients from the model (handle Pipeline vs direct model)
        if hasattr(self.model, 'steps') and len(self.model.steps) > 0:
            # Pipeline - get coefficients from the final estimator (Ridge)
            final_estimator = self.model.steps[-1][1]
            coefficients = final_estimator.coef_
            intercept = float(getattr(final_estimator, 'intercept_', 0.0))
        else:
            # Direct model
            coefficients = self.model.coef_
            intercept = float(getattr(self.model, 'intercept_', 0.0))
        
        # Get feature names
        if not hasattr(self, 'feature_names') or not self.feature_names:
            feature_names = [f"feature_{i}" for i in range(len(coefficients))]
        else:
            feature_names = self.feature_names
        
        # Calculate feature contributions (simplified - would need actual feature values)
        feature_contributions = []
        for i, (name, coef) in enumerate(zip(feature_names, coefficients)):
            # Simplified contribution calculation
            contribution = float(coef) * 1.0  # Would need actual feature value here
            feature_contributions.append({
                "name": name,
                "contribution": contribution,
                "coefficient": float(coef)
            })
        
        # Sort by absolute contribution
        feature_contributions.sort(key=lambda x: abs(x["contribution"]), reverse=True)
        
        total_contribution = sum(f["contribution"] for f in feature_contributions)
        predicted_score = intercept + total_contribution
        
        return {
            "word": word.value,
            "plate": plate.value,
            "predicted_score": float(predicted_score),
            "explanation": {
                "intercept": intercept,
                "total_contribution": float(total_contribution),
                "verification_score": float(predicted_score),
                "top_contributing_features": feature_contributions[:top_k],
                "total_active_features": len([f for f in feature_contributions if abs(f["contribution"]) > 0.001])
            }
        }


class MemoryCacheManager(CacheManager):
    """Simple in-memory cache manager."""
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        return self._cache.get(key)
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache."""
        # Simple implementation ignores TTL for now
        self._cache[key] = value
    
    async def delete(self, key: str) -> None:
        """Delete value from cache."""
        self._cache.pop(key, None)
    
    async def clear(self) -> None:
        """Clear all cache."""
        self._cache.clear()


class SimpleFeatureExtractor(FeatureExtractor):
    """Simple feature extractor implementation."""
    
    def __init__(self, word_repository):
        self.word_repository = word_repository
    
    async def extract_features(self, word: Word, plate: LicensePlate) -> Dict[str, Any]:
        """Extract features for a word-plate combination."""
        # Simple feature extraction
        frequency = await self.word_repository.get_word_frequency(word)
        
        return {
            "word_length": len(word),
            "plate_length": len(plate),
            "word_frequency": frequency.value if frequency else 0,
            "character_overlap": len(set(word.value) & set(plate.value.lower())),
            "word": word.value,
            "plate": plate.value
        }
    
    async def build_corpus_statistics(self) -> CorpusStatistics:
        """Build comprehensive corpus statistics."""
        all_words = await self.word_repository.get_all_words()
        
        # Generate some sample plates for statistics
        sample_plates = ["ABC", "DEF", "GHI", "JKL", "MNO"]
        
        plate_word_counts = {}
        dataset_words = list(all_words.keys())[:1000]  # First 1000 words as sample
        
        for plate_str in sample_plates:
            plate = LicensePlate(plate_str)
            count = 0
            for word in all_words.keys():
                if word.matches_plate(plate):
                    count += 1
            plate_word_counts[plate_str] = count
        
        # Word frequency distribution
        freq_distribution = {}
        for word, freq in all_words.items():
            freq_bucket = f"{freq.value // 1000 * 1000}-{(freq.value // 1000 + 1) * 1000}"
            freq_distribution[freq_bucket] = freq_distribution.get(freq_bucket, 0) + 1
        
        return CorpusStatistics(
            total_plates=len(sample_plates),
            total_unique_words=len(all_words),
            dataset_words=[word.value for word in dataset_words],
            plate_word_counts=plate_word_counts,
            word_frequency_distribution=freq_distribution
        )
    
    async def build_corpus_features(self) -> CorpusFeatures:
        """Build pre-computed features for all word-plate combinations."""
        # This would be very expensive in a real implementation
        # For now, return a minimal set
        
        sample_features = {
            "ambulance:abc": {
                "word_length": 9,
                "plate_length": 3,
                "word_frequency": 5000,
                "character_overlap": 3
            }
        }
        
        return CorpusFeatures(
            features=sample_features,
            metadata={"feature_count": len(sample_features)}
        )
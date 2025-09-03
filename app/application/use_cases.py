"""
Application use cases - High-level business operations.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from .interfaces import (
    LLMClient, FeatureExtractor, ModelPredictor, WordSolver, 
    CombinationGenerator, CacheManager
)
from ..domain.entities import (
    WordScore, ScoringSession, CorpusStatistics, CorpusFeatures,
    ScoringSystemStatus, ModelAvailability
)
from ..domain.value_objects import (
    Word, LicensePlate, ModelName, SessionId, Score
)
from ..infrastructure.repositories import (
    WordRepository, ScoringRepository, CorpusRepository
)

logger = logging.getLogger(__name__)


class ScoreWordUseCase:
    """Use case for scoring a word against a license plate."""
    
    def __init__(self, 
                 llm_client: LLMClient,
                 scoring_repository: ScoringRepository,
                 word_repository: WordRepository):
        self.llm_client = llm_client
        self.scoring_repository = scoring_repository
        self.word_repository = word_repository
    
    async def execute(self, 
                     word: Word, 
                     plate: LicensePlate, 
                     models: List[ModelName]) -> WordScore:
        """Score a word with multiple models."""
        
        # Validate word matches plate
        if not word.matches_plate(plate):
            raise ValueError(f"Word '{word.value}' does not match plate '{plate.value}'")
        
        # Get word frequency
        frequency = await self.word_repository.get_word_frequency(word)
        if frequency is None:
            raise ValueError(f"Word '{word.value}' not found in dictionary")
        
        # Score with each model
        individual_scores = []
        for model in models:
            # Check cache first
            cached_score = await self.scoring_repository.get_word_score(word, plate, model)
            
            if cached_score:
                individual_scores.append(cached_score)
                logger.debug(f"Using cached score for {word.value}:{plate.value}:{model.value}")
            else:
                # Generate new score
                try:
                    score = await self.llm_client.generate_score(word, plate, model)
                    individual_scores.append(score)
                    logger.info(f"Generated new score for {word.value}:{plate.value}:{model.value}")
                except Exception as e:
                    logger.error(f"Failed to score {word.value} with {model.value}: {e}")
                    continue
        
        # Create word score
        word_score = WordScore(
            word=word,
            plate=plate,
            individual_scores=individual_scores,
            frequency=frequency
        )
        
        # Save to repository
        await self.scoring_repository.save_word_score(word_score)
        
        return word_score


class PredictWordScoreUseCase:
    """Use case for predicting word score using ML model."""
    
    def __init__(self,
                 model_predictor: ModelPredictor,
                 feature_extractor: FeatureExtractor,
                 word_repository: WordRepository):
        self.model_predictor = model_predictor
        self.feature_extractor = feature_extractor
        self.word_repository = word_repository
    
    async def execute(self, word: Word, plate: LicensePlate) -> Score:
        """Predict score for a word-plate combination."""
        
        # Note: No need to validate word matches plate - caller should ensure validity
        
        # Check if word exists in dictionary
        frequency = await self.word_repository.get_word_frequency(word)
        if frequency is None:
            raise ValueError(f"Word '{word.value}' not found in dictionary")
        
        # Ensure model is loaded
        if not await self.model_predictor.is_model_loaded():
            await self.model_predictor.load_model()
        
        # Predict score
        score = await self.model_predictor.predict_score(word, plate)
        
        logger.info(f"Predicted score for {word.value}:{plate.value} = {score}")
        return score


class FindWordsForPlateUseCase:
    """Use case for finding words that match a license plate."""
    
    def __init__(self, word_solver: WordSolver):
        self.word_solver = word_solver
    
    async def execute(self, 
                     plate: LicensePlate, 
                     strategy: str = "subsequence",
                     limit: Optional[int] = None) -> List[tuple[Word, int]]:
        """Find words matching a license plate."""
        
        matches = await self.word_solver.find_matching_words(plate, strategy)
        
        if limit:
            matches = matches[:limit]
        
        logger.info(f"Found {len(matches)} words for plate {plate.value}")
        return matches


class CreateScoringSessionUseCase:
    """Use case for creating and managing scoring sessions."""
    
    def __init__(self,
                 llm_client: LLMClient,
                 word_solver: WordSolver,
                 combination_generator: CombinationGenerator,
                 scoring_repository: ScoringRepository,
                 word_repository: WordRepository):
        self.llm_client = llm_client
        self.word_solver = word_solver
        self.combination_generator = combination_generator
        self.scoring_repository = scoring_repository
        self.word_repository = word_repository
    
    async def execute(self,
                     num_plates: int,
                     words_per_plate: int,
                     plate_length: int,
                     models: List[ModelName]) -> ScoringSession:
        """Create and execute a scoring session."""
        
        # Create session
        session_id = SessionId.generate()
        session = ScoringSession(
            session_id=session_id,
            models_used=models,
            results=[]
        )
        
        try:
            # Generate random plates
            plates = await self.combination_generator.generate_combinations(
                character_set="abcdefghijklmnopqrstuvwxyz",
                length=plate_length,
                count=num_plates
            )
            
            # Score words for each plate
            for plate in plates:
                # Get random words for this plate
                words = await self.word_solver.get_random_words_for_plate(
                    plate, words_per_plate
                )
                
                # Score each word
                for word in words:
                    try:
                        # Get word frequency
                        frequency = await self.word_repository.get_word_frequency(word)
                        if frequency is None:
                            continue
                        
                        # Score with all models
                        individual_scores = []
                        for model in models:
                            score = await self.llm_client.generate_score(word, plate, model)
                            individual_scores.append(score)
                        
                        # Create word score
                        word_score = WordScore(
                            word=word,
                            plate=plate,
                            individual_scores=individual_scores,
                            frequency=frequency
                        )
                        
                        session.add_result(word_score)
                        
                        # Save partial results
                        await self.scoring_repository.save_word_score(word_score)
                        
                    except Exception as e:
                        logger.error(f"Failed to score {word.value} for {plate.value}: {e}")
                        session.mark_interrupted()
                        break
                
                if session.interrupted:
                    break
            
            # Mark session complete
            session.mark_completed()
            
        except Exception as e:
            logger.error(f"Scoring session failed: {e}")
            session.mark_interrupted()
        
        # Save session
        await self.scoring_repository.save_session(session)
        
        return session


class ManageCorpusUseCase:
    """Use case for managing corpus statistics and features."""
    
    def __init__(self,
                 feature_extractor: FeatureExtractor,
                 corpus_repository: CorpusRepository,
                 cache_manager: Optional[CacheManager] = None):
        self.feature_extractor = feature_extractor
        self.corpus_repository = corpus_repository
        self.cache_manager = cache_manager
    
    async def get_corpus_statistics(self, force_rebuild: bool = False) -> CorpusStatistics:
        """Get or build corpus statistics."""
        
        if not force_rebuild:
            # Try to get from repository first
            stats = await self.corpus_repository.get_statistics()
            if stats:
                logger.info("Retrieved corpus statistics from repository")
                return stats
        
        # Build new statistics
        logger.info("Building corpus statistics...")
        stats = await self.feature_extractor.build_corpus_statistics()
        
        # Save to repository
        await self.corpus_repository.save_statistics(stats)
        
        # Clear cache if available
        if self.cache_manager:
            await self.cache_manager.clear()
        
        logger.info("Corpus statistics built and saved")
        return stats
    
    async def get_corpus_features(self, force_rebuild: bool = False) -> CorpusFeatures:
        """Get or build corpus features."""
        
        if not force_rebuild:
            # Try to get from repository first
            features = await self.corpus_repository.get_features()
            if features:
                logger.info("Retrieved corpus features from repository")
                return features
        
        # Build new features (expensive operation)
        logger.info("Building corpus features (this may take a while)...")
        features = await self.feature_extractor.build_corpus_features()
        
        # Save to repository
        await self.corpus_repository.save_features(features)
        
        # Clear cache if available
        if self.cache_manager:
            await self.cache_manager.clear()
        
        logger.info("Corpus features built and saved")
        return features


class CheckSystemHealthUseCase:
    """Use case for checking system health."""
    
    def __init__(self,
                 llm_client: LLMClient,
                 model_predictor: ModelPredictor):
        self.llm_client = llm_client
        self.model_predictor = model_predictor
    
    async def execute(self, models: List[ModelName]) -> ScoringSystemStatus:
        """Check overall system health."""
        
        # Check LLM service
        ollama_running = await self.llm_client.is_service_healthy()
        
        # Check each model
        model_statuses = []
        for model in models:
            availability = await self.llm_client.check_model_availability(model)
            model_statuses.append(availability)
        
        # Check prediction model
        prediction_model_loaded = await self.model_predictor.is_model_loaded()
        
        return ScoringSystemStatus(
            ollama_running=ollama_running,
            models=model_statuses,
            cache_enabled=True,  # Always enabled in this implementation
            active_sessions=0  # TODO: Track active sessions
        )
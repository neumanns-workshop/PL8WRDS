"""
Word scoring service using LLM models via Ollama.
"""

import json
import logging
import random
import statistics
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import asyncio
import aiofiles

from ..models.scoring import (
    ScoringModel, 
    IndividualScore, 
    WordScore, 
    ScoringSession,
    ModelAvailability,
    ScoringSystemStatus,
    LLMScoringResponse,
    SCORING_PROMPT_TEMPLATE
)
from ..services.word_service import word_service
from ..services.solver_service import solve_combination
from ..services.combination_generator import generate_combinations
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from tools.ollama_client import OllamaClient, check_ollama_health, check_model_available, auto_setup_model

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScoringCache:
    """Persistent cache for scoring results."""
    
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.session_cache_file = self.cache_dir / "scoring_sessions.json"
        self.word_cache_file = self.cache_dir / "word_scores.json"
        
        # In-memory caches
        self._sessions: Dict[str, dict] = {}
        self._word_scores: Dict[str, dict] = {}
        
        # Load existing cache
        self._load_cache()
    
    def _load_cache(self):
        """Load cache from disk."""
        try:
            if self.session_cache_file.exists():
                with open(self.session_cache_file, 'r') as f:
                    self._sessions = json.load(f)
                    
            if self.word_cache_file.exists():
                with open(self.word_cache_file, 'r') as f:
                    self._word_scores = json.load(f)
                    
            logger.info(f"Loaded {len(self._sessions)} sessions and {len(self._word_scores)} word scores from cache")
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")
    
    async def save_cache(self):
        """Save cache to disk asynchronously."""
        try:
            # Create files if they don't exist
            if not self.session_cache_file.exists():
                self.session_cache_file.touch()
            if not self.word_cache_file.exists():
                self.word_cache_file.touch()
                
            # Save sessions
            async with aiofiles.open(self.session_cache_file, 'r+') as f:
                await f.truncate(0)
                await f.seek(0)
                await f.write(json.dumps(self._sessions, indent=2, default=str))
            
            # Save word scores  
            async with aiofiles.open(self.word_cache_file, 'r+') as f:
                await f.truncate(0)
                await f.seek(0)
                await f.write(json.dumps(self._word_scores, indent=2, default=str))
                
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
    
    def get_word_score(self, word: str, combination: str, model: ScoringModel) -> Optional[IndividualScore]:
        """Get cached score for word-combination-model."""
        cache_key = f"{word.lower()}:{combination.lower()}:{model.value}"
        if cache_key in self._word_scores:
            data = self._word_scores[cache_key]
            return IndividualScore(**data)
        return None
    
    def set_word_score(self, word: str, combination: str, score: IndividualScore):
        """Cache score for word-combination-model."""
        cache_key = f"{word.lower()}:{combination.lower()}:{score.model.value}"
        self._word_scores[cache_key] = score.dict()
    
    def get_session(self, session_id: str) -> Optional[dict]:
        """Get cached session."""
        return self._sessions.get(session_id)
    
    def set_session(self, session: ScoringSession):
        """Cache session."""
        self._sessions[session.session_id] = session.dict()

class WordScoringService:
    """Service for scoring words using LLM models."""
    
    def __init__(self):
        self.ollama_client = OllamaClient()
        self.cache = ScoringCache()
        self.active_sessions: Dict[str, ScoringSession] = {}
        
    async def check_system_status(self) -> ScoringSystemStatus:
        """Check the status of the scoring system."""
        ollama_running = check_ollama_health()
        
        model_statuses = []
        for model in ScoringModel:
            try:
                available = check_model_available(model.value) if ollama_running else False
                model_statuses.append(ModelAvailability(
                    model=model,
                    available=available
                ))
            except Exception as e:
                model_statuses.append(ModelAvailability(
                    model=model,
                    available=False,
                    error_message=str(e)
                ))
        
        return ScoringSystemStatus(
            ollama_running=ollama_running,
            models=model_statuses,
            cache_enabled=True,
            active_sessions=len(self.active_sessions)
        )
    
    async def ensure_models_available(self, models: List[ScoringModel]) -> List[ScoringModel]:
        """Ensure models are available, downloading if needed."""
        available_models = []
        
        for model in models:
            try:
                if auto_setup_model(model.value):
                    available_models.append(model)
                    logger.info(f"Model {model.value} is ready")
                else:
                    logger.warning(f"Model {model.value} is not available")
            except Exception as e:
                logger.error(f"Failed to setup model {model.value}: {e}")
        
        return available_models
    
    async def score_word(self, word: str, combination: str, model: ScoringModel) -> IndividualScore:
        """Score a single word with a single model."""
        # Check cache first
        cached_score = self.cache.get_word_score(word, combination, model)
        if cached_score:
            logger.debug(f"Using cached score for {word}:{combination}:{model.value}")
            return cached_score
        
        # Generate prompt
        prompt = SCORING_PROMPT_TEMPLATE.format(
            combination=combination.upper(),
            word=word
        )
        
        try:
            # Get LLM response
            response = self.ollama_client.generate_response(
                model=model.value,
                prompt=prompt,
                response_model=LLMScoringResponse
            )
            
            # Create score object
            score = IndividualScore(
                model=model,
                score=response.score,
                reasoning=response.reasoning
            )
            
            # Cache the result
            self.cache.set_word_score(word, combination, score)
            await self.cache.save_cache()
            
            logger.info(f"Scored {word} for {combination} with {model.value}: {response.score}/100")
            return score
            
        except Exception as e:
            logger.error(f"Failed to score {word} with {model.value}: {e}")
            # Return a default score in case of error
            return IndividualScore(
                model=model,
                score=0,
                reasoning=f"Error scoring word: {str(e)}"
            )
    
    async def score_word_with_models(self, word: str, combination: str, models: List[ScoringModel]) -> WordScore:
        """Score a word with multiple models."""
        # Ensure models are available
        available_models = await self.ensure_models_available(models)
        
        if not available_models:
            logger.error("No models available for scoring")
            return WordScore(
                word=word,
                combination=combination,
                scores=[],
                frequency=word_service.lookup_word(word)
            )
        
        # Score with each model
        scores = []
        for model in available_models:
            try:
                score = await self.score_word(word, combination, model)
                scores.append(score)
            except Exception as e:
                logger.error(f"Failed to score with {model.value}: {e}")
        
        # Calculate aggregate score
        aggregate_score = None
        if scores:
            score_values = [s.score for s in scores]
            aggregate_score = statistics.mean(score_values)
        
        return WordScore(
            word=word,
            combination=combination,
            scores=scores,
            aggregate_score=aggregate_score,
            frequency=word_service.lookup_word(word)
        )
    
    async def get_random_words_for_combination(self, combination: str, count: int = 5, strategy: str = "frequency_weighted") -> List[str]:
        """Get random valid words for a combination using different sampling strategies."""
        # Use the existing solver to find all valid words
        matches = solve_combination(combination, "subsequence")
        
        if not matches:
            return []
        
        if strategy == "uniform":
            # Old behavior: equal probability for all words
            words = [word for word, freq in matches]
            selected = random.sample(words, min(count, len(words)))
            
        elif strategy == "frequency_weighted":
            # New behavior: probability proportional to frequency (common words more likely)
            words, frequencies = zip(*matches)
            
            # Use frequencies as weights for random selection
            selected = []
            words_list = list(words)
            freq_list = list(frequencies)
            
            for _ in range(min(count, len(words_list))):
                # Weighted random choice
                chosen_idx = random.choices(range(len(words_list)), weights=freq_list, k=1)[0]
                selected.append(words_list[chosen_idx])
                
                # Remove selected word to avoid duplicates
                words_list.pop(chosen_idx)
                freq_list.pop(chosen_idx)
                
        elif strategy == "mixed":
            # Balanced: 70% frequency-weighted, 30% uniform rare words
            words, frequencies = zip(*matches)
            words_list = list(words)
            freq_list = list(frequencies)
            
            common_count = int(count * 0.7)
            rare_count = count - common_count
            
            selected = []
            
            # Select common words (frequency-weighted)
            for _ in range(min(common_count, len(words_list))):
                chosen_idx = random.choices(range(len(words_list)), weights=freq_list, k=1)[0]
                selected.append(words_list[chosen_idx])
                words_list.pop(chosen_idx)
                freq_list.pop(chosen_idx)
            
            # Select rare words (uniform from remaining)
            if words_list and rare_count > 0:
                rare_selected = random.sample(words_list, min(rare_count, len(words_list)))
                selected.extend(rare_selected)
                
        else:
            raise ValueError(f"Unknown sampling strategy: {strategy}")
        
        logger.info(f"Selected {len(selected)} {strategy} words for combination '{combination}': {selected}")
        return selected
    
    async def create_scoring_session(self, cache_key: Optional[str] = None) -> ScoringSession:
        """Create a new scoring session."""
        session_id = str(uuid.uuid4())
        session = ScoringSession(
            session_id=session_id,
            cache_key=cache_key
        )
        
        self.active_sessions[session_id] = session
        self.cache.set_session(session)
        
        logger.info(f"Created scoring session {session_id}")
        return session
    
    async def get_session(self, session_id: str) -> Optional[ScoringSession]:
        """Get an existing session."""
        if session_id in self.active_sessions:
            return self.active_sessions[session_id]
        
        # Try to load from cache
        cached_data = self.cache.get_session(session_id)
        if cached_data:
            session = ScoringSession(**cached_data)
            self.active_sessions[session_id] = session
            return session
        
        return None
    
    async def update_session(self, session: ScoringSession):
        """Update session in memory and cache."""
        self.active_sessions[session.session_id] = session
        self.cache.set_session(session)
        await self.cache.save_cache()
    
    async def score_random_words(self, 
                                num_combinations: int,
                                words_per_combination: int,
                                combination_length: int,
                                models: List[ScoringModel],
                                cache_key: Optional[str] = None) -> ScoringSession:
        """Score random words from random combinations."""
        session = await self.create_scoring_session(cache_key)
        session.models_used = models
        
        try:
            # Generate random combinations
            random_combinations = generate_combinations(
                character_set="abcdefghijklmnopqrstuvwxyz",
                length=combination_length,
                mode="batch",
                batch_size=num_combinations
            )
            
            logger.info(f"Generated {len(random_combinations)} random combinations")
            
            # Score words for each combination
            for combination in random_combinations:
                logger.info(f"Processing combination: {combination}")
                
                # Get random words for this combination
                words = await self.get_random_words_for_combination(combination, words_per_combination)
                
                # Score each word
                for word in words:
                    try:
                        word_score = await self.score_word_with_models(word, combination, models)
                        session.results.append(word_score)
                        session.total_scores += len(word_score.scores)
                        
                        # Update session periodically
                        await self.update_session(session)
                        
                    except Exception as e:
                        logger.error(f"Failed to score word '{word}' for combination '{combination}': {e}")
                        session.interrupted = True
                        break
                
                if session.interrupted:
                    break
            
            session.end_time = datetime.utcnow()
            await self.update_session(session)
            
            logger.info(f"Completed scoring session {session.session_id} with {len(session.results)} word scores")
            
        except Exception as e:
            logger.error(f"Scoring session {session.session_id} failed: {e}")
            session.interrupted = True
            session.end_time = datetime.utcnow()
            await self.update_session(session)
        
        return session

# Global service instance
scoring_service = WordScoringService()
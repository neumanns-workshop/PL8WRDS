"""
Repository implementations for data access.
"""

import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import aiofiles

from ..domain.entities import (
    WordMatch, WordScore, ScoringSession, CorpusStatistics, 
    CorpusFeatures, IndividualScore
)
from ..domain.value_objects import (
    Word, LicensePlate, SessionId, ModelName, Frequency, 
    FilePath, DirectoryPath
)

logger = logging.getLogger(__name__)


class WordRepository(ABC):
    """Abstract repository for word data access."""
    
    @abstractmethod
    async def get_word_frequency(self, word: Word) -> Optional[Frequency]:
        """Get frequency of a word."""
        pass
    
    @abstractmethod
    async def get_all_words(self) -> Dict[Word, Frequency]:
        """Get all words and their frequencies."""
        pass
    
    @abstractmethod
    async def find_words_matching_plate(self, plate: LicensePlate) -> List[WordMatch]:
        """Find all words that match a license plate pattern."""
        pass


class ScoringRepository(ABC):
    """Abstract repository for scoring data."""
    
    @abstractmethod
    async def save_word_score(self, word_score: WordScore) -> None:
        """Save a word score."""
        pass
    
    @abstractmethod
    async def get_word_score(self, word: Word, plate: LicensePlate, model: ModelName) -> Optional[IndividualScore]:
        """Get a cached individual score."""
        pass
    
    @abstractmethod
    async def save_session(self, session: ScoringSession) -> None:
        """Save a scoring session."""
        pass
    
    @abstractmethod
    async def get_session(self, session_id: SessionId) -> Optional[ScoringSession]:
        """Get a scoring session."""
        pass


class CorpusRepository(ABC):
    """Abstract repository for corpus data."""
    
    @abstractmethod
    async def save_statistics(self, statistics: CorpusStatistics) -> None:
        """Save corpus statistics."""
        pass
    
    @abstractmethod
    async def get_statistics(self) -> Optional[CorpusStatistics]:
        """Get corpus statistics."""
        pass
    
    @abstractmethod
    async def save_features(self, features: CorpusFeatures) -> None:
        """Save corpus features."""
        pass
    
    @abstractmethod
    async def get_features(self) -> Optional[CorpusFeatures]:
        """Get corpus features."""
        pass


# JSON-based implementations

class JsonWordRepository(WordRepository):
    """JSON file-based word repository."""
    
    def __init__(self, data_file_path: FilePath):
        self.data_file_path = data_file_path
        self._words_cache: Optional[Dict[Word, Frequency]] = None
    
    async def _load_words(self) -> Dict[Word, Frequency]:
        """Load words from JSON file."""
        if self._words_cache is not None:
            return self._words_cache
        
        try:
            async with aiofiles.open(self.data_file_path.value, 'r') as f:
                content = await f.read()
                data = json.loads(content)
            
            self._words_cache = {}
            for item in data:
                word = Word(item['word'])
                frequency = Frequency(item['frequency'])
                self._words_cache[word] = frequency
            
            logger.info(f"Loaded {len(self._words_cache)} words from {self.data_file_path.value}")
            return self._words_cache
            
        except Exception as e:
            logger.error(f"Failed to load words from {self.data_file_path.value}: {e}")
            return {}
    
    async def get_word_frequency(self, word: Word) -> Optional[Frequency]:
        """Get frequency of a word."""
        words = await self._load_words()
        return words.get(word)
    
    async def get_all_words(self) -> Dict[Word, Frequency]:
        """Get all words and their frequencies."""
        return await self._load_words()
    
    async def find_words_matching_plate(self, plate: LicensePlate) -> List[WordMatch]:
        """Find all words that match a license plate pattern."""
        words = await self._load_words()
        matches = []
        
        for word, frequency in words.items():
            if word.matches_plate(plate):
                matches.append(WordMatch(word=word, plate=plate, frequency=frequency))
        
        return matches


class JsonScoringRepository(ScoringRepository):
    """JSON file-based scoring repository."""
    
    def __init__(self, cache_dir: DirectoryPath):
        self.cache_dir = cache_dir
        self.session_cache_file = cache_dir.join("scoring_sessions.json")
        self.word_cache_file = cache_dir.join("word_scores.json")
        
        self._sessions_cache: Dict[str, dict] = {}
        self._word_scores_cache: Dict[str, dict] = {}
        self._loaded = False
    
    async def _ensure_cache_loaded(self):
        """Ensure cache is loaded from disk."""
        if self._loaded:
            return
        
        try:
            # Load sessions
            if Path(self.session_cache_file.value).exists():
                async with aiofiles.open(self.session_cache_file.value, 'r') as f:
                    content = await f.read()
                    self._sessions_cache = json.loads(content)
            
            # Load word scores
            if Path(self.word_cache_file.value).exists():
                async with aiofiles.open(self.word_cache_file.value, 'r') as f:
                    content = await f.read()
                    self._word_scores_cache = json.loads(content)
            
            self._loaded = True
            logger.info(f"Loaded {len(self._sessions_cache)} sessions and {len(self._word_scores_cache)} word scores")
            
        except Exception as e:
            logger.error(f"Failed to load scoring cache: {e}")
    
    async def _save_cache(self):
        """Save cache to disk."""
        try:
            # Ensure directory exists
            Path(self.cache_dir.value).mkdir(parents=True, exist_ok=True)
            
            # Save sessions
            async with aiofiles.open(self.session_cache_file.value, 'w') as f:
                content = json.dumps(self._sessions_cache, indent=2, default=str)
                await f.write(content)
            
            # Save word scores
            async with aiofiles.open(self.word_cache_file.value, 'w') as f:
                content = json.dumps(self._word_scores_cache, indent=2, default=str)
                await f.write(content)
                
        except Exception as e:
            logger.error(f"Failed to save scoring cache: {e}")
    
    def _make_word_score_key(self, word: Word, plate: LicensePlate, model: ModelName) -> str:
        """Create cache key for word score."""
        return f"{word.value}:{plate.value}:{model.value}"
    
    async def save_word_score(self, word_score: WordScore) -> None:
        """Save a word score."""
        await self._ensure_cache_loaded()
        
        for individual_score in word_score.individual_scores:
            key = self._make_word_score_key(word_score.word, word_score.plate, individual_score.model)
            self._word_scores_cache[key] = {
                "model": individual_score.model.value,
                "score": individual_score.score.value,
                "reasoning": individual_score.reasoning.value,
                "created_at": individual_score.created_at.isoformat()
            }
        
        await self._save_cache()
    
    async def get_word_score(self, word: Word, plate: LicensePlate, model: ModelName) -> Optional[IndividualScore]:
        """Get a cached individual score."""
        await self._ensure_cache_loaded()
        
        key = self._make_word_score_key(word, plate, model)
        data = self._word_scores_cache.get(key)
        
        if not data:
            return None
        
        from ..domain.value_objects import Score, Reasoning
        return IndividualScore(
            model=model,
            score=Score(data["score"]),
            reasoning=Reasoning(data["reasoning"]),
            created_at=datetime.fromisoformat(data["created_at"])
        )
    
    async def save_session(self, session: ScoringSession) -> None:
        """Save a scoring session."""
        await self._ensure_cache_loaded()
        
        session_data = {
            "session_id": session.session_id.value,
            "models_used": [model.value for model in session.models_used],
            "cache_key": session.cache_key.value if session.cache_key else None,
            "created_at": session.created_at.isoformat(),
            "end_time": session.end_time.isoformat() if session.end_time else None,
            "interrupted": session.interrupted,
            "total_scores": session.total_scores,
            "results_count": len(session.results)
        }
        
        self._sessions_cache[session.session_id.value] = session_data
        await self._save_cache()
    
    async def get_session(self, session_id: SessionId) -> Optional[ScoringSession]:
        """Get a scoring session."""
        await self._ensure_cache_loaded()
        
        data = self._sessions_cache.get(session_id.value)
        if not data:
            return None
        
        from ..domain.value_objects import CacheKey
        
        # Note: This implementation doesn't store full results to keep cache manageable
        # In a real system, you might store results separately or use a proper database
        return ScoringSession(
            session_id=session_id,
            models_used=[ModelName(model) for model in data["models_used"]],
            results=[],  # Not stored in this simple implementation
            cache_key=CacheKey(data["cache_key"]) if data["cache_key"] else None,
            created_at=datetime.fromisoformat(data["created_at"]),
            end_time=datetime.fromisoformat(data["end_time"]) if data["end_time"] else None,
            interrupted=data["interrupted"],
            total_scores=data["total_scores"]
        )


class JsonCorpusRepository(CorpusRepository):
    """JSON file-based corpus repository."""
    
    def __init__(self, cache_dir: DirectoryPath):
        self.cache_dir = cache_dir
        self.stats_file = cache_dir.join("corpus_stats.json")
        self.features_file = cache_dir.join("corpus_features.json")
    
    async def save_statistics(self, statistics: CorpusStatistics) -> None:
        """Save corpus statistics."""
        try:
            # Ensure directory exists
            Path(self.cache_dir.value).mkdir(parents=True, exist_ok=True)
            
            data = {
                "metadata": {
                    "generated_at": statistics.generated_at.isoformat(),
                    "version": "1.0"
                },
                "stats": {
                    "total_plates": statistics.total_plates,
                    "total_unique_words": statistics.total_unique_words,
                    "dataset_words": statistics.dataset_words,
                    "plate_word_counts": statistics.plate_word_counts,
                    "word_frequency_distribution": statistics.word_frequency_distribution
                }
            }
            
            async with aiofiles.open(self.stats_file.value, 'w') as f:
                content = json.dumps(data, indent=2)
                await f.write(content)
                
            logger.info(f"Saved corpus statistics to {self.stats_file.value}")
            
        except Exception as e:
            logger.error(f"Failed to save corpus statistics: {e}")
            raise
    
    async def get_statistics(self) -> Optional[CorpusStatistics]:
        """Get corpus statistics."""
        try:
            if not Path(self.stats_file.value).exists():
                return None
            
            async with aiofiles.open(self.stats_file.value, 'r') as f:
                content = await f.read()
                data = json.loads(content)
            
            stats_data = data["stats"]
            return CorpusStatistics(
                total_plates=stats_data["total_plates"],
                total_unique_words=stats_data["total_unique_words"],
                dataset_words=stats_data["dataset_words"],
                plate_word_counts=stats_data["plate_word_counts"],
                word_frequency_distribution=stats_data["word_frequency_distribution"],
                generated_at=datetime.fromisoformat(data["metadata"]["generated_at"])
            )
            
        except Exception as e:
            logger.error(f"Failed to load corpus statistics: {e}")
            return None
    
    async def save_features(self, features: CorpusFeatures) -> None:
        """Save corpus features."""
        try:
            # Ensure directory exists
            Path(self.cache_dir.value).mkdir(parents=True, exist_ok=True)
            
            data = {
                "metadata": {
                    "generated_at": features.generated_at.isoformat(),
                    "version": "1.0",
                    **features.metadata
                },
                "features": features.features
            }
            
            async with aiofiles.open(self.features_file.value, 'w') as f:
                content = json.dumps(data, indent=2)
                await f.write(content)
                
            logger.info(f"Saved corpus features to {self.features_file.value}")
            
        except Exception as e:
            logger.error(f"Failed to save corpus features: {e}")
            raise
    
    async def get_features(self) -> Optional[CorpusFeatures]:
        """Get corpus features."""
        try:
            if not Path(self.features_file.value).exists():
                return None
            
            async with aiofiles.open(self.features_file.value, 'r') as f:
                content = await f.read()
                data = json.loads(content)
            
            return CorpusFeatures(
                features=data["features"],
                metadata=data["metadata"],
                generated_at=datetime.fromisoformat(data["metadata"]["generated_at"])
            )
            
        except Exception as e:
            logger.error(f"Failed to load corpus features: {e}")
            return None
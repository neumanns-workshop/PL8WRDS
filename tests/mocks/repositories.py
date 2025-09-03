"""
Mock repository implementations for testing.
"""

from typing import Dict, List, Optional
from datetime import datetime

from app.infrastructure.repositories import (
    WordRepository, ScoringRepository, CorpusRepository
)
from app.domain.entities import (
    WordMatch, WordScore, ScoringSession, CorpusStatistics,
    CorpusFeatures, IndividualScore
)
from app.domain.value_objects import (
    Word, LicensePlate, SessionId, ModelName, Frequency
)


class InMemoryWordRepository(WordRepository):
    """In-memory word repository for testing."""
    
    def __init__(self, initial_words: Optional[Dict[str, int]] = None):
        # Initialize with default test data
        default_words = {
            "ambulance": 5000,
            "albatross": 3000,
            "abstract": 4000,
            "beach": 2500,
            "cat": 8000,
            "dog": 6000,
            "elephant": 1500,
            "about": 9000,
            "cabin": 2000,
        }
        
        word_data = initial_words or default_words
        self._words = {
            Word(word): Frequency(freq) 
            for word, freq in word_data.items()
        }
        
    async def get_word_frequency(self, word: Word) -> Optional[Frequency]:
        """Get frequency of a word."""
        return self._words.get(word)
    
    async def get_all_words(self) -> Dict[Word, Frequency]:
        """Get all words and their frequencies."""
        return self._words.copy()
    
    async def find_words_matching_plate(self, plate: LicensePlate) -> List[WordMatch]:
        """Find all words that match a license plate pattern."""
        matches = []
        
        for word, frequency in self._words.items():
            if word.matches_plate(plate):
                matches.append(WordMatch(word=word, plate=plate, frequency=frequency))
        
        return matches
    
    # Helper methods for testing
    def add_word(self, word_str: str, frequency: int):
        """Add a word to the repository."""
        self._words[Word(word_str)] = Frequency(frequency)
    
    def remove_word(self, word_str: str):
        """Remove a word from the repository."""
        word = Word(word_str)
        if word in self._words:
            del self._words[word]
    
    def word_exists(self, word_str: str) -> bool:
        """Check if a word exists in the repository."""
        return Word(word_str) in self._words
    
    def get_word_count(self) -> int:
        """Get total number of words."""
        return len(self._words)


class InMemoryScoringRepository(ScoringRepository):
    """In-memory scoring repository for testing."""
    
    def __init__(self):
        self._word_scores: Dict[str, IndividualScore] = {}
        self._sessions: Dict[str, ScoringSession] = {}
    
    def _make_word_score_key(self, word: Word, plate: LicensePlate, model: ModelName) -> str:
        """Create cache key for word score."""
        return f"{word.value}:{plate.value}:{model.value}"
    
    async def save_word_score(self, word_score: WordScore) -> None:
        """Save a word score."""
        for individual_score in word_score.individual_scores:
            key = self._make_word_score_key(
                word_score.word, 
                word_score.plate, 
                individual_score.model
            )
            self._word_scores[key] = individual_score
    
    async def get_word_score(self, word: Word, plate: LicensePlate, model: ModelName) -> Optional[IndividualScore]:
        """Get a cached individual score."""
        key = self._make_word_score_key(word, plate, model)
        return self._word_scores.get(key)
    
    async def save_session(self, session: ScoringSession) -> None:
        """Save a scoring session."""
        self._sessions[session.session_id.value] = session
    
    async def get_session(self, session_id: SessionId) -> Optional[ScoringSession]:
        """Get a scoring session."""
        return self._sessions.get(session_id.value)
    
    # Helper methods for testing
    def get_session_count(self) -> int:
        """Get number of stored sessions."""
        return len(self._sessions)
    
    def get_word_score_count(self) -> int:
        """Get number of stored word scores."""
        return len(self._word_scores)
    
    def clear_all_data(self):
        """Clear all stored data."""
        self._word_scores.clear()
        self._sessions.clear()
    
    def get_all_sessions(self) -> List[ScoringSession]:
        """Get all stored sessions."""
        return list(self._sessions.values())
    
    def session_exists(self, session_id: str) -> bool:
        """Check if a session exists."""
        return session_id in self._sessions


class InMemoryCorpusRepository(CorpusRepository):
    """In-memory corpus repository for testing."""
    
    def __init__(self):
        self._statistics: Optional[CorpusStatistics] = None
        self._features: Optional[CorpusFeatures] = None
        self._save_count = 0
        self._load_count = 0
    
    async def save_statistics(self, statistics: CorpusStatistics) -> None:
        """Save corpus statistics."""
        self._statistics = statistics
        self._save_count += 1
    
    async def get_statistics(self) -> Optional[CorpusStatistics]:
        """Get corpus statistics."""
        self._load_count += 1
        return self._statistics
    
    async def save_features(self, features: CorpusFeatures) -> None:
        """Save corpus features."""
        self._features = features
        self._save_count += 1
    
    async def get_features(self) -> Optional[CorpusFeatures]:
        """Get corpus features."""
        self._load_count += 1
        return self._features
    
    # Helper methods for testing
    def has_statistics(self) -> bool:
        """Check if statistics are stored."""
        return self._statistics is not None
    
    def has_features(self) -> bool:
        """Check if features are stored."""
        return self._features is not None
    
    def clear_all_data(self):
        """Clear all stored data."""
        self._statistics = None
        self._features = None
    
    def get_save_count(self) -> int:
        """Get number of save operations."""
        return self._save_count
    
    def get_load_count(self) -> int:
        """Get number of load operations."""
        return self._load_count
    
    def reset_counters(self):
        """Reset operation counters."""
        self._save_count = 0
        self._load_count = 0


# Factory functions for creating pre-configured repositories

def create_populated_word_repository() -> InMemoryWordRepository:
    """Create a word repository with comprehensive test data."""
    word_data = {
        # High frequency words
        "the": 50000,
        "and": 45000,
        "a": 40000,
        "to": 38000,
        "of": 35000,
        
        # ABC pattern matches
        "ambulance": 5000,
        "albatross": 3000,
        "abstract": 4000,
        "about": 9000,
        "absorb": 2500,
        
        # DEF pattern matches  
        "defeat": 3500,
        "defend": 4200,
        "define": 5500,
        "deform": 1800,
        
        # GHI pattern matches
        "garage": 2800,
        "graphics": 3200,
        "geographic": 2200,
        
        # Common words that don't match ABC
        "cat": 8000,
        "dog": 6000,
        "elephant": 1500,
        "beach": 2500,
        "cabin": 2000,
        "xyz": 100,
        
        # Edge cases
        "a": 40000,  # Single letter
        "bb": 500,   # Repeated letters
        "aardvark": 800,  # Double letters at start
    }
    
    return InMemoryWordRepository(word_data)

def create_empty_word_repository() -> InMemoryWordRepository:
    """Create an empty word repository."""
    return InMemoryWordRepository({})

def create_minimal_word_repository() -> InMemoryWordRepository:
    """Create a word repository with minimal test data."""
    word_data = {
        "ambulance": 5000,
        "cat": 8000,
        "xyz": 100,
    }
    return InMemoryWordRepository(word_data)

def create_scoring_repository_with_data() -> InMemoryScoringRepository:
    """Create a scoring repository with some pre-existing data."""
    from tests.factories import WordScoreFactory, ScoringSessionFactory
    
    repo = InMemoryScoringRepository()
    
    # Add some sample word scores
    sample_scores = [
        WordScoreFactory(),
        WordScoreFactory(),
        WordScoreFactory(),
    ]
    
    # Add some sample sessions
    sample_sessions = [
        ScoringSessionFactory(),
        ScoringSessionFactory(),
    ]
    
    # Note: In a real test, you'd use async context or asyncio.run
    # This is simplified for the factory function
    import asyncio
    
    async def populate_data():
        for score in sample_scores:
            await repo.save_word_score(score)
        for session in sample_sessions:
            await repo.save_session(session)
    
    # This would typically be called in test setup
    # asyncio.run(populate_data())
    
    return repo

def create_corpus_repository_with_data() -> InMemoryCorpusRepository:
    """Create a corpus repository with pre-existing data."""
    from tests.factories import CorpusStatisticsFactory, CorpusFeaturesFactory
    
    repo = InMemoryCorpusRepository()
    
    # Pre-populate with sample data
    sample_stats = CorpusStatisticsFactory()
    sample_features = CorpusFeaturesFactory()
    
    import asyncio
    
    async def populate_data():
        await repo.save_statistics(sample_stats)
        await repo.save_features(sample_features)
    
    # This would typically be called in test setup
    # asyncio.run(populate_data())
    
    return repo
"""
Domain entities representing core business concepts.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

from .value_objects import (
    Word, LicensePlate, Score, Frequency, ModelName, 
    SessionId, CacheKey, Reasoning, AggregateScore
)


@dataclass
class WordMatch:
    """Represents a word that matches a license plate pattern."""
    word: Word
    plate: LicensePlate
    frequency: Frequency
    
    def __post_init__(self):
        if not self.word.matches_plate(self.plate):
            raise ValueError(f"Word '{self.word.value}' does not match plate '{self.plate.value}'")


@dataclass
class IndividualScore:
    """Score from a single model for a word-plate combination."""
    model: ModelName
    score: Score
    reasoning: Reasoning
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class WordScore:
    """Complete scoring result for a word-plate combination."""
    word: Word
    plate: LicensePlate
    individual_scores: List[IndividualScore]
    frequency: Frequency
    aggregate_score: Optional[AggregateScore] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        
        if self.individual_scores and self.aggregate_score is None:
            scores = [score.score.value for score in self.individual_scores]
            self.aggregate_score = AggregateScore(sum(scores) / len(scores))
    
    def add_score(self, score: IndividualScore):
        """Add an individual score and recalculate aggregate."""
        self.individual_scores.append(score)
        scores = [s.score.value for s in self.individual_scores]
        self.aggregate_score = AggregateScore(sum(scores) / len(scores))


@dataclass
class ScoringSession:
    """A session containing multiple word scoring results."""
    session_id: SessionId
    models_used: List[ModelName]
    results: List[WordScore]
    cache_key: Optional[CacheKey] = None
    created_at: datetime = None
    end_time: Optional[datetime] = None
    interrupted: bool = False
    total_scores: int = 0
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        
        # Recalculate total scores
        self.total_scores = sum(len(result.individual_scores) for result in self.results)
    
    def add_result(self, word_score: WordScore):
        """Add a word score result to the session."""
        self.results.append(word_score)
        self.total_scores += len(word_score.individual_scores)
    
    def mark_completed(self):
        """Mark the session as completed."""
        if not self.end_time:
            self.end_time = datetime.utcnow()
    
    def mark_interrupted(self):
        """Mark the session as interrupted."""
        self.interrupted = True
        self.mark_completed()
    
    @property
    def is_completed(self) -> bool:
        """Check if the session is completed."""
        return self.end_time is not None
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """Get session duration in seconds."""
        if not self.end_time:
            return None
        return (self.end_time - self.created_at).total_seconds()


@dataclass
class CorpusStatistics:
    """Statistical information about the corpus."""
    total_plates: int
    total_unique_words: int
    dataset_words: List[str]
    plate_word_counts: Dict[str, int]
    word_frequency_distribution: Dict[str, int]
    generated_at: datetime = None
    
    def __post_init__(self):
        if self.generated_at is None:
            self.generated_at = datetime.utcnow()


@dataclass
class CorpusFeatures:
    """Pre-computed features for all word-plate combinations."""
    features: Dict[str, Dict[str, Any]]  # word-plate combination -> features
    metadata: Dict[str, Any]
    generated_at: datetime = None
    
    def __post_init__(self):
        if self.generated_at is None:
            self.generated_at = datetime.utcnow()
    
    def get_features(self, word: Word, plate: LicensePlate) -> Optional[Dict[str, Any]]:
        """Get features for a specific word-plate combination."""
        key = f"{word.value.lower()}:{plate.value.lower()}"
        return self.features.get(key)


@dataclass
class ModelAvailability:
    """Information about model availability in the system."""
    model: ModelName
    available: bool
    error_message: Optional[str] = None
    last_checked: datetime = None
    
    def __post_init__(self):
        if self.last_checked is None:
            self.last_checked = datetime.utcnow()


@dataclass
class ScoringSystemStatus:
    """Overall status of the scoring system."""
    ollama_running: bool
    models: List[ModelAvailability]
    cache_enabled: bool
    active_sessions: int
    checked_at: datetime = None
    
    def __post_init__(self):
        if self.checked_at is None:
            self.checked_at = datetime.utcnow()
    
    @property
    def available_models(self) -> List[ModelName]:
        """Get list of available models."""
        return [model.model for model in self.models if model.available]
    
    @property
    def is_healthy(self) -> bool:
        """Check if the system is in a healthy state."""
        return self.ollama_running and len(self.available_models) > 0
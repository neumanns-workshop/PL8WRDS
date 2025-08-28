"""
Pydantic models for the word scoring system.
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime

class ScoringModel(str, Enum):
    """Available LLM models for scoring."""
    # Large models (10-32B)
    COGITO_14B = "cogito:14b"
    GEMMA3_12B = "gemma3:12b"
    PHI4_PLUS = "phi4-reasoning:plus"
    QWEN3_32B = "qwen3:32b"
    COGITO_32B = "cogito:32b"
    GPT_OSS_20B = "gpt-oss:20b"
    
    # Medium models (7-8B)
    GRANITE = "granite3.3:8b"
    MISTRAL = "mistral:7b"  
    DEEPSEEK = "deepseek-r1:8b"
    DEEPSEEK_7B = "deepseek-r1:7b"
    LLAMA3 = "llama3:8b"
    LLAMA31 = "llama3.1:8b"
    QWEN3 = "qwen3:8b"
    MINICPM = "minicpm-v:8b"
    
    # Small models (1-4B)
    GRANITE_2B = "granite3.3:2b"
    PHI4_MINI = "phi4-mini-reasoning:3.8b"
    PHI3_MINI = "phi3:mini"
    LLAMA32_3B = "llama3.2:3b"
    QWEN25_3B = "qwen2.5vl:3b"
    DEEPSEEK_1_5B = "deepseek-r1:1.5b"

# Removed MetricType enum - using simple impressiveness scoring

class ScoringRequest(BaseModel):
    """Request for scoring a word with a combination."""
    word: str = Field(..., description="The word to score")
    combination: str = Field(..., description="The license plate combination")
    models: List[ScoringModel] = Field(default_factory=lambda: list(ScoringModel), description="Models to use for scoring")
    cache_key: Optional[str] = Field(None, description="Optional cache key for this scoring session")

class IndividualScore(BaseModel):
    """Score from a single model for impressiveness."""
    model: ScoringModel
    score: int = Field(..., ge=0, le=100, description="Score from 0-100")
    reasoning: str = Field(..., description="Model's reasoning for the score")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class WordScore(BaseModel):
    """Complete scoring result for a word-combination pair."""
    word: str
    combination: str
    scores: List[IndividualScore]
    aggregate_score: Optional[float] = Field(None, description="Overall aggregate score")
    frequency: Optional[int] = Field(None, description="Word frequency from dictionary")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class BatchScoringRequest(BaseModel):
    """Request for scoring multiple words."""
    words: List[str] = Field(..., description="Words to score")
    combination: str = Field(..., description="The license plate combination")
    models: List[ScoringModel] = Field(default_factory=lambda: list(ScoringModel))
    max_words: Optional[int] = Field(50, description="Maximum number of words to score")
    cache_key: Optional[str] = Field(None, description="Optional cache key for this scoring session")

class RandomScoringRequest(BaseModel):
    """Request for scoring random words from random combinations."""
    num_combinations: int = Field(5, ge=1, le=50, description="Number of random combinations to generate")
    words_per_combination: int = Field(3, ge=1, le=20, description="Number of words to score per combination")
    combination_length: int = Field(3, ge=2, le=8, description="Length of license plate combinations")
    models: List[ScoringModel] = Field(default_factory=lambda: list(ScoringModel))
    cache_key: Optional[str] = Field(None, description="Optional cache key for this scoring session")

class ScoringSession(BaseModel):
    """A complete scoring session with multiple results."""
    session_id: str
    cache_key: Optional[str] = None
    results: List[WordScore] = Field(default_factory=list)
    models_used: List[ScoringModel] = Field(default_factory=list)
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    total_scores: int = 0
    interrupted: bool = False

class ModelAvailability(BaseModel):
    """Status of model availability."""
    model: ScoringModel
    available: bool
    last_checked: datetime = Field(default_factory=datetime.utcnow)
    error_message: Optional[str] = None

class ScoringSystemStatus(BaseModel):
    """Overall status of the scoring system."""
    ollama_running: bool
    models: List[ModelAvailability]
    cache_enabled: bool
    active_sessions: int
    last_updated: datetime = Field(default_factory=datetime.utcnow)

# Scoring prompt template for impressiveness scoring
SCORING_PROMPT_TEMPLATE = """You are scoring word discoveries in a letter-matching word game.

GAME RULES: Players are given a sequence of letters (like "ABC") and must THINK OF/GENERATE words that contain those letters in order (but not necessarily consecutive). For example, given letters "ABC", players might think of words like "alphabet", "fabric", "absorb", etc. The challenge is GENERATING these words from memory, not checking if a given word contains the letters.

DEFINITION: "Impressive" means a word discovery that the general person wouldn't expect - something that makes people go "wow, how did you think of that!" The more unexpected and surprising the discovery, the more impressive it is.

Here are example scorings to calibrate your responses:

Letter sequence: NXT
Word found: next
Score: 35
Reasoning: Obvious choice - most players would immediately think of this word when given N-X-T.

Letter sequence: VTH  
Word found: seventh
Score: 30
Reasoning: Predictable discovery - common ordinal number that comes to mind quickly for V-T-H.

Letter sequence: HNI
Word found: technique  
Score: 62
Reasoning: Solid find - thinking of this word when given H-N-I requires moderate vocabulary depth.

Letter sequence: AEJ
Word found: hallelujah
Score: 88
Reasoning: Excellent discovery - coming up with this uncommon religious term from the cues A-E-J shows strong vocabulary recall.

Letter sequence: VTH
Word found: leviathan
Score: 85
Reasoning: Impressive generation - producing this mythological word from V-T-H demonstrates good vocabulary access.

Letter sequence: NXT
Word found: inextricable
Score: 91
Reasoning: Outstanding find - generating this rare, complex word from simple cues N-X-T shows exceptional vocabulary knowledge.

Now score this word using the similar criteria and scoring patterns:

Letter sequence: {combination}
Word found: {word}

This word is already verified as VALID for this sequence (letters appear in correct order).

Score: [0-100]
Reasoning: [Explain why this word deserves this score - how impressive is this discovery?]"""

class LLMScoringResponse(BaseModel):
    """Response format expected from LLM models."""
    score: int = Field(..., ge=0, le=100, description="Numerical score from 0-100")
    reasoning: str = Field(..., description="Detailed reasoning for the score")
    key_factors: List[str] = Field(default_factory=list, description="Key factors that influenced the score")

# Aggregate scoring and analysis models
class ScoringStatistics(BaseModel):
    """Statistics for impressiveness scores."""
    mean_score: float
    median_score: float
    std_deviation: float
    min_score: int
    max_score: int
    count: int

class ModelPerformance(BaseModel):
    """Performance analysis for a specific model."""
    model: ScoringModel
    total_scores: int
    average_score: float
    score_statistics: ScoringStatistics
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class RecombinationMetrics(BaseModel):
    """Separate metrics for analyzing score patterns and recombinations."""
    combination: str
    total_words_scored: int
    average_score: float
    score_distribution: Dict[str, int] = Field(default_factory=dict, description="Score ranges and counts")
    top_words: List[str] = Field(default_factory=list, description="Highest scoring words")
    model_agreement: float = Field(0.0, description="Agreement level between models")
    score_correlations: Dict[str, float] = Field(default_factory=dict, description="Correlations between different scoring aspects")
    last_analyzed: datetime = Field(default_factory=datetime.utcnow)

# Dataset API Models
class DatasetMetadata(BaseModel):
    """Metadata for the training dataset."""
    generated_at: str
    total_words: int
    models_used: List[str]
    sampling_strategy: str
    method: str
    combined_from_parts: List[int]
    individual_scores_total: int

class DatasetWordScore(BaseModel):
    """Individual word score entry in the dataset."""
    word: str
    plate: str
    frequency: int
    aggregate_score: float
    weighted_score: float
    individual_scores: List[IndividualScore]

class TrainingDataset(BaseModel):
    """Complete training dataset response."""
    metadata: DatasetMetadata
    word_scores: List[DatasetWordScore]
    
class DatasetSummary(BaseModel):
    """Summary statistics of the dataset."""
    total_words: int
    total_scores: int
    models_used: List[str]
    score_distribution: Dict[str, int]  # score ranges and counts
    plate_distribution: Dict[str, int]  # plates and word counts
    frequency_stats: Dict[str, float]   # min, max, mean, median frequency

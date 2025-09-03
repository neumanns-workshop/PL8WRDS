import logging
import statistics
from fastapi import APIRouter, Query, Depends
from pydantic import BaseModel
from typing import List, Optional
from enum import Enum
from dependency_injector.wiring import Provide, inject

from ..services.solver_service import solve_combination

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

class MatchingMode(str, Enum):
    SUBSEQUENCE = "subsequence"
    SUBSTRING = "substring"
    ANAGRAM = "anagram"
    ANAGRAM_SUBSET = "anagram_subset"
    PATTERN = "pattern"

class WordMatch(BaseModel):
    word: str
    frequency: int

class FrequencyDistribution(BaseModel):
    mean: float
    median: float
    std_dev: float
    min_freq: int
    max_freq: int
    q1: float
    q3: float

class SolverResponse(BaseModel):
    combination: str
    mode: str
    matches: List[WordMatch]
    match_count: int
    total_frequency: int
    frequency_distribution: Optional[FrequencyDistribution]
    lexical_fertility: str

@router.get("/solve/{combination}", response_model=SolverResponse)
async def solve_combination_endpoint(
    combination: str,
    mode: MatchingMode = Query(MatchingMode.SUBSEQUENCE, description="Matching mode for pattern analysis")
):
    """
    Find all real words that match the given combination according to the specified mode.
    
    Modes:
    - subsequence: Letters appear in order, gaps allowed (default)
    - substring: Letters appear in order, no gaps  
    - anagram: Exact letter match, any order
    - anagram_subset: Contains at least these letters, any order
    - pattern: Positional matching with '?' wildcards
    
    Returns words sorted by frequency, along with a lexical fertility assessment.
    """
    logger.info(f"Received solve request for combination: '{combination}' with mode: '{mode}'")
    
    # Use the original working function
    matches = solve_combination(combination, mode.value)
    match_count = len(matches)
    
    # Calculate total frequency score
    total_frequency = sum(freq for word, freq in matches)
    
    # Calculate frequency distribution statistics
    frequency_distribution = None
    if matches:
        frequencies = [freq for word, freq in matches]
        try:
            frequency_distribution = {
                "mean": statistics.mean(frequencies),
                "median": statistics.median(frequencies),
                "std_dev": statistics.stdev(frequencies) if len(frequencies) > 1 else 0.0,
                "min_freq": min(frequencies),
                "max_freq": max(frequencies),
                "q1": statistics.quantiles(frequencies, n=4)[0] if len(frequencies) >= 4 else statistics.median(frequencies),
                "q3": statistics.quantiles(frequencies, n=4)[2] if len(frequencies) >= 4 else statistics.median(frequencies)
            }
        except statistics.StatisticsError:
            # Handle edge cases where statistical functions might fail
            frequency_distribution = {
                "mean": frequencies[0] if frequencies else 0,
                "median": frequencies[0] if frequencies else 0,
                "std_dev": 0.0,
                "min_freq": frequencies[0] if frequencies else 0,
                "max_freq": frequencies[0] if frequencies else 0,
                "q1": frequencies[0] if frequencies else 0,
                "q3": frequencies[0] if frequencies else 0
            }
    
    # Determine lexical fertility
    if match_count == 0:
        fertility = "Barren"
    elif match_count <= 5:
        fertility = "Sparse" 
    elif match_count <= 20:
        fertility = "Moderate"
    elif match_count <= 50:
        fertility = "Rich"
    else:
        fertility = "Abundant"
    
    word_matches = [{"word": word, "frequency": freq} for word, freq in matches]
    
    return {
        "combination": combination,
        "mode": mode.value,
        "matches": word_matches,
        "match_count": match_count,
        "total_frequency": total_frequency,
        "frequency_distribution": frequency_distribution,
        "lexical_fertility": fertility
    }

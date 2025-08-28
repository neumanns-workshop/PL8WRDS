"""
Dataset API router for serving training data.
"""

import json
import statistics
from pathlib import Path
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from collections import Counter

from app.models.scoring import (
    TrainingDataset, 
    DatasetSummary, 
    DatasetMetadata, 
    DatasetWordScore,
    IndividualScore
)
from app.services.feature_extraction import FeatureExtractor

router = APIRouter(prefix="/dataset", tags=["dataset"])

DATASET_PATH = Path("cache/scoring_dataset_complete.json")

def load_dataset() -> Dict:
    """Load the complete dataset from JSON file."""
    if not DATASET_PATH.exists():
        raise HTTPException(status_code=404, detail="Dataset file not found")
    
    try:
        with open(DATASET_PATH, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Invalid dataset file format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading dataset: {str(e)}")

def calculate_dataset_summary(data: Dict) -> DatasetSummary:
    """Calculate summary statistics for the dataset."""
    word_scores = data.get("word_scores", [])
    metadata = data.get("metadata", {})
    
    # Score distribution (in 10-point ranges)
    score_ranges = {
        "0-10": 0, "11-20": 0, "21-30": 0, "31-40": 0, "41-50": 0,
        "51-60": 0, "61-70": 0, "71-80": 0, "81-90": 0, "91-100": 0
    }
    
    plates = Counter()
    frequencies = []
    
    for entry in word_scores:
        # Aggregate score distribution
        agg_score = entry.get("aggregate_score", 0)
        range_key = f"{int(agg_score//10)*10}-{int(agg_score//10)*10+10}"
        if range_key == "100-110":
            range_key = "91-100"
        if range_key in score_ranges:
            score_ranges[range_key] += 1
        
        # Plate distribution
        plates[entry.get("plate", "")] += 1
        
        # Frequency stats
        frequencies.append(entry.get("frequency", 0))
    
    # Frequency statistics
    frequency_stats = {}
    if frequencies:
        frequency_stats = {
            "min": float(min(frequencies)),
            "max": float(max(frequencies)),
            "mean": float(statistics.mean(frequencies)),
            "median": float(statistics.median(frequencies))
        }
    
    return DatasetSummary(
        total_words=len(word_scores),
        total_scores=len(word_scores) * len(metadata.get("models_used", [])),
        models_used=metadata.get("models_used", []),
        score_distribution=score_ranges,
        plate_distribution=dict(plates),
        frequency_stats=frequency_stats
    )

@router.get("/", response_model=TrainingDataset)
async def get_training_dataset(
    limit: Optional[int] = Query(None, description="Limit number of words returned"),
    skip: Optional[int] = Query(0, description="Number of words to skip"),
    min_score: Optional[float] = Query(None, description="Minimum aggregate score filter"),
    max_score: Optional[float] = Query(None, description="Maximum aggregate score filter"),
    plate_filter: Optional[str] = Query(None, description="Filter by specific plate")
):
    """
    Get the complete training dataset with optional filtering.
    
    Returns all scored words with their aggregate scores, individual model scores,
    frequencies, and reasoning from the LLM panel of judges.
    """
    data = load_dataset()
    word_scores = data.get("word_scores", [])
    
    # Apply filters
    filtered_words = word_scores
    
    if min_score is not None:
        filtered_words = [w for w in filtered_words if w.get("aggregate_score", 0) >= min_score]
    
    if max_score is not None:
        filtered_words = [w for w in filtered_words if w.get("aggregate_score", 0) <= max_score]
    
    if plate_filter:
        filtered_words = [w for w in filtered_words if w.get("plate", "").upper() == plate_filter.upper()]
    
    # Apply pagination
    if skip:
        filtered_words = filtered_words[skip:]
    if limit:
        filtered_words = filtered_words[:limit]
    
    # Convert to Pydantic models
    dataset_words = []
    for entry in filtered_words:
        individual_scores = []
        for score_data in entry.get("individual_scores", []):
            individual_scores.append(IndividualScore(
                model=score_data.get("model"),
                score=score_data.get("score"),
                reasoning=score_data.get("reasoning"),
                timestamp=score_data.get("timestamp")
            ))
        
        dataset_words.append(DatasetWordScore(
            word=entry.get("word"),
            plate=entry.get("plate"),
            frequency=entry.get("frequency"),
            aggregate_score=entry.get("aggregate_score"),
            weighted_score=entry.get("weighted_score"),
            individual_scores=individual_scores
        ))
    
    # Convert metadata
    metadata_dict = data.get("metadata", {})
    metadata = DatasetMetadata(
        generated_at=metadata_dict.get("generated_at", ""),
        total_words=metadata_dict.get("total_words", len(word_scores)),
        models_used=metadata_dict.get("models_used", []),
        sampling_strategy=metadata_dict.get("sampling_strategy", ""),
        method=metadata_dict.get("method", ""),
        combined_from_parts=metadata_dict.get("combined_from_parts", []),
        individual_scores_total=metadata_dict.get("individual_scores_total", 0)
    )
    
    return TrainingDataset(
        metadata=metadata,
        word_scores=dataset_words
    )

@router.get("/summary", response_model=DatasetSummary)
async def get_dataset_summary():
    """
    Get summary statistics of the training dataset.
    
    Returns counts, distributions, and statistical information about
    the scored words, plates, and model performance.
    """
    data = load_dataset()
    return calculate_dataset_summary(data)

@router.get("/plates")
async def get_available_plates():
    """Get list of all plates in the dataset with word counts."""
    data = load_dataset()
    word_scores = data.get("word_scores", [])
    
    plates = Counter()
    for entry in word_scores:
        plates[entry.get("plate", "")] += 1
    
    return {
        "total_plates": len(plates),
        "plates": dict(plates.most_common())
    }

@router.get("/models")
async def get_dataset_models():
    """Get information about models used in the dataset."""
    data = load_dataset()
    metadata = data.get("metadata", {})
    
    return {
        "models_used": metadata.get("models_used", []),
        "total_individual_scores": metadata.get("individual_scores_total", 0),
        "sampling_strategy": metadata.get("sampling_strategy", ""),
        "generation_method": metadata.get("method", "")
    }

@router.get("/features")
async def get_dataset_with_features(
    limit: Optional[int] = Query(10, description="Limit number of words returned"),
    skip: Optional[int] = Query(0, description="Number of words to skip"),
    include_ngrams: bool = Query(False, description="Include character n-gram features")
):
    """
    Get dataset with extracted features for regression model training.
    
    Returns words with their scores plus extracted linguistic features:
    - TF/IDF relative to plates
    - Plate difficulty 
    - Surprisal
    - Character n-grams (optional, since there are many)
    - Positional entropy
    - Word intrinsic features
    """
    # Load dataset
    data = load_dataset()
    word_scores = data.get("word_scores", [])
    
    # Initialize feature extractor
    extractor = FeatureExtractor()
    
    # Build corpus statistics if not already built (using full corpus for API)
    await extractor.build_corpus_statistics(use_full_corpus=True)
    
    # Apply pagination
    if skip:
        word_scores = word_scores[skip:]
    if limit:
        word_scores = word_scores[:limit]
    
    # Extract features for each word
    enriched_data = []
    
    for i, entry in enumerate(word_scores):
        word = entry.get("word", "")
        plate = entry.get("plate", "")
        
        print(f"Extracting features for word {i+1}/{len(word_scores)}: {word} ({plate})")
        
        try:
            # Extract all features
            features = extractor.extract_all_features(word, plate)
            
            # Filter out n-grams if not requested (too many features)
            if not include_ngrams:
                features = {k: v for k, v in features.items() if not k.startswith("ngram_")}
            
            # Combine original data with features
            enriched_entry = {
                "word": word,
                "plate": plate,
                "aggregate_score": entry.get("aggregate_score"),
                "weighted_score": entry.get("weighted_score"),
                "frequency": entry.get("frequency"),
                "individual_scores": [
                    {
                        "model": score.get("model"),
                        "score": score.get("score")
                    }
                    for score in entry.get("individual_scores", [])
                ],
                "features": features
            }
            
            enriched_data.append(enriched_entry)
            
        except Exception as e:
            print(f"Error extracting features for {word}/{plate}: {e}")
            # Include entry without features
            enriched_data.append({
                "word": word,
                "plate": plate,
                "aggregate_score": entry.get("aggregate_score"),
                "error": str(e)
            })
    
    return {
        "metadata": {
            "total_entries": len(enriched_data),
            "features_included": not include_ngrams,
            "ngrams_included": include_ngrams
        },
        "data": enriched_data
    }

@router.get("/features/sample")
async def get_feature_sample(word: str, plate: str):
    """
    Get features for a specific word-plate pair (for testing).
    """
    extractor = FeatureExtractor()
    await extractor.build_corpus_statistics(use_full_corpus=True)
    
    features = extractor.extract_all_features(word, plate)
    
    return {
        "word": word,
        "plate": plate, 
        "features": features,
        "feature_count": len(features)
    }

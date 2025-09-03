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
# from app.services.feature_extraction import FeatureExtractor  # Disabled - using new 3D scoring system

router = APIRouter(prefix="/dataset", tags=["dataset"])

# DATASET_PATH = Path("cache/scoring_dataset_complete.json")  # DISABLED - old training data system

# DISABLED - Old dataset loading functions no longer needed
# def load_dataset() -> Dict: ...
# def calculate_dataset_summary(data: Dict) -> DatasetSummary: ...

# DISABLED - Old training dataset system replaced by 3D scoring
# @router.get("/", response_model=TrainingDataset)  
# async def get_training_dataset(...):
#     """Old training dataset endpoint - use new 3D scoring system instead"""
#     return {"message": "Dataset endpoints disabled - use /predict/ensemble instead"}

# DISABLED - Old training dataset endpoints replaced by 3D scoring
# All these endpoints depended on cache/scoring_dataset_complete.json which doesn't exist

@router.get("/status")
async def get_dataset_status():
    """Get status of current data systems."""
    return {
        "message": "Using new 3D scoring system",
        "old_dataset": "disabled",
        "active_endpoints": [
            "/predict/ensemble - 3D scoring system",
            "/solve/{plate} - word solver", 
            "/corpus/stats - corpus statistics"
        ]
    }

# DISABLED - Old feature extraction system replaced by 3D scoring
# @router.get("/features")
# async def get_dataset_with_features(...):
#     """Old feature extraction endpoint - use new 3D scoring system instead"""
#     pass

# DISABLED - Old feature extraction system replaced by 3D scoring  
# @router.get("/features/sample")
# async def get_feature_sample(word: str, plate: str):
#     """Old feature sample endpoint - use new 3D scoring system instead"""
#     pass

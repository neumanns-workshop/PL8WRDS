"""
FastAPI router for model-based score predictions.
"""

from fastapi import APIRouter, HTTPException, Body, Query
from pydantic import BaseModel, Field
from typing import Dict, Any

from ..services.prediction_service import prediction_service

router = APIRouter(prefix="/predict", tags=["prediction"])

class PredictionRequest(BaseModel):
    word: str = Field(..., example="syzygy", description="The word to score.")
    plate: str = Field(..., min_length=3, max_length=3, example="SGY", description="The 3-letter plate.")

class PredictionResponse(BaseModel):
    word: str
    plate: str
    predicted_score: float
    model_version: str

@router.post("/score", response_model=PredictionResponse)
async def predict_score(request: PredictionRequest):
    """
    Predict the impressiveness score of a word for a given 3-letter plate
    using the trained regression model.
    """
    try:
        if not prediction_service._is_initialized:
            raise HTTPException(
                status_code=503, 
                detail="Prediction service is not initialized. This may be due to a startup error."
            )
            
        result = prediction_service.predict_score(request.word, request.plate)
        return result
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=f"Model not loaded: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

@router.get("/health")
async def prediction_health_check():
    """Health check for the prediction service."""
    is_ready = prediction_service._is_initialized
    status_code = 200 if is_ready else 503
    
    return {
        "status": "ready" if is_ready else "initializing",
        "model_path": prediction_service.model_path,
        "model_loaded": prediction_service.model is not None
    }

@router.get("/feature-importance")
async def get_feature_importance(top_k: int = Query(20, ge=1, le=100, description="Number of top features to return")):
    """
    Get the most important features from the trained regression model.
    Shows which linguistic features have the strongest influence on predictions.
    """
    try:
        if not prediction_service._is_initialized:
            raise HTTPException(
                status_code=503, 
                detail="Prediction service is not initialized. This may be due to a startup error."
            )
            
        importance_data = prediction_service.get_feature_importance(top_k=top_k)
        return importance_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get feature importance: {e}")

@router.post("/explain")
async def explain_prediction(
    request: PredictionRequest,
    top_k: int = Query(10, ge=1, le=50, description="Number of top contributing features to return")
):
    """
    Explain a specific prediction by showing which features contributed most 
    to the predicted score for a given word-plate pair.
    """
    try:
        if not prediction_service._is_initialized:
            raise HTTPException(
                status_code=503, 
                detail="Prediction service is not initialized. This may be due to a startup error."
            )
            
        explanation = prediction_service.explain_prediction(request.word, request.plate, top_k=top_k)
        return explanation
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to explain prediction: {e}")

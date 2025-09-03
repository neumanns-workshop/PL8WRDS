"""
FastAPI router for word scoring endpoints.
"""

import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, Depends
from typing import List, Optional
from dependency_injector.wiring import Provide, inject

from ..models.scoring import (
    ScoringRequest,
    BatchScoringRequest,
    RandomScoringRequest,
    ScoringModel,
    WordScore,
    ScoringSession,
    ScoringSystemStatus,
    ModelAvailability
)
from ..core.container import Container
from ..application.services import WordScoringService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scoring", tags=["scoring"])

@router.get("/status", response_model=ScoringSystemStatus)
@inject
async def get_system_status(
    word_scoring_service: WordScoringService = Depends(Provide[Container.word_scoring_service])
):
    """Get the current status of the scoring system."""
    try:
        # TODO: Implement system status check in WordScoringService
        # For now, return a basic status
        models = [ScoringModel.GRANITE]  # Default models
        status = await word_scoring_service.check_system_health([model.value for model in models])
        return status
    except Exception as e:
        logger.error(f"Failed to get system status: {e}")
        # Return a default error status
        return ScoringSystemStatus(
            ollama_running=False,
            models=[],
            active_sessions=0
        )

@router.post("/score-word", response_model=WordScore)
async def score_single_word(request: ScoringRequest):
    """Score a single word with specified models."""
    logger.info(f"Scoring word '{request.word}' for combination '{request.combination}' with models: {[m.value for m in request.models]}")
    
    try:
        result = await scoring_service.score_word_with_models(
            word=request.word,
            combination=request.combination,
            models=request.models
        )
        return result
    except Exception as e:
        logger.error(f"Failed to score word: {e}")
        raise HTTPException(status_code=500, detail=f"Scoring failed: {str(e)}")

@router.post("/score-batch", response_model=List[WordScore])
async def score_batch_words(request: BatchScoringRequest):
    """Score multiple words for a combination."""
    logger.info(f"Batch scoring {len(request.words)} words for combination '{request.combination}'")
    
    # Limit the number of words to prevent overwhelming the system
    words_to_score = request.words[:request.max_words]
    
    try:
        results = []
        for word in words_to_score:
            try:
                result = await scoring_service.score_word_with_models(
                    word=word,
                    combination=request.combination,
                    models=request.models
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to score word '{word}': {e}")
                # Continue with other words even if one fails
                continue
        
        logger.info(f"Successfully scored {len(results)} out of {len(words_to_score)} words")
        return results
        
    except Exception as e:
        logger.error(f"Batch scoring failed: {e}")
        raise HTTPException(status_code=500, detail=f"Batch scoring failed: {str(e)}")

@router.post("/score-random", response_model=ScoringSession)
async def score_random_words(request: RandomScoringRequest, background_tasks: BackgroundTasks):
    """Score random words from random combinations."""
    logger.info(f"Starting random scoring: {request.num_combinations} combinations, {request.words_per_combination} words each")
    
    try:
        # Start the scoring session
        session = await scoring_service.score_random_words(
            num_combinations=request.num_combinations,
            words_per_combination=request.words_per_combination,
            combination_length=request.combination_length,
            models=request.models,
            cache_key=request.cache_key
        )
        
        return session
        
    except Exception as e:
        logger.error(f"Random scoring failed: {e}")
        raise HTTPException(status_code=500, detail=f"Random scoring failed: {str(e)}")

@router.get("/session/{session_id}", response_model=ScoringSession)
async def get_scoring_session(session_id: str):
    """Get details of a scoring session."""
    session = await scoring_service.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return session

@router.get("/models", response_model=List[ModelAvailability])
async def get_model_status():
    """Get the availability status of all models."""
    status = await scoring_service.check_system_status()
    return status.models

@router.post("/models/setup")
async def setup_models(models: List[ScoringModel]):
    """Ensure specified models are downloaded and available."""
    logger.info(f"Setting up models: {[m.value for m in models]}")
    
    try:
        available_models = await scoring_service.ensure_models_available(models)
        
        return {
            "requested": [m.value for m in models],
            "available": [m.value for m in available_models],
            "setup_complete": len(available_models) == len(models)
        }
    except Exception as e:
        logger.error(f"Model setup failed: {e}")
        raise HTTPException(status_code=500, detail=f"Model setup failed: {str(e)}")

@router.get("/combinations/{combination}/words")
async def get_random_words_for_combination(
    combination: str,
    count: int = Query(5, ge=1, le=20, description="Number of random words to return")
):
    """Get random valid words for a license plate combination."""
    try:
        words = await scoring_service.get_random_words_for_combination(combination, count)
        
        return {
            "combination": combination,
            "words": words,
            "count": len(words)
        }
    except Exception as e:
        logger.error(f"Failed to get random words for '{combination}': {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get words: {str(e)}")

@router.delete("/cache")
async def clear_cache():
    """Clear the scoring cache."""
    try:
        # Reset the cache
        scoring_service.cache._word_scores.clear()
        scoring_service.cache._sessions.clear()
        await scoring_service.cache.save_cache()
        
        return {"message": "Cache cleared successfully"}
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")

# Health check endpoint
@router.get("/health")
async def health_check():
    """Simple health check endpoint."""
    status = await scoring_service.check_system_status()
    
    if not status.ollama_running:
        raise HTTPException(status_code=503, detail="Ollama server not running")
    
    available_models = [m for m in status.models if m.available]
    if not available_models:
        raise HTTPException(status_code=503, detail="No models available")
    
    return {
        "status": "healthy",
        "ollama_running": status.ollama_running,
        "available_models": len(available_models),
        "active_sessions": status.active_sessions
    }

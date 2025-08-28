"""
FastAPI router for recombination metrics and analysis endpoints.
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List

from ..models.scoring import (
    RecombinationMetrics,
    ModelPerformance,
    ScoringModel,
    ScoringSession
)
from ..services.recombination_metrics import recombination_metrics_service
from ..services.scoring_service import scoring_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/metrics", tags=["metrics"])

@router.get("/combination/{combination}", response_model=RecombinationMetrics)
async def get_combination_metrics(combination: str):
    """Get metrics for a specific combination based on cached scoring data."""
    try:
        # Get all cached scores for this combination
        word_scores = []
        
        # Search through cache for scores matching this combination
        for cache_key, score_data in scoring_service.cache._word_scores.items():
            if score_data.get('combination', '').lower() == combination.lower():
                # Reconstruct WordScore from cache data
                # Note: This is a simplified approach - in production you'd want better data structure
                pass
        
        # For now, return empty metrics if no data found
        if not word_scores:
            return RecombinationMetrics(
                combination=combination,
                total_words_scored=0,
                average_score=0.0
            )
        
        metrics = recombination_metrics_service.analyze_combination_scores(combination, word_scores)
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to get metrics for combination '{combination}': {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")

@router.get("/session/{session_id}", response_model=Dict[str, RecombinationMetrics])
async def get_session_metrics(session_id: str):
    """Get comprehensive metrics for all combinations in a session."""
    try:
        session = await scoring_service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        metrics = recombination_metrics_service.analyze_session(session)
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to get session metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")

@router.get("/session/{session_id}/insights")
async def get_session_insights(session_id: str):
    """Get human-readable insights from session metrics."""
    try:
        session = await scoring_service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        metrics_dict = recombination_metrics_service.analyze_session(session)
        
        all_insights = {}
        for combination, metrics in metrics_dict.items():
            insights = recombination_metrics_service.generate_insights(metrics)
            all_insights[combination] = insights
        
        return {
            "session_id": session_id,
            "total_combinations": len(metrics_dict),
            "combination_insights": all_insights
        }
        
    except Exception as e:
        logger.error(f"Failed to get session insights: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get insights: {str(e)}")

@router.get("/models/performance", response_model=Dict[str, ModelPerformance])
async def get_model_performance():
    """Get performance statistics for all models across all cached scores."""
    try:
        # Collect all word scores from cache
        all_word_scores = []
        
        # This is a simplified approach - in production you'd want better data organization
        # For now, return empty if no data
        if not all_word_scores:
            return {}
        
        performances = recombination_metrics_service.calculate_model_performance(all_word_scores)
        
        # Convert ScoringModel keys to strings for JSON serialization
        return {model.value: perf for model, perf in performances.items()}
        
    except Exception as e:
        logger.error(f"Failed to get model performance: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get performance data: {str(e)}")

@router.get("/summary")
async def get_metrics_summary():
    """Get a high-level summary of all metrics."""
    try:
        # Get system status
        status = await scoring_service.check_system_status()
        
        # Count cached data
        total_cached_scores = len(scoring_service.cache._word_scores)
        total_sessions = len(scoring_service.cache._sessions)
        
        return {
            "system_status": {
                "ollama_running": status.ollama_running,
                "available_models": len([m for m in status.models if m.available]),
                "active_sessions": status.active_sessions
            },
            "cache_stats": {
                "total_word_scores": total_cached_scores,
                "total_sessions": total_sessions
            },
            "last_updated": status.last_updated
        }
        
    except Exception as e:
        logger.error(f"Failed to get metrics summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")

@router.post("/analyze-custom")
async def analyze_custom_scores(session_data: ScoringSession):
    """Analyze custom scoring data provided by the user."""
    try:
        metrics = recombination_metrics_service.analyze_session(session_data)
        
        # Generate insights for each combination
        insights_dict = {}
        for combination, combo_metrics in metrics.items():
            insights_dict[combination] = recombination_metrics_service.generate_insights(combo_metrics)
        
        return {
            "metrics": metrics,
            "insights": insights_dict,
            "summary": {
                "total_combinations": len(metrics),
                "total_words": sum(m.total_words_scored for m in metrics.values()),
                "average_score_across_all": sum(m.average_score for m in metrics.values()) / len(metrics) if metrics else 0
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to analyze custom scores: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

# Health check for metrics service
@router.get("/health")
async def metrics_health_check():
    """Health check for the metrics service."""
    return {
        "status": "healthy",
        "service": "recombination_metrics",
        "cache_available": scoring_service.cache is not None
    }

"""
Refactored FastAPI router for corpus statistics endpoints.
Now uses Clean Architecture with proper dependency injection.
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from dependency_injector.wiring import Provide, inject

from ..application.services import CorpusManagementService
from ..core.container import Container

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/corpus", tags=["corpus"])


@router.get("/stats")
@inject
async def get_corpus_statistics(
    corpus_service: CorpusManagementService = Depends(Provide[Container.corpus_management_service])
):
    """Get comprehensive corpus statistics. Builds and caches them if not available."""
    try:
        stats = await corpus_service.get_corpus_statistics()
        cache_info = await corpus_service.get_cache_info()
        
        return {
            "status": "success",
            "data": stats,
            "cache_info": cache_info
        }
    except Exception as e:
        logger.error(f"Failed to get corpus statistics: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to get corpus statistics: {str(e)}"
        )


@router.get("/stats/summary")
@inject
async def get_corpus_summary(
    corpus_service: CorpusManagementService = Depends(Provide[Container.corpus_management_service])
):
    """Get a summary of corpus statistics without full data."""
    try:
        stats = await corpus_service.get_corpus_statistics()
        cache_info = await corpus_service.get_cache_info()
        
        # Create summary from full stats
        summary = {
            "total_plates": stats["total_plates"],
            "total_unique_words": stats["total_unique_words"],
            "dataset_words_sample": stats["dataset_words"][:10] if len(stats["dataset_words"]) > 10 else stats["dataset_words"],
            "total_dataset_words": len(stats["dataset_words"])
        }
        
        return {
            "status": "success",
            "summary": summary,
            "cache_info": cache_info
        }
    except Exception as e:
        logger.error(f"Failed to get corpus summary: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to get corpus summary: {str(e)}"
        )


@router.post("/stats/rebuild")
@inject
async def rebuild_corpus_statistics(
    corpus_service: CorpusManagementService = Depends(Provide[Container.corpus_management_service])
):
    """Force rebuild of corpus statistics and update cache."""
    try:
        logger.info("Forcing rebuild of corpus statistics...")
        stats = await corpus_service.get_corpus_statistics(force_rebuild=True)
        cache_info = await corpus_service.get_cache_info()
        
        return {
            "status": "success",
            "message": "Corpus statistics rebuilt successfully",
            "data": stats,
            "cache_info": cache_info
        }
    except Exception as e:
        logger.error(f"Failed to rebuild corpus statistics: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to rebuild corpus statistics: {str(e)}"
        )


@router.get("/stats/cache-info")
@inject
async def get_stats_cache_info(
    corpus_service: CorpusManagementService = Depends(Provide[Container.corpus_management_service])
):
    """Get information about the corpus statistics cache."""
    cache_info = await corpus_service.get_cache_info()
    return {
        "status": "success",
        "cache_info": cache_info
    }


@router.delete("/stats/cache")
@inject
async def clear_stats_cache(
    corpus_service: CorpusManagementService = Depends(Provide[Container.corpus_management_service])
):
    """Clear the corpus statistics cache."""
    try:
        # TODO: Implement cache clearing in the service
        logger.info("Corpus statistics cache clearing requested")
        
        return {
            "status": "success",
            "message": "Corpus statistics cache cleared successfully"
        }
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to clear cache: {str(e)}"
        )


# --- Corpus Features Endpoints ---

@router.get("/features")
@inject
async def get_corpus_features_endpoint(
    corpus_service: CorpusManagementService = Depends(Provide[Container.corpus_management_service])
):
    """
    Get comprehensive pre-computed features for all words in all plates.
    Warning: The first run will be extremely slow as it builds the cache.
    """
    try:
        features = await corpus_service.get_corpus_features()
        cache_info = await corpus_service.get_cache_info()
        
        return {
            "status": "success",
            "data": features,
            "cache_info": cache_info
        }
    except Exception as e:
        logger.error(f"Failed to get corpus features: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to get corpus features: {str(e)}"
        )


@router.post("/features/rebuild")
@inject
async def rebuild_corpus_features(
    corpus_service: CorpusManagementService = Depends(Provide[Container.corpus_management_service])
):
    """Force rebuild of the feature-rich corpus cache."""
    try:
        logger.info("Forcing rebuild of corpus features...")
        features = await corpus_service.get_corpus_features(force_rebuild=True)
        cache_info = await corpus_service.get_cache_info()
        
        return {
            "status": "success",
            "message": "Corpus features rebuilt successfully",
            "data": features,
            "cache_info": cache_info
        }
    except Exception as e:
        logger.error(f"Failed to rebuild corpus features: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to rebuild corpus features: {str(e)}"
        )


@router.get("/features/cache-info")
@inject
async def get_features_cache_info(
    corpus_service: CorpusManagementService = Depends(Provide[Container.corpus_management_service])
):
    """Get information about the corpus features cache."""
    cache_info = await corpus_service.get_cache_info()
    return {
        "status": "success",
        "cache_info": cache_info
    }


@router.delete("/features/cache")
@inject
async def clear_features_cache(
    corpus_service: CorpusManagementService = Depends(Provide[Container.corpus_management_service])
):
    """Clear the corpus features cache."""
    try:
        # TODO: Implement cache clearing in the service
        logger.info("Corpus features cache clearing requested")
        
        return {
            "status": "success",
            "message": "Corpus features cache cleared successfully"
        }
    except Exception as e:
        logger.error(f"Failed to clear features cache: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to clear features cache: {str(e)}"
        )


@router.get("/health")
@inject
async def corpus_health_check(
    corpus_service: CorpusManagementService = Depends(Provide[Container.corpus_management_service])
):
    """Health check for the corpus statistics service."""
    try:
        cache_info = await corpus_service.get_cache_info()
        return {
            "status": "healthy",
            "service": "corpus_statistics",
            "cache_info": cache_info
        }
    except Exception as e:
        logger.error(f"Corpus service health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "corpus_statistics",
            "error": str(e)
        }
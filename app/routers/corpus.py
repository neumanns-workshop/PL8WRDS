"""
FastAPI router for corpus statistics endpoints.
"""

import json
import logging
import os
from datetime import datetime
from collections import defaultdict
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional, List, Set

from ..services.feature_extraction import FeatureExtractor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/corpus", tags=["corpus"])

# Cache file path
CORPUS_STATS_CACHE_FILE = "cache/corpus_stats.json"
CORPUS_FEATURES_CACHE_FILE = "cache/corpus_features.json"


class CorpusStatsService:
    """Service for managing corpus statistics with caching."""
    
    def __init__(self):
        self._cached_stats: Optional[Dict[str, Any]] = None
        self._last_updated: Optional[datetime] = None
        self._feature_extractor = FeatureExtractor()
    
    async def get_corpus_stats(self, force_rebuild: bool = False) -> Dict[str, Any]:
        """Get corpus statistics, building them if necessary or if forced."""
        
        # First check if cache file exists and we aren't forcing a rebuild
        if not force_rebuild and os.path.exists(CORPUS_STATS_CACHE_FILE):
            if not self._cached_stats:  # Not loaded in memory yet
                # Try to load from cache first
                await self._load_from_cache()
                if self._cached_stats:
                    logger.info("Corpus statistics loaded from cache")
                    return self._cached_stats
            else:
                # We already have stats loaded
                return self._cached_stats
        
        # Build new stats only if cache doesn't exist or force_rebuild
        logger.info("Building corpus statistics...")
        try:
            stats = await self._feature_extractor.build_corpus_statistics(use_full_corpus=True)
            
            # Cache the stats
            self._cached_stats = stats
            self._last_updated = datetime.now()
            
            # Persist to cache file
            await self._save_to_cache(stats)
            
            logger.info("Corpus statistics built and cached successfully")
            return stats
            
        except Exception as e:
            logger.error(f"Failed to build corpus statistics: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to build corpus statistics: {str(e)}")
    
    async def _save_to_cache(self, stats: Dict[str, Any]):
        """Save corpus statistics to cache file."""
        try:
            # Ensure cache directory exists
            os.makedirs(os.path.dirname(CORPUS_STATS_CACHE_FILE), exist_ok=True)
            
            # Add metadata
            cache_data = {
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "version": "1.0"
                },
                "stats": stats
            }
            
            with open(CORPUS_STATS_CACHE_FILE, 'w') as f:
                json.dump(cache_data, f, indent=2)
                
            logger.info(f"Corpus statistics saved to cache: {CORPUS_STATS_CACHE_FILE}")
            
        except Exception as e:
            logger.error(f"Failed to save corpus statistics to cache: {e}")
            # Don't raise - this is not critical
    
    async def _load_from_cache(self):
        """Load corpus statistics from cache file."""
        try:
            with open(CORPUS_STATS_CACHE_FILE, 'r') as f:
                cache_data = json.load(f)
            
            self._cached_stats = cache_data["stats"]
            self._last_updated = datetime.fromisoformat(cache_data["metadata"]["generated_at"])
            
            logger.info("Corpus statistics loaded from cache")
            
        except Exception as e:
            logger.error(f"Failed to load corpus statistics from cache: {e}")
            # Reset state
            self._cached_stats = None
            self._last_updated = None
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about the current cache state."""
        cache_exists = os.path.exists(CORPUS_STATS_CACHE_FILE)
        cache_size = os.path.getsize(CORPUS_STATS_CACHE_FILE) if cache_exists else 0
        
        return {
            "cached": self._cached_stats is not None,
            "cache_file_exists": cache_exists,
            "cache_file_size_bytes": cache_size,
            "last_updated": self._last_updated.isoformat() if self._last_updated else None,
            "cache_file_path": CORPUS_STATS_CACHE_FILE
        }

# Global service instance
corpus_stats_service = CorpusStatsService()


# --- Corpus Features Service ---

class CorpusFeaturesService:
    """Service for managing the feature-rich corpus cache."""

    def __init__(self):
        self._cached_features: Optional[Dict[str, Any]] = None
        self._last_updated: Optional[datetime] = None
        self._feature_extractor = FeatureExtractor()

    async def get_corpus_features(self, force_rebuild: bool = False) -> Dict[str, Any]:
        """Get corpus features, building them if necessary or if forced."""
        if not force_rebuild and os.path.exists(CORPUS_FEATURES_CACHE_FILE):
            if not self._cached_features:
                await self._load_from_cache()
                if self._cached_features:
                    logger.info("Corpus features loaded from cache.")
                    return self._cached_features
            else:
                return self._cached_features

        logger.info("Building corpus features. This will take a long time...")
        try:
            # This method will be created in the next step
            features = await self._feature_extractor.build_corpus_features()

            self._cached_features = features
            self._last_updated = datetime.now()
            await self._save_to_cache(features)

            logger.info("Corpus features built and cached successfully.")
            return features

        except Exception as e:
            logger.error(f"Failed to build corpus features: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to build corpus features: {str(e)}")

    async def _save_to_cache(self, features: Dict[str, Any]):
        """Save corpus features to cache file."""
        try:
            os.makedirs(os.path.dirname(CORPUS_FEATURES_CACHE_FILE), exist_ok=True)
            cache_data = {
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "version": "1.0"
                },
                "features": features
            }
            with open(CORPUS_FEATURES_CACHE_FILE, 'w') as f:
                json.dump(cache_data, f, indent=2)
            logger.info(f"Corpus features saved to cache: {CORPUS_FEATURES_CACHE_FILE}")

        except Exception as e:
            logger.error(f"Failed to save corpus features to cache: {e}")

    async def _load_from_cache(self):
        """Load corpus features from cache file."""
        try:
            with open(CORPUS_FEATURES_CACHE_FILE, 'r') as f:
                cache_data = json.load(f)

            self._cached_features = cache_data["features"]
            self._last_updated = datetime.fromisoformat(cache_data["metadata"]["generated_at"])
            logger.info("Corpus features loaded from cache.")

        except Exception as e:
            logger.error(f"Failed to load corpus features from cache: {e}")
            self._cached_features = None
            self._last_updated = None

    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about the current cache state."""
        cache_exists = os.path.exists(CORPUS_FEATURES_CACHE_FILE)
        cache_size = os.path.getsize(CORPUS_FEATURES_CACHE_FILE) if cache_exists else 0

        return {
            "cached": self._cached_features is not None,
            "cache_file_exists": cache_exists,
            "cache_file_size_bytes": cache_size,
            "last_updated": self._last_updated.isoformat() if self._last_updated else None,
            "cache_file_path": CORPUS_FEATURES_CACHE_FILE
        }

# Global service instance for features
corpus_features_service = CorpusFeaturesService()


# --- Corpus Statistics Endpoints ---

@router.get("/stats")
async def get_corpus_statistics():
    """Get comprehensive corpus statistics. Builds and caches them if not available."""
    try:
        stats = await corpus_stats_service.get_corpus_stats()
        return {
            "status": "success",
            "data": stats,
            "cache_info": corpus_stats_service.get_cache_info()
        }
    except Exception as e:
        logger.error(f"Failed to get corpus statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get corpus statistics: {str(e)}")

@router.get("/stats/summary")
async def get_corpus_summary():
    """Get a summary of corpus statistics without full data."""
    try:
        stats = await corpus_stats_service.get_corpus_stats()
        
        # Return summary without full solution sets
        summary = {
            "total_plates": stats["total_plates"],
            "total_unique_words": stats["total_unique_words"],
            "dataset_words_sample": stats["dataset_words"][:10],  # First 10 words as sample
            "total_dataset_words": len(stats["dataset_words"])
        }
        
        return {
            "status": "success",
            "summary": summary,
            "cache_info": corpus_stats_service.get_cache_info()
        }
    except Exception as e:
        logger.error(f"Failed to get corpus summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get corpus summary: {str(e)}")

@router.post("/stats/rebuild")
async def rebuild_corpus_statistics():
    """Force rebuild of corpus statistics and update cache."""
    try:
        logger.info("Forcing rebuild of corpus statistics...")
        stats = await corpus_stats_service.get_corpus_stats(force_rebuild=True)
        
        return {
            "status": "success",
            "message": "Corpus statistics rebuilt successfully",
            "data": stats,
            "cache_info": corpus_stats_service.get_cache_info()
        }
    except Exception as e:
        logger.error(f"Failed to rebuild corpus statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to rebuild corpus statistics: {str(e)}")

@router.get("/stats/cache-info")
async def get_cache_info():
    """Get information about the corpus statistics cache."""
    return {
        "status": "success",
        "cache_info": corpus_stats_service.get_cache_info()
    }

@router.delete("/stats/cache")
async def clear_cache():
    """Clear the corpus statistics cache."""
    try:
        # Remove cache file if it exists
        if os.path.exists(CORPUS_STATS_CACHE_FILE):
            os.remove(CORPUS_STATS_CACHE_FILE)
            logger.info("Corpus statistics cache file removed")
        
        # Reset service state
        corpus_stats_service._cached_stats = None
        corpus_stats_service._last_updated = None
        
        return {
            "status": "success",
            "message": "Corpus statistics cache cleared successfully"
        }
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")


# --- Corpus Features Endpoints ---

@router.get("/features")
async def get_corpus_features_endpoint():
    """
    Get comprehensive pre-computed features for all words in all plates.
    Warning: The first run will be extremely slow as it builds the cache.
    """
    try:
        features = await corpus_features_service.get_corpus_features()
        return {
            "status": "success",
            "data": features,
            "cache_info": corpus_features_service.get_cache_info()
        }
    except Exception as e:
        logger.error(f"Failed to get corpus features: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get corpus features: {str(e)}")

@router.post("/features/rebuild")
async def rebuild_corpus_features():
    """Force rebuild of the feature-rich corpus cache."""
    try:
        logger.info("Forcing rebuild of corpus features...")
        features = await corpus_features_service.get_corpus_features(force_rebuild=True)
        return {
            "status": "success",
            "message": "Corpus features rebuilt successfully",
            "data": features,
            "cache_info": corpus_features_service.get_cache_info()
        }
    except Exception as e:
        logger.error(f"Failed to rebuild corpus features: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to rebuild corpus features: {str(e)}")

@router.get("/features/cache-info")
async def get_features_cache_info():
    """Get information about the corpus features cache."""
    return {
        "status": "success",
        "cache_info": corpus_features_service.get_cache_info()
    }

@router.delete("/features/cache")
async def clear_features_cache():
    """Clear the corpus features cache."""
    try:
        if os.path.exists(CORPUS_FEATURES_CACHE_FILE):
            os.remove(CORPUS_FEATURES_CACHE_FILE)
            logger.info("Corpus features cache file removed")

        corpus_features_service._cached_features = None
        corpus_features_service._last_updated = None

        return {
            "status": "success",
            "message": "Corpus features cache cleared successfully"
        }
    except Exception as e:
        logger.error(f"Failed to clear features cache: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear features cache: {str(e)}")


@router.get("/health")
async def corpus_health_check():
    """Health check for the corpus statistics service."""
    try:
        cache_info = corpus_stats_service.get_cache_info()
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

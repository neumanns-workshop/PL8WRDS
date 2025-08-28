"""
Service for loading the trained regression model and making predictions.
"""

import joblib
import pandas as pd
import numpy as np
from typing import Dict, Any, List
import logging
import os
import json

from .feature_extraction import FeatureExtractor
# No longer need corpus_stats_service, this service will be self-sufficient
# from ..routers.corpus import corpus_stats_service 

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PredictionService:
    """Loads and uses the trained word scoring model."""

    def __init__(self, 
                 model_path: str = "models/word_scoring_ridge_v3.joblib",
                 features_cache_path: str = "cache/corpus_features.json"):
        self.model_path = model_path
        self.features_cache_path = features_cache_path
        self.model = None
        self.feature_names: List[str] = []
        self.feature_extractor = FeatureExtractor()
        self._is_initialized = False

    async def initialize(self):
        """
        Loads the model and all necessary feature data from the pre-computed cache.
        This should be called during application startup.
        """
        if self._is_initialized:
            return

        # Step 1: Load the trained model
        if not os.path.exists(self.model_path):
            logger.error(f"Model file not found at {self.model_path}")
            raise FileNotFoundError(f"Model file not found at {self.model_path}")
            
        logger.info(f"Loading model from {self.model_path}...")
        model_data = joblib.load(self.model_path)
        self.model = model_data['model']
        self.feature_names = model_data['feature_names']
        logger.info("Model loaded successfully.")

        # Step 2: Load the pre-computed features and build in-memory lookups
        # This makes the service self-sufficient and avoids re-calculating stats.
        if not os.path.exists(self.features_cache_path):
            msg = f"Features cache file not found at {self.features_cache_path}. The server cannot make predictions."
            logger.error(msg)
            raise FileNotFoundError(msg)

        logger.info(f"Loading features data from {self.features_cache_path} to initialize extractor...")
        with open(self.features_cache_path, 'r') as f:
            features_data = json.load(f).get("features", {})

        # Reconstruct the necessary data for the FeatureExtractor from the features cache
        plate_solutions = {plate: {item['word'] for item in items} for plate, items in features_data.items()}
        
        word_plates = {}
        for plate, items in features_data.items():
            for item in items:
                word = item['word']
                if word not in word_plates:
                    word_plates[word] = set()
                word_plates[word].add(plate)

        corpus_stats = {
            "total_plates": len(plate_solutions),
            "total_unique_words": len(word_plates),
            "plate_solutions": {p: list(w) for p, w in plate_solutions.items()},
            "word_plates": {w: list(p) for w, p in word_plates.items()}
        }
        
        self.feature_extractor.initialize_from_corpus_stats(corpus_stats)
        logger.info("Feature extractor initialized successfully from pre-computed cache.")

        self._is_initialized = True

    def predict_score(self, word: str, plate: str) -> Dict[str, Any]:
        """Predicts the impressiveness score for a word-plate pair."""
        if not self._is_initialized:
            raise RuntimeError("PredictionService must be initialized before use. Call initialize().")

        # Step 1: Extract features for the new word-plate pair
        features = self.feature_extractor.extract_all_features(word, plate)

        # Step 2: Prepare the feature vector for the model
        # The model expects a DataFrame with columns in a specific order.
        feature_vector = pd.DataFrame([features])
        
        # Ensure all required columns are present, filling missing ones with 0
        # This handles cases where n-grams or other features might not be generated for a short word.
        feature_vector = feature_vector.reindex(columns=self.feature_names, fill_value=0.0)
        
        # Clean data: handle NaN and infinite values, same as in training
        feature_vector = feature_vector.replace([np.inf, -np.inf], 0.0).fillna(0.0)

        # Step 3: Make the prediction
        predicted_score = self.model.predict(feature_vector)[0]

        return {
            "word": word,
            "plate": plate,
            "predicted_score": float(predicted_score),
            "model_version": self.model_path
        }

    def get_feature_importance(self, top_k: int = 20) -> Dict[str, Any]:
        """Get feature importance from the trained Ridge model."""
        if not self._is_initialized:
            raise RuntimeError("PredictionService must be initialized before use. Call initialize().")
        
        # Get Ridge coefficients from the pipeline
        ridge_step = self.model.named_steps['ridge']
        scaler_step = self.model.named_steps['scaler']
        
        # Raw coefficients
        raw_coefs = ridge_step.coef_
        
        # Scale coefficients by feature standard deviation for interpretability
        feature_std = scaler_step.scale_
        scaled_coefs = raw_coefs * feature_std
        
        # Create feature importance data
        feature_importance = []
        for i, (feature_name, raw_coef, scaled_coef) in enumerate(zip(self.feature_names, raw_coefs, scaled_coefs)):
            feature_importance.append({
                'feature': feature_name,
                'coefficient': float(raw_coef),
                'scaled_coefficient': float(scaled_coef),
                'abs_coefficient': float(abs(scaled_coef)),
                'rank': i + 1  # Will be re-ranked after sorting
            })
        
        # Sort by absolute scaled coefficient (most important first)
        feature_importance.sort(key=lambda x: x['abs_coefficient'], reverse=True)
        
        # Update ranks after sorting
        for i, item in enumerate(feature_importance):
            item['rank'] = i + 1
        
        return {
            "total_features": len(self.feature_names),
            "top_features": feature_importance[:top_k],
            "model_info": {
                "model_type": "Ridge Regression",
                "total_coefficients": len(raw_coefs),
                "model_path": self.model_path
            }
        }

    def explain_prediction(self, word: str, plate: str, top_k: int = 10) -> Dict[str, Any]:
        """Explain a specific prediction by showing feature contributions."""
        if not self._is_initialized:
            raise RuntimeError("PredictionService must be initialized before use. Call initialize().")

        # Get the base prediction
        prediction_result = self.predict_score(word, plate)
        
        # Extract features for this word-plate pair
        features = self.feature_extractor.extract_all_features(word, plate)
        feature_vector = pd.DataFrame([features])
        feature_vector = feature_vector.reindex(columns=self.feature_names, fill_value=0.0)
        feature_vector = feature_vector.replace([np.inf, -np.inf], 0.0).fillna(0.0)
        
        # Get Ridge coefficients
        ridge_step = self.model.named_steps['ridge']
        scaler_step = self.model.named_steps['scaler']
        
        # Transform features the same way the model does
        scaled_features = scaler_step.transform(feature_vector)[0]
        coefficients = ridge_step.coef_
        
        # Calculate feature contributions (coefficient * feature_value)
        contributions = scaled_features * coefficients
        intercept = ridge_step.intercept_
        
        # Create contribution data
        feature_contributions = []
        for feature_name, contribution, feature_value, coef in zip(
            self.feature_names, contributions, scaled_features, coefficients
        ):
            if abs(contribution) > 1e-10:  # Only include non-zero contributions
                feature_contributions.append({
                    'feature': feature_name,
                    'contribution': float(contribution),
                    'feature_value': float(feature_value),
                    'coefficient': float(coef),
                    'abs_contribution': float(abs(contribution))
                })
        
        # Sort by absolute contribution
        feature_contributions.sort(key=lambda x: x['abs_contribution'], reverse=True)
        
        # Verification: sum of contributions + intercept should equal prediction
        total_contribution = sum(c['contribution'] for c in feature_contributions)
        verification_score = total_contribution + intercept
        
        return {
            "word": word,
            "plate": plate,
            "predicted_score": prediction_result["predicted_score"],
            "explanation": {
                "intercept": float(intercept),
                "total_contribution": float(total_contribution),
                "verification_score": float(verification_score),
                "top_contributing_features": feature_contributions[:top_k],
                "total_active_features": len([c for c in feature_contributions if abs(c['contribution']) > 1e-10])
            }
        }

# Global instance of the service to be used by the router
prediction_service = PredictionService()

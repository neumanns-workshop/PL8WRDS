"""
Regression model trainer for word impressiveness scoring.
"""

import json
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any
from pathlib import Path
import asyncio

from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.linear_model import Ridge, Lasso, ElasticNet
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import SelectKBest, f_regression
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib

from app.services.feature_extraction import FeatureExtractor
from app.services.solver_service import solve_combination

class RegressionTrainer:
    """Train regression models for word impressiveness scoring."""
    
    def __init__(self):
        self.feature_extractor = FeatureExtractor()
        self.model = None
        self.scaler = None
        self.feature_names = None
        self.training_stats = {}
    
    async def prepare_training_data_from_precomputed_features(
        self,
        labeled_dataset_path: str = "cache/scoring_dataset_complete.json",
        features_cache_path: str = "cache/corpus_features.json",
        max_samples: int = None
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Load labeled dataset and join with pre-computed features for training.
        This is much faster than computing features on the fly.
        """
        # Step 1: Load the labeled (ground-truth) dataset
        print(f"Loading labeled dataset from {labeled_dataset_path}...")
        with open(labeled_dataset_path, 'r') as f:
            labeled_data = json.load(f)
        
        word_scores = labeled_data.get("word_scores", [])
        if max_samples:
            word_scores = word_scores[:max_samples]
        
        print(f"Loaded {len(word_scores)} labeled word-score pairs.")

        # Step 2: Load the massive pre-computed features cache
        print(f"Loading pre-computed features from {features_cache_path}...")
        with open(features_cache_path, 'r') as f:
            # This is a large file, so this step might take some time and memory
            features_data = json.load(f).get("features", {})
        
        # Create a lookup dictionary for faster access: {(plate, word): features}
        features_lookup = {
            (plate.upper(), item['word'].lower()): item['features']
            for plate, items in features_data.items()
            for item in items
        }
        print("Pre-computed features loaded and indexed.")

        # Step 3: Join the datasets
        feature_data = []
        target_data = []
        
        print(f"Joining {len(word_scores)} labeled samples with feature cache...")
        for entry in word_scores:
            word = entry.get("word", "")
            plate = entry.get("plate", "")
            aggregate_score = entry.get("aggregate_score", 0)
            
            # Find the pre-computed features for this word-plate pair, ensuring case consistency
            feature_dict = features_lookup.get((plate.upper(), word.lower()))
            
            if feature_dict:
                # Add word and plate for reference
                feature_dict["word"] = word
                feature_dict["plate"] = plate
                
                feature_data.append(feature_dict)
                target_data.append(aggregate_score)
            else:
                print(f"  Warning: No pre-computed features found for {word}/{plate}. Skipping.")

        print(f"Successfully joined {len(feature_data)} samples.")
        
        if not feature_data:
            raise ValueError("No matching features found for the given dataset. Training cannot proceed.")

        # Convert to DataFrame
        X = pd.DataFrame(feature_data)
        y = pd.Series(target_data, name="aggregate_score")
        
        # Remove non-numeric columns for training
        self.reference_cols = ["word", "plate"]
        X_numeric = X.drop(columns=self.reference_cols, errors='ignore')
        
        # Clean data (as before)
        X_numeric = X_numeric.replace([np.inf, -np.inf], np.nan)
        X_numeric = X_numeric.fillna(0)
        
        # Store feature names
        self.feature_names = list(X_numeric.columns)
        
        print(f"Feature matrix shape: {X_numeric.shape}")
        
        return X_numeric, y

    async def prepare_training_data(
        self, 
        dataset_path: str = "cache/scoring_dataset_complete.json",
        include_ngrams: bool = True,
        max_samples: int = None
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Load dataset and extract features for training.
        
        Returns:
            X: Feature DataFrame
            y: Target Series (aggregate scores)
        """
        print("Loading dataset...")
        with open(dataset_path, 'r') as f:
            data = json.load(f)
        
        word_scores = data.get("word_scores", [])
        if max_samples:
            word_scores = word_scores[:max_samples]
        
        print(f"Processing {len(word_scores)} word-score pairs...")
        
        # Build corpus statistics for ALL possible plates (not just dataset plates)
        # This ensures features like TF-IDF, plate difficulty, and surprisal work for any plate
        await self.feature_extractor.build_corpus_statistics(dataset_path, use_full_corpus=True)
        
        # Extract features for each word-plate pair
        feature_data = []
        target_data = []
        
        for i, entry in enumerate(word_scores):
            if i % 100 == 0:
                print(f"  Processing {i}/{len(word_scores)}...")
                
            word = entry.get("word", "")
            plate = entry.get("plate", "")
            aggregate_score = entry.get("aggregate_score", 0)
            
            try:
                # Extract features
                features = self.feature_extractor.extract_all_features(word, plate)
                
                # Filter n-grams if requested
                if not include_ngrams:
                    features = {k: v for k, v in features.items() if not k.startswith("ngram_")}
                
                # Add word and plate for reference
                features["word"] = word
                features["plate"] = plate
                
                feature_data.append(features)
                target_data.append(aggregate_score)
                
            except Exception as e:
                print(f"  Warning: Could not process {word}/{plate}: {e}")
        
        print(f"Successfully processed {len(feature_data)} samples")
        
        # Convert to DataFrame
        X = pd.DataFrame(feature_data)
        y = pd.Series(target_data, name="aggregate_score")
        
        # Remove non-numeric columns for training
        self.reference_cols = ["word", "plate"]
        X_numeric = X.drop(columns=self.reference_cols, errors='ignore')
        
        # Clean data: handle NaN values and infinite values
        print("Cleaning data...")
        print(f"  NaN values before: {X_numeric.isna().sum().sum()}")
        print(f"  Infinite values before: {np.isinf(X_numeric.select_dtypes(include=[np.number])).sum().sum()}")
        
        # Replace infinite values with a large finite number
        X_numeric = X_numeric.replace([np.inf, -np.inf], np.nan)
        
        # Fill NaN values with 0 (reasonable for most of our features)
        X_numeric = X_numeric.fillna(0)
        
        # Ensure all columns are numeric
        X_numeric = X_numeric.select_dtypes(include=[np.number])
        
        print(f"  NaN values after: {X_numeric.isna().sum().sum()}")
        print(f"  Infinite values after: {np.isinf(X_numeric).sum().sum()}")
        
        # Store feature names
        self.feature_names = list(X_numeric.columns)
        
        print(f"Feature matrix shape: {X_numeric.shape}")
        print(f"Target range: {y.min():.1f} - {y.max():.1f}")
        
        return X_numeric, y
    
    def split_data_by_plate(self, X: pd.DataFrame, y: pd.Series, 
                           test_size: float = 0.3, random_state: int = 42) -> Tuple:
        """
        Split data ensuring plates don't appear in both train and test sets.
        """
        # Get unique plates (we'll need to reconstruct this info)
        # For now, use random split - could enhance to be plate-aware
        return train_test_split(X, y, test_size=test_size, random_state=random_state)
    
    def train_ridge_model(self, X_train: pd.DataFrame, y_train: pd.Series,
                         alpha_range: List[float] = None) -> Dict[str, Any]:
        """Train Ridge regression with cross-validation for alpha selection."""
        if alpha_range is None:
            alpha_range = [0.1, 1.0, 10.0, 100.0, 1000.0]
        
        print("Training Ridge regression with cross-validation...")
        
        # Create pipeline with scaling
        pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('ridge', Ridge())
        ])
        
        # Grid search for best alpha
        param_grid = {'ridge__alpha': alpha_range}
        
        grid_search = GridSearchCV(
            pipeline, 
            param_grid, 
            cv=5, 
            scoring='neg_mean_absolute_error',
            n_jobs=-1
        )
        
        grid_search.fit(X_train, y_train)
        
        print(f"Best alpha: {grid_search.best_params_['ridge__alpha']}")
        print(f"Best CV MAE: {-grid_search.best_score_:.3f}")
        
        self.model = grid_search.best_estimator_
        
        return {
            'best_alpha': grid_search.best_params_['ridge__alpha'],
            'cv_mae': -grid_search.best_score_,
            'cv_results': grid_search.cv_results_
        }
    
    def evaluate_model(self, X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, float]:
        """Evaluate trained model on test set."""
        if self.model is None:
            raise ValueError("Model not trained yet!")
        
        y_pred = self.model.predict(X_test)
        
        metrics = {
            'mae': mean_absolute_error(y_test, y_pred),
            'rmse': np.sqrt(mean_squared_error(y_test, y_pred)),
            'r2': r2_score(y_test, y_pred),
            'mean_target': y_test.mean(),
            'std_target': y_test.std()
        }
        
        print("Model Performance:")
        print(f"  MAE:  {metrics['mae']:.3f} points")
        print(f"  RMSE: {metrics['rmse']:.3f} points") 
        print(f"  R²:   {metrics['r2']:.3f}")
        print(f"  Target mean ± std: {metrics['mean_target']:.1f} ± {metrics['std_target']:.1f}")
        
        return metrics
    
    def get_feature_importance(self, top_k: int = 20) -> pd.DataFrame:
        """Get feature importance from trained Ridge model."""
        if self.model is None:
            raise ValueError("Model not trained yet!")
        
        # Get Ridge coefficients (after scaling)
        ridge_step = self.model.named_steps['ridge']
        scaler_step = self.model.named_steps['scaler']
        
        # Raw coefficients
        raw_coefs = ridge_step.coef_
        
        # Scale coefficients by feature standard deviation for interpretability
        feature_std = scaler_step.scale_
        scaled_coefs = raw_coefs * feature_std
        
        importance_df = pd.DataFrame({
            'feature': self.feature_names,
            'coefficient': raw_coefs,
            'scaled_coefficient': scaled_coefs,
            'abs_coefficient': np.abs(scaled_coefs)
        }).sort_values('abs_coefficient', ascending=False)
        
        print(f"\nTop {top_k} Most Important Features:")
        print("=" * 60)
        for i, row in importance_df.head(top_k).iterrows():
            sign = "+" if row['scaled_coefficient'] > 0 else "-"
            print(f"{row['feature']:25} {sign}{abs(row['scaled_coefficient']):8.3f}")
        
        return importance_df
    

    def predict_word_score(self, word: str, plate: str, 
                           use_intersection_only: bool = True) -> Dict[str, Any]:
        """Predict score for a new word-plate pair."""
        if self.model is None:
            raise ValueError("Model not trained yet!")
        

        # Extract features
        features = self.feature_extractor.extract_all_features(word, plate)
        
        if use_intersection_only:
            # Only use features that exist in both training and prediction
            available_features = [col for col in self.feature_names if col in features]
            
            if not available_features:
                # Fallback: use non-ngram features only
                available_features = [col for col in self.feature_names 
                                    if not col.startswith("ngram_")]
            
            # Create feature vector with only available features
            feature_vector = pd.DataFrame([{col: features.get(col, 0.0) 
                                          for col in available_features}])
            
            # Predict using partial features (model will handle missing columns)
            # We need to pad with zeros for missing features to match model expectations
            full_feature_vector = pd.DataFrame(0.0, index=[0], columns=self.feature_names)
            for col in available_features:
                if col in features:
                    full_feature_vector[col] = features[col]
                    
            predicted_score = self.model.predict(full_feature_vector)[0]
            
            return {
                'word': word,
                'plate': plate,
                'predicted_score': predicted_score,
                'features_used': len(available_features),
                'features_available': len(available_features),
                'features_total': len(self.feature_names),
                'features_missing': len(self.feature_names) - len(available_features),
                'ngram_features_used': len([f for f in available_features if f.startswith("ngram_")])
            }
        else:
            # Original approach: pad all missing features with 0.0
            feature_vector = pd.DataFrame([features])
            feature_vector = feature_vector.reindex(columns=self.feature_names, fill_value=0.0)
            
            # Clean data (same as training)
            feature_vector = feature_vector.replace([np.inf, -np.inf], 0.0)
            feature_vector = feature_vector.fillna(0.0)
            
            predicted_score = self.model.predict(feature_vector)[0]
            
            return {
                'word': word,
                'plate': plate,
                'predicted_score': predicted_score,
                'features_used': len(self.feature_names),
                'features_missing': len([col for col in self.feature_names if col not in features])
            }
    
    def save_model(self, filepath: str):
        """Save trained model and metadata."""
        model_data = {
            'model': self.model,
            'feature_names': self.feature_names,
            'training_stats': self.training_stats
        }
        
        joblib.dump(model_data, filepath)
        print(f"Model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """Load trained model and metadata."""
        model_data = joblib.load(filepath)
        
        self.model = model_data['model']
        self.feature_names = model_data['feature_names']
        self.training_stats = model_data.get('training_stats', {})
        
        print(f"Model loaded from {filepath}")

async def train_word_scoring_model(
    dataset_path: str = "cache/scoring_dataset_complete.json",
    use_precomputed_features: bool = True,
    features_cache_path: str = "cache/corpus_features.json",
    max_samples: int = None,
    save_path: str = "models/word_scoring_ridge_v3.joblib"
) -> RegressionTrainer:
    """
    Complete training pipeline for word scoring model.
    """
    trainer = RegressionTrainer()
    
    # Prepare data
    if use_precomputed_features:
        print("Using pre-computed features for training...")
        X, y = await trainer.prepare_training_data_from_precomputed_features(
            labeled_dataset_path=dataset_path,
            features_cache_path=features_cache_path,
            max_samples=max_samples
        )
    else:
        print("Computing features on the fly for training...")
        X, y = await trainer.prepare_training_data(
            dataset_path=dataset_path,
            include_ngrams=True,  # Assuming ngrams are desired for this path
            max_samples=max_samples
        )
    
    # Split data
    X_train, X_test, y_train, y_test = trainer.split_data_by_plate(X, y)
    
    print(f"\nTraining set: {X_train.shape[0]} samples")
    print(f"Test set: {X_test.shape[0]} samples")
    
    # Train model
    training_results = trainer.train_ridge_model(X_train, y_train)
    trainer.training_stats['training'] = training_results
    
    # Evaluate
    test_metrics = trainer.evaluate_model(X_test, y_test)
    trainer.training_stats['test'] = test_metrics
    
    # Feature importance
    importance_df = trainer.get_feature_importance()
    trainer.training_stats['feature_importance'] = importance_df
    
    # Save model
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    trainer.save_model(save_path)
    
    return trainer

if __name__ == "__main__":
    # Example usage
    async def main():
        trainer = await train_word_scoring_model(
            max_samples=1000  # Use a reasonable number of samples
        )
        
        # Test prediction
        result = trainer.predict_word_score("ambulance", "abc")
        print(f"\nTest prediction: {result}")
    
    asyncio.run(main())

"""
Service for analyzing scoring patterns and recombination metrics.
"""

import logging
import statistics
from collections import defaultdict, Counter
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from ..models.scoring import (
    WordScore,
    ScoringSession,
    RecombinationMetrics,
    ScoringStatistics,
    ModelPerformance,
    ScoringModel
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RecombinationMetricsService:
    """Service for analyzing score patterns and computing recombination metrics."""
    
    def __init__(self):
        self._cached_metrics: Dict[str, RecombinationMetrics] = {}
    
    def analyze_combination_scores(self, combination: str, word_scores: List[WordScore]) -> RecombinationMetrics:
        """Analyze scores for a specific combination."""
        if not word_scores:
            return RecombinationMetrics(
                combination=combination,
                total_words_scored=0,
                average_score=0.0
            )
        
        # Collect all scores
        all_scores = []
        model_scores = defaultdict(list)
        
        for word_score in word_scores:
            for individual_score in word_score.scores:
                all_scores.append(individual_score.score)
                model_scores[individual_score.model].append(individual_score.score)
        
        # Calculate basic statistics
        average_score = statistics.mean(all_scores) if all_scores else 0.0
        
        # Score distribution (in ranges)
        score_distribution = self._calculate_score_distribution(all_scores)
        
        # Top words (by average score)
        top_words = self._get_top_words(word_scores, limit=10)
        
        # Model agreement (how similar are the models' scores?)
        model_agreement = self._calculate_model_agreement(model_scores)
        
        # Score correlations (placeholder for future implementation)
        score_correlations = self._calculate_score_correlations(word_scores)
        
        return RecombinationMetrics(
            combination=combination,
            total_words_scored=len(word_scores),
            average_score=average_score,
            score_distribution=score_distribution,
            top_words=top_words,
            model_agreement=model_agreement,
            score_correlations=score_correlations,
            last_analyzed=datetime.utcnow()
        )
    
    def analyze_session(self, session: ScoringSession) -> Dict[str, RecombinationMetrics]:
        """Analyze all combinations in a scoring session."""
        # Group results by combination
        combination_scores = defaultdict(list)
        
        for word_score in session.results:
            combination_scores[word_score.combination].append(word_score)
        
        # Analyze each combination
        metrics = {}
        for combination, scores in combination_scores.items():
            metrics[combination] = self.analyze_combination_scores(combination, scores)
        
        return metrics
    
    def calculate_model_performance(self, word_scores: List[WordScore]) -> Dict[ScoringModel, ModelPerformance]:
        """Calculate performance statistics for each model."""
        model_data = defaultdict(list)
        
        # Collect scores by model
        for word_score in word_scores:
            for individual_score in word_score.scores:
                model_data[individual_score.model].append(individual_score.score)
        
        performances = {}
        for model, scores in model_data.items():
            if not scores:
                continue
                
            statistics_obj = ScoringStatistics(
                mean_score=statistics.mean(scores),
                median_score=statistics.median(scores),
                std_deviation=statistics.stdev(scores) if len(scores) > 1 else 0.0,
                min_score=min(scores),
                max_score=max(scores),
                count=len(scores)
            )
            
            performances[model] = ModelPerformance(
                model=model,
                total_scores=len(scores),
                average_score=statistics.mean(scores),
                score_statistics=statistics_obj
            )
        
        return performances
    
    def _calculate_score_distribution(self, scores: List[int]) -> Dict[str, int]:
        """Calculate distribution of scores in ranges."""
        if not scores:
            return {}
        
        ranges = {
            "0-20": 0,
            "21-40": 0,
            "41-60": 0,
            "61-80": 0,
            "81-100": 0
        }
        
        for score in scores:
            if score <= 20:
                ranges["0-20"] += 1
            elif score <= 40:
                ranges["21-40"] += 1
            elif score <= 60:
                ranges["41-60"] += 1
            elif score <= 80:
                ranges["61-80"] += 1
            else:
                ranges["81-100"] += 1
        
        return ranges
    
    def _get_top_words(self, word_scores: List[WordScore], limit: int = 10) -> List[str]:
        """Get the highest scoring words."""
        # Calculate average score for each word
        word_averages = []
        
        for word_score in word_scores:
            if word_score.aggregate_score is not None:
                word_averages.append((word_score.word, word_score.aggregate_score))
            elif word_score.scores:
                avg = statistics.mean([s.score for s in word_score.scores])
                word_averages.append((word_score.word, avg))
        
        # Sort by score descending and return top words
        word_averages.sort(key=lambda x: x[1], reverse=True)
        return [word for word, score in word_averages[:limit]]
    
    def _calculate_model_agreement(self, model_scores: Dict[ScoringModel, List[int]]) -> float:
        """Calculate how much the models agree in their scoring."""
        if len(model_scores) < 2:
            return 1.0  # Perfect agreement if only one model
        
        # Calculate pairwise correlations (simplified approach)
        # For now, we'll use the coefficient of variation across models as a proxy
        
        # Get scores that all models have scored
        model_lists = list(model_scores.values())
        if not all(model_lists):
            return 0.0
        
        min_length = min(len(scores) for scores in model_lists)
        if min_length == 0:
            return 0.0
        
        # Calculate average coefficient of variation across score positions
        variations = []
        for i in range(min_length):
            position_scores = [scores[i] for scores in model_lists]
            if len(set(position_scores)) == 1:
                variations.append(0.0)  # Perfect agreement
            else:
                mean_score = statistics.mean(position_scores)
                if mean_score > 0:
                    std_dev = statistics.stdev(position_scores)
                    cv = std_dev / mean_score
                    variations.append(cv)
        
        if not variations:
            return 1.0
        
        # Convert coefficient of variation to agreement score (0-1)
        avg_cv = statistics.mean(variations)
        agreement = max(0.0, 1.0 - avg_cv)  # Higher CV = lower agreement
        
        return round(agreement, 3)
    
    def _calculate_score_correlations(self, word_scores: List[WordScore]) -> Dict[str, float]:
        """Calculate correlations between different scoring aspects."""
        # Placeholder for future implementation
        # Could include correlations between:
        # - Word frequency vs. score
        # - Word length vs. score
        # - Pattern complexity vs. score
        # etc.
        
        correlations = {}
        
        # Word frequency vs. score correlation
        freq_score_pairs = []
        for word_score in word_scores:
            if word_score.frequency and word_score.aggregate_score:
                freq_score_pairs.append((word_score.frequency, word_score.aggregate_score))
        
        if len(freq_score_pairs) > 1:
            try:
                # Simple correlation calculation
                freqs, scores = zip(*freq_score_pairs)
                correlation = self._pearson_correlation(freqs, scores)
                correlations["frequency_vs_score"] = round(correlation, 3)
            except:
                correlations["frequency_vs_score"] = 0.0
        
        # Word length vs. score correlation
        length_score_pairs = []
        for word_score in word_scores:
            if word_score.aggregate_score:
                length_score_pairs.append((len(word_score.word), word_score.aggregate_score))
        
        if len(length_score_pairs) > 1:
            try:
                lengths, scores = zip(*length_score_pairs)
                correlation = self._pearson_correlation(lengths, scores)
                correlations["length_vs_score"] = round(correlation, 3)
            except:
                correlations["length_vs_score"] = 0.0
        
        return correlations
    
    def _pearson_correlation(self, x: List[float], y: List[float]) -> float:
        """Calculate Pearson correlation coefficient."""
        if len(x) != len(y) or len(x) < 2:
            return 0.0
        
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(x[i] ** 2 for i in range(n))
        sum_y2 = sum(y[i] ** 2 for i in range(n))
        
        numerator = n * sum_xy - sum_x * sum_y
        denominator = ((n * sum_x2 - sum_x ** 2) * (n * sum_y2 - sum_y ** 2)) ** 0.5
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    def generate_insights(self, metrics: RecombinationMetrics) -> List[str]:
        """Generate human-readable insights from metrics."""
        insights = []
        
        # Score level insights
        if metrics.average_score > 75:
            insights.append(f"High-quality combination: '{metrics.combination}' produces impressive words (avg: {metrics.average_score:.1f})")
        elif metrics.average_score < 25:
            insights.append(f"Challenging combination: '{metrics.combination}' has low-scoring words (avg: {metrics.average_score:.1f})")
        
        # Model agreement insights
        if metrics.model_agreement > 0.8:
            insights.append("Models show strong agreement on word quality")
        elif metrics.model_agreement < 0.4:
            insights.append("Models disagree significantly - subjective scoring")
        
        # Distribution insights
        if metrics.score_distribution:
            high_scores = metrics.score_distribution.get("81-100", 0)
            total_scores = sum(metrics.score_distribution.values())
            if total_scores > 0:
                high_ratio = high_scores / total_scores
                if high_ratio > 0.3:
                    insights.append("Many exceptional words found (30%+ scored 81-100)")
                elif high_ratio < 0.05:
                    insights.append("Few exceptional words found (<5% scored 81-100)")
        
        # Top words insight
        if metrics.top_words:
            insights.append(f"Best discoveries: {', '.join(metrics.top_words[:3])}")
        
        return insights

# Global service instance
recombination_metrics_service = RecombinationMetricsService()

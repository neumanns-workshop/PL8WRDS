"""
Global Frequency Scorer for PL8WRDS
===================================

Measures word impressiveness based purely on global corpus frequency.
This captures vocabulary sophistication independent of game constraints.

Frequency Score = f(global_corpus_frequency)
Higher scores = rarer words = more impressive vocabulary
"""

import math
from typing import Dict, Any, List, Tuple
from app.services.word_service import word_service


class FrequencyScorer:
    """
    Pure global frequency-based impressiveness scorer.
    Measures vocabulary sophistication using corpus frequency distributions.
    """
    
    def __init__(self):
        self.frequency_stats = None
        self.percentile_thresholds = None
        
    def _compute_frequency_stats(self):
        """Compute frequency distribution statistics from the corpus."""
        if self.frequency_stats is not None:
            return
            
        print("📊 Computing global frequency statistics...")
        
        frequencies = list(word_service._words.values())
        if not frequencies:
            print("❌ No frequency data available")
            return
            
        frequencies.sort(reverse=True)  # Highest to lowest
        
        # Basic statistics
        total_words = len(frequencies)
        max_freq = max(frequencies)
        min_freq = min(frequencies)
        median_freq = frequencies[total_words // 2]
        mean_freq = sum(frequencies) / total_words
        
        # Log-space statistics (more meaningful for frequency data)
        log_frequencies = [math.log(f + 1) for f in frequencies]
        max_log_freq = max(log_frequencies)
        min_log_freq = min(log_frequencies)
        median_log_freq = log_frequencies[total_words // 2]
        mean_log_freq = sum(log_frequencies) / total_words
        
        # Percentile thresholds for scoring  
        percentiles = [5, 10, 25, 50, 75, 90, 95, 99, 99.9]
        percentile_indices = [int((100 - p) * total_words // 100) for p in percentiles]
        percentile_thresholds = {
            p: frequencies[min(idx, total_words - 1)] 
            for p, idx in zip(percentiles, percentile_indices)
        }
        
        self.frequency_stats = {
            "total_words": total_words,
            "max_frequency": max_freq,
            "min_frequency": min_freq,
            "median_frequency": median_freq,
            "mean_frequency": mean_freq,
            "max_log_frequency": max_log_freq,
            "min_log_frequency": min_log_freq,
            "median_log_frequency": median_log_freq,
            "mean_log_frequency": mean_log_freq
        }
        
        self.percentile_thresholds = percentile_thresholds
        
        print(f"✅ Frequency stats computed for {total_words:,} words")
        print(f"   Range: {min_freq:,} to {max_freq:,}")
        print(f"   Median: {median_freq:,}, Mean: {mean_freq:,.0f}")

    def get_frequency_percentile(self, frequency: int) -> float:
        """Get the frequency percentile for a word (higher = more common)."""
        if self.percentile_thresholds is None:
            self._compute_frequency_stats()
            
        if not self.percentile_thresholds:
            return 50.0
        
        # Find which percentile bucket this frequency falls into
        for percentile in [5, 10, 25, 50, 75, 90, 95, 99, 99.9]:
            if frequency >= self.percentile_thresholds[percentile]:
                return 100 - percentile  # Convert to "rarity percentile"
                
        return 99.9  # Extremely rare

    def score_word(self, word: str) -> Dict[str, Any]:
        """Generate comprehensive frequency-based scoring for a word."""
        if self.frequency_stats is None:
            self._compute_frequency_stats()
            
        word_lower = word.lower()
        frequency = word_service._words.get(word_lower, 0)
        
        if frequency == 0:
            return {"error": f"Word '{word}' not found in corpus"}
        
        # Basic frequency metrics
        log_frequency = math.log(frequency + 1)
        
        # Rarity scores (higher = rarer = more impressive)
        
        # 1. Inverse frequency score (normalized)
        max_log_freq = self.frequency_stats["max_log_frequency"]
        inverse_freq_score = (max_log_freq - log_frequency) / max_log_freq * 100
        
        # 2. Percentile-based rarity score
        frequency_percentile = self.get_frequency_percentile(frequency)
        percentile_score = frequency_percentile  # Already 0-100 scale
        
        # 3. Z-score based rarity (how many standard deviations from mean)
        mean_log_freq = self.frequency_stats["mean_log_frequency"]
        log_frequencies = [math.log(f + 1) for f in word_service._words.values()]
        log_std = math.sqrt(sum((lf - mean_log_freq)**2 for lf in log_frequencies) / len(log_frequencies))
        
        z_score = (mean_log_freq - log_frequency) / log_std if log_std > 0 else 0
        z_score_normalized = max(0, min(100, (z_score + 3) / 6 * 100))  # -3 to +3 σ → 0 to 100
        
        # Combined rarity score (weighted combination)
        combined_score = (
            inverse_freq_score * 0.4 +    # Inverse frequency
            percentile_score * 0.4 +      # Percentile rarity  
            z_score_normalized * 0.2      # Statistical rarity
        )
        
        return {
            "word": word,
            "scores": {
                "inverse_frequency": round(inverse_freq_score, 1),
                "percentile_rarity": round(percentile_score, 1), 
                "z_score_rarity": round(z_score_normalized, 1),
                "combined": round(combined_score, 1)
            },
            "raw_metrics": {
                "frequency": frequency,
                "log_frequency": round(log_frequency, 3),
                "z_score": round(z_score, 3)
            },
            "context": {
                "frequency_rank": self._get_frequency_rank(frequency),
                "total_corpus_words": self.frequency_stats["total_words"],
                "corpus_frequency_percentile": round(100 - frequency_percentile, 1),  # Commonality percentile
                "median_frequency": self.frequency_stats["median_frequency"],
                "mean_frequency": round(self.frequency_stats["mean_frequency"], 0)
            },
            "interpretation": self._interpret_scores(inverse_freq_score, percentile_score, combined_score, frequency)
        }

    def _get_frequency_rank(self, frequency: int) -> int:
        """Get the rank of this frequency (1 = most common)."""
        frequencies = list(word_service._words.values())
        frequencies.sort(reverse=True)
        
        try:
            return frequencies.index(frequency) + 1
        except ValueError:
            # Find closest frequency
            for i, freq in enumerate(frequencies):
                if freq <= frequency:
                    return i + 1
            return len(frequencies)

    def _interpret_scores(self, inverse_freq: float, percentile: float, combined: float, frequency: int) -> Dict[str, str]:
        """Provide human-readable interpretation of frequency scores."""
        
        # Inverse frequency interpretation
        if inverse_freq >= 90:
            inverse_desc = "Extremely rare word (top 0.1% vocabulary)"
        elif inverse_freq >= 80:
            inverse_desc = "Very rare word (sophisticated vocabulary)"
        elif inverse_freq >= 60:
            inverse_desc = "Uncommon word (above average vocabulary)"
        elif inverse_freq >= 40:
            inverse_desc = "Moderately common word"
        elif inverse_freq >= 20:
            inverse_desc = "Common word (everyday vocabulary)"
        else:
            inverse_desc = "Very common word (basic vocabulary)"
        
        # Percentile interpretation
        if percentile >= 95:
            percentile_desc = "Top 5% rarest words"
        elif percentile >= 90:
            percentile_desc = "Top 10% rarest words"
        elif percentile >= 75:
            percentile_desc = "Top 25% rarest words"
        elif percentile >= 50:
            percentile_desc = "Above median rarity"
        elif percentile >= 25:
            percentile_desc = "Below median rarity"
        else:
            percentile_desc = "Very common word"
        
        # Combined interpretation
        if combined >= 85:
            combined_desc = "Exceptional vocabulary sophistication"
        elif combined >= 70:
            combined_desc = "High vocabulary sophistication" 
        elif combined >= 50:
            combined_desc = "Moderate vocabulary level"
        elif combined >= 30:
            combined_desc = "Common vocabulary level"
        else:
            combined_desc = "Basic vocabulary level"
        
        # Frequency bracket
        if frequency >= 100000:
            freq_bracket = "Ultra-high frequency (core vocabulary)"
        elif frequency >= 10000:
            freq_bracket = "High frequency (common words)"
        elif frequency >= 1000:
            freq_bracket = "Medium frequency (familiar words)"
        elif frequency >= 100:
            freq_bracket = "Low frequency (less familiar)"
        elif frequency >= 10:
            freq_bracket = "Very low frequency (rare words)"
        else:
            freq_bracket = "Ultra-low frequency (very rare words)"
        
        return {
            "inverse_frequency": inverse_desc,
            "percentile": percentile_desc,
            "combined": combined_desc,
            "frequency_bracket": freq_bracket
        }

    def get_top_rare_words(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get the rarest words in the corpus by frequency."""
        if self.frequency_stats is None:
            self._compute_frequency_stats()
            
        # Sort words by frequency (lowest first)
        word_freq_pairs = [(word, freq) for word, freq in word_service._words.items()]
        word_freq_pairs.sort(key=lambda x: x[1])  # Lowest frequency first
        
        rare_words = []
        for word, frequency in word_freq_pairs[:limit]:
            score_data = self.score_word(word)
            if "error" not in score_data:
                rare_words.append({
                    "word": word,
                    "frequency": frequency,
                    "combined_score": score_data["scores"]["combined"],
                    "percentile_rarity": score_data["scores"]["percentile_rarity"]
                })
        
        return rare_words

    def get_frequency_distribution(self) -> Dict[str, Any]:
        """Get frequency distribution statistics."""
        if self.frequency_stats is None:
            self._compute_frequency_stats()
            
        return {
            "stats": self.frequency_stats,
            "percentile_thresholds": self.percentile_thresholds
        }

    def batch_score(self, words: List[str]) -> List[Dict[str, Any]]:
        """Score multiple words efficiently."""
        results = []
        for word in words:
            try:
                score = self.score_word(word)
                results.append(score)
            except Exception as e:
                results.append({
                    "word": word,
                    "error": str(e)
                })
        return results


# Global instance
frequency_scorer = FrequencyScorer()

if __name__ == "__main__":
    # Demo the frequency scorer
    print("📊 Frequency Scorer Demo")
    print("=" * 50)
    
    scorer = FrequencyScorer()
    
    test_words = [
        "the",        # Very common
        "dog",        # Common  
        "ambulance",  # Medium
        "pedagogue",  # Rare
        "scaramouche" # Very rare?
    ]
    
    for word in test_words:
        print(f"\n📊 Frequency Analysis: '{word}'")
        print("-" * 30)
        
        result = scorer.score_word(word)
        
        if "error" in result:
            print(f"❌ {result['error']}")
            continue
        
        scores = result["scores"]
        context = result["context"] 
        interpretation = result["interpretation"]
        
        print(f"Scores:")
        print(f"  Inverse Freq: {scores['inverse_frequency']:5.1f}/100 - {interpretation['inverse_frequency']}")
        print(f"  Percentile:   {scores['percentile_rarity']:5.1f}/100 - {interpretation['percentile']}")
        print(f"  Combined:     {scores['combined']:5.1f}/100 - {interpretation['combined']}")
        
        print(f"Context:")
        print(f"  Frequency: {context['frequency']:,} ({interpretation['frequency_bracket']})")
        print(f"  Rank: #{context['frequency_rank']:,} of {context['total_corpus_words']:,}")
    
    # Show frequency distribution
    print(f"\n📈 Corpus Frequency Distribution:")
    distribution = scorer.get_frequency_distribution()
    stats = distribution["stats"]
    print(f"  Total words: {stats['total_words']:,}")
    print(f"  Max frequency: {stats['max_frequency']:,}")
    print(f"  Median frequency: {stats['median_frequency']:,}")
    print(f"  Mean frequency: {stats['mean_frequency']:,.0f}")
    
    # Show top rare words
    print(f"\n🏆 Top 10 Rarest Words:")
    rare_words = scorer.get_top_rare_words(10)
    for i, word_data in enumerate(rare_words, 1):
        word = word_data['word']
        freq = word_data['frequency']
        score = word_data['combined_score']
        print(f"  {i:2d}. {word:15s} - freq: {freq:3d}, score: {score:5.1f}")
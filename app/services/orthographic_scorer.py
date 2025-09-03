"""
Orthographic Complexity Scorer for PL8WRDS
===========================================

Measures the cognitive difficulty of processing letter sequence patterns.
Uses n-gram probabilities from our corpus to score how "natural" vs "unnatural" 
the orthographic patterns are in English spelling.

Orthographic Complexity = f(n-gram_probabilities_in_matching_sequence)
Lower probability patterns = higher complexity = more impressive
"""

import math
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple
from collections import defaultdict
from app.services.word_service import word_service


class OrthographicComplexityScorer:
    """
    Orthographic complexity scorer using n-gram probabilities.
    Measures how cognitively difficult letter patterns are to process.
    """
    
    def __init__(self, model_path: str = "models/orthographic_model.json"):
        self.model_path = model_path
        self.model_loaded = False
        
        # N-gram models (loaded from file or built from corpus)
        self.bigram_probs = {}   # "ab" -> probability
        self.trigram_probs = {}  # "abc" -> probability
        self.total_bigrams = 0
        self.total_trigrams = 0
        
        # Model statistics
        self.model_stats = {}

    def build_model(self) -> None:
        """Build n-gram probability model from word corpus."""
        print("🔤 Building orthographic n-gram model from corpus...")
        
        bigram_counts = defaultdict(int)
        trigram_counts = defaultdict(int)
        total_words = 0
        
        # Extract n-grams from all corpus words, weighted by frequency
        for word, frequency in word_service._words.items():
            word_lower = word.lower()
            word_len = len(word_lower)
            total_words += 1
            
            # Add word boundary markers for more accurate modeling
            padded_word = f"^{word_lower}$"
            
            # Extract bigrams
            for i in range(len(padded_word) - 1):
                bigram = padded_word[i:i+2]
                bigram_counts[bigram] += frequency
            
            # Extract trigrams  
            for i in range(len(padded_word) - 2):
                trigram = padded_word[i:i+3]
                trigram_counts[trigram] += frequency
        
        # Convert counts to probabilities
        self.total_bigrams = sum(bigram_counts.values())
        self.total_trigrams = sum(trigram_counts.values())
        
        self.bigram_probs = {
            bigram: count / self.total_bigrams 
            for bigram, count in bigram_counts.items()
        }
        
        self.trigram_probs = {
            trigram: count / self.total_trigrams
            for trigram, count in trigram_counts.items()
        }
        
        # Compute model statistics
        self._compute_model_stats(bigram_counts, trigram_counts)
        
        self.model_loaded = True
        
        print(f"✅ Orthographic model built:")
        print(f"   Corpus words: {total_words:,}")
        print(f"   Unique bigrams: {len(self.bigram_probs):,}")
        print(f"   Unique trigrams: {len(self.trigram_probs):,}")
        print(f"   Total bigram instances: {self.total_bigrams:,}")
        print(f"   Total trigram instances: {self.total_trigrams:,}")

    def _compute_model_stats(self, bigram_counts: Dict, trigram_counts: Dict) -> None:
        """Compute statistics about the n-gram model."""
        
        # Find most/least common n-grams
        sorted_bigrams = sorted(bigram_counts.items(), key=lambda x: x[1], reverse=True)
        sorted_trigrams = sorted(trigram_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Entropy calculations
        bigram_entropy = -sum(
            p * math.log2(p) for p in self.bigram_probs.values() if p > 0
        )
        trigram_entropy = -sum(
            p * math.log2(p) for p in self.trigram_probs.values() if p > 0
        )
        
        self.model_stats = {
            "total_unique_bigrams": len(self.bigram_probs),
            "total_unique_trigrams": len(self.trigram_probs),
            "bigram_entropy": bigram_entropy,
            "trigram_entropy": trigram_entropy,
            "most_common_bigrams": sorted_bigrams[:20],
            "least_common_bigrams": sorted_bigrams[-20:],
            "most_common_trigrams": sorted_trigrams[:20], 
            "least_common_trigrams": sorted_trigrams[-20:]
        }

    def _extract_matching_sequence(self, word: str, plate: str) -> List[str]:
        """Extract the subsequence from word that matches the plate pattern."""
        word_lower = word.lower()
        plate_lower = plate.lower()
        
        # Find positions of plate letters in word (subsequence matching)
        matching_chars = []
        word_pos = 0
        
        for plate_char in plate_lower:
            # Find next occurrence of this plate character in word
            while word_pos < len(word_lower) and word_lower[word_pos] != plate_char:
                word_pos += 1
            
            if word_pos < len(word_lower):
                matching_chars.append(word_lower[word_pos])
                word_pos += 1
            else:
                # Should not happen if word actually matches plate
                break
        
        return matching_chars

    def _get_ngram_complexity(self, sequence: List[str], n: int) -> Tuple[float, List[Tuple[str, float]]]:
        """Calculate orthographic complexity for n-grams in sequence."""
        if len(sequence) < n:
            return 0.0, []
        
        # Add boundary markers for complete words (since we're now analyzing full words)
        padded_sequence = ['^'] + sequence + ['$']
        
        ngram_scores = []
        total_surprisal = 0.0
        
        for i in range(len(padded_sequence) - n + 1):
            ngram = "".join(padded_sequence[i:i+n])
            
            # Get probability from model (with boundary markers for full words)
            if n == 2:
                prob = self.bigram_probs.get(ngram, 1e-10)  # Smoothing for unseen n-grams
            elif n == 3:
                prob = self.trigram_probs.get(ngram, 1e-10)
            else:
                prob = 1e-10
            
            # Calculate surprisal (information content)
            surprisal = -math.log2(prob) if prob > 0 else 20  # Cap at reasonable value
            
            ngram_scores.append((ngram, surprisal))
            total_surprisal += surprisal
        
        return total_surprisal, ngram_scores

    def score_word_plate(self, word: str, plate: str) -> Dict[str, Any]:
        """Score orthographic complexity of the full word."""
        if not self.model_loaded:
            if not self._load_model():
                self.build_model()
        
        # Verify word matches plate (but analyze full word complexity)
        matching_sequence = self._extract_matching_sequence(word, plate)
        
        if len(matching_sequence) != len(plate):
            return {"error": f"Word '{word}' does not properly match plate '{plate}'"}
        
        # Analyze the FULL WORD'S orthographic complexity, not just the matching sequence
        full_word_chars = list(word.lower())
        
        # Calculate bigram and trigram complexity for the entire word
        bigram_total_surprisal, bigram_details = self._get_ngram_complexity(full_word_chars, 2)
        trigram_total_surprisal, trigram_details = self._get_ngram_complexity(full_word_chars, 3)
        
        # Use AVERAGE surprisal per n-gram for better discrimination
        bigram_complexity = bigram_total_surprisal / len(bigram_details) if bigram_details else 0
        trigram_complexity = trigram_total_surprisal / len(trigram_details) if trigram_details else 0
        
        # Normalize complexities to 0-100 scale
        # Based on actual corpus statistics from 100 word sample:
        # Bigrams: 6.2-11.7 (mean 8.3), Trigrams: 7.3-17.5 (mean 11.9)
        min_bigram_surprisal = 6.0   # 10th percentile (very common patterns)
        max_bigram_surprisal = 12.0  # 90th+ percentile (very rare patterns)
        min_trigram_surprisal = 7.0  # 10th percentile (very common patterns)  
        max_trigram_surprisal = 18.0 # Max observed (very rare patterns)
        
        # Normalize to 0-100 scale with better distribution
        bigram_score = max(0, min(100, 
            (bigram_complexity - min_bigram_surprisal) / (max_bigram_surprisal - min_bigram_surprisal) * 100
        ))
        trigram_score = max(0, min(100,
            (trigram_complexity - min_trigram_surprisal) / (max_trigram_surprisal - min_trigram_surprisal) * 100
        ))
        
        # Combined orthographic complexity score
        combined_score = (
            bigram_score * 0.4 +     # Bigram patterns
            trigram_score * 0.6      # Trigram patterns (more informative)
        )
        
        return {
            "word": word,
            "plate": plate,
            "matching_sequence": "".join(matching_sequence),  # Still show what matched the plate
            "full_word_analyzed": word.lower(),  # Show we analyzed the full word
            "scores": {
                "bigram_complexity": round(bigram_score, 1),
                "trigram_complexity": round(trigram_score, 1),
                "combined_complexity": round(combined_score, 1)
            },
            "raw_metrics": {
                "avg_bigram_surprisal": round(bigram_complexity, 3),
                "avg_trigram_surprisal": round(trigram_complexity, 3),
                "total_bigram_surprisal": round(bigram_total_surprisal, 3),
                "total_trigram_surprisal": round(trigram_total_surprisal, 3),
                "word_length": len(word),
                "total_bigrams": len(bigram_details),
                "total_trigrams": len(trigram_details)
            },
            "ngram_details": {
                "bigrams": [(ngram, round(surprisal, 3)) for ngram, surprisal in bigram_details],
                "trigrams": [(ngram, round(surprisal, 3)) for ngram, surprisal in trigram_details]
            },
            "interpretation": self._interpret_scores(bigram_score, trigram_score, combined_score)
        }

    def _interpret_scores(self, bigram_score: float, trigram_score: float, combined_score: float) -> Dict[str, str]:
        """Provide human-readable interpretation of orthographic complexity scores."""
        
        # Bigram interpretation
        if bigram_score >= 80:
            bigram_desc = "Highly unusual bigram patterns"
        elif bigram_score >= 60:
            bigram_desc = "Somewhat unusual bigram patterns"
        elif bigram_score >= 40:
            bigram_desc = "Moderately natural bigram patterns"
        elif bigram_score >= 20:
            bigram_desc = "Fairly natural bigram patterns"
        else:
            bigram_desc = "Very natural bigram patterns"
        
        # Trigram interpretation
        if trigram_score >= 80:
            trigram_desc = "Highly complex trigram sequences"
        elif trigram_score >= 60:
            trigram_desc = "Moderately complex trigram sequences"
        elif trigram_score >= 40:
            trigram_desc = "Average trigram complexity"
        elif trigram_score >= 20:
            trigram_desc = "Simple trigram sequences"
        else:
            trigram_desc = "Very simple trigram sequences"
        
        # Combined interpretation
        if combined_score >= 85:
            combined_desc = "Extremely high orthographic complexity"
        elif combined_score >= 70:
            combined_desc = "High orthographic complexity"
        elif combined_score >= 50:
            combined_desc = "Moderate orthographic complexity"
        elif combined_score >= 30:
            combined_desc = "Low orthographic complexity"
        else:
            combined_desc = "Very low orthographic complexity"
        
        return {
            "bigram_patterns": bigram_desc,
            "trigram_patterns": trigram_desc,
            "overall_complexity": combined_desc
        }

    def save_model(self, output_path: str = None) -> None:
        """Save the orthographic model to disk."""
        if not output_path:
            output_path = self.model_path
            
        print(f"💾 Saving orthographic model to {output_path}...")
        
        model_data = {
            "metadata": {
                "version": "1.0",
                "created_at": __import__('time').strftime("%Y-%m-%d %H:%M:%S"),
                "model_type": "orthographic_complexity"
            },
            "bigram_probs": self.bigram_probs,
            "trigram_probs": self.trigram_probs,
            "total_bigrams": self.total_bigrams,
            "total_trigrams": self.total_trigrams,
            "model_stats": self.model_stats
        }
        
        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(model_data, f, indent=2)
        
        file_size = Path(output_path).stat().st_size
        print(f"✅ Orthographic model saved: {file_size / 1024 / 1024:.1f} MB")

    def _load_model(self) -> bool:
        """Load the pre-built orthographic model from disk."""
        if self.model_loaded:
            return True
            
        model_file = Path(self.model_path)
        if not model_file.exists():
            print(f"📝 Orthographic model not found at {self.model_path}, will build from corpus")
            return False
        
        try:
            print(f"🔤 Loading orthographic model from {self.model_path}...")
            
            with open(model_file, 'r') as f:
                model_data = json.load(f)
            
            self.bigram_probs = model_data.get("bigram_probs", {})
            self.trigram_probs = model_data.get("trigram_probs", {})
            self.total_bigrams = model_data.get("total_bigrams", 0)
            self.total_trigrams = model_data.get("total_trigrams", 0)
            self.model_stats = model_data.get("model_stats", {})
            
            self.model_loaded = True
            
            print(f"✅ Orthographic model loaded:")
            print(f"   Bigrams: {len(self.bigram_probs):,}")
            print(f"   Trigrams: {len(self.trigram_probs):,}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error loading orthographic model: {e}")
            return False

    def get_model_stats(self) -> Dict[str, Any]:
        """Get statistics about the orthographic model."""
        if not self.model_loaded:
            if not self._load_model():
                return {"error": "Orthographic model could not be loaded"}
        
        return {
            "model_ready": self.model_loaded,
            "stats": self.model_stats,
            "ngram_counts": {
                "bigrams": len(self.bigram_probs),
                "trigrams": len(self.trigram_probs)
            }
        }

    def batch_score(self, word_plate_pairs: List[Tuple[str, str]]) -> List[Dict[str, Any]]:
        """Score multiple word-plate pairs efficiently."""
        results = []
        for word, plate in word_plate_pairs:
            try:
                score = self.score_word_plate(word, plate)
                results.append(score)
            except Exception as e:
                results.append({
                    "word": word,
                    "plate": plate,
                    "error": str(e)
                })
        return results


# Global instance
orthographic_scorer = OrthographicComplexityScorer()

if __name__ == "__main__":
    # Demo the orthographic complexity scorer
    print("🔤 Orthographic Complexity Scorer Demo")
    print("=" * 60)
    
    scorer = OrthographicComplexityScorer()
    scorer.build_model()
    
    test_cases = [
        ("car", "CAR"),      # Simple, natural
        ("care", "CAR"),     # Moderate complexity
        ("macabre", "CAR"),  # Higher complexity
        ("ambulance", "ABC"), # Mixed patterns
        ("pedagogue", "DOG")  # Complex patterns
    ]
    
    for word, plate in test_cases:
        print(f"\n🔤 Orthographic Analysis: '{word}' + '{plate}'")
        print("-" * 40)
        
        result = scorer.score_word_plate(word, plate)
        
        if "error" in result:
            print(f"❌ {result['error']}")
            continue
        
        scores = result["scores"]
        raw_metrics = result["raw_metrics"]
        interpretation = result["interpretation"]
        ngram_details = result["ngram_details"]
        
        print(f"Matching sequence: '{result['matching_sequence']}'")
        print(f"Scores:")
        print(f"  Bigram complexity:  {scores['bigram_complexity']:5.1f}/100 - {interpretation['bigram_patterns']}")
        print(f"  Trigram complexity: {scores['trigram_complexity']:5.1f}/100 - {interpretation['trigram_patterns']}")
        print(f"  Combined:           {scores['combined_complexity']:5.1f}/100 - {interpretation['overall_complexity']}")
        
        print(f"N-gram details:")
        print(f"  Bigrams: {ngram_details['bigrams']}")
        print(f"  Trigrams: {ngram_details['trigrams']}")
    
    # Show model statistics
    print(f"\n📊 Model Statistics:")
    stats = scorer.get_model_stats()
    if "error" not in stats:
        model_stats = stats["stats"]
        print(f"  Bigram entropy: {model_stats.get('bigram_entropy', 0):.2f}")
        print(f"  Trigram entropy: {model_stats.get('trigram_entropy', 0):.2f}")
        print(f"  Most common trigrams: {model_stats.get('most_common_trigrams', [])[:5]}")

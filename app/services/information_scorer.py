"""
Information Content Scorer for PL8WRDS
======================================

Measures the Shannon information content of word choices given plate constraints.
Uses information theory to quantify how surprising/informative a word choice is.

Information Content = -log₂(P(word|plate))
where P(word|plate) = corpus_freq(word) / sum(corpus_freq of all solutions)
"""

import json
import math
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from app.services.solver_service import solve_combination
from app.services.word_service import word_service


class InformationContentScorer:
    """
    Information-theoretic scorer measuring Shannon content of word choices.
    Quantifies how many bits of information a word choice conveys given plate constraints.
    """
    
    def __init__(self, model_path: str = "models/information_model.json"):
        self.model_path = model_path
        self.model_loaded = False
        
        # Model data
        self.metadata = {}
        self.plate_solutions = {}  # plate -> [(word, corpus_freq), ...]
        self.plate_info_stats = {}  # plate -> {total_freq_mass, entropy, etc.}
        self.word_info_scores = {}  # (word, plate) -> information_bits

    def build_model(self, max_plates: int = 500) -> None:
        """Build information content model from solver data."""
        print(f"🧮 Building Information Content model (up to {max_plates} plates)...")
        
        # Generate systematic plates
        plates = self._generate_plates(max_plates)
        
        processed = 0
        successful = 0
        
        for plate in plates:
            try:
                # Get solutions from solver
                matches = solve_combination(plate, mode="subsequence")
                
                if matches and len(matches) > 0:
                    successful += 1
                    
                    # Get corpus frequencies for all solutions
                    solution_data = []
                    total_freq_mass = 0
                    
                    for word, _ in matches:  # solver returns (word, corpus_freq)
                        corpus_freq = word_service._words.get(word.lower(), 1)
                        solution_data.append((word.lower(), corpus_freq))
                        total_freq_mass += corpus_freq
                    
                    self.plate_solutions[plate] = solution_data
                    
                    # Pre-compute information statistics for this plate
                    self._compute_plate_info_stats(plate, solution_data, total_freq_mass)
                
                processed += 1
                if processed % 100 == 0:
                    print(f"   Processed {processed}/{len(plates)} plates, {successful} with solutions...")
                    
            except Exception as e:
                processed += 1
                continue
        
        print(f"✅ Information model built: {successful}/{processed} plates processed")
        self.model_loaded = True

    def _generate_plates(self, max_plates: int) -> List[str]:
        """Generate systematic 3-letter plate combinations."""
        consonants = 'BCDFGHJKLMNPQRSTVWXYZ'
        vowels = 'AEIOU'
        plates = []
        
        # Consonant-Vowel-Consonant patterns (most readable)
        for c1 in consonants:
            for v in vowels:
                for c2 in consonants:
                    if len(plates) < max_plates:
                        plates.append(c1 + v + c2)
        
        return plates[:max_plates]

    def _compute_plate_info_stats(self, plate: str, solution_data: List[Tuple[str, int]], total_freq_mass: int) -> None:
        """Compute information statistics for a plate."""
        if total_freq_mass == 0:
            return
            
        # Compute entropy and information content for each solution
        entropy = 0.0
        word_info_scores = {}
        
        for word, corpus_freq in solution_data:
            p_word_given_plate = corpus_freq / total_freq_mass
            
            if p_word_given_plate > 0:
                # Shannon information content in bits
                info_bits = -math.log2(p_word_given_plate)
                word_info_scores[word] = info_bits
                
                # Contribute to plate entropy
                entropy -= p_word_given_plate * math.log2(p_word_given_plate)
            
            # Store individual word information scores
            self.word_info_scores[(word, plate)] = info_bits
        
        # Store plate-level statistics
        self.plate_info_stats[plate] = {
            "total_freq_mass": total_freq_mass,
            "entropy": entropy,
            "num_solutions": len(solution_data),
            "avg_info_bits": sum(word_info_scores.values()) / len(word_info_scores) if word_info_scores else 0,
            "max_info_bits": max(word_info_scores.values()) if word_info_scores else 0,
            "min_info_bits": min(word_info_scores.values()) if word_info_scores else 0
        }

    def score_word(self, word: str, plate: str) -> Dict[str, Any]:
        """Generate information content score for a word-plate pair."""
        if not self.model_loaded:
            if not self._load_model():
                return {"error": "Information model could not be loaded. Build it first with build_model()"}
        
        word_lower = word.lower()
        plate_upper = plate.upper()
        
        # Get pre-computed information score
        info_bits = self.word_info_scores.get((word_lower, plate_upper))
        if info_bits is None:
            return {"error": f"No information data for word '{word}' on plate '{plate}'"}
        
        # Get plate statistics for context
        plate_stats = self.plate_info_stats.get(plate_upper, {})
        
        # Get global corpus frequency for reference
        corpus_freq = word_service._words.get(word_lower, 1)
        
        # Normalize information content to 0-100 scale
        # High information (surprising choice) = high score
        # Low information (predictable choice) = low score
        max_possible_info = math.log2(plate_stats.get("total_freq_mass", 1))
        normalized_score = min((info_bits / max_possible_info) * 100, 100) if max_possible_info > 0 else 0
        
        return {
            "word": word,
            "plate": plate,
            "scores": {
                "information_bits": round(info_bits, 2),
                "normalized": round(normalized_score, 1),
                "percentile": self._compute_percentile(info_bits, plate_upper)
            },
            "raw_metrics": {
                "probability": round(2**(-info_bits), 6),
                "corpus_frequency": corpus_freq,
                "log_corpus_freq": round(math.log(corpus_freq + 1), 3)
            },
            "context": {
                "plate_entropy": round(plate_stats.get("entropy", 0), 3),
                "plate_solutions": plate_stats.get("num_solutions", 0),
                "avg_info_bits": round(plate_stats.get("avg_info_bits", 0), 2),
                "max_info_bits": round(plate_stats.get("max_info_bits", 0), 2),
                "total_freq_mass": plate_stats.get("total_freq_mass", 0)
            },
            "interpretation": self._interpret_score(info_bits, normalized_score, plate_stats)
        }

    def _compute_percentile(self, info_bits: float, plate: str) -> float:
        """Compute what percentile this information score is for this plate."""
        plate_stats = self.plate_info_stats.get(plate, {})
        if not plate_stats:
            return 0.0
            
        avg_info = plate_stats.get("avg_info_bits", 0)
        max_info = plate_stats.get("max_info_bits", 0)
        
        if max_info <= avg_info:
            return 50.0
            
        # Simple linear interpolation between avg and max
        if info_bits >= max_info:
            return 100.0
        elif info_bits <= avg_info:
            return 50.0 * (info_bits / avg_info) if avg_info > 0 else 0.0
        else:
            return 50.0 + 50.0 * ((info_bits - avg_info) / (max_info - avg_info))

    def _interpret_score(self, info_bits: float, normalized_score: float, plate_stats: Dict) -> Dict[str, str]:
        """Provide human-readable interpretation of information scores."""
        
        avg_info = plate_stats.get("avg_info_bits", 0)
        
        # Information content interpretation
        if info_bits >= 15:
            info_desc = "Extremely informative choice (very surprising)"
        elif info_bits >= 10:
            info_desc = "Highly informative choice (quite surprising)"
        elif info_bits >= 7:
            info_desc = "Moderately informative choice"
        elif info_bits >= 4:
            info_desc = "Somewhat predictable choice"
        else:
            info_desc = "Highly predictable choice"
        
        # Relative to plate average
        if info_bits > avg_info * 1.5:
            relative_desc = "Well above average for this plate"
        elif info_bits > avg_info * 1.1:
            relative_desc = "Above average for this plate"  
        elif info_bits > avg_info * 0.9:
            relative_desc = "About average for this plate"
        elif info_bits > avg_info * 0.5:
            relative_desc = "Below average for this plate"
        else:
            relative_desc = "Well below average for this plate"
        
        # Overall impression  
        if normalized_score >= 80:
            overall_desc = "Exceptional information content"
        elif normalized_score >= 60:
            overall_desc = "High information content"
        elif normalized_score >= 40:
            overall_desc = "Moderate information content"
        elif normalized_score >= 20:
            overall_desc = "Low information content"
        else:
            overall_desc = "Very predictable choice"
        
        return {
            "information": info_desc,
            "relative": relative_desc,
            "overall": overall_desc
        }

    def get_top_words_for_plate(self, plate: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top words for a plate by information content."""
        if not self.model_loaded:
            if not self._load_model():
                return []
        
        plate_upper = plate.upper()
        if plate_upper not in self.plate_solutions:
            return []
        
        # Score all words for this plate
        word_scores = []
        for word, corpus_freq in self.plate_solutions[plate_upper]:
            info_bits = self.word_info_scores.get((word, plate_upper), 0)
            word_scores.append({
                "word": word,
                "information_bits": round(info_bits, 2),
                "probability": round(2**(-info_bits), 6),
                "corpus_frequency": corpus_freq
            })
        
        # Sort by information content (highest first)
        word_scores.sort(key=lambda x: x["information_bits"], reverse=True)
        return word_scores[:limit]

    def save_model(self, output_path: str = None) -> None:
        """Save the information content model to disk."""
        if not output_path:
            output_path = self.model_path
            
        print(f"💾 Saving information model to {output_path}...")
        
        # Convert data for JSON serialization
        word_info_scores_serializable = {
            f"{word}|{plate}": score 
            for (word, plate), score in self.word_info_scores.items()
        }
        
        model_data = {
            "metadata": {
                "version": "1.0",
                "created_at": __import__('time').strftime("%Y-%m-%d %H:%M:%S"),
                "model_type": "information_content"
            },
            "plate_solutions": self.plate_solutions,
            "plate_info_stats": self.plate_info_stats,
            "word_info_scores": word_info_scores_serializable
        }
        
        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(model_data, f, indent=2, sort_keys=True)
        
        file_size = Path(output_path).stat().st_size
        print(f"✅ Information model saved: {file_size / 1024 / 1024:.1f} MB")

    def _load_model(self) -> bool:
        """Load the pre-built information content model from disk."""
        if self.model_loaded:
            return True
            
        model_file = Path(self.model_path)
        if not model_file.exists():
            print(f"❌ Information model not found: {self.model_path}")
            return False
        
        try:
            print(f"🧮 Loading information model from {self.model_path}...")
            
            with open(model_file, 'r') as f:
                model_data = json.load(f)
            
            self.metadata = model_data.get("metadata", {})
            self.plate_solutions = model_data.get("plate_solutions", {})
            self.plate_info_stats = model_data.get("plate_info_stats", {})
            
            # Deserialize word info scores
            word_info_scores_data = model_data.get("word_info_scores", {})
            self.word_info_scores = {}
            for key, score in word_info_scores_data.items():
                word, plate = key.split("|", 1)
                self.word_info_scores[(word, plate)] = score
            
            self.model_loaded = True
            
            print(f"✅ Information model loaded:")
            print(f"   Version: {self.metadata.get('version', 'unknown')}")
            print(f"   Plates: {len(self.plate_solutions)}")
            print(f"   Info scores: {len(self.word_info_scores)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error loading information model: {e}")
            return False

    def get_model_stats(self) -> Dict[str, Any]:
        """Get statistics about the loaded model."""
        if not self.model_loaded:
            if not self._load_model():
                return {"error": "Information model could not be loaded"}
        
        # Aggregate statistics across all plates
        all_entropies = [stats["entropy"] for stats in self.plate_info_stats.values()]
        all_info_scores = list(self.word_info_scores.values())
        
        return {
            "metadata": self.metadata,
            "model_ready": self.model_loaded,
            "stats": {
                "total_plates": len(self.plate_solutions),
                "total_info_scores": len(self.word_info_scores),
                "avg_plate_entropy": sum(all_entropies) / len(all_entropies) if all_entropies else 0,
                "avg_information_bits": sum(all_info_scores) / len(all_info_scores) if all_info_scores else 0,
                "max_information_bits": max(all_info_scores) if all_info_scores else 0,
                "min_information_bits": min(all_info_scores) if all_info_scores else 0
            }
        }


# Global instance
information_scorer = InformationContentScorer()

if __name__ == "__main__":
    # Demo the Information Content scorer
    import asyncio
    
    async def demo():
        print("🧮 Information Content Scorer Demo")
        print("=" * 50)
        
        scorer = InformationContentScorer()
        
        # Build small model for demo
        scorer.build_model(max_plates=50)
        
        test_cases = [
            ("car", "CAR"),
            ("big", "BIG"),
            ("ambulance", "BAD")
        ]
        
        for word, plate in test_cases:
            print(f"\n📊 Information Analysis: '{word}' + '{plate}'")
            print("-" * 40)
            
            result = scorer.score_word(word, plate)
            
            if "error" in result:
                print(f"❌ {result['error']}")
                continue
            
            scores = result["scores"]
            context = result["context"]
            interpretation = result["interpretation"]
            
            print(f"Information: {scores['information_bits']:.2f} bits - {interpretation['information']}")
            print(f"Normalized:  {scores['normalized']:.1f}/100 - {interpretation['overall']}")
            print(f"Percentile:  {scores['percentile']:.1f}% - {interpretation['relative']}")
            print(f"Context: {context['plate_solutions']} solutions, {context['plate_entropy']:.2f} entropy")
    
    asyncio.run(demo())

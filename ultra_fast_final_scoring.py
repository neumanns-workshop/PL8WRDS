#!/usr/bin/env python3
"""
Ultra-Fast Final Scoring
========================

The ultimate performant approach:
- Frequency & Orthographic: instant lookup (pre-computed) 
- Information: fast lookup table (pre-computed)
- Clean data structure: {word_id: info_score}
"""

import json
import time
from pathlib import Path
from typing import Dict, Any
from tqdm import tqdm

# Import the information scorer (for lookup tables)
from app.services.information_scorer import InformationContentScorer  

class UltraFastScorer:
    """Ultra-fast scoring using all pre-computed data."""
    
    def __init__(self):
        self.information_scorer = InformationContentScorer()
        self.word_properties = {}  # word -> {frequency_score, orthographic_score}
        
    def setup(self):
        """Load all pre-computed data."""
        print("🔧 Setting up ultra-fast scorer...")
        
        # Load pre-computed word properties (frequency + orthographic)
        print("📚 Loading pre-computed word scores...")
        dict_path = Path("client_game_data/words/dictionary.json")
        
        with open(dict_path, 'r') as f:
            word_dict = json.load(f)
        
        # Build word -> properties lookup
        for word_id, word_data in word_dict.items():
            word = word_data["word"]
            self.word_properties[word] = {
                "frequency_score": word_data["frequency_score"],
                "orthographic_score": word_data["orthographic_score"]
            }
        
        print(f"   ✅ Loaded {len(self.word_properties):,} word properties")
        
        # Load information scorer lookup tables
        if not self.information_scorer._load_model():
            print("❌ Information model not found! Run optimized_ensemble_scoring.py first to build it.")
            return False
            
        print("✅ Ultra-fast setup complete!")
        return True
    
    def score_all_solutions_ultra_fast(self):
        """Generate final game data with ultra-fast lookups."""
        print("⚡ Ultra-Fast Final Scoring")
        print("=" * 50)
        
        # Load pregenerated solutions
        solutions_path = Path("client_game_data/pregenerated_solutions.json")
        with open(solutions_path, 'r') as f:
            data = json.load(f)
        
        plates = data["plates"]
        word_dict_old = data["word_dict"]
        
        total_solutions = sum(len(solutions) for solutions in plates.values())
        print(f"🎯 Processing {len(plates):,} plates with {total_solutions:,} solutions")
        
        # Build final data structure
        final_plates = []
        info_lookups = 0
        info_hits = 0
        
        start_time = time.time()
        
        for plate, solution_objects in tqdm(plates.items(), desc="Processing plates"):
            plate_solutions = {}  # word_id -> info_score
            
            for sol_obj in solution_objects:
                word = sol_obj["word"]
                word_id = sol_obj["word_id"]
                
                # Get information score (fast lookup from pre-computed table)
                try:
                    info_lookups += 1
                    info_result = self.information_scorer.score_word(word, plate)
                    
                    if "error" not in info_result:
                        info_score = info_result["scores"]["normalized"]
                        info_hits += 1
                    else:
                        info_score = 0.0
                        
                except Exception:
                    info_score = 0.0
                
                # Store just the info score - frequency & orthographic are in word dictionary
                plate_solutions[str(word_id)] = round(info_score, 1)
            
            # Add to final plates structure
            final_plates.append({
                "letters": list(plate.lower()),
                "solutions": plate_solutions
            })
        
        elapsed = time.time() - start_time
        
        # Create final optimized dictionary (word_id -> word + scores)
        print("📚 Creating final optimized word dictionary...")
        final_word_dict = {}
        
        for word, word_info in word_dict_old.items():
            word_id = str(word_info["word_id"])
            word_props = self.word_properties.get(word, {"frequency_score": 0, "orthographic_score": 0})
            
            final_word_dict[word_id] = {
                "word": word,
                "frequency_score": word_props["frequency_score"],
                "orthographic_score": word_props["orthographic_score"]
            }
        
        # Create final game data
        final_game_data = {
            "format": "v3_ultra_optimized",
            "description": "Ultra-optimized: word properties pre-computed, only info scores stored per plate",
            "data_structure": {
                "word_dictionary": "word_id -> {word, frequency_score, orthographic_score}",
                "plate_solutions": "word_id -> information_score",
                "ensemble_calculation": "(frequency_score + info_score + orthographic_score) / 3"
            },
            "generation_info": {
                "frequency_scores": "pre-computed (word property)",
                "orthographic_scores": "pre-computed (word property)",
                "information_scores": "lookup table (word-plate property)",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            },
            "plates": final_plates
        }
        
        # Save final data
        self.save_ultra_optimized_data(final_game_data, final_word_dict, elapsed, info_hits, info_lookups)
    
    def save_ultra_optimized_data(self, game_data: Dict, word_dict: Dict, elapsed: float, info_hits: int, info_lookups: int):
        """Save the ultra-optimized final data."""
        import gzip
        
        print("💾 Saving ultra-optimized final data...")
        
        # Save compressed game data
        main_path = Path("client_game_data/pl8wrds_complete.json.gz")
        with gzip.open(main_path, 'wt', encoding='utf-8') as f:
            json.dump(game_data, f)
        
        # Save word dictionary
        dict_path = Path("client_game_data/words/dictionary.json")
        with open(dict_path, 'w') as f:
            json.dump(word_dict, f)
        
        # Calculate sizes
        main_size = main_path.stat().st_size / (1024 * 1024)
        dict_size = dict_path.stat().st_size / (1024 * 1024)
        
        total_solutions = sum(len(plate["solutions"]) for plate in game_data["plates"])
        
        print(f"✅ Ultra-optimized data saved!")
        print(f"   📄 Main data: {main_size:.1f}MB (compressed)")
        print(f"   📚 Dictionary: {dict_size:.1f}MB")
        print(f"   📊 Plates: {len(game_data['plates']):,}")
        print(f"   🔤 Solutions: {total_solutions:,}")
        print(f"   ⏱️  Generation time: {elapsed:.1f}s")
        print(f"   🎯 Info lookup success: {info_hits:,}/{info_lookups:,} ({info_hits/info_lookups*100:.1f}%)")
        
        print(f"\n🎮 Frontend Usage:")
        print(f"   📦 Load: pl8wrds_complete.json.gz + words/dictionary.json")
        print(f"   🧮 Calculate: (freq_score + info_score + ortho_score) / 3") 
        print(f"   📊 Display: E(ensemble), V(vocab), I(info), O(ortho) scores")


def main():
    """Main execution."""
    scorer = UltraFastScorer()
    
    if not scorer.setup():
        return
        
    try:
        scorer.score_all_solutions_ultra_fast()
        print("\n🚀 Ultra-fast scoring completed!")
        
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Pre-compute Orthographic Scores
===============================

Add orthographic scores to the word dictionary alongside frequency scores.
This leaves only information scoring for runtime.
"""

import json
import multiprocessing as mp
from pathlib import Path
from tqdm import tqdm
from typing import List, Tuple, Dict

# Import the orthographic scorer
from app.services.orthographic_scorer import OrthographicComplexityScorer

def score_word_batch_ortho(word_batch: List[str]) -> List[Tuple[str, float]]:
    """Score orthographic complexity for a batch of words."""
    from app.services.orthographic_scorer import OrthographicComplexityScorer
    
    scorer = OrthographicComplexityScorer()
    if not scorer._load_model():
        scorer.build_model()
    
    results = []
    for word in word_batch:
        try:
            # For orthographic scoring, we need a plate context, but since it's analyzing
            # word patterns, let's use a dummy plate. Actually, let me check if we can 
            # score just the word without plate context.
            
            # The orthographic scorer needs word + plate for matching sequence
            # Let's use the word itself as plate for pattern analysis
            ortho_result = scorer.score_word_plate(word, word.upper()[:3].ljust(3, 'X'))
            
            if "error" in ortho_result:
                ortho_score = 0.0
            else:
                ortho_score = ortho_result["scores"]["combined_complexity"]
            
            results.append((word, round(ortho_score, 1)))
            
        except Exception as e:
            results.append((word, 0.0))
    
    return results

def add_orthographic_scores():
    """Add orthographic scores to existing word dictionary."""
    print("🔤 Adding Orthographic Scores to Word Dictionary")
    print("=" * 60)
    
    # Load current word dictionary with frequency scores
    dict_path = Path("client_game_data/words/dictionary.json")
    if not dict_path.exists():
        print("❌ Word dictionary not found. Run parallel_frequency_precompute.py first!")
        return
    
    with open(dict_path, 'r') as f:
        word_dict = json.load(f)
    
    print(f"📊 Found {len(word_dict):,} words with frequency scores")
    
    # Extract just the words for orthographic scoring
    words = [word_data["word"] for word_data in word_dict.values()]
    
    # Determine number of workers
    num_cores = mp.cpu_count()
    num_workers = min(num_cores - 1, 8)
    print(f"🚀 Using {num_workers} parallel workers for orthographic scoring")
    
    # Split words into chunks
    chunk_size = len(words) // num_workers
    chunks = [words[i:i + chunk_size] for i in range(0, len(words), chunk_size)]
    print(f"📦 Split into {len(chunks)} chunks (~{chunk_size:,} words each)")
    
    # Process chunks in parallel
    print("⚡ Computing orthographic scores...")
    
    with mp.Pool(processes=num_workers) as pool:
        results = list(tqdm(
            pool.imap(score_word_batch_ortho, chunks),
            total=len(chunks),
            desc="Processing chunks",
            unit="chunk"
        ))
    
    # Build word -> orthographic_score mapping
    print("🔗 Combining results...")
    ortho_scores = {}
    successful = 0
    
    for chunk_results in results:
        for word, ortho_score in chunk_results:
            ortho_scores[word] = ortho_score
            if ortho_score > 0:
                successful += 1
    
    # Update word dictionary with orthographic scores
    print("💾 Updating word dictionary...")
    for word_id, word_data in word_dict.items():
        word = word_data["word"]
        ortho_score = ortho_scores.get(word, 0.0)
        
        # Add orthographic score to existing data
        word_dict[word_id]["orthographic_score"] = ortho_score
    
    # Save updated dictionary
    with open(dict_path, 'w') as f:
        json.dump(word_dict, f)
    
    dict_size = dict_path.stat().st_size / (1024 * 1024)
    
    print(f"✅ Orthographic scores added!")
    print(f"   📚 Updated dictionary: {dict_path} ({dict_size:.1f}MB)")
    print(f"   🔤 Words with ortho scores: {successful:,}/{len(words):,}")
    
    # Show sample scores
    print(f"\n📝 Sample word scores:")
    sample_items = list(word_dict.items())[:10]
    for word_id, data in sample_items:
        word = data["word"]
        freq = data.get("frequency_score", 0)
        ortho = data.get("orthographic_score", 0)
        print(f"   {word:15s}: freq={freq:5.1f}, ortho={ortho:5.1f}")

if __name__ == "__main__":
    try:
        if __name__ == '__main__':
            mp.set_start_method('spawn', force=True)
        
        add_orthographic_scores()
        print("\n🎉 Orthographic score pre-computation completed!")
        
    except KeyboardInterrupt:
        print("\n⚠️  Pre-computation interrupted by user")
    except Exception as e:
        print(f"\n❌ Pre-computation failed: {e}")
        import traceback
        traceback.print_exc()

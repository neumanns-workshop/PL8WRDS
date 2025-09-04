#!/usr/bin/env python3
"""
Parallel Frequency Score Pre-computation
========================================

Pre-compute frequency scores for all words using multiple CPU cores.
Much faster than sequential processing.
"""

import json
import multiprocessing as mp
from pathlib import Path
from tqdm import tqdm
from typing import List, Tuple, Dict

# Import the frequency scorer
from app.services.frequency_scorer import frequency_scorer

def score_word_batch(word_batch: List[Tuple[str, Dict]]) -> List[Tuple[str, Dict]]:
    """Score a batch of words. This runs in a worker process."""
    # Initialize frequency scorer in this worker process
    from app.services.frequency_scorer import frequency_scorer
    frequency_scorer._compute_frequency_stats()
    
    results = []
    for word, word_info in word_batch:
        try:
            freq_result = frequency_scorer.score_word(word)
            
            if "error" in freq_result:
                frequency_score = 0.0
            else:
                frequency_score = freq_result["scores"]["combined"]
            
            updated_info = {
                "word_id": word_info["word_id"],
                "corpus_frequency": word_info["corpus_frequency"],
                "frequency_score": round(frequency_score, 1)
            }
            results.append((word, updated_info))
            
        except Exception as e:
            # Fallback for errors
            updated_info = {
                "word_id": word_info["word_id"], 
                "corpus_frequency": word_info["corpus_frequency"],
                "frequency_score": 0.0
            }
            results.append((word, updated_info))
    
    return results

def chunk_words(word_dict: Dict, num_chunks: int) -> List[List[Tuple[str, Dict]]]:
    """Split words into chunks for parallel processing."""
    words_list = list(word_dict.items())
    chunk_size = len(words_list) // num_chunks
    
    chunks = []
    for i in range(0, len(words_list), chunk_size):
        chunk = words_list[i:i + chunk_size]
        chunks.append(chunk)
    
    return chunks

def parallel_precompute_frequency_scores():
    """Pre-compute frequency scores using multiple processes."""
    print("⚡ Parallel Frequency Score Pre-computation")
    print("=" * 60)
    
    # Load existing pregenerated solutions
    print("📚 Loading pregenerated solutions...")
    solutions_path = Path("client_game_data/pregenerated_solutions.json")
    
    if not solutions_path.exists():
        print(f"❌ Pregenerated solutions not found at {solutions_path}")
        return
    
    with open(solutions_path, 'r') as f:
        data = json.load(f)
    
    word_dict = data["word_dict"]
    total_words = len(word_dict)
    print(f"📊 Found {total_words:,} unique words")
    
    # Determine number of worker processes
    num_cores = mp.cpu_count()
    num_workers = min(num_cores - 1, 8)  # Leave 1 core free, max 8 workers
    print(f"🚀 Using {num_workers} parallel workers ({num_cores} cores available)")
    
    # Split words into chunks
    print("📦 Splitting words into chunks...")
    chunks = chunk_words(word_dict, num_workers)
    actual_chunks = len(chunks)
    avg_chunk_size = total_words // actual_chunks
    print(f"   Created {actual_chunks} chunks (~{avg_chunk_size:,} words each)")
    
    # Process chunks in parallel
    print("⚡ Processing chunks in parallel...")
    
    with mp.Pool(processes=num_workers) as pool:
        # Use imap for progress tracking
        results = list(tqdm(
            pool.imap(score_word_batch, chunks),
            total=len(chunks),
            desc="Processing chunks",
            unit="chunk"
        ))
    
    # Combine results
    print("🔗 Combining results...")
    updated_word_dict = {}
    successful = 0
    failed = 0
    
    for chunk_results in results:
        for word, word_info in chunk_results:
            updated_word_dict[word] = word_info
            if word_info["frequency_score"] > 0:
                successful += 1
            else:
                failed += 1
    
    print(f"📊 Scoring Summary:")
    print(f"   ✅ Successful: {successful:,}/{total_words:,} ({successful/total_words*100:.1f}%)")
    print(f"   ❌ Failed: {failed:,}")
    
    # Update the data with new word dictionary
    data["word_dict"] = updated_word_dict
    
    # Save updated pregenerated solutions
    print("💾 Saving updated data...")
    with open(solutions_path, 'w') as f:
        json.dump(data, f)
    
    # Create the optimized word dictionary for frontend
    print("📚 Creating optimized word dictionary for frontend...")
    frontend_word_dict = {}
    for word, info in updated_word_dict.items():
        frontend_word_dict[str(info["word_id"])] = {
            "word": word,
            "frequency_score": info["frequency_score"]
        }
    
    # Save frontend word dictionary
    dict_path = Path("client_game_data/words/dictionary.json")
    dict_path.parent.mkdir(exist_ok=True)
    with open(dict_path, 'w') as f:
        json.dump(frontend_word_dict, f)
    
    dict_size = dict_path.stat().st_size / (1024 * 1024)  # MB
    
    print(f"✅ Parallel frequency scoring completed!")
    print(f"   📄 Updated solutions: {solutions_path}")
    print(f"   📚 Frontend dictionary: {dict_path} ({dict_size:.1f}MB)")
    print(f"   🔢 Words with scores: {successful:,}")
    
    # Show some examples
    print(f"\n📝 Sample frequency scores:")
    sample_words = list(updated_word_dict.items())[:10]
    for word, info in sample_words:
        freq_score = info['frequency_score']
        corp_freq = info['corpus_frequency']
        print(f"   {word:15s}: {freq_score:5.1f}/100 (freq: {corp_freq:,})")

if __name__ == "__main__":
    try:
        # Ensure we can use multiprocessing
        if __name__ == '__main__':
            mp.set_start_method('spawn', force=True)
        
        parallel_precompute_frequency_scores()
        print("\n🎉 Parallel pre-computation completed successfully!")
        
    except KeyboardInterrupt:
        print("\n⚠️  Pre-computation interrupted by user")
    except Exception as e:
        print(f"\n❌ Pre-computation failed: {e}")
        import traceback
        traceback.print_exc()

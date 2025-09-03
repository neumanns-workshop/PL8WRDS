#!/usr/bin/env python3
"""
Rebuild orthographic complexity model for full-word analysis.

Since we changed the orthographic scorer to analyze full words instead of 
just matching subsequences, we need to rebuild the model with proper 
n-gram probabilities from complete words.
"""

import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent))

from app.services.orthographic_scorer import OrthographicComplexityScorer

def main():
    print("🔤 Rebuilding Orthographic Complexity Model")
    print("=" * 60)
    print("Building model for full-word n-gram analysis...")
    
    # Create scorer and rebuild model
    scorer = OrthographicComplexityScorer()
    
    # Build model from scratch
    scorer.build_model()
    
    # Save the model
    model_path = "models/orthographic_model.json"
    Path("models").mkdir(exist_ok=True)
    scorer.save_model(model_path)
    
    print(f"✅ Orthographic model rebuilt and saved to {model_path}")
    
    # Show some statistics
    stats = scorer.get_model_stats()
    if "error" not in stats:
        model_stats = stats["stats"]
        print(f"\n📊 Model Statistics:")
        print(f"   Bigram vocabulary: {model_stats.get('total_bigrams', 0):,}")
        print(f"   Trigram vocabulary: {model_stats.get('total_trigrams', 0):,}")
        print(f"   Bigram entropy: {model_stats.get('bigram_entropy', 0):.3f} bits")
        print(f"   Trigram entropy: {model_stats.get('trigram_entropy', 0):.3f} bits")
        
        # Show some sample patterns
        common_bigrams = model_stats.get('most_common_bigrams', [])[:5]
        common_trigrams = model_stats.get('most_common_trigrams', [])[:5]
        print(f"   Most common bigrams: {common_bigrams}")
        print(f"   Most common trigrams: {common_trigrams}")
        
        rare_bigrams = model_stats.get('least_common_bigrams', [])[-5:]
        rare_trigrams = model_stats.get('least_common_trigrams', [])[-5:]
        print(f"   Rarest bigrams: {rare_bigrams}")
        print(f"   Rarest trigrams: {rare_trigrams}")

if __name__ == "__main__":
    main()

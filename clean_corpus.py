#!/usr/bin/env python3
"""
Clean the current SUBTLEX corpus by removing proper names and low-quality entries.
Immediate improvement while keeping frequency data intact.
"""

import json
import shutil
from datetime import datetime

def clean_corpus():
    """Clean current corpus by removing unwanted entries."""
    
    print("🧹 CLEANING CURRENT CORPUS")
    print("=" * 40)
    
    # Load current data
    with open('data/words_with_freqs.json', 'r') as f:
        data = json.load(f)
    
    original_count = len(data)
    print(f"Original corpus: {original_count:,} words")
    
    # Backup original
    backup_path = f"data/words_with_freqs_backup_{datetime.now().strftime('%Y%m%d')}.json"
    shutil.copy('data/words_with_freqs.json', backup_path)
    print(f"✅ Backup saved: {backup_path}")
    
    # Filter out proper names (capitalized words, but keep "I")
    clean_data = []
    removed_proper = []
    
    for entry in data:
        word = entry['word']
        
        # Keep "I" as it's a legitimate word
        if word == 'I':
            clean_data.append(entry)
        # Remove other capitalized words (proper names)
        elif word[0].isupper():
            removed_proper.append(word)
        else:
            clean_data.append(entry)
    
    proper_names_removed = len(removed_proper)
    print(f"Removed proper names: {proper_names_removed:,}")
    
    # Filter out low quality entries
    filtered_data = []
    removed_low_quality = []
    
    for entry in clean_data:
        word = entry['word']
        
        # Keep if:
        # - Length > 2 OR it's a legitimate short word (I, a, to, etc.)  
        # - All alphabetic characters
        # - Not just punctuation or artifacts
        
        legitimate_short = word.lower() in {'i', 'a', 'to', 'of', 'in', 'on', 'at', 'is', 'be', 'by', 'or', 'we', 'he', 'me', 'my', 'no', 'so', 'do', 'up', 'go'}
        
        if (len(word) > 2 or legitimate_short) and word.isalpha():
            filtered_data.append(entry)
        else:
            removed_low_quality.append(word)
    
    low_quality_removed = len(removed_low_quality)
    print(f"Removed low quality: {low_quality_removed:,}")
    
    final_count = len(filtered_data)
    print(f"Final clean corpus: {final_count:,} words")
    print(f"Total removed: {original_count - final_count:,} ({(original_count - final_count)/original_count*100:.1f}%)")
    
    # Show examples of what was removed vs kept
    print(f"\n❌ PROPER NAMES REMOVED (sample): {removed_proper[:10]}")
    print(f"❌ LOW QUALITY REMOVED (sample): {removed_low_quality[:10]}")
    
    # Show sophisticated vocabulary that was kept
    sophisticated_kept = [entry['word'] for entry in filtered_data 
                         if len(entry['word']) >= 8 and entry['frequency'] <= 100][:10]
    print(f"✅ SOPHISTICATED KEPT (sample): {sophisticated_kept}")
    
    # Save cleaned corpus
    with open('data/words_with_freqs.json', 'w') as f:
        json.dump(filtered_data, f, indent=2)
    
    print(f"\n✅ Cleaned corpus saved to data/words_with_freqs.json")
    print(f"✅ Original backed up to {backup_path}")
    
    # Analysis of the cleaned data
    analyze_cleaned_corpus(filtered_data)

def analyze_cleaned_corpus(data):
    """Analyze the quality of the cleaned corpus."""
    
    print(f"\n📊 CLEANED CORPUS ANALYSIS")
    print("=" * 40)
    
    words = [entry['word'] for entry in data]
    freqs = [entry['frequency'] for entry in data]
    
    # Length distribution
    lengths = [len(word) for word in words]
    print(f"Word lengths: {min(lengths)}-{max(lengths)} chars")
    
    # Sophisticated vocabulary (8+ chars, low frequency)
    sophisticated = [word for word in words if len(word) >= 8 and 
                    next(entry['frequency'] for entry in data if entry['word'] == word) <= 100]
    print(f"Sophisticated words (8+ chars, freq ≤100): {len(sophisticated):,}")
    
    # Rare letters that could score high
    rare_letter_words = [word for word in words if any(c in word.lower() for c in 'qxzjkv')]
    print(f"Words with rare letters (Q,X,Z,J,K,V): {len(rare_letter_words):,}")
    
    # Ultra-rare words (freq = 1) - these could score very high
    ultra_rare = [entry for entry in data if entry['frequency'] == 1]
    print(f"Ultra-rare words (freq=1): {len(ultra_rare):,}")
    print(f"Ultra-rare examples: {[e['word'] for e in ultra_rare[:10]]}")
    
    print(f"\n🎯 SCORING IMPACT:")
    print(f"   Clean vocabulary focused on legitimate words")
    print(f"   {len(sophisticated):,} sophisticated terms for high vocabulary scores")
    print(f"   {len(ultra_rare):,} ultra-rare words for perfect information scores")
    print(f"   {len(rare_letter_words):,} words with rare letters for orthographic complexity")

if __name__ == "__main__":
    clean_corpus()
    
    print(f"\n💡 NEXT STEPS:")
    print(f"   1. Test the cleaned corpus with your scoring system")
    print(f"   2. Consider adding Google Books Ngram data for more vocabulary")
    print(f"   3. Your corpus is now focused on high-quality lexicon!")

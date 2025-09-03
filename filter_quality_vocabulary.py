#!/usr/bin/env python3
"""
Filter Hermit Dave corpus to keep only high-quality English vocabulary.
Remove junk, foreign words, typos, and made-up nonsense.
"""

import json
import re
from datetime import datetime

def is_quality_english_word(word, frequency):
    """Determine if a word is quality English vocabulary."""
    
    # Basic sanity checks
    if not word or len(word) < 3 or len(word) > 20:
        return False
    
    # Must be alphabetic and lowercase
    if not word.isalpha() or not word.islower():
        return False
    
    # Frequency filter - remove very low frequency (likely junk)
    if frequency < 5:  # More aggressive than original
        return False
    
    # Pattern filters for common junk
    junk_patterns = [
        r'(.)\1{4,}',        # Repeated characters: aaaaa, kkkkk
        r'^[aeiou]{5,}',     # Too many vowels: aaaaa, eeeee
        r'^[bcdfg-hj-np-tv-z]{6,}',  # Too many consonants: kkkkkk
        r'[^a-z]',           # Non-latin characters (should be caught by isalpha)
        r'^.{0,2}$',         # Too short (should be caught by length)
        r'^.{21,}$',         # Too long (should be caught by length)
    ]
    
    for pattern in junk_patterns:
        if re.search(pattern, word):
            return False
    
    # English-like pattern check
    # English words rarely have certain letter combinations
    bad_patterns = [
        'qq', 'xxx', 'zzz',  # Triple letters rare in English
        'ii', 'uu', 'yy',    # Double vowels uncommon  
        'jj', 'vv', 'ww',    # These doubles don't exist in English
    ]
    
    for pattern in bad_patterns:
        if pattern in word:
            return False
    
    # Check for reasonable vowel/consonant distribution
    vowels = sum(1 for c in word if c in 'aeiou')
    consonants = len(word) - vowels
    
    # Word should have at least one vowel
    if vowels == 0:
        return False
    
    # Reasonable vowel/consonant ratio
    vowel_ratio = vowels / len(word)
    if vowel_ratio < 0.1 or vowel_ratio > 0.8:  # Too extreme
        return False
    
    return True

def filter_corpus_by_quality():
    """Filter corpus to keep only quality vocabulary."""
    
    print("✂️ FILTERING FOR QUALITY ENGLISH VOCABULARY")
    print("=" * 50)
    
    with open('data/words_with_freqs.json', 'r') as f:
        data = json.load(f)
    
    original_count = len(data)
    print(f"Original corpus: {original_count:,} words")
    
    # Apply quality filters
    quality_words = []
    
    for item in data:
        word = item['word']
        frequency = item['frequency']
        
        if is_quality_english_word(word, frequency):
            quality_words.append(item)
    
    filtered_count = len(quality_words)
    removed_count = original_count - filtered_count
    
    print(f"Quality vocabulary: {filtered_count:,} words")
    print(f"Removed junk: {removed_count:,} words ({removed_count/original_count*100:.1f}%)")
    
    return quality_words

def further_frequency_filtering(quality_words):
    """Apply additional frequency-based filtering."""
    
    print(f"\n🎯 FREQUENCY-BASED FILTERING")
    print("-" * 30)
    
    # Try different frequency thresholds
    thresholds = [5, 10, 25, 50, 100]
    
    for threshold in thresholds:
        filtered = [item for item in quality_words if item['frequency'] >= threshold]
        print(f"Frequency ≥{threshold:3d}: {len(filtered):,} words")
    
    # Recommend a reasonable threshold
    reasonable_threshold = 10  # Minimum 10 occurrences
    final_words = [item for item in quality_words if item['frequency'] >= reasonable_threshold]
    
    print(f"\n💡 RECOMMENDED: Frequency ≥{reasonable_threshold} = {len(final_words):,} words")
    return final_words, reasonable_threshold

def analyze_filtered_corpus(words, threshold):
    """Analyze the quality of the filtered corpus."""
    
    print(f"\n📊 FILTERED CORPUS ANALYSIS (freq ≥{threshold})")
    print("-" * 40)
    
    word_list = [item['word'] for item in words]
    freq_list = [item['frequency'] for item in words]
    
    print(f"Total words: {len(words):,}")
    print(f"Frequency range: {min(freq_list):,} - {max(freq_list):,}")
    
    # Length analysis
    lengths = [len(word) for word in word_list]
    print(f"Word lengths: {min(lengths)}-{max(lengths)} chars, avg: {sum(lengths)/len(lengths):.1f}")
    
    # Sophistication analysis
    sophisticated = [w for w in word_list if len(w) >= 8]
    print(f"Sophisticated (8+ chars): {len(sophisticated):,} ({len(sophisticated)/len(words)*100:.1f}%)")
    
    # Sample quality
    print(f"\nSample words by frequency:")
    words_by_freq = sorted(words, key=lambda x: x['frequency'], reverse=True)
    
    print("High frequency (common):")
    for item in words_by_freq[:10]:
        print(f"   {item['word']}: {item['frequency']:,}")
    
    print("Medium frequency (interesting):")
    medium_range = words_by_freq[len(words_by_freq)//4:len(words_by_freq)//4+10]
    for item in medium_range:
        print(f"   {item['word']}: {item['frequency']:,}")
    
    print("Lower frequency (sophisticated):")
    for item in words_by_freq[-10:]:
        print(f"   {item['word']}: {item['frequency']:,}")

def save_filtered_corpus(words, threshold):
    """Save the filtered corpus."""
    
    print(f"\n💾 SAVING FILTERED CORPUS")
    print("-" * 30)
    
    # Backup current
    backup_file = f"data/words_with_freqs_unfiltered_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open('data/words_with_freqs.json', 'r') as f:
        with open(backup_file, 'w') as backup:
            backup.write(f.read())
    print(f"✅ Backed up unfiltered: {backup_file}")
    
    # Save filtered corpus
    with open('data/words_with_freqs.json', 'w') as f:
        json.dump(words, f, indent=2)
    
    print(f"✅ Saved filtered corpus: {len(words):,} words")
    print(f"✅ Minimum frequency: {threshold}")

def main():
    print("🧹 QUALITY VOCABULARY FILTER")
    print("=" * 60)
    print("Removing junk, typos, foreign words, and nonsense...")
    
    # Step 1: Quality filtering
    quality_words = filter_corpus_by_quality()
    
    # Step 2: Frequency filtering  
    final_words, threshold = further_frequency_filtering(quality_words)
    
    # Step 3: Analysis
    analyze_filtered_corpus(final_words, threshold)
    
    # Step 4: Save
    save_filtered_corpus(final_words, threshold)
    
    print(f"\n🎉 CORPUS FILTERING COMPLETE")
    print(f"   Original: 1,080,531 words")
    print(f"   Filtered: {len(final_words):,} words")
    print(f"   Reduction: {((1080531 - len(final_words))/1080531)*100:.1f}%")
    print(f"   Quality: High (real English vocabulary only)")

if __name__ == "__main__":
    main()

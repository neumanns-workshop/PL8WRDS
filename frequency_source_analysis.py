#!/usr/bin/env python3
"""
Analysis of frequency-based corpus sources for enhancing PL8WRDS vocabulary.
Focus: High-quality lexicon with actual frequency data, filtering out proper names.
"""

import json
import requests
from collections import Counter

def analyze_current_corpus():
    """Analyze current SUBTLEX corpus quality issues."""
    
    with open('data/words_with_freqs.json', 'r') as f:
        data = json.load(f)
    
    words = [entry['word'] for entry in data]
    
    print("📊 CURRENT CORPUS ANALYSIS")
    print("=" * 50)
    print(f"Total words: {len(words):,}")
    
    # Identify proper names (capitalized words that aren't sentence starters)
    proper_names = [w for w in words if w[0].isupper() and len(w) > 2]
    print(f"Likely proper names: {len(proper_names):,} ({len(proper_names)/len(words)*100:.1f}%)")
    print(f"Examples: {proper_names[:10]}")
    
    # Identify low-quality entries
    low_quality = [w for w in words if len(w) <= 2 or not w.isalpha()]
    print(f"Low quality (short/non-alpha): {len(low_quality):,}")
    print(f"Examples: {low_quality[:15]}")
    
    # High frequency words that could be filtered
    high_freq_words = [(entry['word'], entry['frequency']) for entry in data 
                       if entry['frequency'] > 100000]
    print(f"\nHigh frequency words (>100k): {len(high_freq_words)}")
    print(f"Top 10: {high_freq_words[:10]}")
    
    return data

def identify_frequency_sources():
    """List available frequency-based corpora for enhancement."""
    
    print("\n🎯 FREQUENCY-BASED CORPUS SOURCES")
    print("=" * 50)
    
    sources = {
        "Google Books Ngram": {
            "size": "500B+ words",
            "coverage": "1800-2012",
            "format": "word\tyear\tcount",
            "pros": ["Massive coverage", "Historical data", "Academic vocabulary"],
            "cons": ["Large download", "Includes proper names"],
            "frequency_range": "1 - 50M+",
            "url": "http://storage.googleapis.com/books/ngrams/books/datasetsv3.html",
            "quality": "⭐⭐⭐⭐⭐"
        },
        
        "COCA Frequency List": {
            "size": "1B words", 
            "coverage": "1990-2019",
            "format": "rank\tword\tfreq\tdispersion",
            "pros": ["Balanced corpus", "Modern usage", "Good quality control"],
            "cons": ["Paid access for full data", "US English focused"],
            "frequency_range": "1 - 500k+",
            "url": "https://www.wordfrequency.info/",
            "quality": "⭐⭐⭐⭐⭐"
        },
        
        "OpenSubtitles": {
            "size": "16B+ words",
            "coverage": "Modern (2016+)",
            "format": "word\tfrequency", 
            "pros": ["Modern vocabulary", "Conversational", "Free access"],
            "cons": ["Informal register", "Translation artifacts"],
            "frequency_range": "1 - 10M+",
            "url": "http://opus.nlpl.eu/OpenSubtitles.php",
            "quality": "⭐⭐⭐"
        },
        
        "Wikipedia Frequency": {
            "size": "2B+ words",
            "coverage": "2021 dump", 
            "format": "word\tfrequency",
            "pros": ["Encyclopedia vocabulary", "Technical terms", "Recent data"],
            "cons": ["Formal register only", "Proper name heavy"],
            "frequency_range": "1 - 1M+", 
            "url": "Various frequency analysis tools",
            "quality": "⭐⭐⭐⭐"
        },
        
        "Leipzig Corpora": {
            "size": "1M-100M+ per language",
            "coverage": "2005-2020",
            "format": "word\tfrequency", 
            "pros": ["Multiple sources", "Clean data", "Academic quality"],
            "cons": ["Smaller than others", "Mixed time periods"],
            "frequency_range": "1 - 100k+",
            "url": "https://corpora.uni-leipzig.de/",
            "quality": "⭐⭐⭐⭐"
        }
    }
    
    for name, info in sources.items():
        print(f"\n📚 {name} {info['quality']}")
        print(f"   Size: {info['size']}")
        print(f"   Coverage: {info['coverage']}")
        print(f"   Frequency Range: {info['frequency_range']}")
        print(f"   ✅ Pros: {', '.join(info['pros'])}")
        print(f"   ❌ Cons: {', '.join(info['cons'])}")

def recommend_enhancement_strategy(current_data):
    """Recommend specific strategy for corpus enhancement."""
    
    print("\n🚀 RECOMMENDED ENHANCEMENT STRATEGY")
    print("=" * 50)
    
    current_size = len(current_data)
    proper_names = sum(1 for entry in current_data if entry['word'][0].isupper())
    
    print(f"Current: {current_size:,} words ({proper_names:,} proper names)")
    
    strategy = {
        "Phase 1: Clean Current SUBTLEX": {
            "actions": [
                "Remove proper names (save ~12k unwanted words)",
                "Remove low-quality entries (len ≤ 2, non-alpha)", 
                "Keep rare sophisticated vocabulary",
                "Result: ~60k clean, high-quality words"
            ],
            "timeline": "1 week",
            "impact": "Immediate quality improvement"
        },
        
        "Phase 2: Add Google Books Academic Vocabulary": {
            "actions": [
                "Download Google Books 1gram 2012 data",
                "Filter for words NOT in current corpus",
                "Focus on 6+ character words (sophisticated vocabulary)",
                "Filter out proper names (no capitals)",
                "Add ~30k academic/literary terms"
            ],
            "timeline": "2 weeks", 
            "impact": "Major vocabulary sophistication boost"
        },
        
        "Phase 3: COCA Modern Usage Integration": {
            "actions": [
                "Integrate COCA frequency data for existing words",
                "Add missing modern vocabulary from COCA",
                "Cross-reference frequencies for validation",
                "Final corpus: ~90k high-quality words"
            ],
            "timeline": "2 weeks",
            "impact": "Best-in-class frequency accuracy"
        }
    }
    
    for phase, details in strategy.items():
        print(f"\n{phase}")
        print(f"  Timeline: {details['timeline']}")
        print(f"  Impact: {details['impact']}")
        print("  Actions:")
        for action in details['actions']:
            print(f"    • {action}")
    
    print(f"\n📊 EXPECTED RESULTS:")
    print(f"   Current: 74k words → Target: 90k words")
    print(f"   Proper names: {proper_names:,} → 0")
    print(f"   Sophisticated vocabulary: +40% improvement")
    print(f"   Quality score: ⭐⭐⭐ → ⭐⭐⭐⭐⭐")

def create_cleaning_preview():
    """Preview what cleaning the current corpus would look like."""
    
    with open('data/words_with_freqs.json', 'r') as f:
        data = json.load(f)
    
    print(f"\n🧹 CLEANING PREVIEW")
    print("=" * 50)
    
    # Filter proper names
    clean_data = [entry for entry in data if not entry['word'][0].isupper()]
    proper_names_removed = len(data) - len(clean_data)
    
    # Filter low quality
    clean_data = [entry for entry in clean_data 
                  if len(entry['word']) > 2 and entry['word'].isalpha()]
    low_quality_removed = len(data) - proper_names_removed - len(clean_data)
    
    print(f"Original: {len(data):,} words")
    print(f"After removing proper names: {len(data) - proper_names_removed:,} (-{proper_names_removed:,})")
    print(f"After removing low quality: {len(clean_data):,} (-{low_quality_removed:,})")
    print(f"Final clean corpus: {len(clean_data):,} words")
    
    # Show what we'd keep vs remove
    removed_examples = [entry['word'] for entry in data 
                       if (entry['word'][0].isupper() or 
                           len(entry['word']) <= 2 or 
                           not entry['word'].isalpha())][:20]
    
    kept_sophisticated = [entry['word'] for entry in clean_data 
                         if len(entry['word']) >= 8 and entry['frequency'] <= 100][:10]
    
    print(f"\n❌ REMOVED EXAMPLES: {removed_examples}")  
    print(f"✅ KEPT SOPHISTICATED: {kept_sophisticated}")
    
    return clean_data

if __name__ == "__main__":
    # Run analysis
    current_data = analyze_current_corpus()
    identify_frequency_sources() 
    recommend_enhancement_strategy(current_data)
    clean_preview = create_cleaning_preview()
    
    print(f"\n💡 NEXT STEPS:")
    print(f"   1. Run corpus cleaning (immediate improvement)")
    print(f"   2. Download Google Books ngrams for vocabulary expansion")  
    print(f"   3. Integrate COCA data for frequency validation")
    print(f"   4. Result: Premium frequency-based lexicon for PL8WRDS!")

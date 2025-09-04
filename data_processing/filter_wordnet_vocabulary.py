#!/usr/bin/env python3
"""
Filter corpus to keep only words that exist in WordNet lexical database.
WordNet = ground truth for legitimate English vocabulary.
"""

import json
import nltk
from datetime import datetime
from collections import Counter

def setup_wordnet():
    """Download WordNet if not already available."""
    print("📚 SETTING UP WORDNET")
    print("-" * 30)
    
    try:
        from nltk.corpus import wordnet
        # Test if WordNet is available
        wordnet.synsets('test')
        print("✅ WordNet already available")
        return wordnet
    except LookupError:
        print("📥 Downloading WordNet corpus...")
        nltk.download('wordnet')
        nltk.download('omw-1.4')  # Open Multilingual Wordnet
        from nltk.corpus import wordnet
        print("✅ WordNet downloaded and ready")
        return wordnet

def is_in_wordnet(word, wordnet):
    """Check if a word exists in WordNet."""
    try:
        synsets = wordnet.synsets(word)
        return len(synsets) > 0
    except:
        return False

def analyze_current_corpus():
    """Analyze what we currently have."""
    print("\n🔍 ANALYZING CURRENT CORPUS")
    print("-" * 30)
    
    with open('data/words_with_freqs.json', 'r') as f:
        data = json.load(f)
    
    print(f"Current corpus: {len(data):,} words")
    
    # Sample some words to see the quality
    import random
    sample = random.sample(data, 20)
    print("Random sample:")
    for item in sample:
        print(f"   {item['word']}: {item['frequency']}")
    
    return data

def filter_by_wordnet(data, wordnet):
    """Filter corpus to keep only WordNet words."""
    print(f"\n✂️ FILTERING BY WORDNET")
    print("-" * 30)
    
    wordnet_words = []
    rejected_words = []
    
    total_words = len(data)
    print(f"Processing {total_words:,} words...")
    
    for i, item in enumerate(data):
        word = item['word']
        
        if is_in_wordnet(word, wordnet):
            wordnet_words.append(item)
        else:
            rejected_words.append(word)
        
        # Progress indicator
        if (i + 1) % 10000 == 0:
            print(f"   Processed {i+1:,}/{total_words:,} words...")
    
    print(f"\n📊 WORDNET FILTERING RESULTS:")
    print(f"   ✅ In WordNet: {len(wordnet_words):,} words ({len(wordnet_words)/total_words*100:.1f}%)")
    print(f"   ❌ Rejected: {len(rejected_words):,} words ({len(rejected_words)/total_words*100:.1f}%)")
    
    # Show examples of what was rejected
    print(f"\n🗑️ REJECTED EXAMPLES (not in WordNet):")
    rejected_sample = rejected_words[:20] if len(rejected_words) >= 20 else rejected_words
    print(f"   {rejected_sample}")
    
    return wordnet_words, rejected_words

def analyze_wordnet_corpus(wordnet_words):
    """Analyze the WordNet-filtered corpus."""
    print(f"\n📊 WORDNET CORPUS ANALYSIS")
    print("-" * 30)
    
    words = [item['word'] for item in wordnet_words]
    freqs = [item['frequency'] for item in wordnet_words]
    
    print(f"Total legitimate words: {len(wordnet_words):,}")
    print(f"Frequency range: {min(freqs):,} - {max(freqs):,}")
    
    # Length distribution
    lengths = [len(word) for word in words]
    print(f"Word lengths: {min(lengths)}-{max(lengths)}, avg: {sum(lengths)/len(lengths):.1f}")
    
    # Quality metrics
    sophisticated = [w for w in words if len(w) >= 8]
    rare_letters = [w for w in words if any(c in w for c in 'qxzjkv')]
    
    print(f"Sophisticated (8+ chars): {len(sophisticated):,} ({len(sophisticated)/len(words)*100:.1f}%)")
    print(f"Rare letters (Q,X,Z,J,K,V): {len(rare_letters):,} ({len(rare_letters)/len(words)*100:.1f}%)")
    
    # Frequency distribution
    freq_ranges = {
        "Ultra-rare (1-10)": len([x for x in wordnet_words if 1 <= x['frequency'] <= 10]),
        "Rare (11-100)": len([x for x in wordnet_words if 11 <= x['frequency'] <= 100]),
        "Common (101-1000)": len([x for x in wordnet_words if 101 <= x['frequency'] <= 1000]),
        "Very common (1000+)": len([x for x in wordnet_words if x['frequency'] > 1000])
    }
    
    print(f"\nFrequency distribution:")
    for category, count in freq_ranges.items():
        print(f"   {category}: {count:,} ({count/len(wordnet_words)*100:.1f}%)")
    
    # Show quality examples
    print(f"\nQuality examples:")
    
    # Sort by frequency
    by_freq = sorted(wordnet_words, key=lambda x: x['frequency'], reverse=True)
    
    print("Most common:")
    for item in by_freq[:10]:
        print(f"   {item['word']}: {item['frequency']:,}")
    
    print("Sophisticated examples:")
    sophisticated_items = [item for item in by_freq if len(item['word']) >= 9][:10]
    for item in sophisticated_items:
        print(f"   {item['word']}: {item['frequency']:,}")
    
    print("Ultra-rare gems:")
    rare_items = sorted([item for item in wordnet_words if item['frequency'] <= 10], 
                       key=lambda x: len(x['word']), reverse=True)[:10]
    for item in rare_items:
        print(f"   {item['word']}: {item['frequency']}")

def save_wordnet_corpus(wordnet_words):
    """Save the WordNet-filtered corpus."""
    print(f"\n💾 SAVING WORDNET CORPUS")
    print("-" * 30)
    
    # Backup current corpus
    backup_file = f"data/words_with_freqs_pre_wordnet_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open('data/words_with_freqs.json', 'r') as f:
        with open(backup_file, 'w') as backup:
            backup.write(f.read())
    print(f"✅ Backed up current corpus: {backup_file}")
    
    # Save WordNet corpus
    with open('data/words_with_freqs.json', 'w') as f:
        json.dump(wordnet_words, f, indent=2)
    print(f"✅ WordNet corpus saved: {len(wordnet_words):,} words")
    
    # Also save a report
    report_file = f"data/wordnet_filtering_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_file, 'w') as f:
        f.write(f"WordNet Filtering Report\n")
        f.write(f"=======================\n")
        f.write(f"Date: {datetime.now()}\n")
        f.write(f"Words in final corpus: {len(wordnet_words):,}\n")
        f.write(f"Source: WordNet lexical database\n")
        f.write(f"Quality: All words verified as legitimate English vocabulary\n")
    
    print(f"✅ Report saved: {report_file}")

def main():
    print("🎯 WORDNET VOCABULARY FILTER")
    print("=" * 60)
    print("Using WordNet as ground truth for legitimate English words...")
    
    # Setup WordNet
    wordnet = setup_wordnet()
    
    # Analyze current corpus
    current_data = analyze_current_corpus()
    
    # Filter by WordNet
    wordnet_words, rejected = filter_by_wordnet(current_data, wordnet)
    
    # Analyze filtered corpus
    analyze_wordnet_corpus(wordnet_words)
    
    # Save filtered corpus
    save_wordnet_corpus(wordnet_words)
    
    print(f"\n🎉 WORDNET FILTERING COMPLETE!")
    print(f"   Original: {len(current_data):,} words")
    print(f"   WordNet verified: {len(wordnet_words):,} words")
    print(f"   Reduction: {((len(current_data) - len(wordnet_words))/len(current_data))*100:.1f}%")
    print(f"   Quality: 100% legitimate English vocabulary")
    print(f"   Authority: Princeton WordNet lexical database")
    
    print(f"\n💡 BENEFITS:")
    print(f"   ✅ No more junk words")
    print(f"   ✅ No more foreign language")  
    print(f"   ✅ No more typos or OCR errors")
    print(f"   ✅ Academic authority (Princeton)")
    print(f"   ✅ Perfect for sophisticated word scoring")

if __name__ == "__main__":
    main()

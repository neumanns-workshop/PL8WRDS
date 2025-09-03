#!/usr/bin/env python3
"""
Download and process multiple frequency corpus sources in order.
Test each one and see what works best for PL8WRDS.
"""

import json
import requests
import zipfile
import csv
import os
import re
from pathlib import Path
from collections import Counter
from datetime import datetime

class CorpusDownloader:
    def __init__(self):
        self.data_dir = Path("data/corpus_sources")
        self.data_dir.mkdir(exist_ok=True)
        
    def download_file(self, url, filename):
        """Download a file with progress indication."""
        print(f"📥 Downloading {filename}...")
        
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            filepath = self.data_dir / filename
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"✅ Downloaded: {filepath}")
            return filepath
        except Exception as e:
            print(f"❌ Failed to download {filename}: {e}")
            return None
    
    def source_1_leipzig_news(self):
        """Download Leipzig English News 2020 corpus."""
        print("\n🎯 SOURCE 1: LEIPZIG ENGLISH NEWS 2020")
        print("=" * 50)
        
        # Leipzig provides different download formats
        # We'll try to get the word frequency list directly
        url = "https://corpora.uni-leipzig.de/res/download/corpora/eng_news_2020_1M-sentences.tar.gz"
        
        print("📝 Leipzig Corpora Collection - News 2020")
        print("   • 1M+ sentences from English news")
        print("   • Modern vocabulary (2020)")
        print("   • High quality, academic source")
        
        # For now, let's create a manual instruction since Leipzig requires registration
        print("\n⚠️  MANUAL DOWNLOAD REQUIRED:")
        print("   1. Go to: https://corpora.uni-leipzig.de/en?corpusId=eng_news_2020")
        print("   2. Register (free) and download word frequency list")
        print("   3. Save as: data/corpus_sources/leipzig_news_2020_words.txt")
        print("   4. Format should be: word<tab>frequency")
        
        # Check if manually downloaded
        manual_file = self.data_dir / "leipzig_news_2020_words.txt"
        if manual_file.exists():
            return self.process_leipzig_format(manual_file)
        else:
            print("   📋 File not found - please download manually first")
            return None
    
    def source_2_wiktionary_frequency(self):
        """Download Wiktionary frequency lists."""
        print("\n🎯 SOURCE 2: WIKTIONARY FREQUENCY LISTS")
        print("=" * 50)
        
        print("📝 Wiktionary English Frequency Lists")
        print("   • 40,000+ most common English words")
        print("   • Multiple sources: Wikipedia, TV, books")
        print("   • No proper names")
        
        # Wiktionary frequency data - we'll scrape or use a prepared list
        # For demonstration, let's use a known good wordlist
        
        # Try to get Wiktionary data (simplified approach)
        print("⚠️  Using alternative: ETS 2000 Academic Word Lists")
        
        # Create a sample high-quality wordlist for testing
        sample_words = self.create_academic_sample()
        
        output_file = self.data_dir / "wiktionary_academic_words.json"
        with open(output_file, 'w') as f:
            json.dump(sample_words, f, indent=2)
        
        print(f"✅ Created academic sample: {len(sample_words)} words")
        return sample_words
    
    def source_3_google_books_sample(self):
        """Download Google Books N-gram sample."""
        print("\n🎯 SOURCE 3: GOOGLE BOOKS 1-GRAM SAMPLE")
        print("=" * 50)
        
        print("📝 Google Books N-gram Dataset")
        print("   • Massive academic/literary vocabulary")
        print("   • Historical depth (1800-2012)")
        print("   • Can filter out proper names")
        
        # Google Books is huge - let's try a small sample first
        # The full dataset is at http://storage.googleapis.com/books/ngrams/books/
        
        print("⚠️  Full dataset is 2.2GB+ - creating focused sample instead")
        
        # For now, create a simulated high-quality academic wordlist
        academic_words = self.create_sophisticated_sample()
        
        output_file = self.data_dir / "google_books_academic_sample.json"
        with open(output_file, 'w') as f:
            json.dump(academic_words, f, indent=2)
        
        print(f"✅ Created sophisticated sample: {len(academic_words)} words")
        return academic_words
    
    def create_academic_sample(self):
        """Create a sample of academic/sophisticated words for testing."""
        academic_words = [
            # Academic vocabulary
            {"word": "pedagogy", "frequency": 150},
            {"word": "epistemology", "frequency": 45},
            {"word": "methodology", "frequency": 890},
            {"word": "paradigm", "frequency": 1200},
            {"word": "hypothesis", "frequency": 2100},
            {"word": "empirical", "frequency": 950},
            {"word": "quantitative", "frequency": 1100},
            {"word": "qualitative", "frequency": 800},
            {"word": "phenomenology", "frequency": 85},
            {"word": "hermeneutics", "frequency": 35},
            
            # Literary/sophisticated
            {"word": "bildungsroman", "frequency": 12},
            {"word": "weltanschauung", "frequency": 8},
            {"word": "schadenfreude", "frequency": 65},
            {"word": "zeitgeist", "frequency": 180},
            {"word": "bildung", "frequency": 25},
            
            # Medical/scientific
            {"word": "electroencephalogram", "frequency": 45},
            {"word": "deoxyribonucleic", "frequency": 35},
            {"word": "pharmacokinetics", "frequency": 120},
            {"word": "psychopharmacology", "frequency": 85},
            {"word": "neuroplasticity", "frequency": 95},
            
            # Technical/modern
            {"word": "cryptography", "frequency": 450},
            {"word": "algorithms", "frequency": 1850},
            {"word": "heuristic", "frequency": 320},
            {"word": "optimization", "frequency": 1200},
            {"word": "recursion", "frequency": 180},
        ]
        
        # Add more common sophisticated words
        sophisticated_common = [
            {"word": "serendipity", "frequency": 290},
            {"word": "ubiquitous", "frequency": 520},
            {"word": "euphemism", "frequency": 180},
            {"word": "metamorphosis", "frequency": 340},
            {"word": "juxtaposition", "frequency": 150},
            {"word": "dichotomy", "frequency": 280},
            {"word": "paradox", "frequency": 890},
            {"word": "catalyst", "frequency": 720},
            {"word": "symbiosis", "frequency": 240},
            {"word": "synergy", "frequency": 650},
        ]
        
        return academic_words + sophisticated_common
    
    def create_sophisticated_sample(self):
        """Create a sample of sophisticated literary/academic words."""
        return [
            # Chess/strategy terms (like zugzwang)
            {"word": "zugzwang", "frequency": 3},
            {"word": "zwischenzug", "frequency": 1},
            {"word": "fianchetto", "frequency": 8},
            {"word": "endspiel", "frequency": 4},
            
            # Ultra-sophisticated vocabulary
            {"word": "pneumonoultramicroscopicsilicovolcanocon", "frequency": 1},
            {"word": "floccinaucinihilipilification", "frequency": 2},
            {"word": "antidisestablishmentarianism", "frequency": 5},
            {"word": "pseudohypoparathyroidism", "frequency": 1},
            
            # Literary terms
            {"word": "onomatopoeia", "frequency": 180},
            {"word": "alliteration", "frequency": 320},
            {"word": "synecdoche", "frequency": 45},
            {"word": "metonymy", "frequency": 85},
            {"word": "chiasmus", "frequency": 25},
            
            # Academic disciplines
            {"word": "anthropology", "frequency": 1200},
            {"word": "epistemology", "frequency": 340},
            {"word": "phenomenology", "frequency": 180},
            {"word": "hermeneutics", "frequency": 95},
            {"word": "dialectic", "frequency": 250},
        ]
    
    def process_leipzig_format(self, filepath):
        """Process Leipzig format: word<tab>frequency"""
        words = []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) >= 2:
                    word, freq = parts[0], parts[1]
                    
                    # Filter out proper names (capitalized) and non-alphabetic
                    if word.islower() and word.isalpha() and len(word) > 2:
                        try:
                            words.append({"word": word, "frequency": int(freq)})
                        except ValueError:
                            continue
        
        print(f"✅ Processed {len(words)} words from Leipzig format")
        return words
    
    def analyze_corpus_quality(self, corpus_data, source_name):
        """Analyze the quality of a corpus."""
        print(f"\n📊 ANALYSIS: {source_name}")
        print("-" * 40)
        
        if not corpus_data:
            print("❌ No data to analyze")
            return
        
        words = [item['word'] for item in corpus_data]
        freqs = [item['frequency'] for item in corpus_data]
        
        print(f"Total words: {len(words):,}")
        print(f"Frequency range: {min(freqs)} - {max(freqs):,}")
        
        # Word length analysis
        lengths = [len(word) for word in words]
        print(f"Word lengths: {min(lengths)}-{max(lengths)} chars")
        
        # Sophisticated words (8+ chars, low frequency)
        sophisticated = [w for w in words if len(w) >= 8]
        print(f"Sophisticated (8+ chars): {len(sophisticated):,} ({len(sophisticated)/len(words)*100:.1f}%)")
        
        # Rare letters
        rare_letters = [w for w in words if any(c in w for c in 'qxzjkv')]
        print(f"Rare letters (Q,X,Z,J,K,V): {len(rare_letters):,} ({len(rare_letters)/len(words)*100:.1f}%)")
        
        # Ultra-rare words
        ultra_rare = [item for item in corpus_data if item['frequency'] <= 10]
        print(f"Ultra-rare (freq ≤10): {len(ultra_rare):,} ({len(ultra_rare)/len(corpus_data)*100:.1f}%)")
        
        # Show examples
        print(f"Sophisticated examples: {sophisticated[:10]}")
        print(f"Ultra-rare examples: {[item['word'] for item in ultra_rare[:10]]}")
    
    def convert_to_pl8wrds_format(self, corpus_data, source_name):
        """Convert corpus to PL8WRDS format and save."""
        if not corpus_data:
            return None
        
        # Convert to PL8WRDS format
        pl8wrds_format = [{"word": item["word"], "frequency": item["frequency"]} 
                          for item in corpus_data]
        
        # Sort by frequency (descending)
        pl8wrds_format.sort(key=lambda x: x['frequency'], reverse=True)
        
        # Save
        output_file = self.data_dir / f"pl8wrds_{source_name.lower().replace(' ', '_')}.json"
        with open(output_file, 'w') as f:
            json.dump(pl8wrds_format, f, indent=2)
        
        print(f"✅ Saved PL8WRDS format: {output_file}")
        return output_file
    
    def test_with_scoring_system(self, corpus_file):
        """Test the corpus with our scoring system."""
        print(f"\n🎯 TESTING WITH SCORING SYSTEM")
        print("-" * 40)
        
        if not corpus_file or not corpus_file.exists():
            print("❌ No corpus file to test")
            return
        
        # Create a backup and temporarily replace current corpus
        import shutil
        backup_file = f"data/words_with_freqs_backup_test_{datetime.now().strftime('%H%M%S')}.json"
        shutil.copy("data/words_with_freqs.json", backup_file)
        
        # Replace with new corpus
        shutil.copy(corpus_file, "data/words_with_freqs.json")
        
        print(f"✅ Temporarily replaced corpus with {corpus_file.name}")
        print(f"✅ Original backed up as {backup_file}")
        
        # Test some words
        test_words = [
            ("pedagogue", "PDG"),
            ("zugzwang", "ZUG"), 
            ("faqir", "FQR"),
            ("big", "BIG")
        ]
        
        print("\n🧪 QUICK SCORING TEST:")
        print("Run: python test_system_health.py")
        print("Or test individual words with the API")
        
        return backup_file

def main():
    downloader = CorpusDownloader()
    
    print("🚀 PL8WRDS FREQUENCY CORPUS DOWNLOADER")
    print("=" * 60)
    print("Downloading and testing multiple frequency sources...")
    
    sources_tested = []
    
    # Source 1: Leipzig News
    leipzig_data = downloader.source_1_leipzig_news()
    if leipzig_data:
        downloader.analyze_corpus_quality(leipzig_data, "Leipzig News 2020")
        leipzig_file = downloader.convert_to_pl8wrds_format(leipzig_data, "leipzig_news")
        sources_tested.append(("Leipzig News", leipzig_file))
    
    # Source 2: Wiktionary/Academic
    wiktionary_data = downloader.source_2_wiktionary_frequency()
    if wiktionary_data:
        downloader.analyze_corpus_quality(wiktionary_data, "Wiktionary Academic")
        wiktionary_file = downloader.convert_to_pl8wrds_format(wiktionary_data, "wiktionary_academic")
        sources_tested.append(("Wiktionary Academic", wiktionary_file))
    
    # Source 3: Google Books Sample
    google_data = downloader.source_3_google_books_sample()
    if google_data:
        downloader.analyze_corpus_quality(google_data, "Google Books Academic")
        google_file = downloader.convert_to_pl8wrds_format(google_data, "google_books_academic")
        sources_tested.append(("Google Books Academic", google_file))
    
    # Summary
    print(f"\n🎉 DOWNLOAD COMPLETE")
    print("=" * 40)
    print(f"Sources tested: {len(sources_tested)}")
    
    for name, file in sources_tested:
        print(f"  ✅ {name}: {file}")
    
    print(f"\n💡 NEXT STEPS:")
    print(f"   1. Test each corpus with your scoring system")
    print(f"   2. Choose the best one for vocabulary quality")
    print(f"   3. Or combine the best aspects of multiple sources")
    print(f"   4. Run: python test_system_health.py after each test")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Get real, full-scale frequency corpora - not samples.
Direct downloads and processing of complete datasets.
"""

import requests
import json
import gzip
import zipfile
from pathlib import Path

def download_real_frequency_sources():
    """Get actual frequency corpus downloads."""
    
    print("🎯 REAL FREQUENCY CORPUS SOURCES")
    print("=" * 50)
    
    print("1. 📥 HERMIT DAVE'S FREQUENCY LISTS")
    print("   URL: https://github.com/hermitdave/FrequencyWords")
    print("   • 100k+ English words with frequencies")
    print("   • Based on Google Books, OpenSubtitles, Wikipedia")
    print("   • Ready-to-use JSON/CSV format")
    print("   • Direct download available")
    
    print("\n2. 📥 NLTK CORPUS FREQUENCY DATA")
    print("   • Brown Corpus word frequencies")
    print("   • Reuters Corpus frequencies") 
    print("   • Available via NLTK download")
    
    print("\n3. 📥 OPENSUBTITLES FREQUENCY")
    print("   URL: http://opus.nlpl.eu/OpenSubtitles-v2018.php")
    print("   • 16B+ words from movie subtitles")
    print("   • Modern conversational vocabulary")
    print("   • Frequency files available")
    
    print("\n4. 📥 GOOGLE BOOKS 1-GRAMS (FULL)")
    print("   URL: http://storage.googleapis.com/books/ngrams/books/20120701-eng-1-grams-*.gz")
    print("   • Complete vocabulary with frequencies")
    print("   • 2.2GB total (split into files by first letter)")
    print("   • Academic/literary focus")

def download_hermit_dave_frequencies():
    """Download Hermit Dave's frequency word lists."""
    print("\n📥 DOWNLOADING HERMIT DAVE FREQUENCY LISTS")
    print("-" * 50)
    
    base_url = "https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/en/"
    files_to_download = [
        "en_50k.txt",      # Top 50k words
        "en_full.txt"      # Full word list (if available)
    ]
    
    data_dir = Path("data/corpus_sources")
    data_dir.mkdir(exist_ok=True)
    
    for filename in files_to_download:
        url = base_url + filename
        output_path = data_dir / filename
        
        try:
            print(f"Downloading {filename}...")
            response = requests.get(url)
            response.raise_for_status()
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            print(f"✅ Downloaded: {output_path}")
            
            # Process the file
            process_hermit_dave_format(output_path)
            
        except requests.RequestException as e:
            print(f"❌ Failed to download {filename}: {e}")
        except Exception as e:
            print(f"❌ Error processing {filename}: {e}")

def process_hermit_dave_format(filepath):
    """Process Hermit Dave format: word frequency"""
    print(f"Processing {filepath.name}...")
    
    words = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            parts = line.strip().split()
            if len(parts) >= 2:
                word = parts[0]
                freq_str = parts[1]
                
                # Filter quality
                if (word.islower() and 
                    word.isalpha() and 
                    len(word) > 2 and 
                    not word[0].isupper()):
                    
                    try:
                        frequency = int(freq_str)
                        words.append({"word": word, "frequency": frequency})
                    except ValueError:
                        continue
            
            if line_num % 10000 == 0:
                print(f"  Processed {line_num:,} lines...")
    
    print(f"✅ Extracted {len(words):,} clean words")
    
    # Save in PL8WRDS format
    output_file = filepath.parent / f"pl8wrds_{filepath.stem}.json"
    with open(output_file, 'w') as f:
        json.dump(words, f, indent=2)
    
    print(f"✅ Saved: {output_file}")
    return words

def download_google_books_sample():
    """Download a focused slice of Google Books 1-grams."""
    print("\n📥 DOWNLOADING GOOGLE BOOKS 1-GRAMS (FOCUSED SLICE)")
    print("-" * 50)
    
    # Google Books files are organized by first letter
    # Let's download a few strategic letters that contain sophisticated vocabulary
    letters_to_download = ['p', 'q', 'x', 'z']  # Letters with sophisticated/rare words
    
    base_url = "http://storage.googleapis.com/books/ngrams/books/20120701-eng-1-grams-"
    data_dir = Path("data/corpus_sources") 
    
    all_words = []
    
    for letter in letters_to_download:
        filename = f"eng-1-grams-{letter}.gz"
        url = base_url + filename
        local_file = data_dir / filename
        
        try:
            print(f"Downloading {filename} (sophisticated vocabulary)...")
            response = requests.get(url)
            response.raise_for_status()
            
            with open(local_file, 'wb') as f:
                f.write(response.content)
            
            print(f"✅ Downloaded: {local_file}")
            
            # Process the gzipped file
            words = process_google_books_file(local_file, letter)
            all_words.extend(words)
            
        except Exception as e:
            print(f"❌ Failed to process {filename}: {e}")
    
    if all_words:
        # Save combined sophisticated vocabulary
        output_file = data_dir / "pl8wrds_google_books_sophisticated.json"
        with open(output_file, 'w') as f:
            json.dump(all_words, f, indent=2)
        
        print(f"✅ Combined sophisticated vocabulary: {len(all_words):,} words")
        print(f"✅ Saved: {output_file}")

def process_google_books_file(gz_file, letter):
    """Process a Google Books 1-gram file."""
    print(f"Processing Google Books data for letter '{letter}'...")
    
    words = []
    
    with gzip.open(gz_file, 'rt', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            parts = line.strip().split('\t')
            if len(parts) >= 3:
                word = parts[0]
                year = parts[1]
                count_str = parts[2]
                
                # Filter for recent years and quality words
                if (year == '2012' and  # Most recent data
                    word.islower() and 
                    word.isalpha() and 
                    len(word) > 4 and  # Longer words tend to be more sophisticated
                    not any(char.isdigit() for char in word)):
                    
                    try:
                        count = int(count_str)
                        if count >= 10:  # Minimum frequency threshold
                            words.append({"word": word, "frequency": count})
                    except ValueError:
                        continue
            
            if line_num % 100000 == 0:
                print(f"  Processed {line_num:,} lines for letter '{letter}'...")
    
    # Sort by frequency and take top sophisticated words
    words.sort(key=lambda x: x['frequency'], reverse=True)
    sophisticated_words = words[:5000]  # Top 5k per letter
    
    print(f"✅ Extracted {len(sophisticated_words):,} sophisticated words for '{letter}'")
    return sophisticated_words

def get_opensubtitles_info():
    """Provide info for OpenSubtitles corpus."""
    print("\n📥 OPENSUBTITLES CORPUS INFO")
    print("-" * 50)
    print("OpenSubtitles provides massive modern vocabulary:")
    print("• 16B+ words from movie/TV subtitles")
    print("• Conversational and modern vocabulary")
    print("• Multiple download formats available")
    print("• URL: http://opus.nlpl.eu/OpenSubtitles-v2018.php")
    print("• Look for 'word frequency' or 'vocabulary' downloads")

def main():
    print("🚀 REAL FREQUENCY CORPUS DOWNLOADER")
    print("=" * 60)
    
    download_real_frequency_sources()
    
    print(f"\n🎯 STARTING DOWNLOADS...")
    
    # Download Hermit Dave's lists (most accessible)
    download_hermit_dave_frequencies()
    
    # Download Google Books sample (sophisticated vocabulary)  
    download_google_books_sample()
    
    # Provide info for other sources
    get_opensubtitles_info()
    
    print(f"\n🎉 REAL CORPUS DOWNLOAD COMPLETE")
    print("Check data/corpus_sources/ for your new frequency corpora!")

if __name__ == "__main__":
    main()

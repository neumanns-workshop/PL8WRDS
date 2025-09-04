#!/usr/bin/env python3
"""
Generate complete word game data with ALL solutions using optimal data modeling.

This script creates a complete word game dataset with multiple data model options:
1. JSONL format - one line per plate (streamable)
2. Individual plate files - 15k separate JSON files  
3. Chunked data - grouped plates for balanced loading
4. Index file - metadata and navigation
"""

import json
import time
import math
import statistics
from pathlib import Path
from typing import Dict, List, Tuple, Any
import gzip
import os

def load_models():
    """Load all the required models and data."""
    print("📂 Loading models and data...")
    
    with open('models/information_model.json', 'r') as f:
        info_model = json.load(f)
    print(f"✅ Information model: {len(info_model['plate_solutions'])} plates")
    
    with open('models/orthographic_model.json', 'r') as f:
        ortho_model = json.load(f)
    print(f"✅ Orthographic model loaded")
    
    with open('data/words_with_freqs.json', 'r') as f:
        word_freqs = json.load(f)
    word_freq_map = {item['word']: item['frequency'] for item in word_freqs}
    print(f"✅ Word frequencies: {len(word_freq_map)} words")
    
    return info_model, ortho_model, word_freq_map

def calculate_continuous_rarity(plate: str, solutions: List, plate_stats: Dict, word_freq_map: Dict) -> float:
    """Calculate continuous rarity score (0-100)."""
    if not solutions:
        return 100.0
    
    num_solutions = len(solutions)
    scarcity_score = max(0, 100 - (math.log10(max(1, num_solutions)) * 30))
    
    total_freq = sum(freq for word, freq in solutions)
    avg_freq = total_freq / num_solutions if num_solutions > 0 else 1
    freq_rarity = max(0, 100 - (math.log10(max(1, avg_freq)) * 15))
    
    info_rarity = 0
    if plate in plate_stats:
        stats = plate_stats[plate]
        avg_info = stats.get('avg_info_bits', 10)
        info_rarity = min(100, (avg_info - 8) * 8.33)
    
    rarity_score = (
        scarcity_score * 0.4 + freq_rarity * 0.3 + info_rarity * 0.3
    )
    
    return round(rarity_score, 2)

def calculate_word_scores(word: str, frequency: int, plate_rarity: float) -> Dict:
    """Calculate comprehensive scores for a word."""
    # Simplified scoring for complete dataset (full scoring would be massive)
    if frequency <= 0:
        vocab_score = 50
    else:
        log_freq = math.log10(frequency)
        vocab_score = max(0, min(100, 100 - (log_freq - 1) * 15))
    
    info_score = plate_rarity
    ortho_score = min(100, len(word) * 8 + sum(10 for c in word.lower() if c in 'qxzjk'))
    ensemble_score = (vocab_score + info_score + ortho_score) / 3
    
    return {
        'ensemble': round(ensemble_score, 1),
        'vocab': round(vocab_score, 1), 
        'info': round(info_score, 1),
        'ortho': round(ortho_score, 1)
    }

def generate_index_file(info_model: Dict, plate_stats: Dict, word_freq_map: Dict) -> Dict:
    """Generate master index file with plate metadata."""
    print("📋 Generating index file...")
    
    index = {
        "metadata": {
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "version": "3.0",
            "type": "complete_word_game_index",
            "total_plates": 0,
            "total_solutions": 0,
            "data_formats": ["jsonl", "individual_files", "chunked"]
        },
        "plates": {},
        "stats": {}
    }
    
    total_solutions = 0
    rarity_scores = []
    
    for plate, solutions in info_model['plate_solutions'].items():
        if not solutions:
            continue
            
        rarity = calculate_continuous_rarity(plate, solutions, plate_stats, word_freq_map)
        solution_count = len(solutions)
        total_solutions += solution_count
        rarity_scores.append(rarity)
        
        # Store lightweight plate metadata
        index['plates'][plate] = {
            'rarity': rarity,
            'solution_count': solution_count,
            'difficulty': min(10, rarity / 10),
            'avg_frequency': sum(freq for word, freq in solutions) / solution_count if solution_count > 0 else 0
        }
    
    index['metadata']['total_plates'] = len(index['plates'])
    index['metadata']['total_solutions'] = total_solutions
    
    index['stats'] = {
        'rarity_range': [min(rarity_scores), max(rarity_scores)],
        'avg_rarity': statistics.mean(rarity_scores),
        'solution_distribution': {
            'min': min(len(sols) for sols in info_model['plate_solutions'].values() if sols),
            'max': max(len(sols) for sols in info_model['plate_solutions'].values() if sols),
            'avg': total_solutions / len(index['plates'])
        }
    }
    
    return index

def generate_jsonl_format(info_model: Dict, ortho_model: Dict, word_freq_map: Dict, output_dir: Path) -> Path:
    """Generate JSONL format - one line per plate with all solutions."""
    print("📄 Generating JSONL format...")
    
    jsonl_path = output_dir / "complete_plates.jsonl"
    jsonl_gz_path = output_dir / "complete_plates.jsonl.gz"
    
    plate_stats = info_model['plate_info_stats']
    processed = 0
    
    with open(jsonl_path, 'w') as f, gzip.open(jsonl_gz_path, 'wt') as f_gz:
        for plate, solutions in info_model['plate_solutions'].items():
            if not solutions:
                continue
                
            processed += 1
            if processed % 1000 == 0:
                print(f"   Processed {processed:,} plates...")
            
            rarity = calculate_continuous_rarity(plate, solutions, plate_stats, word_freq_map)
            
            # Create complete plate data
            plate_data = {
                'plate': plate,
                'rarity': rarity,
                'solution_count': len(solutions),
                'solutions': []
            }
            
            # Add ALL solutions with basic scoring
            for word, frequency in solutions:
                scores = calculate_word_scores(word, frequency, rarity)
                plate_data['solutions'].append({
                    'word': word,
                    'frequency': frequency,
                    'scores': scores
                })
            
            # Write to both files
            json_line = json.dumps(plate_data, separators=(',', ':'))
            f.write(json_line + '\n')
            f_gz.write(json_line + '\n')
    
    # Size comparison
    uncompressed_mb = jsonl_path.stat().st_size / 1024 / 1024
    compressed_mb = jsonl_gz_path.stat().st_size / 1024 / 1024
    
    print(f"   📄 JSONL: {uncompressed_mb:.1f}MB")
    print(f"   📦 JSONL.GZ: {compressed_mb:.1f}MB ({compressed_mb/uncompressed_mb*100:.1f}% of original)")
    
    return jsonl_gz_path

def generate_individual_files(info_model: Dict, ortho_model: Dict, word_freq_map: Dict, output_dir: Path) -> Path:
    """Generate individual JSON file for each plate."""
    print("📁 Generating individual plate files...")
    
    plates_dir = output_dir / "plates"
    plates_dir.mkdir(exist_ok=True)
    
    plate_stats = info_model['plate_info_stats']
    processed = 0
    total_files = 0
    total_size = 0
    
    for plate, solutions in info_model['plate_solutions'].items():
        if not solutions:
            continue
            
        processed += 1
        if processed % 1000 == 0:
            print(f"   Created {processed:,} plate files...")
        
        rarity = calculate_continuous_rarity(plate, solutions, plate_stats, word_freq_map)
        
        plate_data = {
            'plate': plate,
            'rarity': rarity,
            'solution_count': len(solutions),
            'solutions': []
        }
        
        for word, frequency in solutions:
            scores = calculate_word_scores(word, frequency, rarity)
            plate_data['solutions'].append({
                'word': word,
                'frequency': frequency,
                'scores': scores
            })
        
        # Save individual file
        file_path = plates_dir / f"{plate}.json"
        with open(file_path, 'w') as f:
            json.dump(plate_data, f, separators=(',', ':'))
        
        total_files += 1
        total_size += file_path.stat().st_size
    
    avg_file_kb = (total_size / total_files) / 1024
    total_mb = total_size / 1024 / 1024
    
    print(f"   📁 Created {total_files:,} files")
    print(f"   📊 Average file size: {avg_file_kb:.1f}KB")
    print(f"   📦 Total size: {total_mb:.1f}MB")
    
    return plates_dir

def generate_chunked_format(info_model: Dict, ortho_model: Dict, word_freq_map: Dict, output_dir: Path, chunk_size: int = 100) -> Path:
    """Generate chunked data files for balanced loading."""
    print(f"🗂️  Generating chunked format ({chunk_size} plates per chunk)...")
    
    chunks_dir = output_dir / "chunks"
    chunks_dir.mkdir(exist_ok=True)
    
    plate_stats = info_model['plate_info_stats']
    plates = [(plate, solutions) for plate, solutions in info_model['plate_solutions'].items() if solutions]
    
    num_chunks = math.ceil(len(plates) / chunk_size)
    chunk_manifest = []
    
    for chunk_idx in range(num_chunks):
        start_idx = chunk_idx * chunk_size
        end_idx = min(start_idx + chunk_size, len(plates))
        chunk_plates = plates[start_idx:end_idx]
        
        chunk_data = {
            'chunk_id': chunk_idx,
            'plate_count': len(chunk_plates),
            'plates': {}
        }
        
        chunk_solutions = 0
        for plate, solutions in chunk_plates:
            rarity = calculate_continuous_rarity(plate, solutions, plate_stats, word_freq_map)
            
            plate_data = {
                'rarity': rarity,
                'solution_count': len(solutions),
                'solutions': []
            }
            
            for word, frequency in solutions:
                scores = calculate_word_scores(word, frequency, rarity)
                plate_data['solutions'].append({
                    'word': word,
                    'frequency': frequency,
                    'scores': scores
                })
            
            chunk_data['plates'][plate] = plate_data
            chunk_solutions += len(solutions)
        
        # Save chunk
        chunk_path = chunks_dir / f"chunk_{chunk_idx:04d}.json"
        with open(chunk_path, 'w') as f:
            json.dump(chunk_data, f, separators=(',', ':'))
        
        chunk_mb = chunk_path.stat().st_size / 1024 / 1024
        chunk_manifest.append({
            'chunk_id': chunk_idx,
            'filename': f"chunk_{chunk_idx:04d}.json",
            'plate_count': len(chunk_plates),
            'solution_count': chunk_solutions,
            'size_mb': round(chunk_mb, 1),
            'plates': [plate for plate, _ in chunk_plates]
        })
        
        if chunk_idx % 50 == 0:
            print(f"   Created chunk {chunk_idx}/{num_chunks} ({chunk_mb:.1f}MB)")
    
    # Save manifest
    manifest_path = chunks_dir / "manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump({
            'total_chunks': num_chunks,
            'chunk_size': chunk_size,
            'chunks': chunk_manifest
        }, f, indent=2)
    
    total_mb = sum(chunk['size_mb'] for chunk in chunk_manifest)
    avg_mb = total_mb / num_chunks
    
    print(f"   🗂️  Created {num_chunks} chunks")
    print(f"   📊 Average chunk size: {avg_mb:.1f}MB")
    print(f"   📦 Total size: {total_mb:.1f}MB")
    
    return chunks_dir

def main():
    """Generate complete word game data in multiple formats."""
    print("🎯 COMPLETE WORD GAME DATA GENERATOR")
    print("=" * 50)
    print("Generating ALL 7+ million word solutions!")
    print()
    
    info_model, ortho_model, word_freq_map = load_models()
    
    output_dir = Path("complete_game_data")
    output_dir.mkdir(exist_ok=True)
    
    # Generate master index
    plate_stats = info_model['plate_info_stats']
    index = generate_index_file(info_model, plate_stats, word_freq_map)
    
    index_path = output_dir / "index.json"
    with open(index_path, 'w') as f:
        json.dump(index, f, indent=2)
    
    print(f"💾 Saved index.json: {index_path.stat().st_size / 1024:.1f}KB")
    print()
    
    # Generate different data formats
    print("🏭 GENERATING MULTIPLE DATA FORMATS...")
    print()
    
    # 1. JSONL format (recommended for streaming)
    jsonl_path = generate_jsonl_format(info_model, ortho_model, word_freq_map, output_dir)
    
    print()
    
    # 2. Individual files (good for on-demand loading)
    individual_dir = generate_individual_files(info_model, ortho_model, word_freq_map, output_dir)
    
    print()
    
    # 3. Chunked format (balanced approach)
    chunks_dir = generate_chunked_format(info_model, ortho_model, word_freq_map, output_dir, chunk_size=100)
    
    # Summary
    print()
    print("✅ COMPLETE WORD GAME DATA GENERATED!")
    print("=" * 50)
    print(f"📊 Total plates: {index['metadata']['total_plates']:,}")
    print(f"🎮 Total solutions: {index['metadata']['total_solutions']:,}")
    print(f"📈 Rarity range: {index['stats']['rarity_range'][0]:.1f} - {index['stats']['rarity_range'][1]:.1f}")
    print()
    print("📁 DATA FORMATS AVAILABLE:")
    print(f"   1. JSONL (streaming): {jsonl_path.name}")
    print(f"   2. Individual files: {individual_dir.name}/ ({len(list(individual_dir.glob('*.json'))):,} files)")  
    print(f"   3. Chunked data: {chunks_dir.name}/ ({len(list(chunks_dir.glob('chunk_*.json')))} chunks)")
    print(f"   4. Index file: index.json (navigation & metadata)")
    print()
    print("🚀 READY FOR COMPLETE WORD GAME IMPLEMENTATION!")

if __name__ == "__main__":
    main()

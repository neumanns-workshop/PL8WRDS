#!/usr/bin/env python3
"""
Build comprehensive Information Content model with full 3-letter plate coverage.

This script generates all possible 3-letter license plates (AAA-ZZZ),
finds solutions for each using the solver, and builds a complete 
Information Content model for scoring word impressiveness.
"""

import string
import time
from pathlib import Path
import json
from collections import defaultdict

# Add the app directory to the Python path
import sys
sys.path.append(str(Path(__file__).parent))

from app.services.information_scorer import InformationContentScorer
from app.services.solver_service import solve_combination

def generate_all_plates():
    """Generate all possible 3-letter license plates (AAA to ZZZ)."""
    plates = []
    for c1 in string.ascii_uppercase:
        for c2 in string.ascii_uppercase:
            for c3 in string.ascii_uppercase:
                plates.append(c1 + c2 + c3)
    return plates

def build_comprehensive_model():
    """Build Information Content model with comprehensive plate coverage."""
    
    print("🚀 Building comprehensive Information Content model...")
    print(f"📊 Processing all possible 3-letter plates (17,576 combinations)")
    
    # Generate all possible plates
    all_plates = generate_all_plates()
    print(f"✅ Generated {len(all_plates)} possible plates")
    
    # Track progress
    plates_with_solutions = []
    empty_plates = 0
    start_time = time.time()
    
    print("\n🔍 Finding plates with solutions...")
    
    # Process in batches for progress reporting
    batch_size = 500
    total_solutions = 0
    
    for i in range(0, len(all_plates), batch_size):
        batch = all_plates[i:i+batch_size]
        batch_solutions = 0
        
        for plate in batch:
            # Find solutions for this plate
            solutions = solve_combination(plate)
            if solutions:
                plates_with_solutions.append(plate)
                batch_solutions += len(solutions)
                total_solutions += len(solutions)
            else:
                empty_plates += 1
        
        # Progress report
        elapsed = time.time() - start_time
        processed = i + len(batch)
        rate = processed / elapsed if elapsed > 0 else 0
        eta = (len(all_plates) - processed) / rate if rate > 0 else 0
        
        print(f"⏳ Processed {processed:,}/17,576 plates ({processed/175.76:.1f}%) - "
              f"Found {len(plates_with_solutions):,} with solutions - "
              f"Rate: {rate:.1f} plates/sec - ETA: {eta/60:.1f}m")
    
    elapsed_time = time.time() - start_time
    
    print(f"\n📈 Discovery Summary:")
    print(f"   🎯 Plates with solutions: {len(plates_with_solutions):,}")
    print(f"   🚫 Empty plates: {empty_plates:,}")
    print(f"   💫 Total solutions found: {total_solutions:,}")
    print(f"   ⏰ Processing time: {elapsed_time:.1f} seconds")
    print(f"   🏃 Average rate: {len(all_plates)/elapsed_time:.1f} plates/sec")
    
    # Now build the Information Content model
    print(f"\n🧮 Building Information Content model from {len(plates_with_solutions):,} plates...")
    
    scorer = InformationContentScorer()
    
    # Override the plate generation to use our discovered plates
    def use_discovered_plates(max_plates):
        return plates_with_solutions[:max_plates]
    
    # Temporarily replace the method
    original_method = scorer._generate_plates
    scorer._generate_plates = use_discovered_plates
    
    # Build the model with all discovered plates
    model_start = time.time()
    scorer.build_model(max_plates=len(plates_with_solutions))
    model_time = time.time() - model_start
    
    # Restore original method
    scorer._generate_plates = original_method
    
    print(f"✅ Model built in {model_time:.1f} seconds")
    
    # Save the model
    model_path = Path("models/information_model.json")
    model_path.parent.mkdir(exist_ok=True)
    scorer.save_model(str(model_path))
    
    print(f"💾 Model saved to {model_path}")
    
    # Verify coverage with test cases
    print(f"\n🔬 Verifying coverage...")
    test_plates = ['THE', 'BIG', 'ABC', 'DOG', 'CAR', 'XYZ', 'ZZZ', 'AAA']
    
    for plate in test_plates:
        available = plate in scorer.plate_solutions
        solution_count = len(scorer.plate_solutions.get(plate, []))
        print(f"   {plate}: {'✅' if available else '❌'} "
              f"({solution_count} solutions)" if available else f"(no solutions)")
    
    print(f"\n🎉 Comprehensive Information Content model complete!")
    print(f"   📊 Coverage: {len(plates_with_solutions):,} plates")
    print(f"   💫 Solutions: {total_solutions:,} word-plate pairs")
    print(f"   📁 Model size: ~{model_path.stat().st_size/1024/1024:.1f}MB")
    
    return scorer

if __name__ == "__main__":
    build_comprehensive_model()

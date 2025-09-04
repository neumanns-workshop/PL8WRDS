#!/usr/bin/env python3
"""
Step 1: Pregenerate ALL solutions for ALL plates first.
Step 2: Then score them efficiently.
"""

import asyncio
import httpx
import json
import gzip
from pathlib import Path
from typing import Dict, List, Any
from tqdm import tqdm

# API Configuration
BASE_URL = "http://localhost:8000"
OUTPUT_DIR = Path("client_game_data")
WORDS_DIR = OUTPUT_DIR / "words"

class AllSolutionsGenerator:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.all_plates = []
        self.all_solutions = {}  # {plate: [words]}
        self.word_dict = {}  # {word: {word_id, corpus_frequency}}
        self.next_word_id = 1
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    def get_word_id(self, word: str, frequency: int) -> int:
        """Get or create word ID for a word."""
        if word not in self.word_dict:
            self.word_dict[word] = {
                "word_id": self.next_word_id,
                "corpus_frequency": frequency
            }
            word_id = self.next_word_id
            self.next_word_id += 1
            return word_id
        return self.word_dict[word]["word_id"]
    
    async def generate_all_plates(self):
        """Generate all 3-letter plate combinations."""
        print("Generating all 3-letter plate combinations...")
        
        response = await self.client.post(f"{BASE_URL}/generate-combinations", json={
            "lengths": [3],
            "character_set": "abcdefghijklmnopqrstuvwxyz", 
            "generation_mode": "all"
        })
        response.raise_for_status()
        
        combinations = response.json()["combinations"]
        self.all_plates = [combo.upper() for combo in combinations]
        print(f"Generated {len(self.all_plates)} plate combinations")
    
    async def get_solutions_for_plate(self, plate: str):
        """Get solutions for a single plate."""
        response = await self.client.get(f"{BASE_URL}/solve/{plate.lower()}")
        response.raise_for_status()
        
        data = response.json()
        solutions = []
        
        for match in data["matches"]:
            word = match["word"]
            frequency = match["frequency"]
            word_id = self.get_word_id(word, frequency)
            
            solutions.append({
                "word": word,
                "word_id": word_id,
                "frequency": frequency
            })
        
        return solutions
    
    async def pregenerate_all_solutions(self):
        """Pregenerate ALL solutions for ALL plates."""
        print(f"Pregenerating solutions for {len(self.all_plates)} plates...")
        
        # Process in parallel batches
        batch_size = 100
        for i in tqdm(range(0, len(self.all_plates), batch_size), desc="Generating solutions"):
            batch = self.all_plates[i:i + batch_size]
            
            # Create tasks for this batch
            tasks = [self.get_solutions_for_plate(plate) for plate in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Store results
            for j, result in enumerate(results):
                plate = batch[j]
                if isinstance(result, Exception):
                    print(f"Error getting solutions for {plate}: {result}")
                    continue
                
                if result:
                    self.all_solutions[plate] = result
        
        total_solutions = sum(len(solutions) for solutions in self.all_solutions.values())
        print(f"Pregenerated {total_solutions} total solutions for {len(self.all_solutions)} plates")
        print(f"Unique words discovered: {len(self.word_dict)}")
    
    def save_pregenerated_data(self):
        """Save pregenerated solutions to file for scoring step."""
        print("Saving pregenerated solutions...")
        
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        # Save solutions data
        with open(OUTPUT_DIR / "pregenerated_solutions.json", 'w') as f:
            json.dump({
                "plates": self.all_solutions,
                "word_dict": self.word_dict
            }, f, indent=2)
        
        print("Saved pregenerated solutions to pregenerated_solutions.json")
        return len(self.all_solutions), sum(len(sols) for sols in self.all_solutions.values())

async def main():
    """Main function to pregenerate all solutions."""
    async with AllSolutionsGenerator() as generator:
        try:
            # Step 1: Generate all plate combinations
            await generator.generate_all_plates()
            
            # Step 2: Pregenerate ALL solutions for ALL plates
            await generator.pregenerate_all_solutions()
            
            # Step 3: Save for next step
            plates_count, solutions_count = generator.save_pregenerated_data()
            
            print("=" * 60)
            print("PREGENERATION COMPLETE")
            print(f"Plates: {plates_count}")
            print(f"Total solutions: {solutions_count}")
            print(f"Unique words: {len(generator.word_dict)}")
            print("Next: Run scoring step")
            print("=" * 60)
            
        except Exception as e:
            print(f"Pregeneration failed: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(main())



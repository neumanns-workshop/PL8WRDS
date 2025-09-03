#!/usr/bin/env python3
"""
Comprehensive PL8WRDS Gameplay Pipeline

Uses the built-in API endpoints to create a complete analysis workflow:
1. Solver endpoint: Generate all valid solutions for plates
2. Ensemble endpoint: Score solutions with tunable weights
3. Analysis: Rank and analyze solution impressiveness
"""

import httpx
import asyncio
import random
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class ScoringWeights:
    """Configuration for ensemble scoring weights."""
    vocabulary: float = 0.33
    information: float = 0.33  
    orthographic: float = 0.34
    description: str = "Balanced"
    
    def normalize(self):
        """Normalize weights to sum to 1.0."""
        total = self.vocabulary + self.information + self.orthographic
        if total > 0:
            self.vocabulary /= total
            self.information /= total
            self.orthographic /= total

class GameplayPipeline:
    """Complete gameplay analysis pipeline using API endpoints."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    async def get_solutions_for_plate(self, plate: str) -> Dict[str, Any]:
        """Get all solutions for a plate using the solver endpoint."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/solve/{plate}")
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"error": f"HTTP {response.status_code}: {response.text}"}
            except Exception as e:
                return {"error": f"Request failed: {e}"}
    
    async def score_solution(self, word: str, plate: str, weights: ScoringWeights) -> Dict[str, Any]:
        """Score a solution using the ensemble endpoint."""
        weights.normalize()
        
        async with httpx.AsyncClient() as client:
            try:
                params = {
                    "vocab_weight": weights.vocabulary,
                    "info_weight": weights.information,
                    "ortho_weight": weights.orthographic
                }
                payload = {"word": word, "plate": plate}
                
                response = await client.post(f"{self.base_url}/predict/ensemble", 
                                           json=payload, params=params)
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"error": f"HTTP {response.status_code}: {response.text}"}
            except Exception as e:
                return {"error": f"Request failed: {e}"}
    
    async def analyze_plate_comprehensive(self, plate: str, weights: ScoringWeights, 
                                        top_n: int = 10) -> Dict[str, Any]:
        """Complete analysis of a plate with solution scoring."""
        
        print(f"\n🎯 COMPREHENSIVE PLATE ANALYSIS: {plate.upper()}")
        print(f"⚖️  Scoring Strategy: {weights.description}")
        print(f"📊 Weights: Vocab {weights.vocabulary:.0%} | Info {weights.information:.0%} | Pattern {weights.orthographic:.0%}")
        print("=" * 80)
        
        # Step 1: Get all solutions
        print("🔍 Finding solutions...")
        solutions_result = await self.get_solutions_for_plate(plate)
        
        if "error" in solutions_result:
            return {"error": f"Failed to get solutions: {solutions_result['error']}"}
        
        solutions = solutions_result.get("matches", [])
        if not solutions:
            return {"error": f"No solutions found for plate {plate}"}
        
        print(f"✅ Found {len(solutions)} solutions")
        print(f"📈 Lexical Fertility: {solutions_result['lexical_fertility']}")
        
        # Step 2: Score each solution
        print(f"\n📊 Scoring solutions with ensemble endpoint...")
        scored_solutions = []
        
        for i, solution in enumerate(solutions, 1):
            word = solution["word"]
            corpus_freq = solution["frequency"]
            
            # Score with ensemble
            score_result = await self.score_solution(word, plate, weights)
            
            if "error" not in score_result:
                scored_solutions.append({
                    "word": word,
                    "corpus_frequency": corpus_freq,
                    "ensemble_score": score_result["ensemble_score"],
                    "confidence": score_result["confidence"],
                    "individual_scores": score_result["individual_scores"],
                    "interpretation": score_result["interpretation"]
                })
            else:
                scored_solutions.append({
                    "word": word,
                    "corpus_frequency": corpus_freq,
                    "ensemble_score": 0,
                    "confidence": 0,
                    "error": score_result["error"]
                })
            
            # Progress indicator
            if i % 10 == 0 or i == len(solutions):
                print(f"   Processed {i}/{len(solutions)} solutions...")
        
        # Step 3: Sort by ensemble score
        scored_solutions.sort(key=lambda x: x.get("ensemble_score", 0), reverse=True)
        
        return {
            "plate": plate,
            "total_solutions": len(solutions),
            "fertility": solutions_result["lexical_fertility"],
            "frequency_stats": solutions_result.get("frequency_distribution", {}),
            "weights_used": {
                "vocabulary": weights.vocabulary,
                "information": weights.information,
                "orthographic": weights.orthographic,
                "description": weights.description
            },
            "top_solutions": scored_solutions[:top_n],
            "all_solutions": scored_solutions
        }
    
    def print_analysis_results(self, analysis: Dict[str, Any]):
        """Print formatted analysis results."""
        
        if "error" in analysis:
            print(f"❌ Analysis failed: {analysis['error']}")
            return
        
        plate = analysis["plate"]
        top_solutions = analysis["top_solutions"]
        weights_used = analysis["weights_used"]
        
        print(f"\n🏆 TOP SOLUTIONS FOR {plate.upper()}:")
        print("=" * 80)
        
        for i, solution in enumerate(top_solutions, 1):
            if "error" in solution:
                print(f"{i:2}. {solution['word']:12} ❌ Scoring Error: {solution['error']}")
                continue
            
            word = solution["word"]
            ensemble_score = solution["ensemble_score"]
            confidence = solution["confidence"]
            corpus_freq = solution["corpus_frequency"]
            interpretation = solution["interpretation"]
            individual = solution["individual_scores"]
            
            print(f"\n{i:2}. {word.upper():12} | {ensemble_score:5.1f}/100 | {interpretation}")
            print(f"    Confidence: {confidence:.1%} | Corpus Freq: {corpus_freq:,}")
            
            # Show component breakdown
            components = []
            for component, data in individual.items():
                if data["status"] == "success":
                    score = data["score"]
                    contribution = data["weighted_contribution"]
                    components.append(f"{component.title()}: {score:.1f} ({contribution:+.1f})")
                else:
                    components.append(f"{component.title()}: ❌")
            
            print(f"    Components: {' | '.join(components)}")
        
        # Summary statistics
        successful_scores = [s for s in top_solutions if "error" not in s and s["confidence"] > 0]
        if successful_scores:
            avg_score = sum(s["ensemble_score"] for s in successful_scores) / len(successful_scores)
            avg_confidence = sum(s["confidence"] for s in successful_scores) / len(successful_scores)
            
            print(f"\n📊 SUMMARY:")
            print(f"   Average Score (Top {len(successful_scores)}): {avg_score:.1f}/100")
            print(f"   Average Confidence: {avg_confidence:.1%}")
            print(f"   Fertility: {analysis['fertility']} ({analysis['total_solutions']} solutions)")

async def run_gameplay_experiments():
    """Run comprehensive gameplay pipeline experiments."""
    
    pipeline = GameplayPipeline()
    
    # Different scoring strategies to test
    strategies = [
        ScoringWeights(0.33, 0.33, 0.34, "Balanced"),
        ScoringWeights(0.6, 0.2, 0.2, "Vocabulary-Heavy"),
        ScoringWeights(0.2, 0.6, 0.2, "Information-Heavy"),
        ScoringWeights(0.2, 0.2, 0.6, "Pattern-Heavy"),
    ]
    
    # Test plates (mix of different characteristics)
    test_plates = ["PDG", "THE", "CAR", "BIG", "XYZ"]
    
    print("🚀 PL8WRDS COMPREHENSIVE GAMEPLAY PIPELINE")
    print("=" * 80)
    print("Testing different scoring strategies across various plates")
    
    for plate in test_plates:
        print(f"\n" + "="*100)
        print(f"🎯 ANALYZING PLATE: {plate.upper()}")
        print("="*100)
        
        for strategy in strategies:
            try:
                analysis = await pipeline.analyze_plate_comprehensive(plate, strategy, top_n=5)
                pipeline.print_analysis_results(analysis)
                
                print(f"\n{'-'*80}")
                await asyncio.sleep(0.1)  # Brief pause between strategies
                
            except Exception as e:
                print(f"❌ Strategy '{strategy.description}' failed for {plate}: {e}")
        
        await asyncio.sleep(0.5)  # Pause between plates

async def analyze_single_plate(plate: str, strategy_name: str = "balanced"):
    """Analyze a single plate with specified strategy."""
    
    strategies = {
        "balanced": ScoringWeights(0.33, 0.33, 0.34, "Balanced"),
        "vocabulary": ScoringWeights(0.6, 0.2, 0.2, "Vocabulary-Heavy"), 
        "information": ScoringWeights(0.2, 0.6, 0.2, "Information-Heavy"),
        "pattern": ScoringWeights(0.2, 0.2, 0.6, "Pattern-Heavy"),
    }
    
    pipeline = GameplayPipeline()
    weights = strategies.get(strategy_name, strategies["balanced"])
    
    analysis = await pipeline.analyze_plate_comprehensive(plate, weights, top_n=10)
    pipeline.print_analysis_results(analysis)

if __name__ == "__main__":
    import sys
    
    print("🎮 PL8WRDS Gameplay Pipeline")
    print("Make sure FastAPI server is running on localhost:8000\n")
    
    if len(sys.argv) > 1:
        # Single plate analysis mode
        plate = sys.argv[1].upper()
        strategy = sys.argv[2].lower() if len(sys.argv) > 2 else "balanced"
        
        print(f"Analyzing single plate: {plate} with {strategy} strategy")
        try:
            asyncio.run(analyze_single_plate(plate, strategy))
        except KeyboardInterrupt:
            print("\n👋 Analysis interrupted")
        except Exception as e:
            print(f"❌ Analysis failed: {e}")
    else:
        # Full experiment mode
        print("Running comprehensive experiments...")
        try:
            asyncio.run(run_gameplay_experiments())
        except KeyboardInterrupt:
            print("\n👋 Experiments interrupted")
        except Exception as e:
            print(f"❌ Experiments failed: {e}")

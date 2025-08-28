#!/usr/bin/env python3
"""
Demo script for the PL8WRDS word scoring system.
"""

import asyncio
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(__file__))

from app.services.scoring_service import scoring_service
from app.models.scoring import ScoringModel, RandomScoringRequest

async def demo_scoring_system():
    """Demonstrate the word scoring system."""
    print("🎯 PL8WRDS Word Scoring System Demo")
    print("=" * 50)
    
    # Check system status
    print("\n1. Checking system status...")
    status = await scoring_service.check_system_status()
    print(f"   Ollama running: {status.ollama_running}")
    print(f"   Available models: {len([m for m in status.models if m.available])}")
    
    if not status.ollama_running:
        print("❌ Ollama is not running. Please start it with: ollama serve")
        return
    
    # Ensure models are available
    print("\n2. Setting up models...")
    models = [ScoringModel.GRANITE, ScoringModel.MISTRAL]  # Start with 2 models
    available_models = await scoring_service.ensure_models_available(models)
    print(f"   Available models: {[m.value for m in available_models]}")
    
    if not available_models:
        print("❌ No models available. Please check your Ollama installation.")
        return
    
    # Demo single word scoring
    print("\n3. Scoring individual words...")
    test_cases = [
        ("cat", "cat"),
        ("ambulance", "abc"),
        ("elephant", "eph"),
        ("amazing", "amz")
    ]
    
    for word, combination in test_cases:
        print(f"\n   Scoring '{word}' for combination '{combination}':")
        try:
            result = await scoring_service.score_word_with_models(word, combination, available_models)
            print(f"   - Aggregate score: {result.aggregate_score:.1f}/100")
            for score in result.scores:
                print(f"   - {score.model.value}: {score.score}/100")
                print(f"     Reasoning: {score.reasoning[:100]}...")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Demo random scoring session
    print("\n4. Running random scoring session...")
    try:
        session = await scoring_service.score_random_words(
            num_combinations=2,
            words_per_combination=3,
            combination_length=3,
            models=available_models[:1],  # Use just one model for demo
            cache_key="demo_session"
        )
        
        print(f"   Session ID: {session.session_id}")
        print(f"   Total words scored: {len(session.results)}")
        print(f"   Session completed: {session.end_time is not None}")
        
        # Show some results
        if session.results:
            print("\n   Sample results:")
            for i, result in enumerate(session.results[:3]):
                avg_score = result.aggregate_score or 0
                print(f"   - '{result.word}' ({result.combination}): {avg_score:.1f}/100")
    
    except Exception as e:
        print(f"   ❌ Error in random scoring: {e}")
    
    print("\n✅ Demo completed!")
    print("\nNext steps:")
    print("- Start the FastAPI server: uvicorn app.main:app --reload")
    print("- Visit http://localhost:8000/docs for the API documentation")
    print("- Use the /scoring endpoints to score words")
    print("- Use the /metrics endpoints to analyze results")

if __name__ == "__main__":
    asyncio.run(demo_scoring_system())

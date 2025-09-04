#!/usr/bin/env python3
"""
Quick validation of the 3-dimensional scoring system.
Tests several examples to ensure clean functionality.
"""

import asyncio
import httpx
import json

async def test_3d_system():
    """Test the 3-dimensional ensemble system with various examples."""
    
    test_cases = [
        ("pedagogue", "PDG", "Classic sophisticated example"),
        ("faqir", "FQR", "Ultra-rare with Q - should max out"),
        ("quetzal", "QZL", "Rare bird with Q and Z"),
        ("big", "BIG", "Simple word - should score low"),
        ("razzmatazz", "RZZ", "Fun word with double Z"),
        ("muzhik", "UZK", "Rare word with Z"),
        ("buzzbomb", "BZM", "Double Z compound")
    ]
    
    print("🎯 TESTING 3-DIMENSIONAL SCORING SYSTEM")
    print("=" * 60)
    print(f"{'Word':<12} {'Plate':<5} {'Score':<6} {'V':<4} {'I':<4} {'O':<4} {'Description'}")
    print("-" * 60)
    
    async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
        for word, plate, description in test_cases:
            try:
                response = await client.post(
                    "http://localhost:8000/predict/ensemble",
                    json={"word": word, "plate": plate}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Extract scores
                    ensemble = data["ensemble_score"]
                    individual = data["individual_scores"]
                    
                    vocab_score = individual.get("vocabulary", {}).get("score", 0)
                    info_score = individual.get("information", {}).get("score", 0) 
                    ortho_score = individual.get("orthographic", {}).get("score", 0)
                    
                    # Format output
                    print(f"{word.upper():<12} {plate:<5} {ensemble:<6.1f} {vocab_score:<4.0f} {info_score:<4.0f} {ortho_score:<4.0f} {description}")
                    
                else:
                    print(f"{word.upper():<12} {plate:<5} ERROR  -    -    -    HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"{word.upper():<12} {plate:<5} ERROR  -    -    -    {str(e)[:20]}")
    
    print("-" * 60)
    print("✅ 3D System Test Complete!")
    print("   V=Vocabulary, I=Information, O=Orthographic")

if __name__ == "__main__":
    asyncio.run(test_3d_system())

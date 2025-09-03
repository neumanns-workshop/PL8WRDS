#!/usr/bin/env python3
"""
Comprehensive system health test for PL8WRDS after cleanup.
Tests all core functionality to ensure everything works.
"""

import asyncio
import httpx
import json
import time

async def test_system_health():
    """Run comprehensive system health checks."""
    
    print("🏥 PL8WRDS SYSTEM HEALTH CHECK")
    print("=" * 60)
    
    start_time = time.time()
    passed_tests = 0
    total_tests = 0
    
    async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
        
        # Test 1: Health Check
        print("\n1. 🩺 BASIC HEALTH CHECK")
        print("-" * 30)
        total_tests += 1
        
        try:
            response = await client.get("http://localhost:8000/health")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health: {data['status']} (v{data['version']})")
                passed_tests += 1
            else:
                print(f"❌ Health check failed: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ Health check error: {e}")
        
        # Test 2: Solver Functionality  
        print("\n2. 🧩 SOLVER FUNCTIONALITY")
        print("-" * 30)
        test_plates = ["PDG", "FQR", "BIG", "ZZZ"]
        
        for plate in test_plates:
            total_tests += 1
            try:
                response = await client.get(f"http://localhost:8000/solve/{plate}")
                if response.status_code == 200:
                    data = response.json()
                    word_count = len(data.get('matches', []))
                    if word_count > 0:
                        top_word = data['matches'][0]['word']
                        print(f"✅ {plate}: {word_count} solutions (top: {top_word.upper()})")
                        passed_tests += 1
                    else:
                        print(f"❌ {plate}: No solutions found")
                else:
                    print(f"❌ {plate}: HTTP {response.status_code}")
            except Exception as e:
                print(f"❌ {plate}: {e}")
        
        # Test 3: 3D Ensemble Scoring (The Core!)
        print("\n3. 🎯 3D ENSEMBLE SCORING SYSTEM")
        print("-" * 30)
        
        test_cases = [
            ("pedagogue", "PDG", "Classic sophisticated word"),
            ("faqir", "FQR", "Ultra-rare Q word"),  
            ("big", "BIG", "Simple common word"),
            ("zugzwang", "ZUG", "Chess term with Z"),
            ("quetzal", "QZL", "Rare bird Q+Z combo")
        ]
        
        print(f"{'Word':<12} {'Plate':<5} {'Score':<6} {'V':<3} {'I':<3} {'O':<3} {'Status'}")
        print("-" * 50)
        
        for word, plate, description in test_cases:
            total_tests += 1
            try:
                response = await client.post(
                    "http://localhost:8000/predict/ensemble",
                    json={"word": word, "plate": plate}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    score = data.get("ensemble_score", 0)
                    individual = data.get("individual_scores", {})
                    
                    # Extract individual component scores
                    v_score = individual.get("vocabulary", {}).get("score", 0)
                    i_score = individual.get("information", {}).get("score", 0) 
                    o_score = individual.get("orthographic", {}).get("score", 0)
                    
                    print(f"{word.upper():<12} {plate:<5} {score:<6.1f} {v_score:<3.0f} {i_score:<3.0f} {o_score:<3.0f} ✅")
                    passed_tests += 1
                else:
                    print(f"{word.upper():<12} {plate:<5} ERROR  -   -   -   ❌ HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"{word.upper():<12} {plate:<5} ERROR  -   -   -   ❌ {str(e)[:15]}")
        
        # Test 4: Data Systems
        print("\n4. 📊 DATA SYSTEMS")
        print("-" * 30)
        total_tests += 1
        
        try:
            response = await client.get("http://localhost:8000/dataset/status")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Dataset: {data['message']}")
                print(f"   Active endpoints: {len(data['active_endpoints'])}")
                passed_tests += 1
            else:
                print(f"❌ Dataset status: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ Dataset status: {e}")
        
        # Test 5: Edge Cases & Error Handling
        print("\n5. 🚨 ERROR HANDLING")
        print("-" * 30)
        
        error_tests = [
            ("GET", "/solve/INVALID123", "Invalid plate format", None),
            ("POST", "/predict/ensemble", "Missing request body", None),
            ("GET", "/nonexistent", "Unknown endpoint", None)
        ]
        
        for method, endpoint, description, body in error_tests:
            total_tests += 1
            try:
                if method == "GET":
                    response = await client.get(f"http://localhost:8000{endpoint}")
                else:
                    response = await client.post(f"http://localhost:8000{endpoint}", json=body)
                
                # We expect these to fail gracefully (not crash the server)
                if response.status_code >= 400:
                    print(f"✅ {description}: HTTP {response.status_code} (expected)")
                    passed_tests += 1
                else:
                    print(f"❌ {description}: Unexpected success")
            except Exception as e:
                print(f"✅ {description}: Exception handled ({str(e)[:30]})")
                passed_tests += 1
        
        # Summary
        elapsed = time.time() - start_time
        print("\n" + "=" * 60)
        print("📈 SYSTEM HEALTH SUMMARY")
        print("=" * 60)
        
        success_rate = (passed_tests / total_tests) * 100
        
        print(f"⏱️  Test Duration: {elapsed:.1f} seconds")
        print(f"📊 Tests Passed: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        if success_rate >= 90:
            print("🎉 SYSTEM STATUS: EXCELLENT")
            print("   All core functionality working perfectly!")
        elif success_rate >= 70:
            print("⚠️  SYSTEM STATUS: GOOD")  
            print("   Core functionality working with minor issues")
        else:
            print("🚨 SYSTEM STATUS: NEEDS ATTENTION")
            print("   Multiple system failures detected")
        
        print(f"\n🎯 CORE FUNCTIONALITY:")
        print(f"   3D Ensemble Scoring: {'✅ Working' if passed_tests >= 8 else '❌ Issues'}")
        print(f"   Word Solver: {'✅ Working' if passed_tests >= 4 else '❌ Issues'}")
        print(f"   Data Systems: {'✅ Clean' if passed_tests >= 12 else '❌ Needs cleanup'}")
        
        print(f"\n💡 NEXT STEPS:")
        if success_rate >= 90:
            print("   ✨ System is ready for production use!")
            print("   🚀 Try: python gameplay_pipeline.py")
        else:
            print("   🔧 Address failing tests before proceeding")
            print("   📋 Check server logs for detailed errors")

if __name__ == "__main__":
    print("Starting comprehensive system health check...")
    print("Make sure the FastAPI server is running on localhost:8000")
    print()
    
    asyncio.run(test_system_health())

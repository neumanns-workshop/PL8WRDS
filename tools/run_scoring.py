#!/usr/bin/env python3
"""
Script to run PL8WRDS word scoring using the scoring system.
"""

import asyncio
import sys
import os
import argparse
import random
from typing import List, Optional, Dict

# Add the project root to the path
sys.path.append(os.path.dirname(__file__))

from app.services.scoring_service import scoring_service
from app.models.scoring import ScoringModel, IndividualScore
from app.services.recombination_metrics import recombination_metrics_service
from ollama_client import check_model_available

async def score_single_word(word: str, combination: str, models: List[ScoringModel]):
    """Score a single word with specified models."""
    print(f"🎯 Scoring '{word}' for combination '{combination}'")
    print("-" * 50)
    
    try:
        result = await scoring_service.score_word_with_models(word, combination, models)
        
        print(f"Word: {result.word}")
        print(f"Combination: {result.combination}")
        print(f"Frequency: {result.frequency or 'Unknown'}")
        print(f"Aggregate Score: {result.aggregate_score:.1f}/100" if result.aggregate_score else "No aggregate score")
        print("\nModel Scores:")
        
        for score in result.scores:
            print(f"  {score.model.value}: {score.score}/100")
            print(f"    Reasoning: {score.reasoning}")
            print()
            
        return result
        
    except Exception as e:
        print(f"❌ Error scoring word: {e}")
        return None

async def score_random_session(num_combinations: int, words_per_combo: int, combo_length: int, models: List[ScoringModel]):
    """Run a random scoring session."""
    print(f"🎲 Random Scoring Session")
    print(f"Combinations: {num_combinations}, Words per combo: {words_per_combo}, Length: {combo_length}")
    print("-" * 50)
    
    try:
        session = await scoring_service.score_random_words(
            num_combinations=num_combinations,
            words_per_combination=words_per_combo,
            combination_length=combo_length,
            models=models
        )
        
        print(f"Session ID: {session.session_id}")
        print(f"Total words scored: {len(session.results)}")
        print(f"Total individual scores: {session.total_scores}")
        print(f"Completed: {'Yes' if session.end_time else 'No'}")
        print(f"Interrupted: {'Yes' if session.interrupted else 'No'}")
        
        if session.results:
            print(f"\nTop scoring words:")
            # Sort by aggregate score
            sorted_results = sorted(
                session.results, 
                key=lambda x: x.aggregate_score or 0, 
                reverse=True
            )
            
            for i, result in enumerate(sorted_results[:5]):
                score = result.aggregate_score or 0
                print(f"  {i+1}. '{result.word}' ({result.combination}): {score:.1f}/100")
        
        # Generate metrics
        print(f"\n📊 Session Analysis:")
        metrics = recombination_metrics_service.analyze_session(session)
        
        for combination, combo_metrics in metrics.items():
            print(f"\nCombination '{combination}':")
            print(f"  Words scored: {combo_metrics.total_words_scored}")
            print(f"  Average score: {combo_metrics.average_score:.1f}")
            print(f"  Model agreement: {combo_metrics.model_agreement:.2f}")
            
            if combo_metrics.top_words:
                print(f"  Top words: {', '.join(combo_metrics.top_words[:3])}")
            
            # Show insights
            insights = recombination_metrics_service.generate_insights(combo_metrics)
            if insights:
                print(f"  Insights:")
                for insight in insights:
                    print(f"    • {insight}")
        
        return session
        
    except Exception as e:
        print(f"❌ Error in random scoring: {e}")
        return None

async def check_system():
    """Check system status."""
    print("🔍 System Status Check")
    print("-" * 50)
    
    status = await scoring_service.check_system_status()
    
    print(f"Ollama running: {'✅' if status.ollama_running else '❌'}")
    print(f"Cache enabled: {'✅' if status.cache_enabled else '❌'}")
    print(f"Active sessions: {status.active_sessions}")
    
    print("\nModel Availability:")
    for model_status in status.models:
        status_icon = "✅" if model_status.available else "❌"
        print(f"  {status_icon} {model_status.model.value}")
        if model_status.error_message:
            print(f"      Error: {model_status.error_message}")
    
    available_models = [m.model for m in status.models if m.available]
    print(f"\nAvailable models: {len(available_models)}")
    
    return available_models

def get_model_weights() -> Dict[ScoringModel, float]:
    """Get parameter-based weights for models (normalized to sum to 1)."""
    # Estimated parameter counts in billions
    model_params = {
        # Large models (7-8B)
        ScoringModel.GRANITE: 8.0,
        ScoringModel.MISTRAL: 7.0,
        ScoringModel.DEEPSEEK: 8.0,
        ScoringModel.QWEN3: 8.0,
        ScoringModel.LLAMA31: 8.0,
        
        # Small models (1-4B)
        ScoringModel.GRANITE_2B: 2.0,
        ScoringModel.PHI4_MINI: 3.8,
        ScoringModel.PHI3_MINI: 3.8,
        ScoringModel.LLAMA32_3B: 3.0,
        ScoringModel.QWEN25_3B: 3.0,
        ScoringModel.DEEPSEEK_1_5B: 1.5,
    }
    
    return model_params

def calculate_weighted_score(scores: List[IndividualScore]) -> float:
    """Calculate parameter-weighted average score."""
    if not scores:
        return 0.0
    
    model_weights = get_model_weights()
    total_weight = 0.0
    weighted_sum = 0.0
    
    for score in scores:
        weight = model_weights.get(score.model, 1.0)  # Default weight 1.0
        weighted_sum += score.score * weight
        total_weight += weight
    
    return weighted_sum / total_weight if total_weight > 0 else 0.0

def parse_models(model_strings: List[str]) -> List[ScoringModel]:
    """Parse model strings to ScoringModel enum values."""
    models = []
    model_map = {
        # Large models (10-32B)
        "cogito14b": ScoringModel.COGITO_14B,
        "cogito:14b": ScoringModel.COGITO_14B,
        "gemma3_12b": ScoringModel.GEMMA3_12B,
        "gemma3:12b": ScoringModel.GEMMA3_12B,
        "phi4plus": ScoringModel.PHI4_PLUS,
        "phi4-reasoning:plus": ScoringModel.PHI4_PLUS,
        "gpt-oss": ScoringModel.GPT_OSS_20B,
        "gpt-oss:20b": ScoringModel.GPT_OSS_20B,
        
        # Medium models (7-8B)
        "granite": ScoringModel.GRANITE,
        "granite3.3:8b": ScoringModel.GRANITE,
        "mistral": ScoringModel.MISTRAL,
        "mistral:7b": ScoringModel.MISTRAL,
        "deepseek": ScoringModel.DEEPSEEK,
        "deepseek-r1:8b": ScoringModel.DEEPSEEK,
        "qwen3": ScoringModel.QWEN3,
        "qwen3:8b": ScoringModel.QWEN3,
        "llama3.1": ScoringModel.LLAMA31,
        "llama3.1:8b": ScoringModel.LLAMA31,
        
        # Small models (1-4B)
        "granite2b": ScoringModel.GRANITE_2B,
        "granite3.3:2b": ScoringModel.GRANITE_2B,
        "phi4mini": ScoringModel.PHI4_MINI,
        "phi4-mini": ScoringModel.PHI4_MINI,
        "phi4-mini-reasoning:3.8b": ScoringModel.PHI4_MINI,
        "phi3mini": ScoringModel.PHI3_MINI,
        "phi3:mini": ScoringModel.PHI3_MINI,
        "llama3.2": ScoringModel.LLAMA32_3B,
        "llama3.2:3b": ScoringModel.LLAMA32_3B,
        "qwen2.5": ScoringModel.QWEN25_3B,
        "qwen2.5vl:3b": ScoringModel.QWEN25_3B,
        "deepseek1.5b": ScoringModel.DEEPSEEK_1_5B,
        "deepseek-r1:1.5b": ScoringModel.DEEPSEEK_1_5B,
    }
    
    for model_str in model_strings:
        model_str = model_str.lower()
        if model_str in model_map:
            models.append(model_map[model_str])
        else:
            print(f"⚠️  Unknown model: {model_str}")
            print(f"Available: {list(model_map.keys())}")
    
    return models

async def generate_dataset(num_plates: int, words_per_plate: int, models: List[ScoringModel], output_file: str = "scoring_dataset.json", sampling_strategy: str = "frequency_weighted"):
    """Generate a comprehensive scoring dataset."""
    print(f"📊 Generating Dataset: {num_plates} plates × {words_per_plate} words = {num_plates * words_per_plate} total scores")
    print(f"Models: {[m.value for m in models]}")
    print(f"Output: {output_file}")
    print("-" * 70)
    
    import json
    from datetime import datetime
    
    dataset = {
        "metadata": {
            "generated_at": datetime.utcnow().isoformat(),
            "num_plates": num_plates,
            "words_per_plate": words_per_plate,
            "total_words": num_plates * words_per_plate,
            "models_used": [m.value for m in models],
            "total_expected_scores": num_plates * words_per_plate * len(models),
            "sampling_strategy": sampling_strategy
        },
        "plates": [],
        "summary": {}
    }
    
    try:
        # Generate random combinations (plates)
        from app.services.combination_generator import generate_combinations
        
        print(f"🎲 Generating {num_plates} random license plates...")
        random_plates = generate_combinations(
            character_set="abcdefghijklmnopqrstuvwxyz",
            length=3,  # Standard 3-letter plates
            mode="batch",
            batch_size=num_plates
        )
        
        total_scores_generated = 0
        total_words_processed = 0
        
        for i, plate in enumerate(random_plates):
            print(f"\n📍 Processing plate {i+1}/{num_plates}: '{plate.upper()}'")
            
            # Get random words for this plate
            words = await scoring_service.get_random_words_for_combination(plate, words_per_plate, strategy=sampling_strategy)
            
            if not words:
                print(f"   ⚠️  No valid words found for plate '{plate}', skipping...")
                continue
            
            plate_data = {
                "combination": plate.upper(),
                "words": []
            }
            
            # Score each word
            for j, word in enumerate(words):
                print(f"   🎯 Scoring word {j+1}/{len(words)}: '{word}'")
                
                try:
                    word_score = await scoring_service.score_word_with_models(word, plate, models)
                    
                    # Calculate parameter-weighted score
                    weighted_score = calculate_weighted_score(word_score.scores)
                    
                    word_data = {
                        "word": word,
                        "frequency": word_score.frequency,
                        "aggregate_score": word_score.aggregate_score,
                        "weighted_score": weighted_score,
                        "individual_scores": []
                    }
                    
                    for score in word_score.scores:
                        word_data["individual_scores"].append({
                            "model": score.model.value,
                            "score": score.score,
                            "reasoning": score.reasoning,
                            "timestamp": score.timestamp.isoformat()
                        })
                        total_scores_generated += 1
                    
                    plate_data["words"].append(word_data)
                    total_words_processed += 1
                    
                    print(f"      ✅ Scored: {word_score.aggregate_score:.1f}/100 avg")
                    
                except Exception as e:
                    print(f"      ❌ Failed to score '{word}': {e}")
                    continue
            
            dataset["plates"].append(plate_data)
            
            # Save periodically
            if (i + 1) % 10 == 0:
                print(f"   💾 Saving progress... ({i+1}/{num_plates} plates)")
                with open(f"{output_file}.tmp", 'w') as f:
                    json.dump(dataset, f, indent=2)
        
        # Final summary
        dataset["summary"] = {
            "plates_processed": len(dataset["plates"]),
            "total_words_scored": total_words_processed,
            "total_individual_scores": total_scores_generated,
            "average_words_per_plate": total_words_processed / len(dataset["plates"]) if dataset["plates"] else 0,
            "completion_rate": total_words_processed / (num_plates * words_per_plate) if num_plates * words_per_plate > 0 else 0
        }
        
        # Save final dataset
        with open(output_file, 'w') as f:
            json.dump(dataset, f, indent=2)
        
        # Remove temp file if it exists
        import os
        temp_file = f"{output_file}.tmp"
        if os.path.exists(temp_file):
            os.remove(temp_file)
        
        print(f"\n✅ Dataset Generation Complete!")
        print(f"📊 Summary:")
        print(f"   Plates processed: {dataset['summary']['plates_processed']}")
        print(f"   Words scored: {dataset['summary']['total_words_scored']}")
        print(f"   Individual scores: {dataset['summary']['total_individual_scores']}")
        print(f"   Completion rate: {dataset['summary']['completion_rate']:.1%}")
        print(f"   Saved to: {output_file}")
        
        return dataset
        
    except Exception as e:
        print(f"❌ Dataset generation failed: {e}")
        return None

async def generate_random_word_dataset(num_words: int, models: List[ScoringModel], output_file: str = "random_words_dataset.json", sampling_strategy: str = "frequency_weighted"):
    """Generate dataset by randomly sampling 1000+ words from random plates for maximum variety."""
    print(f"🎲 Generating Random Word Dataset: {num_words} total word-plate pairs")
    print(f"Models: {[m.value for m in models]}")
    print(f"Sampling: {sampling_strategy}")
    print(f"Output: {output_file}")
    print("-" * 70)
    
    import json
    from datetime import datetime
    
    dataset = {
        "metadata": {
            "generated_at": datetime.utcnow().isoformat(),
            "target_words": num_words,
            "models_used": [m.value for m in models],
            "sampling_strategy": sampling_strategy,
            "method": "random_word_plate_pairs"
        },
        "word_scores": [],
        "summary": {}
    }
    
    try:
        from app.services.combination_generator import generate_combinations
        
        total_words_scored = 0
        total_scores_generated = 0
        
        while total_words_scored < num_words:
            # Generate a random plate
            random_plate = generate_combinations(
                character_set="abcdefghijklmnopqrstuvwxyz",
                length=3,
                mode="random",
                batch_size=1
            )[0]
            
            print(f"\n🎯 Random plate: '{random_plate.upper()}' (progress: {total_words_scored}/{num_words})")
            
            # Get random words for this plate (just 1-3 to maximize plate variety)
            words_from_plate = await scoring_service.get_random_words_for_combination(
                random_plate, 
                random.randint(1, 3),  # 1-3 words per plate for maximum variety
                strategy=sampling_strategy
            )
            
            if not words_from_plate:
                print(f"   ⚠️  No valid words for plate '{random_plate}', trying another...")
                continue
            
            # Score each word
            for word in words_from_plate:
                if total_words_scored >= num_words:
                    break
                    
                print(f"   📝 Scoring word {total_words_scored + 1}/{num_words}: '{word}'")
                
                try:
                    word_score = await scoring_service.score_word_with_models(word, random_plate, models)
                    
                    # Calculate parameter-weighted score
                    weighted_score = calculate_weighted_score(word_score.scores)
                    
                    word_data = {
                        "word": word,
                        "plate": random_plate.upper(),
                        "frequency": word_score.frequency,
                        "aggregate_score": word_score.aggregate_score,
                        "weighted_score": weighted_score,
                        "individual_scores": []
                    }
                    
                    for score in word_score.scores:
                        word_data["individual_scores"].append({
                            "model": score.model.value,
                            "score": score.score,
                            "reasoning": score.reasoning,
                            "timestamp": score.timestamp.isoformat()
                        })
                        total_scores_generated += 1
                    
                    dataset["word_scores"].append(word_data)
                    total_words_scored += 1
                    
                    print(f"      ✅ Scored: {word_score.aggregate_score:.1f}/100 avg")
                    
                    # Save progress every 50 words
                    if total_words_scored % 50 == 0:
                        print(f"   💾 Saving progress... ({total_words_scored}/{num_words} words)")
                        with open(f"{output_file}.tmp", 'w') as f:
                            json.dump(dataset, f, indent=2)
                    
                except Exception as e:
                    print(f"      ❌ Failed to score '{word}': {e}")
                    continue
        
        # Final summary
        dataset["summary"] = {
            "words_scored": total_words_scored,
            "total_individual_scores": total_scores_generated,
            "unique_plates": len(set(item["plate"] for item in dataset["word_scores"])),
            "completion_rate": total_words_scored / num_words if num_words > 0 else 0
        }
        
        # Save final dataset
        with open(output_file, 'w') as f:
            json.dump(dataset, f, indent=2)
        
        # Remove temp file if it exists
        import os
        temp_file = f"{output_file}.tmp"
        if os.path.exists(temp_file):
            os.remove(temp_file)
        
        print(f"\n✅ Random Word Dataset Complete!")
        print(f"📊 Summary:")
        print(f"   Words scored: {dataset['summary']['words_scored']}")
        print(f"   Individual scores: {dataset['summary']['total_individual_scores']}")
        print(f"   Unique plates used: {dataset['summary']['unique_plates']}")
        print(f"   Completion rate: {dataset['summary']['completion_rate']:.1%}")
        print(f"   Saved to: {output_file}")
        
        return dataset
        
    except Exception as e:
        print(f"❌ Random word dataset generation failed: {e}")
        return None

async def main():
    parser = argparse.ArgumentParser(description="PL8WRDS Word Scoring System")
    parser.add_argument("command", choices=["check", "score", "random", "dataset", "random-words"], 
                       help="Command to run")
    
    # For single word scoring
    parser.add_argument("--word", help="Word to score")
    parser.add_argument("--combination", help="License plate combination")
    
    # For random scoring
    parser.add_argument("--combinations", type=int, default=3, 
                       help="Number of random combinations (default: 3)")
    parser.add_argument("--words", type=int, default=3,
                       help="Words per combination (default: 3)")
    parser.add_argument("--length", type=int, default=3,
                       help="Combination length (default: 3)")
    
    # For dataset generation
    parser.add_argument("--plates", type=int, default=100,
                       help="Number of license plates for dataset (default: 100)")
    parser.add_argument("--output", default="scoring_dataset.json",
                       help="Output file for dataset (default: scoring_dataset.json)")
    parser.add_argument("--sampling", choices=["frequency_weighted", "uniform", "mixed"], 
                       default="frequency_weighted",
                       help="Word sampling strategy (default: frequency_weighted)")
    
    # For random words dataset
    parser.add_argument("--target", type=int, default=1000,
                       help="Target number of words for random-words dataset (default: 1000)")
    
    # Model selection - 7 models spanning different sizes
    parser.add_argument("--models", nargs="+", 
                       default=["granite", "mistral", "qwen3", "llama3.1", "phi4mini", "llama3.2", "deepseek1.5b"],
                       help="Models to use (default: 7-model mix from 1.5B to 8B)")
    
    args = parser.parse_args()
    
    if args.command == "check":
        await check_system()
        
    elif args.command == "score":
        if not args.word or not args.combination:
            print("❌ For 'score' command, --word and --combination are required")
            return
        
        models = parse_models(args.models)
        if not models:
            print("❌ No valid models specified")
            return
        
        # Check system first
        available_models = await check_system()
        requested_available = [m for m in models if m in available_models]
        
        if not requested_available:
            print("❌ None of the requested models are available")
            return
        
        await score_single_word(args.word, args.combination, requested_available)
        
    elif args.command == "random":
        models = parse_models(args.models)
        if not models:
            print("❌ No valid models specified")
            return
        
        # Check system first
        available_models = await check_system()
        requested_available = [m for m in models if m in available_models]
        
        if not requested_available:
            print("❌ None of the requested models are available")
            return
        
        print() # Add spacing after system check
        await score_random_session(
            args.combinations, 
            args.words, 
            args.length, 
            requested_available
        )
        
    elif args.command == "dataset":
        models = parse_models(args.models)
        if not models:
            print("❌ No valid models specified")
            return
        
        # Quick model check (skip full system check for efficiency)
        print("🔍 Quick Model Check")
        print("-" * 50)
        available_models = []
        for model in models:
            if check_model_available(model.value):
                available_models.append(model)
                print(f"  ✅ {model.value}")
            else:
                print(f"  ❌ {model.value}")
        
        if not available_models:
            print("❌ None of the requested models are available")
            return
        
        print() # Add spacing after model check
        await generate_dataset(
            args.plates,
            args.words,  # Reuse --words for words per plate
            available_models,
            args.output,
            args.sampling
        )
        
    elif args.command == "random-words":
        models = parse_models(args.models)
        if not models:
            print("❌ No valid models specified")
            return
        
        # Quick model check (skip full system check for efficiency)
        print("🔍 Quick Model Check")
        print("-" * 50)
        available_models = []
        for model in models:
            if check_model_available(model.value):
                available_models.append(model)
                print(f"  ✅ {model.value}")
            else:
                print(f"  ❌ {model.value}")
        
        if not available_models:
            print("❌ None of the requested models are available")
            return
        
        print() # Add spacing after model check
        await generate_random_word_dataset(
            args.target,
            available_models,
            args.output,
            args.sampling
        )

if __name__ == "__main__":
    print("🎯 PL8WRDS Word Scoring System")
    print("=" * 50)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Scoring interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

"""
Feature extraction service for regression model training.
Computes linguistic and information-theoretic features from words and plates.
"""

import json
import math
import statistics
from collections import Counter, defaultdict
from typing import Dict, List, Set, Tuple, Any
from pathlib import Path

from .solver_service import solve_combination
from .word_service import word_service

class FeatureExtractor:
    """Extract features for word scoring regression model."""
    
    def __init__(self):
        self._plate_solutions_cache = {}
        self._word_plates_cache = {}
        self._corpus_stats = None
    
    def initialize_from_corpus_stats(self, corpus_stats: Dict[str, Any]):
        """Initialize feature extractor with pre-computed corpus statistics.
        
        This is used by the API to avoid rebuilding corpus stats for each request.
        """
        self._corpus_stats = corpus_stats
        
        # Convert lists back to sets for faster lookups during feature extraction
        plate_solutions = corpus_stats.get("plate_solutions", {})
        self._plate_solutions_cache = {
            plate: set(words) for plate, words in plate_solutions.items()
        }
        
        word_plates = corpus_stats.get("word_plates", {})
        self._word_plates_cache = {
            word: set(plates) for word, plates in word_plates.items()
        }
    
    async def build_corpus_statistics(self, dataset_path: str = "cache/scoring_dataset_complete.json", use_full_corpus: bool = True):
        """Build corpus statistics from the full corpus or training dataset.
        
        Args:
            dataset_path: Path to dataset for getting word-plate mappings from training data
            use_full_corpus: If True, build statistics for ALL possible plates (recommended for API usage)
                           If False, build statistics only for plates in the dataset (old behavior)
        """
        print(f"Building corpus statistics (full_corpus={use_full_corpus})...")
        
        # Load dataset to get word-plate mappings from training data
        with open(dataset_path, 'r') as f:
            data = json.load(f)
        
        word_scores = data.get("word_scores", [])
        
        # Build word -> plates mapping from dataset (for IDF calculations)
        word_plates = defaultdict(set)
        dataset_plates = set()
        
        for entry in word_scores:
            word = entry["word"].lower()
            plate = entry["plate"].upper()
            
            word_plates[word].add(plate)
            dataset_plates.add(plate)
        
        print(f"Dataset contains {len(dataset_plates)} unique plates")
        
        if use_full_corpus:
            # Generate ALL possible 3-letter plates for comprehensive corpus statistics
            from .combination_generator import generate_combinations
            print("Generating all possible 3-letter plates...")
            
            all_plates = generate_combinations(
                character_set="abcdefghijklmnopqrstuvwxyz",
                length=3,
                mode="all"
            )
            all_plates = [plate.upper() for plate in all_plates]
            print(f"Generated {len(all_plates)} total possible plates")
        else:
            # Use only plates from dataset (old behavior)
            all_plates = list(dataset_plates)
            print(f"Using {len(all_plates)} plates from dataset")
        
        # For each plate (dataset or all possible), get complete solution sets
        print("Computing complete solution sets for all plates...")
        complete_plate_solutions = {}
        all_words_in_corpus = set()
        
        for i, plate in enumerate(all_plates):
            if i % 1000 == 0:
                print(f"  Processing plate {i+1}/{len(all_plates)}: {plate}")
            
            try:
                # Use local solver service to get all possible solutions
                solutions_with_freq = solve_combination(plate.lower(), mode="subsequence")
                solutions = [word for word, freq in solutions_with_freq]
                plate_solutions = set(sol.lower() for sol in solutions)
                complete_plate_solutions[plate] = plate_solutions
                all_words_in_corpus.update(plate_solutions)
                
                if i < 10:  # Log first few for verification
                    print(f"    {plate}: {len(plate_solutions)} solutions")
                    
            except Exception as e:
                print(f"Warning: Could not solve plate {plate}: {e}")
                complete_plate_solutions[plate] = set()
        
        # Now update word_plates to include mappings for ALL plates where each word appears
        # This is critical for accurate IDF calculations
        if use_full_corpus:
            print("Building complete word->plates mappings for IDF calculations...")
            complete_word_plates = defaultdict(set)
            
            for plate, words in complete_plate_solutions.items():
                for word in words:
                    complete_word_plates[word].add(plate)
            
            self._word_plates_cache = dict(complete_word_plates)
            print(f"Found {len(complete_word_plates)} unique words across all plates")
        else:
            # Use dataset-based word-plate mappings (old behavior)
            self._word_plates_cache = dict(word_plates)
        
        self._plate_solutions_cache = complete_plate_solutions
        
        # Compute corpus-level statistics
        total_plates = len(complete_plate_solutions)
        total_words = len(all_words_in_corpus)
        
        # Convert sets to lists for JSON serializability in caching
        serializable_plate_solutions = {
            plate: list(words) for plate, words in complete_plate_solutions.items()
        }
        serializable_word_plates = {
            word: list(plates) for word, plates in self._word_plates_cache.items()
        }
        
        self._corpus_stats = {
            "total_plates": total_plates,
            "total_unique_words": total_words,
            "plate_solutions": serializable_plate_solutions,
            "word_plates": serializable_word_plates,
            "dataset_words": list(word_plates.keys()),  # Words from training dataset
            "corpus_words": list(all_words_in_corpus),  # All words in complete corpus
            "use_full_corpus": use_full_corpus
        }
        
        print(f"Corpus stats: {total_plates} plates, {total_words} unique words in corpus")
        if use_full_corpus:
            print("✓ Full corpus statistics built - all plates covered for API usage")
        else:
            print("⚠️  Dataset-only statistics - API may need fallbacks for unseen plates")
        
        return self._corpus_stats
    
    def extract_plate_specific_features(self, word: str, plate: str) -> Dict[str, float]:
        """Extract features specific to word-plate pair."""
        word_lower = word.lower()
        plate_upper = plate.upper()
        
        if not self._corpus_stats:
            raise ValueError("Must call build_corpus_statistics() first")
        
        features = {}
        
        # Get solutions for this plate
        plate_solutions = self._plate_solutions_cache.get(plate_upper, set())
        total_solutions_for_plate = len(plate_solutions)
        
        # If plate not in cache, this means corpus statistics weren't built with full_corpus=True
        if not plate_solutions and self._corpus_stats.get("use_full_corpus", False):
            raise ValueError(f"Plate {plate_upper} not found in corpus statistics. This shouldn't happen with full_corpus=True")
        elif not plate_solutions:
            # Graceful fallback for dataset-only corpus statistics
            print(f"Warning: Plate {plate_upper} not in corpus statistics (using dataset-only mode)")
            total_solutions_for_plate = 0
        
        # 1. Term Frequency (TF) - how often this word appears for THIS plate
        # Since each word appears at most once per plate, TF is binary (0 or 1)
        tf = 1.0 if word_lower in plate_solutions else 0.0
        features["tf"] = tf
        
        # 2. Plate Difficulty - fewer solutions = harder plate
        features["plate_solution_count"] = float(total_solutions_for_plate)
        features["plate_difficulty"] = 1.0 / max(total_solutions_for_plate, 1)
        
        # 3. Inverse Document Frequency (IDF) - how many plates have this word
        word_plates = self._word_plates_cache.get(word_lower, set())
        num_plates_with_word = len(word_plates)
        total_plates = self._corpus_stats["total_plates"]
        
        if num_plates_with_word > 0:
            idf = math.log(total_plates / num_plates_with_word)
        else:
            idf = math.log(total_plates)  # Max IDF for unseen words
        
        features["idf"] = idf
        features["word_plate_count"] = float(num_plates_with_word)
        
        # 4. TF-IDF
        features["tf_idf"] = tf * idf
        
        # 5. Surprisal - negative log probability of this word for this plate
        if total_solutions_for_plate > 0:
            prob = 1.0 / total_solutions_for_plate if tf > 0 else 0.0
            surprisal = -math.log(prob) if prob > 0 else float('inf')
        else:
            surprisal = float('inf')
        
        features["surprisal"] = surprisal if surprisal != float('inf') else 20.0  # Cap at reasonable value
        
        return features
    
    def extract_character_ngrams(self, word: str, n_range: Tuple[int, int] = (1, 4)) -> Dict[str, float]:
        """Extract character n-grams from word."""
        word_lower = word.lower()
        ngram_features = {}
        
        for n in range(n_range[0], n_range[1] + 1):
            ngrams = []
            
            # Add start/end padding for positional information
            padded_word = f"^{word_lower}$"
            
            for i in range(len(padded_word) - n + 1):
                ngram = padded_word[i:i+n]
                ngrams.append(ngram)
            
            # Count n-grams
            ngram_counts = Counter(ngrams)
            total_ngrams = len(ngrams)
            
            # Convert to features (normalized counts)
            for ngram, count in ngram_counts.items():
                feature_name = f"ngram_{n}_{ngram}"
                ngram_features[feature_name] = count / total_ngrams
        
        return ngram_features
    
    def find_plate_letter_positions(self, plate: str, word: str) -> List[int]:
        """Find positions of plate letters in word (subsequence matching)."""
        plate_lower = plate.lower()
        word_lower = word.lower()
        positions = []
        
        plate_idx = 0
        for word_idx, char in enumerate(word_lower):
            if plate_idx < len(plate_lower) and char == plate_lower[plate_idx]:
                positions.append(word_idx)
                plate_idx += 1
        
        return positions if plate_idx == len(plate_lower) else []
    
    def extract_positional_entropy(self, word: str, plate: str) -> Dict[str, float]:
        """Extract positional entropy of plate letters within word."""
        features = {}
        
        # Find positions of plate letters in the word
        positions = self.find_plate_letter_positions(plate, word)
        
        if not positions or len(word) == 0:
            return {
                "positional_entropy": 0.0,
                "pattern_density": 0.0,
                "non_consecutiveness": 0.0,
                "positions_spread": 0.0
            }
        
        word_length = len(word)
        
        # Calculate positional entropy (as defined in scoring_features.md)
        relative_positions = [pos / word_length for pos in positions]
        
        # Calculate entropy of position distribution
        if len(relative_positions) > 1:
            # Discretize into bins for entropy calculation
            bins = [i / 10.0 for i in range(11)]  # 0.0, 0.1, 0.2, ..., 1.0
            bin_counts = Counter()
            
            for pos in relative_positions:
                for i in range(len(bins) - 1):
                    if bins[i] <= pos <= bins[i + 1]:
                        bin_counts[i] += 1
                        break
            
            # Calculate entropy
            total = sum(bin_counts.values())
            if total > 0:
                entropy = -sum((count / total) * math.log2(count / total) 
                              for count in bin_counts.values() if count > 0)
                features["positional_entropy"] = entropy
            else:
                features["positional_entropy"] = 0.0
        else:
            features["positional_entropy"] = 0.0
        
        # Pattern density (percentage of word used by pattern)
        features["pattern_density"] = len(plate) / word_length
        
        # Non-consecutiveness score (how spread out the letters are)
        if len(positions) > 1:
            total_gaps = sum(positions[i+1] - positions[i] - 1 for i in range(len(positions)-1))
            features["non_consecutiveness"] = total_gaps / word_length
        else:
            features["non_consecutiveness"] = 0.0
        
        # Overall spread of positions
        if len(positions) > 1:
            position_span = positions[-1] - positions[0]
            features["positions_spread"] = position_span / word_length
        else:
            features["positions_spread"] = 0.0
        
        return features
    
    def extract_word_intrinsic_features(self, word: str) -> Dict[str, float]:
        """Extract intrinsic word features (independent of plate)."""
        features = {}
        
        word_lower = word.lower()
        
        # Basic word properties
        features["word_length"] = float(len(word_lower))
        features["unique_chars"] = float(len(set(word_lower)))
        features["vowel_count"] = float(sum(1 for c in word_lower if c in 'aeiou'))
        features["consonant_count"] = float(sum(1 for c in word_lower if c.isalpha() and c not in 'aeiou'))
        
        if len(word_lower) > 0:
            features["vowel_ratio"] = features["vowel_count"] / len(word_lower)
            features["consonant_ratio"] = features["consonant_count"] / len(word_lower)
        else:
            features["vowel_ratio"] = 0.0
            features["consonant_ratio"] = 0.0
        
        # Get word frequency from word service
        try:
            # Access frequency directly from word_service
            frequency = word_service._words.get(word_lower, 0)
            # features["corpus_frequency"] = float(frequency) # This feature's scale dominates the model
            features["log_frequency"] = math.log(frequency + 1)
        except:
            # features["corpus_frequency"] = 0.0
            features["log_frequency"] = 0.0
        
        # Add character n-grams
        ngram_features = self.extract_character_ngrams(word)
        features.update(ngram_features)
        
        # Note: Positional entropy is plate-specific, so we can't include it in word-intrinsic features
        # It will be added in extract_all_features() instead
        
        return features
    
    async def build_corpus_features(self, dataset_path: str = "cache/scoring_dataset_complete.json"):
        """
        Build a comprehensive, feature-rich dataset for ALL word-plate pairs.
        Warning: This is a very computationally expensive operation.
        """
        print("Building feature-rich corpus. This will take a very long time...")

        # Step 1: Ensure the basic corpus statistics (plate solutions) are built and available.
        # This is a prerequisite for feature extraction.
        if not self._corpus_stats:
            print("Corpus statistics not found, building them first...")
            await self.build_corpus_statistics(dataset_path, use_full_corpus=True)
            print("Corpus statistics built successfully.")

        # Step 2: Iterate through every plate and its solutions to extract features.
        all_plate_features = {}
        plate_solutions = self._plate_solutions_cache
        total_plates = len(plate_solutions)
        
        print(f"Starting feature extraction for {total_plates} plates...")

        for i, (plate, words) in enumerate(plate_solutions.items()):
            if i % 100 == 0:
                print(f"  Processing plate {i+1}/{total_plates}: {plate} ({len(words)} words)")

            if not words:
                all_plate_features[plate] = []
                continue

            plate_word_features = []
            for word in words:
                try:
                    # Extract all features for the current word-plate pair
                    features = self.extract_all_features(word, plate)
                    
                    # Append the word and its features to the list for this plate
                    plate_word_features.append({
                        "word": word,
                        "features": features
                    })
                except Exception as e:
                    print(f"  Warning: Could not extract features for {word}/{plate}: {e}")
            
            all_plate_features[plate] = plate_word_features

        print("Successfully extracted features for all plates.")
        return all_plate_features
    
    def extract_all_features(self, word: str, plate: str) -> Dict[str, float]:
        """Extract all features for a word-plate pair."""
        features = {}
        
        # Plate-specific features
        try:
            plate_features = self.extract_plate_specific_features(word, plate)
            features.update(plate_features)
        except Exception as e:
            print(f"Warning: Could not extract plate features for {word}/{plate}: {e}")
        
        # Word-intrinsic features
        try:
            word_features = self.extract_word_intrinsic_features(word)
            features.update(word_features)
        except Exception as e:
            print(f"Warning: Could not extract word features for {word}: {e}")
        
        # Plate-specific positional features
        try:
            position_features = self.extract_positional_entropy(word, plate)
            features.update(position_features)
        except Exception as e:
            print(f"Warning: Could not extract positional features for {word}/{plate}: {e}")
        
        return features

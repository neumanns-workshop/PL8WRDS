import logging
from typing import List, Tuple
from collections import Counter
from .word_service import word_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def is_subsequence(pattern: str, word: str) -> bool:
    """
    Check if pattern is a subsequence of word.
    Letters in pattern must appear in word in the same order, but not necessarily consecutively.
    """
    pattern_idx = 0
    
    for char in word:
        if pattern_idx < len(pattern) and char == pattern[pattern_idx]:
            pattern_idx += 1
    
    return pattern_idx == len(pattern)

def is_substring(pattern: str, word: str) -> bool:
    """
    Check if pattern is a substring of word.
    Letters in pattern must appear in word in the same order and consecutively.
    """
    return pattern in word

def is_anagram(pattern: str, word: str) -> bool:
    """
    Check if word uses exactly the letters in pattern (anagram rules).
    """
    return Counter(pattern) == Counter(word)

def is_anagram_subset(pattern: str, word: str) -> bool:
    """
    Check if word contains at least the letters in pattern (Scrabble-style).
    """
    pattern_count = Counter(pattern)
    word_count = Counter(word)
    
    for letter, count in pattern_count.items():
        if word_count[letter] < count:
            return False
    return True

def matches_pattern(pattern: str, word: str) -> bool:
    """
    Check if word matches a positional pattern (Wordle/Hangman style).
    Pattern uses '?' for wildcards, letters for required positions.
    Example: "?a?e" matches "cake", "same", etc.
    """
    if len(pattern) != len(word):
        return False
    
    for p_char, w_char in zip(pattern, word):
        if p_char != '?' and p_char != w_char:
            return False
    return True

def solve_combination(combination: str, mode: str = "subsequence") -> List[Tuple[str, int]]:
    """
    Find all real words that match the combination according to the specified mode.
    
    Modes:
    - "subsequence": Letters appear in order, gaps allowed (default)
    - "substring": Letters appear in order, no gaps
    - "anagram": Exact letter match, any order
    - "anagram_subset": Contains at least these letters, any order
    - "pattern": Positional matching with '?' wildcards
    
    Returns a list of (word, frequency) tuples sorted by frequency (highest first).
    """
    logger.info(f"Solving combination: '{combination}' with mode: '{mode}'")
    
    matching_words = []
    combination_lower = combination.lower()
    
    # Choose matching function based on mode
    if mode == "subsequence":
        match_func = is_subsequence
    elif mode == "substring":
        match_func = is_substring
    elif mode == "anagram":
        match_func = is_anagram
    elif mode == "anagram_subset":
        match_func = is_anagram_subset
    elif mode == "pattern":
        match_func = matches_pattern
    else:
        logger.warning(f"Unknown mode '{mode}', defaulting to subsequence")
        match_func = is_subsequence
    
    # Access the internal words dictionary from word_service
    for word, frequency in word_service._words.items():
        if match_func(combination_lower, word):
            matching_words.append((word, frequency))
    
    # Sort by frequency (highest first)
    matching_words.sort(key=lambda x: x[1], reverse=True)
    
    logger.info(f"Found {len(matching_words)} words matching pattern '{combination}' in mode '{mode}'")
    return matching_words

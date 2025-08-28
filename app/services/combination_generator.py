import random
from itertools import product
from typing import List
from tqdm import tqdm
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _generate_all(alphabet: str, length: int) -> List[str]:
    """Generates the full cartesian product of strings."""
    total_combinations = len(alphabet) ** length
    logger.info(f"Preparing to generate {total_combinations} combinations for length {length}.")

    # Only show tqdm for large jobs to avoid visual clutter on small, fast ones.
    if total_combinations > 100_000:
        iterable = tqdm(product(alphabet, repeat=length), total=total_combinations, desc=f"Generating length {length}")
    else:
        iterable = product(alphabet, repeat=length)
    
    return ["".join(p) for p in iterable]

def _generate_random(alphabet: str, length: int, count: int) -> List[str]:
    """Generates a specified count of random strings."""
    logger.info(f"Generating {count} random combination(s) of length {length}.")
    return ["".join(random.choices(alphabet, k=length)) for _ in range(count)]

def generate_combinations(
    character_set: str,
    length: int,
    mode: str,
    batch_size: int = 1
) -> List[str]:
    """
    Dispatcher function to generate strings based on the selected mode.
    """
    alphabet = "".join(sorted(list(set(character_set))))

    if mode == "all":
        return _generate_all(alphabet, length)
    elif mode == "random":
        return _generate_random(alphabet, length, batch_size)
    elif mode == "batch":
        return _generate_random(alphabet, length, batch_size)
    
    return []

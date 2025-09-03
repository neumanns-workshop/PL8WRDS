import json
import logging
from pathlib import Path
from typing import Dict, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WordService:
    _instance = None
    _words: Dict[str, int] = {}

    def __new__(cls):
        if cls._instance is None:
            logger.info("Initializing WordService and loading data...")
            cls._instance = super(WordService, cls).__new__(cls)
            cls._instance._load_words()
        return cls._instance

    def _load_words(self):
        # Try multiple possible paths for the words file
        possible_paths = [
            Path('data/words_with_freqs.json'),  # From project root
            Path(__file__).parent.parent.parent / 'data/words_with_freqs.json',  # Relative to this file
            Path.cwd() / 'data/words_with_freqs.json'  # From current working directory
        ]
        
        for words_path in possible_paths:
            try:
                if words_path.exists():
                    with open(words_path, 'r') as f:
                        data = json.load(f)
                        self._words = {item['word']: item['frequency'] for item in data}
                        logger.info(f"Successfully loaded {len(self._words)} words from {words_path}")
                        return
            except json.JSONDecodeError as e:
                logger.error(f"Error: Failed to decode JSON from {words_path}: {e}")
                continue
            except Exception as e:
                logger.error(f"Error loading from {words_path}: {e}")
                continue
        
        logger.error("Error: words_with_freqs.json not found in any expected location")
        logger.error(f"Searched paths: {[str(p) for p in possible_paths]}")
        logger.error(f"Current working directory: {Path.cwd()}")

    def lookup_word(self, word: str) -> Optional[int]:
        """Looks up a word and returns its frequency if found, otherwise None."""
        return self._words.get(word.lower())

# Instantiate the service so it's ready to be imported and used.
word_service = WordService()

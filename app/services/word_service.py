import json
import logging
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
        try:
            with open('data/words_with_freqs.json', 'r') as f:
                data = json.load(f)
                self._words = {item['word']: item['frequency'] for item in data}
                logger.info(f"Successfully loaded {len(self._words)} words.")
        except FileNotFoundError:
            logger.error("Error: words_with_freqs.json not found.")
        except json.JSONDecodeError:
            logger.error("Error: Failed to decode JSON from words_with_freqs.json.")

    def lookup_word(self, word: str) -> Optional[int]:
        """Looks up a word and returns its frequency if found, otherwise None."""
        return self._words.get(word.lower())

# Instantiate the service so it's ready to be imported and used.
word_service = WordService()

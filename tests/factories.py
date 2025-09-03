"""
Test data factories using factory_boy for generating test objects.
"""

import factory
from datetime import datetime
from typing import Dict, Any, List
from faker import Faker

from app.domain.entities import (
    WordScore, IndividualScore, ScoringSession, ModelAvailability,
    ScoringSystemStatus, CorpusStatistics, CorpusFeatures, WordMatch
)
from app.domain.value_objects import (
    Word, LicensePlate, Score, Frequency, ModelName, SessionId,
    Reasoning, AggregateScore, CacheKey
)

fake = Faker()

# Value Object Factories
class WordFactory(factory.Factory):
    class Meta:
        model = Word
    
    value = factory.LazyFunction(lambda: fake.word().lower())


class LicensePlateFactory(factory.Factory):
    class Meta:
        model = LicensePlate
    
    value = factory.LazyFunction(lambda: ''.join(fake.random_letters(length=3)).upper())


class ScoreFactory(factory.Factory):
    class Meta:
        model = Score
    
    value = factory.LazyFunction(lambda: round(fake.random.uniform(0, 100), 2))


class FrequencyFactory(factory.Factory):
    class Meta:
        model = Frequency
    
    value = factory.LazyFunction(lambda: fake.random_int(min=1, max=100000))


class ModelNameFactory(factory.Factory):
    class Meta:
        model = ModelName
    
    value = factory.LazyFunction(lambda: fake.random_element(elements=("granite", "mistral", "deepseek")))


class SessionIdFactory(factory.Factory):
    class Meta:
        model = SessionId
    
    value = factory.LazyFunction(lambda: fake.uuid4())


class ReasoningFactory(factory.Factory):
    class Meta:
        model = Reasoning
    
    value = factory.LazyFunction(lambda: fake.text(max_nb_chars=200))


class CacheKeyFactory(factory.Factory):
    class Meta:
        model = CacheKey
    
    value = factory.LazyFunction(lambda: fake.slug())


# Entity Factories
class IndividualScoreFactory(factory.Factory):
    class Meta:
        model = IndividualScore
    
    model = factory.SubFactory(ModelNameFactory)
    score = factory.SubFactory(ScoreFactory)
    reasoning = factory.SubFactory(ReasoningFactory)
    created_at = factory.LazyFunction(datetime.utcnow)


class WordMatchFactory(factory.Factory):
    class Meta:
        model = WordMatch
    
    word = factory.LazyAttribute(lambda obj: Word("ambulance"))  # Default valid match
    plate = factory.LazyAttribute(lambda obj: LicensePlate("ABC"))
    frequency = factory.SubFactory(FrequencyFactory)


class WordScoreFactory(factory.Factory):
    class Meta:
        model = WordScore
    
    word = factory.LazyAttribute(lambda obj: Word("ambulance"))
    plate = factory.LazyAttribute(lambda obj: LicensePlate("ABC"))
    individual_scores = factory.SubFactory(IndividualScoreFactory)
    frequency = factory.SubFactory(FrequencyFactory)
    created_at = factory.LazyFunction(datetime.utcnow)
    
    @factory.post_generation
    def individual_scores(self, create, extracted, **kwargs):
        if not create:
            return
        
        if extracted:
            for score in extracted:
                self.individual_scores.append(score)
        else:
            # Create a default individual score
            score = IndividualScoreFactory()
            self.individual_scores = [score]


class ScoringSessionFactory(factory.Factory):
    class Meta:
        model = ScoringSession
    
    session_id = factory.SubFactory(SessionIdFactory)
    models_used = factory.LazyFunction(lambda: [ModelNameFactory() for _ in range(2)])
    results = factory.LazyFunction(lambda: [])
    created_at = factory.LazyFunction(datetime.utcnow)
    
    @factory.post_generation
    def results(self, create, extracted, **kwargs):
        if not create:
            return
        
        if extracted:
            for result in extracted:
                self.results.append(result)
        else:
            # Create default results
            self.results = [WordScoreFactory() for _ in range(3)]


class ModelAvailabilityFactory(factory.Factory):
    class Meta:
        model = ModelAvailability
    
    model = factory.SubFactory(ModelNameFactory)
    available = factory.LazyFunction(lambda: fake.boolean(chance_of_getting_true=80))
    error_message = factory.Maybe(
        'available',
        yes_declaration=None,
        no_declaration=factory.LazyFunction(lambda: fake.sentence())
    )
    last_checked = factory.LazyFunction(datetime.utcnow)


class ScoringSystemStatusFactory(factory.Factory):
    class Meta:
        model = ScoringSystemStatus
    
    ollama_running = factory.LazyFunction(lambda: fake.boolean(chance_of_getting_true=80))
    models = factory.LazyFunction(lambda: [ModelAvailabilityFactory() for _ in range(3)])
    cache_enabled = factory.LazyFunction(lambda: fake.boolean(chance_of_getting_true=70))
    active_sessions = factory.LazyFunction(lambda: fake.random_int(min=0, max=10))
    checked_at = factory.LazyFunction(datetime.utcnow)


class CorpusStatisticsFactory(factory.Factory):
    class Meta:
        model = CorpusStatistics
    
    total_plates = factory.LazyFunction(lambda: fake.random_int(min=100, max=1000))
    total_unique_words = factory.LazyFunction(lambda: fake.random_int(min=1000, max=10000))
    dataset_words = factory.LazyFunction(lambda: [fake.word().lower() for _ in range(10)])
    plate_word_counts = factory.LazyFunction(lambda: {
        fake.random_letters(length=3).upper(): fake.random_int(min=1, max=50)
        for _ in range(5)
    })
    word_frequency_distribution = factory.LazyFunction(lambda: {
        "rare": fake.random_int(min=100, max=500),
        "common": fake.random_int(min=1000, max=5000),
        "very_common": fake.random_int(min=5000, max=10000)
    })
    generated_at = factory.LazyFunction(datetime.utcnow)


class CorpusFeaturesFactory(factory.Factory):
    class Meta:
        model = CorpusFeatures
    
    features = factory.LazyFunction(lambda: {
        f"{fake.word().lower()}:{fake.random_letters(length=3).lower()}": {
            "tfidf": fake.random.uniform(0, 1),
            "length": fake.random_int(min=3, max=15),
            "vowel_ratio": fake.random.uniform(0.2, 0.6),
            "consonant_ratio": fake.random.uniform(0.4, 0.8),
            "position_entropy": fake.random.uniform(1.0, 3.0)
        }
        for _ in range(10)
    })
    metadata = factory.LazyFunction(lambda: {
        "total_features": fake.random_int(min=50, max=500),
        "feature_types": ["tfidf", "length", "vowel_ratio", "consonant_ratio", "position_entropy"],
        "extraction_time_seconds": fake.random.uniform(10.0, 300.0)
    })
    generated_at = factory.LazyFunction(datetime.utcnow)


# Specialized factories for specific test cases
class ValidWordPlateMatchFactory(WordMatchFactory):
    """Factory that creates valid word-plate matches."""
    
    @factory.lazy_attribute
    def word(self):
        # Create word that definitely matches the plate
        plate_letters = self.plate.value.lower()
        # Build a word that contains the plate letters in order
        word_letters = list(plate_letters)
        # Insert random letters between plate letters
        for i in range(len(word_letters) - 1, 0, -1):
            word_letters.insert(i, fake.random_letter().lower())
        return Word(''.join(word_letters))


class InvalidWordPlateMatchFactory(WordMatchFactory):
    """Factory that creates invalid word-plate matches."""
    
    word = factory.LazyAttribute(lambda obj: Word("xyz"))  # Won't match most plates
    plate = factory.LazyAttribute(lambda obj: LicensePlate("ABC"))


class HighScoreFactory(IndividualScoreFactory):
    """Factory for high scores (80-100)."""
    
    score = factory.LazyFunction(lambda: Score(fake.random.uniform(80, 100)))


class LowScoreFactory(IndividualScoreFactory):
    """Factory for low scores (0-40)."""
    
    score = factory.LazyFunction(lambda: Score(fake.random.uniform(0, 40)))


class RareWordFactory(WordFactory):
    """Factory for rare words with low frequency."""
    
    frequency = factory.LazyFunction(lambda: Frequency(fake.random_int(min=1, max=100)))


class CommonWordFactory(WordFactory):
    """Factory for common words with high frequency."""
    
    frequency = factory.LazyFunction(lambda: Frequency(fake.random_int(min=10000, max=100000)))


# Helper functions for generating test data
def create_word_plate_pairs(count: int = 10, valid_only: bool = True) -> List[tuple]:
    """Create a list of word-plate pairs for testing."""
    pairs = []
    for _ in range(count):
        if valid_only:
            match = ValidWordPlateMatchFactory()
            pairs.append((match.word.value, match.plate.value))
        else:
            word = WordFactory().value
            plate = LicensePlateFactory().value
            pairs.append((word, plate))
    return pairs


def create_test_features(word: str, plate: str) -> Dict[str, Any]:
    """Create sample feature data for a word-plate combination."""
    return {
        "tfidf": fake.random.uniform(0, 1),
        "length": len(word),
        "vowel_ratio": fake.random.uniform(0.2, 0.6),
        "consonant_ratio": fake.random.uniform(0.4, 0.8),
        "position_entropy": fake.random.uniform(1.0, 3.0),
        "ngram_features": {
            "2gram": fake.random.uniform(0, 1),
            "3gram": fake.random.uniform(0, 1)
        },
        "frequency_features": {
            "raw_frequency": fake.random_int(min=1, max=100000),
            "log_frequency": fake.random.uniform(0, 10)
        }
    }


def create_mock_model_responses(models: List[str]) -> List[IndividualScore]:
    """Create mock model responses for testing."""
    return [
        IndividualScore(
            model=ModelName(model),
            score=Score(fake.random.uniform(0, 100)),
            reasoning=Reasoning(fake.text(max_nb_chars=100))
        )
        for model in models
    ]
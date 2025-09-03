"""
Test configuration and fixtures.
"""

import pytest
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
from unittest.mock import Mock, AsyncMock

from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app
from app.core.container import create_container
from app.domain.entities import (
    WordScore, IndividualScore, ScoringSession, ModelAvailability,
    ScoringSystemStatus, CorpusStatistics, CorpusFeatures, WordMatch
)
from app.domain.value_objects import (
    Word, LicensePlate, Score, Frequency, ModelName, SessionId,
    Reasoning, AggregateScore, CacheKey
)

# Test data directory
TEST_DATA_DIR = Path(__file__).parent / "data"
TEST_DATA_DIR.mkdir(exist_ok=True)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_container():
    """Create a test dependency injection container."""
    container = create_container()
    return container


@pytest.fixture
def client(test_container):
    """Create a test client for the FastAPI application."""
    app.container = test_container
    with TestClient(app) as c:
        yield c


@pytest.fixture
async def async_client(test_container):
    """Create an async test client for the FastAPI application."""
    app.container = test_container
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


# Domain fixtures
@pytest.fixture
def sample_word():
    """Sample word for testing."""
    return Word("ambulance")


@pytest.fixture
def sample_plate():
    """Sample license plate for testing."""
    return LicensePlate("ABC")


@pytest.fixture
def sample_score():
    """Sample score for testing."""
    return Score(85.5)


@pytest.fixture
def sample_frequency():
    """Sample frequency for testing."""
    return Frequency(1000)


@pytest.fixture
def sample_model():
    """Sample model name for testing."""
    return ModelName("granite")


@pytest.fixture
def sample_reasoning():
    """Sample reasoning for testing."""
    return Reasoning("This is a clever match because the word 'ambulance' contains the letters A, B, C in order.")


@pytest.fixture
def sample_individual_score(sample_model, sample_score, sample_reasoning):
    """Sample individual score for testing."""
    return IndividualScore(
        model=sample_model,
        score=sample_score,
        reasoning=sample_reasoning
    )


@pytest.fixture
def sample_word_match(sample_word, sample_plate, sample_frequency):
    """Sample word match for testing."""
    return WordMatch(
        word=sample_word,
        plate=sample_plate,
        frequency=sample_frequency
    )


@pytest.fixture
def sample_word_score(sample_word, sample_plate, sample_individual_score, sample_frequency):
    """Sample word score for testing."""
    return WordScore(
        word=sample_word,
        plate=sample_plate,
        individual_scores=[sample_individual_score],
        frequency=sample_frequency
    )


@pytest.fixture
def sample_scoring_session(sample_model, sample_word_score):
    """Sample scoring session for testing."""
    return ScoringSession(
        session_id=SessionId.generate(),
        models_used=[sample_model],
        results=[sample_word_score]
    )


@pytest.fixture
def sample_corpus_statistics():
    """Sample corpus statistics for testing."""
    return CorpusStatistics(
        total_plates=100,
        total_unique_words=500,
        dataset_words=["ambulance", "beach", "cat"],
        plate_word_counts={"ABC": 10, "XYZ": 5},
        word_frequency_distribution={"rare": 100, "common": 400}
    )


@pytest.fixture
def sample_corpus_features():
    """Sample corpus features for testing."""
    return CorpusFeatures(
        features={
            "ambulance:abc": {
                "tfidf": 0.5,
                "length": 9,
                "vowel_ratio": 0.44
            }
        },
        metadata={"total_features": 100}
    )


# Mock fixtures
@pytest.fixture
def mock_llm_client():
    """Mock LLM client for testing."""
    mock_client = AsyncMock()
    mock_client.generate_score.return_value = IndividualScore(
        model=ModelName("granite"),
        score=Score(85.0),
        reasoning=Reasoning("Test reasoning")
    )
    mock_client.check_model_availability.return_value = ModelAvailability(
        model=ModelName("granite"),
        available=True
    )
    mock_client.is_service_healthy.return_value = True
    return mock_client


@pytest.fixture
def mock_model_predictor():
    """Mock model predictor for testing."""
    mock_predictor = AsyncMock()
    mock_predictor.predict_score.return_value = Score(85.0)
    mock_predictor.is_model_loaded.return_value = True
    mock_predictor.load_model.return_value = None
    return mock_predictor


@pytest.fixture
def mock_word_solver():
    """Mock word solver for testing."""
    mock_solver = AsyncMock()
    mock_solver.find_matching_words.return_value = [
        (Word("ambulance"), 1000),
        (Word("beach"), 500),
        (Word("cabbage"), 200)
    ]
    mock_solver.get_random_words_for_plate.return_value = [
        Word("ambulance"),
        Word("beach"),
        Word("cabbage")
    ]
    return mock_solver


@pytest.fixture
def mock_feature_extractor():
    """Mock feature extractor for testing."""
    mock_extractor = AsyncMock()
    mock_extractor.extract_features.return_value = {
        "tfidf": 0.5,
        "length": 9,
        "vowel_ratio": 0.44,
        "consonant_ratio": 0.56,
        "ngram_features": {"2gram": 0.3, "3gram": 0.2}
    }
    mock_extractor.build_corpus_statistics.return_value = CorpusStatistics(
        total_plates=100,
        total_unique_words=500,
        dataset_words=["ambulance", "beach", "cat"],
        plate_word_counts={"ABC": 10, "XYZ": 5},
        word_frequency_distribution={"rare": 100, "common": 400}
    )
    mock_extractor.build_corpus_features.return_value = CorpusFeatures(
        features={
            "ambulance:abc": {
                "tfidf": 0.5,
                "length": 9,
                "vowel_ratio": 0.44
            }
        },
        metadata={"total_features": 100}
    )
    return mock_extractor


@pytest.fixture
def mock_cache_manager():
    """Mock cache manager for testing."""
    mock_cache = AsyncMock()
    mock_cache.get.return_value = None
    mock_cache.set.return_value = None
    mock_cache.delete.return_value = None
    mock_cache.clear.return_value = None
    return mock_cache


@pytest.fixture
def mock_combination_generator():
    """Mock combination generator for testing."""
    mock_generator = AsyncMock()
    mock_generator.generate_combinations.return_value = [
        LicensePlate("ABC"),
        LicensePlate("XYZ"),
        LicensePlate("DEF")
    ]
    return mock_generator


# Repository fixtures
@pytest.fixture
def mock_word_repository():
    """Mock word repository for testing."""
    mock_repo = AsyncMock()
    mock_repo.get_word_frequency.return_value = Frequency(1000)
    mock_repo.word_exists.return_value = True
    return mock_repo


@pytest.fixture
def mock_scoring_repository():
    """Mock scoring repository for testing."""
    mock_repo = AsyncMock()
    mock_repo.save_word_score.return_value = None
    mock_repo.get_word_score.return_value = None
    mock_repo.save_session.return_value = None
    mock_repo.get_session.return_value = None
    return mock_repo


@pytest.fixture
def mock_corpus_repository():
    """Mock corpus repository for testing."""
    mock_repo = AsyncMock()
    mock_repo.save_statistics.return_value = None
    mock_repo.get_statistics.return_value = None
    mock_repo.save_features.return_value = None
    mock_repo.get_features.return_value = None
    return mock_repo


# Test data fixtures
@pytest.fixture
def valid_word_plate_pairs():
    """Valid word-plate pairs for testing."""
    return [
        ("ambulance", "ABC"),
        ("beach", "BCH"),
        ("cat", "CAT"),
        ("dog", "DG"),
        ("elephant", "ELH")
    ]


@pytest.fixture
def invalid_word_plate_pairs():
    """Invalid word-plate pairs for testing."""
    return [
        ("cabin", "ABC"),  # Wrong order
        ("xyz", "ABC"),    # No matching letters
        ("", "ABC"),       # Empty word
        ("abc", ""),       # Empty plate
    ]


@pytest.fixture
def test_models():
    """List of test model names."""
    return ["granite", "mistral", "deepseek"]


@pytest.fixture
def sample_features_data():
    """Sample features data for testing."""
    return {
        "tfidf": 0.5,
        "length": 9,
        "vowel_ratio": 0.44,
        "consonant_ratio": 0.56,
        "position_entropy": 2.1,
        "ngram_features": {
            "2gram": 0.3,
            "3gram": 0.2
        },
        "frequency_features": {
            "raw_frequency": 1000,
            "log_frequency": 6.9
        }
    }


# Performance test fixtures
@pytest.fixture
def performance_test_data():
    """Generate test data for performance tests."""
    plates = [f"{''.join([chr(65 + i) for i in range(3)])}{j:02d}" for j in range(10)]
    words = [f"word{i:03d}" for i in range(100)]
    return {"plates": plates, "words": words}


# Cleanup fixtures
@pytest.fixture(autouse=True)
async def cleanup_test_data():
    """Cleanup test data after each test."""
    yield
    # Cleanup logic here if needed
    pass


# Markers for pytest
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers",
        "unit: marks tests as unit tests (fast, isolated)"
    )
    config.addinivalue_line(
        "markers", 
        "integration: marks tests as integration tests (with external dependencies)"
    )
    config.addinivalue_line(
        "markers",
        "api: marks tests as API/endpoint tests"
    )
    config.addinivalue_line(
        "markers",
        "e2e: marks tests as end-to-end tests"
    )
    config.addinivalue_line(
        "markers",
        "performance: marks tests as performance/benchmark tests"
    )
    config.addinivalue_line(
        "markers",
        "slow: marks tests as slow running"
    )
    config.addinivalue_line(
        "markers",
        "requires_ollama: marks tests that require Ollama service"
    )
    config.addinivalue_line(
        "markers",
        "requires_cache: marks tests that require cache files"
    )
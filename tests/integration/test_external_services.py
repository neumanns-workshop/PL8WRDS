"""
Integration tests for external service implementations.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.infrastructure.external_services import (
    OllamaLLMClient, SimpleWordSolver, SimpleCombinationGenerator,
    JoblibModelPredictor, MemoryCacheManager, SimpleFeatureExtractor
)
from app.core.config import get_settings
from app.domain.entities import ModelAvailability, CorpusStatistics, CorpusFeatures
from app.domain.value_objects import (
    Word, LicensePlate, ModelName, Score, Frequency
)
from tests.factories import WordFactory, LicensePlateFactory


class TestOllamaLLMClient:
    """Test the Ollama LLM client."""
    
    @pytest.mark.integration
    async def test_llm_client_initialization_no_ollama(self):
        """Test LLM client initialization when Ollama is not available."""
        settings = get_settings()
        client = OllamaLLMClient(settings)
        
        # Should handle missing Ollama gracefully
        assert hasattr(client, 'ollama_client')
        
        # Service should be unhealthy
        is_healthy = await client.is_service_healthy()
        assert is_healthy is False
    
    @pytest.mark.integration
    async def test_llm_client_generate_score_no_ollama(self):
        """Test score generation when Ollama is not available."""
        settings = get_settings()
        client = OllamaLLMClient(settings)
        
        word = Word("ambulance")
        plate = LicensePlate("ABC")
        model = ModelName("granite")
        
        # Should return fallback score
        individual_score = await client.generate_score(word, plate, model)
        
        assert individual_score.model == model
        assert individual_score.score.value == 50.0
        assert "not available" in individual_score.reasoning.value.lower()
    
    @pytest.mark.integration
    async def test_llm_client_check_model_availability_no_ollama(self):
        """Test model availability check when Ollama is not available."""
        settings = get_settings()
        client = OllamaLLMClient(settings)
        
        model = ModelName("granite")
        availability = await client.check_model_availability(model)
        
        assert availability.model == model
        assert availability.available is False
        assert "not initialized" in availability.error_message.lower()


class TestSimpleWordSolver:
    """Test the simple word solver implementation."""
    
    @pytest.mark.integration
    async def test_word_solver_find_matching_words(self, mock_word_repository):
        """Test finding matching words for a plate."""
        # Setup mock repository
        mock_words = {
            Word("ambulance"): Frequency(5000),
            Word("beach"): Frequency(3000),
            Word("cabin"): Frequency(2000),  # Doesn't match ABC
            Word("cat"): Frequency(8000)     # Doesn't match ABC
        }
        mock_word_repository.get_all_words.return_value = mock_words
        
        solver = SimpleWordSolver(mock_word_repository)
        plate = LicensePlate("ABC")
        
        matches = await solver.find_matching_words(plate)
        
        # Should only return "ambulance" (matches ABC pattern)
        matching_words = [word.value for word, freq in matches]
        assert "ambulance" in matching_words
        assert "cabin" not in matching_words  # Wrong order
        assert "cat" not in matching_words    # Missing letters
        
        # Should be sorted by frequency (descending)
        if len(matches) > 1:
            for i in range(len(matches) - 1):
                assert matches[i][1] >= matches[i + 1][1]
    
    @pytest.mark.integration
    async def test_word_solver_get_random_words_uniform(self, mock_word_repository):
        """Test getting random words with uniform strategy."""
        # Setup mock repository with words that match ABC
        mock_words = {
            Word("ambulance"): Frequency(5000),
            Word("albatross"): Frequency(3000),
            Word("aberrant"): Frequency(1000)
        }
        mock_word_repository.get_all_words.return_value = mock_words
        
        solver = SimpleWordSolver(mock_word_repository)
        plate = LicensePlate("ABC")
        
        # Get random words
        random_words = await solver.get_random_words_for_plate(
            plate, count=2, strategy="uniform"
        )
        
        assert len(random_words) <= 2
        for word in random_words:
            assert isinstance(word, Word)
            assert word.matches_plate(plate)
    
    @pytest.mark.integration
    async def test_word_solver_get_random_words_frequency_weighted(self, mock_word_repository):
        """Test getting random words with frequency-weighted strategy."""
        mock_words = {
            Word("ambulance"): Frequency(5000),
            Word("albatross"): Frequency(3000)
        }
        mock_word_repository.get_all_words.return_value = mock_words
        
        solver = SimpleWordSolver(mock_word_repository)
        plate = LicensePlate("ABC")
        
        random_words = await solver.get_random_words_for_plate(
            plate, count=2, strategy="frequency_weighted"
        )
        
        assert len(random_words) <= 2
        for word in random_words:
            assert isinstance(word, Word)
    
    @pytest.mark.integration
    async def test_word_solver_no_matches(self, mock_word_repository):
        """Test word solver when no words match the plate."""
        mock_words = {
            Word("xyz"): Frequency(1000),
            Word("qrs"): Frequency(2000)
        }
        mock_word_repository.get_all_words.return_value = mock_words
        
        solver = SimpleWordSolver(mock_word_repository)
        plate = LicensePlate("ABC")
        
        matches = await solver.find_matching_words(plate)
        assert len(matches) == 0
        
        random_words = await solver.get_random_words_for_plate(plate)
        assert len(random_words) == 0


class TestSimpleCombinationGenerator:
    """Test the simple combination generator."""
    
    @pytest.mark.integration
    async def test_combination_generator_basic(self):
        """Test basic combination generation."""
        generator = SimpleCombinationGenerator()
        
        combinations = await generator.generate_combinations(
            character_set="ABC", length=3, count=5
        )
        
        assert len(combinations) == 5
        for combo in combinations:
            assert isinstance(combo, LicensePlate)
            assert len(combo) == 3
            # All characters should be from the set
            for char in combo.value:
                assert char in "ABC"
    
    @pytest.mark.integration
    async def test_combination_generator_different_lengths(self):
        """Test combination generation with different lengths."""
        generator = SimpleCombinationGenerator()
        
        # Test different lengths
        for length in [2, 4, 6]:
            combinations = await generator.generate_combinations(
                character_set="ABCDEF", length=length, count=3
            )
            
            assert len(combinations) == 3
            for combo in combinations:
                assert len(combo) == length
    
    @pytest.mark.integration
    async def test_combination_generator_empty_result(self):
        """Test combination generation with zero count."""
        generator = SimpleCombinationGenerator()
        
        combinations = await generator.generate_combinations(
            character_set="ABC", length=3, count=0
        )
        
        assert len(combinations) == 0


class TestJoblibModelPredictor:
    """Test the Joblib model predictor."""
    
    @pytest.mark.integration
    async def test_model_predictor_initialization(self):
        """Test model predictor initialization."""
        settings = get_settings()
        predictor = JoblibModelPredictor(settings)
        
        # Initially model should not be loaded
        is_loaded = await predictor.is_model_loaded()
        assert is_loaded is False
    
    @pytest.mark.integration 
    async def test_model_predictor_load_nonexistent_model(self):
        """Test loading non-existent model file."""
        settings = get_settings()
        predictor = JoblibModelPredictor(settings)
        
        # Should handle missing model file gracefully
        try:
            await predictor.load_model()
            # If it doesn't raise an exception, that's also acceptable
        except Exception:
            # Exception is expected for missing model file
            pass
    
    @pytest.mark.integration
    async def test_model_predictor_predict_without_model(self):
        """Test prediction without loaded model."""
        settings = get_settings()
        predictor = JoblibModelPredictor(settings)
        
        word = Word("ambulance")
        plate = LicensePlate("ABC")
        
        # Should raise RuntimeError when model is not loaded
        with pytest.raises(RuntimeError, match="Model not loaded"):
            await predictor.predict_score(word, plate)
    
    @pytest.mark.integration
    @patch('joblib.load')
    async def test_model_predictor_mock_prediction(self, mock_joblib_load):
        """Test prediction with mocked model."""
        settings = get_settings()
        predictor = JoblibModelPredictor(settings)
        
        # Mock the joblib.load to return a dummy model
        mock_model = MagicMock()
        mock_joblib_load.return_value = mock_model
        
        # Mock successful load
        predictor.model = mock_model
        
        word = Word("ambulance")
        plate = LicensePlate("ABC")
        
        score = await predictor.predict_score(word, plate)
        assert isinstance(score, Score)
        assert 0 <= score.value <= 100


class TestMemoryCacheManager:
    """Test the memory cache manager."""
    
    @pytest.mark.integration
    async def test_cache_manager_basic_operations(self):
        """Test basic cache operations."""
        cache = MemoryCacheManager()
        
        # Test set and get
        await cache.set("key1", "value1")
        value = await cache.get("key1")
        assert value == "value1"
        
        # Test non-existent key
        value = await cache.get("nonexistent")
        assert value is None
    
    @pytest.mark.integration
    async def test_cache_manager_delete(self):
        """Test cache deletion."""
        cache = MemoryCacheManager()
        
        await cache.set("key1", "value1")
        assert await cache.get("key1") == "value1"
        
        await cache.delete("key1")
        assert await cache.get("key1") is None
        
        # Deleting non-existent key should not raise error
        await cache.delete("nonexistent")
    
    @pytest.mark.integration
    async def test_cache_manager_clear(self):
        """Test clearing all cache."""
        cache = MemoryCacheManager()
        
        # Add multiple items
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.set("key3", "value3")
        
        # Verify they exist
        assert await cache.get("key1") == "value1"
        assert await cache.get("key2") == "value2"
        
        # Clear cache
        await cache.clear()
        
        # Verify all items are gone
        assert await cache.get("key1") is None
        assert await cache.get("key2") is None
        assert await cache.get("key3") is None
    
    @pytest.mark.integration
    async def test_cache_manager_complex_objects(self):
        """Test caching complex objects."""
        cache = MemoryCacheManager()
        
        # Test with dictionary
        complex_data = {
            "list": [1, 2, 3],
            "dict": {"nested": "value"},
            "number": 42
        }
        
        await cache.set("complex", complex_data)
        retrieved = await cache.get("complex")
        
        assert retrieved == complex_data
        assert retrieved["list"] == [1, 2, 3]
        assert retrieved["dict"]["nested"] == "value"


class TestSimpleFeatureExtractor:
    """Test the simple feature extractor."""
    
    @pytest.mark.integration
    async def test_feature_extractor_extract_features(self, mock_word_repository):
        """Test basic feature extraction."""
        # Setup mock repository
        mock_word_repository.get_word_frequency.return_value = Frequency(5000)
        
        extractor = SimpleFeatureExtractor(mock_word_repository)
        word = Word("ambulance")
        plate = LicensePlate("ABC")
        
        features = await extractor.extract_features(word, plate)
        
        assert isinstance(features, dict)
        assert "word_length" in features
        assert "plate_length" in features
        assert "word_frequency" in features
        assert "character_overlap" in features
        
        assert features["word_length"] == len(word)
        assert features["plate_length"] == len(plate)
        assert features["word_frequency"] == 5000
        assert features["character_overlap"] >= 0
    
    @pytest.mark.integration
    async def test_feature_extractor_build_corpus_statistics(self, mock_word_repository):
        """Test building corpus statistics."""
        # Setup mock repository with sample data
        mock_words = {
            Word("ambulance"): Frequency(5000),
            Word("beach"): Frequency(3000),
            Word("cat"): Frequency(8000),
            Word("dog"): Frequency(4000)
        }
        mock_word_repository.get_all_words.return_value = mock_words
        
        extractor = SimpleFeatureExtractor(mock_word_repository)
        stats = await extractor.build_corpus_statistics()
        
        assert isinstance(stats, CorpusStatistics)
        assert stats.total_unique_words == len(mock_words)
        assert isinstance(stats.dataset_words, list)
        assert isinstance(stats.plate_word_counts, dict)
        assert isinstance(stats.word_frequency_distribution, dict)
        assert len(stats.dataset_words) > 0
    
    @pytest.mark.integration
    async def test_feature_extractor_build_corpus_features(self, mock_word_repository):
        """Test building corpus features."""
        extractor = SimpleFeatureExtractor(mock_word_repository)
        features = await extractor.build_corpus_features()
        
        assert isinstance(features, CorpusFeatures)
        assert isinstance(features.features, dict)
        assert isinstance(features.metadata, dict)
        assert len(features.features) > 0
        
        # Check that at least one feature set exists
        sample_key = list(features.features.keys())[0]
        sample_features = features.features[sample_key]
        assert isinstance(sample_features, dict)
        assert "word_length" in sample_features
    
    @pytest.mark.integration
    async def test_feature_extractor_word_not_found(self, mock_word_repository):
        """Test feature extraction when word frequency is not found."""
        # Setup mock to return None for frequency
        mock_word_repository.get_word_frequency.return_value = None
        
        extractor = SimpleFeatureExtractor(mock_word_repository)
        word = Word("nonexistent")
        plate = LicensePlate("ABC")
        
        features = await extractor.extract_features(word, plate)
        
        assert features["word_frequency"] == 0
        assert features["word_length"] == len(word)
        assert features["plate_length"] == len(plate)


@pytest.mark.integration
async def test_service_integration_chain(mock_word_repository):
    """Test integration between multiple services."""
    # Setup mock data
    mock_words = {
        Word("ambulance"): Frequency(5000),
        Word("beach"): Frequency(3000),
        Word("albatross"): Frequency(2000)
    }
    mock_word_repository.get_all_words.return_value = mock_words
    mock_word_repository.get_word_frequency.return_value = Frequency(5000)
    
    # Create service instances
    solver = SimpleWordSolver(mock_word_repository)
    extractor = SimpleFeatureExtractor(mock_word_repository)
    generator = SimpleCombinationGenerator()
    cache = MemoryCacheManager()
    
    # Generate a plate combination
    plates = await generator.generate_combinations("ABC", 3, 1)
    plate = plates[0]
    
    # Find matching words
    matches = await solver.find_matching_words(plate)
    
    if matches:
        word = matches[0][0]  # Get first matching word
        
        # Extract features for the word-plate combination
        features = await extractor.extract_features(word, plate)
        
        # Cache the features
        cache_key = f"features:{word.value}:{plate.value}"
        await cache.set(cache_key, features)
        
        # Retrieve from cache
        cached_features = await cache.get(cache_key)
        
        # Verify the chain worked
        assert cached_features == features
        assert cached_features["word"] == word.value
        assert cached_features["plate"] == plate.value
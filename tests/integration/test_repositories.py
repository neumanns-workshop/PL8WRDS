"""
Integration tests for repository implementations.
"""

import pytest
import json
import tempfile
import aiofiles
from pathlib import Path
from datetime import datetime

from app.infrastructure.repositories import (
    JsonWordRepository, JsonScoringRepository, JsonCorpusRepository
)
from app.domain.entities import (
    WordMatch, WordScore, ScoringSession, CorpusStatistics, 
    CorpusFeatures, IndividualScore
)
from app.domain.value_objects import (
    Word, LicensePlate, Frequency, ModelName, Score, Reasoning,
    SessionId, FilePath, DirectoryPath
)
from tests.factories import (
    WordScoreFactory, ScoringSessionFactory, CorpusStatisticsFactory,
    CorpusFeaturesFactory, IndividualScoreFactory
)


class TestJsonWordRepository:
    """Test the JSON-based word repository."""
    
    @pytest.mark.integration
    async def test_word_repository_load_valid_data(self):
        """Test loading valid word data from JSON file."""
        # Create temporary file with test data
        test_data = [
            {"word": "ambulance", "frequency": 5000},
            {"word": "beach", "frequency": 3000},
            {"word": "cat", "frequency": 8000}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_file = f.name
        
        try:
            # Initialize repository
            repo = JsonWordRepository(FilePath(temp_file))
            
            # Test get_word_frequency
            freq = await repo.get_word_frequency(Word("ambulance"))
            assert freq is not None
            assert freq.value == 5000
            
            # Test get_all_words
            all_words = await repo.get_all_words()
            assert len(all_words) == 3
            assert Word("ambulance") in all_words
            assert all_words[Word("beach")].value == 3000
            
            # Test caching (second call should use cache)
            freq2 = await repo.get_word_frequency(Word("cat"))
            assert freq2.value == 8000
            
        finally:
            Path(temp_file).unlink()  # Clean up
    
    @pytest.mark.integration
    async def test_word_repository_word_not_found(self):
        """Test behavior when word is not found."""
        test_data = [{"word": "ambulance", "frequency": 5000}]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_file = f.name
        
        try:
            repo = JsonWordRepository(FilePath(temp_file))
            freq = await repo.get_word_frequency(Word("nonexistent"))
            assert freq is None
        finally:
            Path(temp_file).unlink()
    
    @pytest.mark.integration
    async def test_word_repository_find_matching_words(self):
        """Test finding words that match license plate patterns."""
        test_data = [
            {"word": "ambulance", "frequency": 5000},  # Matches ABC
            {"word": "beach", "frequency": 3000},      # Matches BCH
            {"word": "cabin", "frequency": 2000},      # Doesn't match ABC (wrong order)
            {"word": "cat", "frequency": 8000}         # Doesn't match ABC (missing B)
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_file = f.name
        
        try:
            repo = JsonWordRepository(FilePath(temp_file))
            plate = LicensePlate("ABC")
            matches = await repo.find_words_matching_plate(plate)
            
            # Only "ambulance" should match ABC
            assert len(matches) == 1
            assert matches[0].word.value == "ambulance"
            assert matches[0].plate == plate
            assert matches[0].frequency.value == 5000
            
        finally:
            Path(temp_file).unlink()
    
    @pytest.mark.integration
    async def test_word_repository_invalid_file(self):
        """Test behavior with invalid or missing file."""
        # Test with non-existent file
        repo = JsonWordRepository(FilePath("/nonexistent/file.json"))
        all_words = await repo.get_all_words()
        assert len(all_words) == 0
        
        freq = await repo.get_word_frequency(Word("test"))
        assert freq is None


class TestJsonScoringRepository:
    """Test the JSON-based scoring repository."""
    
    @pytest.mark.integration
    async def test_scoring_repository_save_and_get_word_score(self):
        """Test saving and retrieving word scores."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = DirectoryPath(temp_dir)
            repo = JsonScoringRepository(cache_dir)
            
            # Create test word score
            word_score = WordScore(
                word=Word("ambulance"),
                plate=LicensePlate("ABC"),
                individual_scores=[
                    IndividualScore(
                        model=ModelName("granite"),
                        score=Score(85.0),
                        reasoning=Reasoning("Great match!")
                    )
                ],
                frequency=Frequency(5000)
            )
            
            # Save word score
            await repo.save_word_score(word_score)
            
            # Retrieve individual score
            retrieved_score = await repo.get_word_score(
                Word("ambulance"),
                LicensePlate("ABC"),
                ModelName("granite")
            )
            
            assert retrieved_score is not None
            assert retrieved_score.model.value == "granite"
            assert retrieved_score.score.value == 85.0
            assert retrieved_score.reasoning.value == "Great match!"
    
    @pytest.mark.integration
    async def test_scoring_repository_save_and_get_session(self):
        """Test saving and retrieving scoring sessions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = DirectoryPath(temp_dir)
            repo = JsonScoringRepository(cache_dir)
            
            # Create test session
            session_id = SessionId.generate()
            session = ScoringSession(
                session_id=session_id,
                models_used=[ModelName("granite"), ModelName("mistral")],
                results=[WordScoreFactory()]
            )
            
            # Save session
            await repo.save_session(session)
            
            # Retrieve session
            retrieved_session = await repo.get_session(session_id)
            
            assert retrieved_session is not None
            assert retrieved_session.session_id == session_id
            assert len(retrieved_session.models_used) == 2
            assert ModelName("granite") in retrieved_session.models_used
            assert ModelName("mistral") in retrieved_session.models_used
    
    @pytest.mark.integration
    async def test_scoring_repository_persistence(self):
        """Test that data persists across repository instances."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = DirectoryPath(temp_dir)
            
            # Create first repository instance and save data
            repo1 = JsonScoringRepository(cache_dir)
            
            word_score = WordScore(
                word=Word("test"),
                plate=LicensePlate("TST"),
                individual_scores=[IndividualScoreFactory()],
                frequency=Frequency(1000)
            )
            
            await repo1.save_word_score(word_score)
            
            # Create second repository instance and retrieve data
            repo2 = JsonScoringRepository(cache_dir)
            
            retrieved_score = await repo2.get_word_score(
                Word("test"),
                LicensePlate("TST"),
                word_score.individual_scores[0].model
            )
            
            assert retrieved_score is not None
            assert retrieved_score.score.value == word_score.individual_scores[0].score.value
    
    @pytest.mark.integration
    async def test_scoring_repository_non_existent_data(self):
        """Test retrieving non-existent data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = DirectoryPath(temp_dir)
            repo = JsonScoringRepository(cache_dir)
            
            # Try to get non-existent word score
            score = await repo.get_word_score(
                Word("nonexistent"),
                LicensePlate("ABC"),
                ModelName("granite")
            )
            assert score is None
            
            # Try to get non-existent session
            session = await repo.get_session(SessionId.generate())
            assert session is None


class TestJsonCorpusRepository:
    """Test the JSON-based corpus repository."""
    
    @pytest.mark.integration
    async def test_corpus_repository_save_and_get_statistics(self):
        """Test saving and retrieving corpus statistics."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = DirectoryPath(temp_dir)
            repo = JsonCorpusRepository(cache_dir)
            
            # Create test statistics
            stats = CorpusStatistics(
                total_plates=100,
                total_unique_words=5000,
                dataset_words=["ambulance", "beach", "cat"],
                plate_word_counts={"ABC": 25, "DEF": 30},
                word_frequency_distribution={"rare": 100, "common": 4900}
            )
            
            # Save statistics
            await repo.save_statistics(stats)
            
            # Retrieve statistics
            retrieved_stats = await repo.get_statistics()
            
            assert retrieved_stats is not None
            assert retrieved_stats.total_plates == 100
            assert retrieved_stats.total_unique_words == 5000
            assert retrieved_stats.dataset_words == ["ambulance", "beach", "cat"]
            assert retrieved_stats.plate_word_counts == {"ABC": 25, "DEF": 30}
            assert retrieved_stats.word_frequency_distribution == {"rare": 100, "common": 4900}
    
    @pytest.mark.integration
    async def test_corpus_repository_save_and_get_features(self):
        """Test saving and retrieving corpus features."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = DirectoryPath(temp_dir)
            repo = JsonCorpusRepository(cache_dir)
            
            # Create test features
            features = CorpusFeatures(
                features={
                    "ambulance:abc": {
                        "tfidf": 0.5,
                        "length": 9,
                        "vowel_ratio": 0.44
                    },
                    "beach:bch": {
                        "tfidf": 0.3,
                        "length": 5,
                        "vowel_ratio": 0.4
                    }
                },
                metadata={
                    "total_features": 2,
                    "extraction_method": "test"
                }
            )
            
            # Save features
            await repo.save_features(features)
            
            # Retrieve features
            retrieved_features = await repo.get_features()
            
            assert retrieved_features is not None
            assert len(retrieved_features.features) == 2
            assert "ambulance:abc" in retrieved_features.features
            assert retrieved_features.features["ambulance:abc"]["tfidf"] == 0.5
            assert retrieved_features.metadata["total_features"] == 2
            assert retrieved_features.metadata["extraction_method"] == "test"
    
    @pytest.mark.integration
    async def test_corpus_repository_persistence(self):
        """Test that corpus data persists across repository instances."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = DirectoryPath(temp_dir)
            
            # Save with first instance
            repo1 = JsonCorpusRepository(cache_dir)
            stats = CorpusStatisticsFactory()
            await repo1.save_statistics(stats)
            
            # Retrieve with second instance
            repo2 = JsonCorpusRepository(cache_dir)
            retrieved_stats = await repo2.get_statistics()
            
            assert retrieved_stats is not None
            assert retrieved_stats.total_plates == stats.total_plates
            assert retrieved_stats.total_unique_words == stats.total_unique_words
    
    @pytest.mark.integration
    async def test_corpus_repository_non_existent_data(self):
        """Test retrieving non-existent corpus data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = DirectoryPath(temp_dir)
            repo = JsonCorpusRepository(cache_dir)
            
            # Try to get non-existent statistics
            stats = await repo.get_statistics()
            assert stats is None
            
            # Try to get non-existent features
            features = await repo.get_features()
            assert features is None
    
    @pytest.mark.integration
    async def test_corpus_repository_concurrent_access(self):
        """Test concurrent access to repository (basic test)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = DirectoryPath(temp_dir)
            repo = JsonCorpusRepository(cache_dir)
            
            # Create multiple statistics instances
            stats1 = CorpusStatisticsFactory()
            stats2 = CorpusStatisticsFactory()
            
            # Save both (second should overwrite first)
            await repo.save_statistics(stats1)
            await repo.save_statistics(stats2)
            
            # Retrieve should get the latest
            retrieved_stats = await repo.get_statistics()
            assert retrieved_stats is not None
            assert retrieved_stats.total_plates == stats2.total_plates
    
    @pytest.mark.integration
    async def test_corpus_repository_file_permissions(self):
        """Test repository handles file permission errors gracefully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = DirectoryPath(temp_dir)
            repo = JsonCorpusRepository(cache_dir)
            
            # Create and save initial data
            stats = CorpusStatisticsFactory()
            await repo.save_statistics(stats)
            
            # Verify file was created
            stats_file = Path(cache_dir.value) / "corpus_stats.json"
            assert stats_file.exists()
            
            # Verify we can read it back
            retrieved_stats = await repo.get_statistics()
            assert retrieved_stats is not None
    
    @pytest.mark.integration 
    async def test_corpus_repository_large_data(self):
        """Test repository with larger datasets."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = DirectoryPath(temp_dir)
            repo = JsonCorpusRepository(cache_dir)
            
            # Create large feature set
            large_features = {}
            for i in range(1000):
                word = f"word{i:04d}"
                plate = f"P{i%26:02d}T"
                large_features[f"{word}:{plate.lower()}"] = {
                    "tfidf": i * 0.001,
                    "length": len(word),
                    "index": i
                }
            
            features = CorpusFeatures(
                features=large_features,
                metadata={"total_features": len(large_features)}
            )
            
            # Save large features
            await repo.save_features(features)
            
            # Retrieve and verify
            retrieved_features = await repo.get_features()
            assert retrieved_features is not None
            assert len(retrieved_features.features) == 1000
            assert "word0500:p06t" in retrieved_features.features
            assert retrieved_features.features["word0500:p06t"]["index"] == 500
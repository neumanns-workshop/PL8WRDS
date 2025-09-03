"""
Unit tests for domain entities.
"""

import pytest
from datetime import datetime, timedelta
from freezegun import freeze_time

from app.domain.entities import (
    WordMatch, IndividualScore, WordScore, ScoringSession,
    CorpusStatistics, CorpusFeatures, ModelAvailability,
    ScoringSystemStatus
)
from app.domain.value_objects import (
    Word, LicensePlate, Score, Frequency, ModelName, SessionId,
    Reasoning, AggregateScore, CacheKey
)
from tests.factories import (
    WordMatchFactory, IndividualScoreFactory, WordScoreFactory,
    ScoringSessionFactory, CorpusStatisticsFactory, CorpusFeaturesFactory,
    ModelAvailabilityFactory, ScoringSystemStatusFactory
)


class TestWordMatch:
    """Test the WordMatch entity."""
    
    @pytest.mark.unit
    def test_word_match_creation_valid(self):
        """Test creating valid word matches."""
        word = Word("ambulance")
        plate = LicensePlate("ABC")
        frequency = Frequency(1000)
        
        match = WordMatch(
            word=word,
            plate=plate,
            frequency=frequency
        )
        
        assert match.word == word
        assert match.plate == plate
        assert match.frequency == frequency
    
    @pytest.mark.unit
    def test_word_match_validation_invalid(self):
        """Test word match creation fails with invalid word-plate combination."""
        word = Word("xyz")  # Doesn't match ABC
        plate = LicensePlate("ABC")
        frequency = Frequency(1000)
        
        with pytest.raises(ValueError, match="Word 'xyz' does not match plate 'ABC'"):
            WordMatch(
                word=word,
                plate=plate,
                frequency=frequency
            )
    
    @pytest.mark.unit
    def test_word_match_factory(self):
        """Test word match creation using factory."""
        match = WordMatchFactory()
        
        assert isinstance(match.word, Word)
        assert isinstance(match.plate, LicensePlate)
        assert isinstance(match.frequency, Frequency)
        assert match.word.matches_plate(match.plate)


class TestIndividualScore:
    """Test the IndividualScore entity."""
    
    @pytest.mark.unit
    def test_individual_score_creation_valid(self):
        """Test creating valid individual scores."""
        model = ModelName("granite")
        score = Score(85.5)
        reasoning = Reasoning("Good match")
        
        individual_score = IndividualScore(
            model=model,
            score=score,
            reasoning=reasoning
        )
        
        assert individual_score.model == model
        assert individual_score.score == score
        assert individual_score.reasoning == reasoning
        assert isinstance(individual_score.created_at, datetime)
    
    @pytest.mark.unit
    @freeze_time("2023-01-01T10:00:00Z")
    def test_individual_score_auto_timestamp(self):
        """Test individual score automatically sets timestamp."""
        individual_score = IndividualScoreFactory()
        assert individual_score.created_at == datetime(2023, 1, 1, 10, 0, 0)
    
    @pytest.mark.unit
    def test_individual_score_custom_timestamp(self):
        """Test individual score with custom timestamp."""
        custom_time = datetime(2023, 6, 15, 12, 0, 0)
        
        individual_score = IndividualScore(
            model=ModelName("granite"),
            score=Score(85.5),
            reasoning=Reasoning("Good match"),
            created_at=custom_time
        )
        
        assert individual_score.created_at == custom_time
    
    @pytest.mark.unit
    def test_individual_score_factory(self):
        """Test individual score creation using factory."""
        score = IndividualScoreFactory()
        
        assert isinstance(score.model, ModelName)
        assert isinstance(score.score, Score)
        assert isinstance(score.reasoning, Reasoning)
        assert isinstance(score.created_at, datetime)


class TestWordScore:
    """Test the WordScore entity."""
    
    @pytest.mark.unit
    def test_word_score_creation_valid(self):
        """Test creating valid word scores."""
        word = Word("ambulance")
        plate = LicensePlate("ABC")
        frequency = Frequency(1000)
        individual_score = IndividualScoreFactory()
        
        word_score = WordScore(
            word=word,
            plate=plate,
            individual_scores=[individual_score],
            frequency=frequency
        )
        
        assert word_score.word == word
        assert word_score.plate == plate
        assert word_score.individual_scores == [individual_score]
        assert word_score.frequency == frequency
        assert isinstance(word_score.created_at, datetime)
        assert isinstance(word_score.aggregate_score, AggregateScore)
        assert word_score.aggregate_score.value == individual_score.score.value
    
    @pytest.mark.unit
    def test_word_score_aggregate_calculation(self):
        """Test word score aggregate calculation."""
        scores = [
            IndividualScore(ModelName("model1"), Score(80.0), Reasoning("Good")),
            IndividualScore(ModelName("model2"), Score(90.0), Reasoning("Great")),
            IndividualScore(ModelName("model3"), Score(70.0), Reasoning("OK"))
        ]
        
        word_score = WordScore(
            word=Word("ambulance"),
            plate=LicensePlate("ABC"),
            individual_scores=scores,
            frequency=Frequency(1000)
        )
        
        # Average should be (80 + 90 + 70) / 3 = 80
        assert word_score.aggregate_score.value == 80.0
    
    @pytest.mark.unit
    def test_word_score_add_score(self):
        """Test adding individual scores to word score."""
        word_score = WordScore(
            word=Word("ambulance"),
            plate=LicensePlate("ABC"),
            individual_scores=[],
            frequency=Frequency(1000)
        )
        
        # Initially no aggregate score
        assert word_score.aggregate_score is None
        
        # Add first score
        score1 = IndividualScore(ModelName("model1"), Score(80.0), Reasoning("Good"))
        word_score.add_score(score1)
        
        assert len(word_score.individual_scores) == 1
        assert word_score.aggregate_score.value == 80.0
        
        # Add second score
        score2 = IndividualScore(ModelName("model2"), Score(90.0), Reasoning("Great"))
        word_score.add_score(score2)
        
        assert len(word_score.individual_scores) == 2
        assert word_score.aggregate_score.value == 85.0  # (80 + 90) / 2
    
    @pytest.mark.unit
    def test_word_score_factory(self):
        """Test word score creation using factory."""
        word_score = WordScoreFactory()
        
        assert isinstance(word_score.word, Word)
        assert isinstance(word_score.plate, LicensePlate)
        assert isinstance(word_score.frequency, Frequency)
        assert isinstance(word_score.created_at, datetime)
        assert len(word_score.individual_scores) > 0
        assert isinstance(word_score.aggregate_score, AggregateScore)


class TestScoringSession:
    """Test the ScoringSession entity."""
    
    @pytest.mark.unit
    def test_scoring_session_creation_valid(self):
        """Test creating valid scoring sessions."""
        session_id = SessionId.generate()
        models = [ModelName("granite"), ModelName("mistral")]
        word_scores = [WordScoreFactory(), WordScoreFactory()]
        
        session = ScoringSession(
            session_id=session_id,
            models_used=models,
            results=word_scores
        )
        
        assert session.session_id == session_id
        assert session.models_used == models
        assert session.results == word_scores
        assert isinstance(session.created_at, datetime)
        assert session.end_time is None
        assert not session.interrupted
        assert session.total_scores == sum(len(ws.individual_scores) for ws in word_scores)
    
    @pytest.mark.unit
    def test_scoring_session_add_result(self):
        """Test adding results to scoring session."""
        session = ScoringSession(
            session_id=SessionId.generate(),
            models_used=[ModelName("granite")],
            results=[]
        )
        
        initial_count = session.total_scores
        
        word_score = WordScoreFactory()
        session.add_result(word_score)
        
        assert len(session.results) == 1
        assert session.results[0] == word_score
        assert session.total_scores == initial_count + len(word_score.individual_scores)
    
    @pytest.mark.unit
    def test_scoring_session_completion(self):
        """Test scoring session completion."""
        session = ScoringSessionFactory()
        
        assert not session.is_completed
        assert session.duration_seconds is None
        
        with freeze_time("2023-01-01T10:05:00Z") as frozen_time:
            session.mark_completed()
            
            assert session.is_completed
            assert session.end_time is not None
            
            # Test duration calculation
            frozen_time.tick(delta=timedelta(minutes=5))
            duration = session.duration_seconds
            assert duration is not None
            assert duration >= 0
    
    @pytest.mark.unit
    def test_scoring_session_interruption(self):
        """Test scoring session interruption."""
        session = ScoringSessionFactory()
        
        assert not session.interrupted
        assert not session.is_completed
        
        session.mark_interrupted()
        
        assert session.interrupted
        assert session.is_completed
        assert session.end_time is not None
    
    @pytest.mark.unit
    def test_scoring_session_factory(self):
        """Test scoring session creation using factory."""
        session = ScoringSessionFactory()
        
        assert isinstance(session.session_id, SessionId)
        assert len(session.models_used) > 0
        assert len(session.results) >= 0
        assert isinstance(session.created_at, datetime)


class TestCorpusStatistics:
    """Test the CorpusStatistics entity."""
    
    @pytest.mark.unit
    def test_corpus_statistics_creation_valid(self):
        """Test creating valid corpus statistics."""
        stats = CorpusStatistics(
            total_plates=100,
            total_unique_words=500,
            dataset_words=["ambulance", "beach", "cat"],
            plate_word_counts={"ABC": 10, "XYZ": 5},
            word_frequency_distribution={"rare": 100, "common": 400}
        )
        
        assert stats.total_plates == 100
        assert stats.total_unique_words == 500
        assert stats.dataset_words == ["ambulance", "beach", "cat"]
        assert stats.plate_word_counts == {"ABC": 10, "XYZ": 5}
        assert stats.word_frequency_distribution == {"rare": 100, "common": 400}
        assert isinstance(stats.generated_at, datetime)
    
    @pytest.mark.unit
    @freeze_time("2023-01-01T10:00:00Z")
    def test_corpus_statistics_auto_timestamp(self):
        """Test corpus statistics automatically sets timestamp."""
        stats = CorpusStatisticsFactory()
        assert stats.generated_at == datetime(2023, 1, 1, 10, 0, 0)
    
    @pytest.mark.unit
    def test_corpus_statistics_factory(self):
        """Test corpus statistics creation using factory."""
        stats = CorpusStatisticsFactory()
        
        assert isinstance(stats.total_plates, int)
        assert isinstance(stats.total_unique_words, int)
        assert isinstance(stats.dataset_words, list)
        assert isinstance(stats.plate_word_counts, dict)
        assert isinstance(stats.word_frequency_distribution, dict)
        assert isinstance(stats.generated_at, datetime)


class TestCorpusFeatures:
    """Test the CorpusFeatures entity."""
    
    @pytest.mark.unit
    def test_corpus_features_creation_valid(self):
        """Test creating valid corpus features."""
        features = {
            "ambulance:abc": {
                "tfidf": 0.5,
                "length": 9,
                "vowel_ratio": 0.44
            }
        }
        metadata = {"total_features": 100}
        
        corpus_features = CorpusFeatures(
            features=features,
            metadata=metadata
        )
        
        assert corpus_features.features == features
        assert corpus_features.metadata == metadata
        assert isinstance(corpus_features.generated_at, datetime)
    
    @pytest.mark.unit
    def test_corpus_features_get_features(self):
        """Test getting features for specific word-plate combination."""
        features = {
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
        }
        
        corpus_features = CorpusFeatures(
            features=features,
            metadata={"total_features": 2}
        )
        
        # Test existing combination
        word_features = corpus_features.get_features(Word("ambulance"), LicensePlate("ABC"))
        assert word_features == {
            "tfidf": 0.5,
            "length": 9,
            "vowel_ratio": 0.44
        }
        
        # Test non-existing combination
        missing_features = corpus_features.get_features(Word("cat"), LicensePlate("CAT"))
        assert missing_features is None
    
    @pytest.mark.unit
    def test_corpus_features_case_insensitive_lookup(self):
        """Test case-insensitive feature lookup."""
        features = {
            "ambulance:abc": {
                "tfidf": 0.5,
                "length": 9
            }
        }
        
        corpus_features = CorpusFeatures(
            features=features,
            metadata={"total_features": 1}
        )
        
        # Test with different cases
        word_features1 = corpus_features.get_features(Word("AMBULANCE"), LicensePlate("abc"))
        word_features2 = corpus_features.get_features(Word("ambulance"), LicensePlate("ABC"))
        
        assert word_features1 == word_features2
        assert word_features1 is not None
    
    @pytest.mark.unit
    def test_corpus_features_factory(self):
        """Test corpus features creation using factory."""
        corpus_features = CorpusFeaturesFactory()
        
        assert isinstance(corpus_features.features, dict)
        assert isinstance(corpus_features.metadata, dict)
        assert isinstance(corpus_features.generated_at, datetime)


class TestModelAvailability:
    """Test the ModelAvailability entity."""
    
    @pytest.mark.unit
    def test_model_availability_creation_available(self):
        """Test creating available model availability."""
        model = ModelName("granite")
        
        availability = ModelAvailability(
            model=model,
            available=True
        )
        
        assert availability.model == model
        assert availability.available is True
        assert availability.error_message is None
        assert isinstance(availability.last_checked, datetime)
    
    @pytest.mark.unit
    def test_model_availability_creation_unavailable(self):
        """Test creating unavailable model availability."""
        model = ModelName("granite")
        error_msg = "Model not found"
        
        availability = ModelAvailability(
            model=model,
            available=False,
            error_message=error_msg
        )
        
        assert availability.model == model
        assert availability.available is False
        assert availability.error_message == error_msg
        assert isinstance(availability.last_checked, datetime)
    
    @pytest.mark.unit
    def test_model_availability_factory(self):
        """Test model availability creation using factory."""
        availability = ModelAvailabilityFactory()
        
        assert isinstance(availability.model, ModelName)
        assert isinstance(availability.available, bool)
        assert isinstance(availability.last_checked, datetime)


class TestScoringSystemStatus:
    """Test the ScoringSystemStatus entity."""
    
    @pytest.mark.unit
    def test_scoring_system_status_creation_valid(self):
        """Test creating valid scoring system status."""
        models = [
            ModelAvailability(ModelName("granite"), True),
            ModelAvailability(ModelName("mistral"), False, "Not installed")
        ]
        
        status = ScoringSystemStatus(
            ollama_running=True,
            models=models,
            cache_enabled=True,
            active_sessions=2
        )
        
        assert status.ollama_running is True
        assert status.models == models
        assert status.cache_enabled is True
        assert status.active_sessions == 2
        assert isinstance(status.checked_at, datetime)
    
    @pytest.mark.unit
    def test_scoring_system_status_available_models(self):
        """Test getting available models from system status."""
        models = [
            ModelAvailability(ModelName("granite"), True),
            ModelAvailability(ModelName("mistral"), False, "Not installed"),
            ModelAvailability(ModelName("deepseek"), True)
        ]
        
        status = ScoringSystemStatus(
            ollama_running=True,
            models=models,
            cache_enabled=True,
            active_sessions=0
        )
        
        available_models = status.available_models
        assert len(available_models) == 2
        assert ModelName("granite") in available_models
        assert ModelName("deepseek") in available_models
        assert ModelName("mistral") not in available_models
    
    @pytest.mark.unit
    def test_scoring_system_status_health_check(self):
        """Test system health check."""
        # Healthy system
        healthy_models = [ModelAvailability(ModelName("granite"), True)]
        healthy_status = ScoringSystemStatus(
            ollama_running=True,
            models=healthy_models,
            cache_enabled=True,
            active_sessions=0
        )
        assert healthy_status.is_healthy
        
        # Unhealthy - no Ollama
        unhealthy_status1 = ScoringSystemStatus(
            ollama_running=False,
            models=healthy_models,
            cache_enabled=True,
            active_sessions=0
        )
        assert not unhealthy_status1.is_healthy
        
        # Unhealthy - no available models
        unavailable_models = [ModelAvailability(ModelName("granite"), False)]
        unhealthy_status2 = ScoringSystemStatus(
            ollama_running=True,
            models=unavailable_models,
            cache_enabled=True,
            active_sessions=0
        )
        assert not unhealthy_status2.is_healthy
    
    @pytest.mark.unit
    def test_scoring_system_status_factory(self):
        """Test scoring system status creation using factory."""
        status = ScoringSystemStatusFactory()
        
        assert isinstance(status.ollama_running, bool)
        assert isinstance(status.models, list)
        assert isinstance(status.cache_enabled, bool)
        assert isinstance(status.active_sessions, int)
        assert isinstance(status.checked_at, datetime)
"""
Unit tests for domain value objects.
"""

import pytest
from typing import List

from app.domain.value_objects import (
    Word, LicensePlate, Score, AggregateScore, Frequency, ModelName,
    SessionId, CacheKey, Reasoning, FilePath, DirectoryPath
)


class TestWord:
    """Test the Word value object."""
    
    @pytest.mark.unit
    def test_word_creation_valid(self):
        """Test creating valid words."""
        word = Word("ambulance")
        assert word.value == "ambulance"
        assert str(word) == "ambulance"
        assert len(word) == 9
    
    @pytest.mark.unit
    def test_word_normalization(self):
        """Test word normalization to lowercase."""
        word = Word("AMBULANCE")
        assert word.value == "ambulance"
    
    @pytest.mark.unit
    def test_word_invalid_empty(self):
        """Test word creation fails with empty string."""
        with pytest.raises(ValueError, match="Word value must be a non-empty string"):
            Word("")
    
    @pytest.mark.unit
    def test_word_invalid_non_string(self):
        """Test word creation fails with non-string."""
        with pytest.raises(ValueError, match="Word value must be a non-empty string"):
            Word(123)
    
    @pytest.mark.unit
    def test_word_invalid_non_alphabetic(self):
        """Test word creation fails with non-alphabetic characters."""
        with pytest.raises(ValueError, match="Word must contain only alphabetic characters"):
            Word("word123")
        
        with pytest.raises(ValueError, match="Word must contain only alphabetic characters"):
            Word("word-with-dash")
    
    @pytest.mark.unit
    def test_word_matches_plate_valid(self):
        """Test word matching valid license plates."""
        word = Word("ambulance")
        
        # Test exact subsequence match
        assert word.matches_plate(LicensePlate("ABC"))
        assert word.matches_plate(LicensePlate("AMB"))
        assert word.matches_plate(LicensePlate("AMBUL"))
        
        # Test full word
        assert word.matches_plate(LicensePlate("AMBULANCE"))
    
    @pytest.mark.unit
    def test_word_matches_plate_invalid(self):
        """Test word not matching invalid license plates."""
        word = Word("ambulance")
        
        # Test wrong order
        assert not word.matches_plate(LicensePlate("CBA"))
        assert not word.matches_plate(LicensePlate("BCA"))
        
        # Test missing letters
        assert not word.matches_plate(LicensePlate("XYZ"))
        assert not word.matches_plate(LicensePlate("AXC"))
    
    @pytest.mark.unit
    def test_word_matches_plate_edge_cases(self):
        """Test word matching edge cases."""
        # Single letter word
        word = Word("a")
        assert word.matches_plate(LicensePlate("A"))
        assert word.matches_plate(LicensePlate("AB"))
        assert not word.matches_plate(LicensePlate("B"))
        
        # Repeated letters
        word = Word("banana")
        assert word.matches_plate(LicensePlate("BAN"))
        assert word.matches_plate(LicensePlate("BANA"))
        assert not word.matches_plate(LicensePlate("NAB"))


class TestLicensePlate:
    """Test the LicensePlate value object."""
    
    @pytest.mark.unit
    def test_license_plate_creation_valid(self):
        """Test creating valid license plates."""
        plate = LicensePlate("abc")
        assert plate.value == "ABC"
        assert str(plate) == "ABC"
        assert len(plate) == 3
    
    @pytest.mark.unit
    def test_license_plate_normalization(self):
        """Test license plate normalization to uppercase."""
        plate = LicensePlate("abc")
        assert plate.value == "ABC"
    
    @pytest.mark.unit
    def test_license_plate_invalid_empty(self):
        """Test license plate creation fails with empty string."""
        with pytest.raises(ValueError, match="License plate value must be a non-empty string"):
            LicensePlate("")
    
    @pytest.mark.unit
    def test_license_plate_invalid_non_string(self):
        """Test license plate creation fails with non-string."""
        with pytest.raises(ValueError, match="License plate value must be a non-empty string"):
            LicensePlate(123)
    
    @pytest.mark.unit
    def test_license_plate_invalid_non_alphabetic(self):
        """Test license plate creation fails with non-alphabetic characters."""
        with pytest.raises(ValueError, match="License plate must contain only alphabetic characters"):
            LicensePlate("ABC123")
        
        with pytest.raises(ValueError, match="License plate must contain only alphabetic characters"):
            LicensePlate("A-B-C")
    
    @pytest.mark.unit
    def test_license_plate_invalid_length(self):
        """Test license plate creation fails with invalid length."""
        with pytest.raises(ValueError, match="License plate must be between 2 and 8 characters"):
            LicensePlate("A")  # Too short
        
        with pytest.raises(ValueError, match="License plate must be between 2 and 8 characters"):
            LicensePlate("ABCDEFGHI")  # Too long


class TestScore:
    """Test the Score value object."""
    
    @pytest.mark.unit
    def test_score_creation_valid(self):
        """Test creating valid scores."""
        score = Score(85.5)
        assert score.value == 85.5
        assert float(score) == 85.5
        assert str(score) == "85.5"
    
    @pytest.mark.unit
    def test_score_rounding(self):
        """Test score rounding to 2 decimal places."""
        score = Score(85.567)
        assert score.value == 85.57
        
        score = Score(85.564)
        assert score.value == 85.56
    
    @pytest.mark.unit
    def test_score_boundary_values(self):
        """Test score boundary values."""
        assert Score(0).value == 0
        assert Score(100).value == 100
        assert Score(0.0).value == 0.0
        assert Score(100.0).value == 100.0
    
    @pytest.mark.unit
    def test_score_invalid_non_number(self):
        """Test score creation fails with non-numeric values."""
        with pytest.raises(ValueError, match="Score must be a number"):
            Score("85")
        
        with pytest.raises(ValueError, match="Score must be a number"):
            Score(None)
    
    @pytest.mark.unit
    def test_score_invalid_out_of_range(self):
        """Test score creation fails with out-of-range values."""
        with pytest.raises(ValueError, match="Score must be between 0 and 100"):
            Score(-1)
        
        with pytest.raises(ValueError, match="Score must be between 0 and 100"):
            Score(101)


class TestAggregateScore:
    """Test the AggregateScore value object."""
    
    @pytest.mark.unit
    def test_aggregate_score_creation_valid(self):
        """Test creating valid aggregate scores."""
        score = AggregateScore(85.5)
        assert score.value == 85.5
        assert float(score) == 85.5
        assert str(score) == "85.5"
    
    @pytest.mark.unit
    def test_aggregate_score_rounding(self):
        """Test aggregate score rounding to 2 decimal places."""
        score = AggregateScore(85.567)
        assert score.value == 85.57
    
    @pytest.mark.unit
    def test_aggregate_score_invalid_non_number(self):
        """Test aggregate score creation fails with non-numeric values."""
        with pytest.raises(ValueError, match="Aggregate score must be a number"):
            AggregateScore("85")
    
    @pytest.mark.unit
    def test_aggregate_score_invalid_out_of_range(self):
        """Test aggregate score creation fails with out-of-range values."""
        with pytest.raises(ValueError, match="Aggregate score must be between 0 and 100"):
            AggregateScore(-1)
        
        with pytest.raises(ValueError, match="Aggregate score must be between 0 and 100"):
            AggregateScore(101)


class TestFrequency:
    """Test the Frequency value object."""
    
    @pytest.mark.unit
    def test_frequency_creation_valid(self):
        """Test creating valid frequencies."""
        freq = Frequency(1000)
        assert freq.value == 1000
        assert int(freq) == 1000
        assert str(freq) == "1000"
    
    @pytest.mark.unit
    def test_frequency_invalid_non_integer(self):
        """Test frequency creation fails with non-integer values."""
        with pytest.raises(ValueError, match="Frequency must be an integer"):
            Frequency(85.5)
        
        with pytest.raises(ValueError, match="Frequency must be an integer"):
            Frequency("1000")
    
    @pytest.mark.unit
    def test_frequency_invalid_negative(self):
        """Test frequency creation fails with negative values."""
        with pytest.raises(ValueError, match="Frequency cannot be negative"):
            Frequency(-1)
    
    @pytest.mark.unit
    def test_frequency_rarity_properties(self):
        """Test frequency rarity classification properties."""
        rare_freq = Frequency(500)
        assert rare_freq.is_rare
        assert not rare_freq.is_common
        
        medium_freq = Frequency(5000)
        assert not medium_freq.is_rare
        assert not medium_freq.is_common
        
        common_freq = Frequency(15000)
        assert not common_freq.is_rare
        assert common_freq.is_common
        
        # Boundary cases
        boundary_rare = Frequency(999)
        assert boundary_rare.is_rare
        
        boundary_common = Frequency(10000)
        assert boundary_common.is_common


class TestModelName:
    """Test the ModelName value object."""
    
    @pytest.mark.unit
    def test_model_name_creation_valid(self):
        """Test creating valid model names."""
        model = ModelName("granite")
        assert model.value == "granite"
        assert str(model) == "granite"
    
    @pytest.mark.unit
    def test_model_name_with_special_chars(self):
        """Test model names with allowed special characters."""
        model = ModelName("model-name_123")
        assert model.value == "model-name_123"
    
    @pytest.mark.unit
    def test_model_name_invalid_empty(self):
        """Test model name creation fails with empty string."""
        with pytest.raises(ValueError, match="Model name must be a non-empty string"):
            ModelName("")
    
    @pytest.mark.unit
    def test_model_name_invalid_non_string(self):
        """Test model name creation fails with non-string."""
        with pytest.raises(ValueError, match="Model name must be a non-empty string"):
            ModelName(123)
    
    @pytest.mark.unit
    def test_model_name_invalid_format(self):
        """Test model name creation fails with invalid format."""
        with pytest.raises(ValueError, match="Model name must contain only alphanumeric characters"):
            ModelName("model name")  # Space not allowed
        
        with pytest.raises(ValueError, match="Model name must contain only alphanumeric characters"):
            ModelName("model.name")  # Dot not allowed


class TestSessionId:
    """Test the SessionId value object."""
    
    @pytest.mark.unit
    def test_session_id_creation_valid(self):
        """Test creating valid session IDs."""
        session_id = SessionId("test-session-123")
        assert session_id.value == "test-session-123"
        assert str(session_id) == "test-session-123"
    
    @pytest.mark.unit
    def test_session_id_generate(self):
        """Test generating session IDs."""
        session_id = SessionId.generate()
        assert isinstance(session_id.value, str)
        assert len(session_id.value) == 36  # UUID4 length
        
        # Test uniqueness
        session_id2 = SessionId.generate()
        assert session_id.value != session_id2.value
    
    @pytest.mark.unit
    def test_session_id_invalid_empty(self):
        """Test session ID creation fails with empty string."""
        with pytest.raises(ValueError, match="Session ID must be a non-empty string"):
            SessionId("")
    
    @pytest.mark.unit
    def test_session_id_invalid_non_string(self):
        """Test session ID creation fails with non-string."""
        with pytest.raises(ValueError, match="Session ID must be a non-empty string"):
            SessionId(123)


class TestCacheKey:
    """Test the CacheKey value object."""
    
    @pytest.mark.unit
    def test_cache_key_creation_valid(self):
        """Test creating valid cache keys."""
        cache_key = CacheKey("user:123:data")
        assert cache_key.value == "user:123:data"
        assert str(cache_key) == "user:123:data"
    
    @pytest.mark.unit
    def test_cache_key_invalid_empty(self):
        """Test cache key creation fails with empty string."""
        with pytest.raises(ValueError, match="Cache key must be a non-empty string"):
            CacheKey("")
    
    @pytest.mark.unit
    def test_cache_key_invalid_non_string(self):
        """Test cache key creation fails with non-string."""
        with pytest.raises(ValueError, match="Cache key must be a non-empty string"):
            CacheKey(123)


class TestReasoning:
    """Test the Reasoning value object."""
    
    @pytest.mark.unit
    def test_reasoning_creation_valid(self):
        """Test creating valid reasoning."""
        reasoning = Reasoning("This is a good match because...")
        assert reasoning.value == "This is a good match because..."
        assert str(reasoning) == "This is a good match because..."
    
    @pytest.mark.unit
    def test_reasoning_whitespace_trimming(self):
        """Test reasoning whitespace trimming."""
        reasoning = Reasoning("  This has whitespace  ")
        assert reasoning.value == "This has whitespace"
    
    @pytest.mark.unit
    def test_reasoning_empty_check(self):
        """Test reasoning empty check."""
        reasoning = Reasoning("")
        assert reasoning.is_empty
        
        reasoning = Reasoning("   ")
        assert reasoning.is_empty
        
        reasoning = Reasoning("Not empty")
        assert not reasoning.is_empty
    
    @pytest.mark.unit
    def test_reasoning_invalid_non_string(self):
        """Test reasoning creation fails with non-string."""
        with pytest.raises(ValueError, match="Reasoning must be a string"):
            Reasoning(123)


class TestFilePath:
    """Test the FilePath value object."""
    
    @pytest.mark.unit
    def test_file_path_creation_valid(self):
        """Test creating valid file paths."""
        path = FilePath("/path/to/file.txt")
        assert path.value == "/path/to/file.txt"
        assert str(path) == "/path/to/file.txt"
    
    @pytest.mark.unit
    def test_file_path_is_absolute(self):
        """Test file path absolute check."""
        abs_path = FilePath("/path/to/file.txt")
        assert abs_path.is_absolute
        
        rel_path = FilePath("path/to/file.txt")
        assert not rel_path.is_absolute
    
    @pytest.mark.unit
    def test_file_path_invalid_empty(self):
        """Test file path creation fails with empty string."""
        with pytest.raises(ValueError, match="File path must be a non-empty string"):
            FilePath("")
    
    @pytest.mark.unit
    def test_file_path_invalid_non_string(self):
        """Test file path creation fails with non-string."""
        with pytest.raises(ValueError, match="File path must be a non-empty string"):
            FilePath(123)


class TestDirectoryPath:
    """Test the DirectoryPath value object."""
    
    @pytest.mark.unit
    def test_directory_path_creation_valid(self):
        """Test creating valid directory paths."""
        path = DirectoryPath("/path/to/directory")
        assert path.value == "/path/to/directory"
        assert str(path) == "/path/to/directory"
    
    @pytest.mark.unit
    def test_directory_path_join(self):
        """Test directory path joining with filename."""
        dir_path = DirectoryPath("/path/to/directory")
        file_path = dir_path.join("file.txt")
        
        assert isinstance(file_path, FilePath)
        assert file_path.value == "/path/to/directory/file.txt"
    
    @pytest.mark.unit
    def test_directory_path_join_with_slashes(self):
        """Test directory path joining handles slashes correctly."""
        dir_path = DirectoryPath("/path/to/directory/")
        file_path = dir_path.join("/file.txt")
        
        assert file_path.value == "/path/to/directory/file.txt"
    
    @pytest.mark.unit
    def test_directory_path_invalid_empty(self):
        """Test directory path creation fails with empty string."""
        with pytest.raises(ValueError, match="Directory path must be a non-empty string"):
            DirectoryPath("")
    
    @pytest.mark.unit
    def test_directory_path_invalid_non_string(self):
        """Test directory path creation fails with non-string."""
        with pytest.raises(ValueError, match="Directory path must be a non-empty string"):
            DirectoryPath(123)
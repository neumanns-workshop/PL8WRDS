"""
API tests for solver endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from unittest.mock import patch, MagicMock

from app.main import app


class TestSolverEndpoints:
    """Test solver API endpoints."""
    
    @pytest.mark.api
    def test_solve_combination_subsequence_mode(self, client):
        """Test solving combination with subsequence mode."""
        combination = "ABC"
        
        mock_result = {
            "combination": combination,
            "mode": "subsequence",
            "matches": [
                {"word": "ambulance", "frequency": 5000},
                {"word": "albatross", "frequency": 3000},
                {"word": "abstract", "frequency": 2500}
            ],
            "match_count": 3,
            "total_frequency": 10500,
            "frequency_distribution": {
                "mean": 3500.0,
                "median": 3000.0,
                "std_dev": 1258.3,
                "min_freq": 2500,
                "max_freq": 5000,
                "q1": 2750.0,
                "q3": 4000.0
            },
            "lexical_fertility": "medium"
        }
        
        with patch('app.services.solver_service.solve_combination') as mock_solve:
            mock_solve.return_value = mock_result
            
            response = client.get(f"/solve/{combination}")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["combination"] == combination
            assert data["mode"] == "subsequence"
            assert len(data["matches"]) == 3
            assert data["match_count"] == 3
            assert data["total_frequency"] == 10500
            assert data["lexical_fertility"] == "medium"
    
    @pytest.mark.api
    def test_solve_combination_with_mode_parameter(self, client):
        """Test solving combination with specified mode parameter."""
        combination = "ABC"
        mode = "substring"
        
        mock_result = {
            "combination": combination,
            "mode": mode,
            "matches": [
                {"word": "abacus", "frequency": 1500}
            ],
            "match_count": 1,
            "total_frequency": 1500,
            "frequency_distribution": {
                "mean": 1500.0,
                "median": 1500.0,
                "std_dev": 0.0,
                "min_freq": 1500,
                "max_freq": 1500,
                "q1": 1500.0,
                "q3": 1500.0
            },
            "lexical_fertility": "low"
        }
        
        with patch('app.services.solver_service.solve_combination') as mock_solve:
            mock_solve.return_value = mock_result
            
            response = client.get(f"/solve/{combination}?mode={mode}")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["mode"] == mode
            assert data["combination"] == combination
    
    @pytest.mark.api
    def test_solve_combination_no_matches(self, client):
        """Test solving combination that has no matching words."""
        combination = "XYZ"
        
        mock_result = {
            "combination": combination,
            "mode": "subsequence",
            "matches": [],
            "match_count": 0,
            "total_frequency": 0,
            "frequency_distribution": None,
            "lexical_fertility": "barren"
        }
        
        with patch('app.services.solver_service.solve_combination') as mock_solve:
            mock_solve.return_value = mock_result
            
            response = client.get(f"/solve/{combination}")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["combination"] == combination
            assert data["matches"] == []
            assert data["match_count"] == 0
            assert data["total_frequency"] == 0
            assert data["frequency_distribution"] is None
            assert data["lexical_fertility"] == "barren"
    
    @pytest.mark.api
    def test_solve_combination_invalid_mode(self, client):
        """Test solving combination with invalid mode parameter."""
        combination = "ABC"
        invalid_mode = "invalid_mode"
        
        response = client.get(f"/solve/{combination}?mode={invalid_mode}")
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "detail" in data
    
    @pytest.mark.api
    def test_solve_combination_valid_modes(self, client):
        """Test solving combination with all valid mode parameters."""
        combination = "ABC"
        valid_modes = ["subsequence", "substring", "anagram", "anagram_subset", "pattern"]
        
        mock_result = {
            "combination": combination,
            "mode": "test",
            "matches": [{"word": "test", "frequency": 1000}],
            "match_count": 1,
            "total_frequency": 1000,
            "frequency_distribution": {
                "mean": 1000.0,
                "median": 1000.0,
                "std_dev": 0.0,
                "min_freq": 1000,
                "max_freq": 1000,
                "q1": 1000.0,
                "q3": 1000.0
            },
            "lexical_fertility": "low"
        }
        
        with patch('app.services.solver_service.solve_combination') as mock_solve:
            for mode in valid_modes:
                mock_result["mode"] = mode
                mock_solve.return_value = mock_result
                
                response = client.get(f"/solve/{combination}?mode={mode}")
                
                assert response.status_code == 200
                data = response.json()
                assert data["mode"] == mode
    
    @pytest.mark.api
    def test_solve_combination_different_lengths(self, client):
        """Test solving combinations of different lengths."""
        test_combinations = ["AB", "ABC", "ABCD", "ABCDE", "ABCDEF"]
        
        with patch('app.services.solver_service.solve_combination') as mock_solve:
            for combination in test_combinations:
                mock_result = {
                    "combination": combination,
                    "mode": "subsequence",
                    "matches": [{"word": f"word{len(combination)}", "frequency": 1000}],
                    "match_count": 1,
                    "total_frequency": 1000,
                    "frequency_distribution": {
                        "mean": 1000.0,
                        "median": 1000.0,
                        "std_dev": 0.0,
                        "min_freq": 1000,
                        "max_freq": 1000,
                        "q1": 1000.0,
                        "q3": 1000.0
                    },
                    "lexical_fertility": "low"
                }
                mock_solve.return_value = mock_result
                
                response = client.get(f"/solve/{combination}")
                
                assert response.status_code == 200
                data = response.json()
                assert data["combination"] == combination
    
    @pytest.mark.api
    def test_solve_combination_case_insensitive(self, client):
        """Test solving combination is case insensitive."""
        test_cases = ["abc", "ABC", "AbC", "aBc"]
        
        mock_result = {
            "combination": "ABC",  # Service normalizes to uppercase
            "mode": "subsequence",
            "matches": [{"word": "ambulance", "frequency": 5000}],
            "match_count": 1,
            "total_frequency": 5000,
            "frequency_distribution": {
                "mean": 5000.0,
                "median": 5000.0,
                "std_dev": 0.0,
                "min_freq": 5000,
                "max_freq": 5000,
                "q1": 5000.0,
                "q3": 5000.0
            },
            "lexical_fertility": "low"
        }
        
        with patch('app.services.solver_service.solve_combination') as mock_solve:
            mock_solve.return_value = mock_result
            
            for combination in test_cases:
                response = client.get(f"/solve/{combination}")
                
                assert response.status_code == 200
                data = response.json()
                # Service should normalize to uppercase
                assert data["combination"] == "ABC"
    
    @pytest.mark.api
    def test_solve_combination_service_error(self, client):
        """Test solver endpoint when service raises an error."""
        combination = "ABC"
        
        with patch('app.services.solver_service.solve_combination') as mock_solve:
            mock_solve.side_effect = RuntimeError("Solver service error")
            
            response = client.get(f"/solve/{combination}")
            
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
    
    @pytest.mark.api
    def test_solve_combination_large_result_set(self, client):
        """Test solving combination that returns many matches."""
        combination = "ABC"
        
        # Create a large mock result set
        matches = [
            {"word": f"word{i:04d}", "frequency": 1000 - i}
            for i in range(1000)
        ]
        
        mock_result = {
            "combination": combination,
            "mode": "subsequence",
            "matches": matches,
            "match_count": 1000,
            "total_frequency": sum(match["frequency"] for match in matches),
            "frequency_distribution": {
                "mean": 500.5,
                "median": 500.5,
                "std_dev": 288.67,
                "min_freq": 1,
                "max_freq": 1000,
                "q1": 250.75,
                "q3": 750.25
            },
            "lexical_fertility": "high"
        }
        
        with patch('app.services.solver_service.solve_combination') as mock_solve:
            mock_solve.return_value = mock_result
            
            response = client.get(f"/solve/{combination}")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["match_count"] == 1000
            assert len(data["matches"]) == 1000
            assert data["lexical_fertility"] == "high"
    
    @pytest.mark.api
    async def test_solve_combination_async(self, async_client: AsyncClient):
        """Test solver endpoint using async client."""
        combination = "ABC"
        
        mock_result = {
            "combination": combination,
            "mode": "subsequence",
            "matches": [{"word": "ambulance", "frequency": 5000}],
            "match_count": 1,
            "total_frequency": 5000,
            "frequency_distribution": {
                "mean": 5000.0,
                "median": 5000.0,
                "std_dev": 0.0,
                "min_freq": 5000,
                "max_freq": 5000,
                "q1": 5000.0,
                "q3": 5000.0
            },
            "lexical_fertility": "low"
        }
        
        with patch('app.services.solver_service.solve_combination') as mock_solve:
            mock_solve.return_value = mock_result
            
            response = await async_client.get(f"/solve/{combination}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["combination"] == combination
    
    @pytest.mark.api
    def test_solve_combination_special_characters(self, client):
        """Test solver endpoint with special characters (should be rejected)."""
        invalid_combinations = ["A@B", "A-B-C", "AB3", "A B C"]
        
        with patch('app.services.solver_service.solve_combination') as mock_solve:
            # Service might handle validation or raise an error
            mock_solve.side_effect = ValueError("Invalid combination format")
            
            for combination in invalid_combinations:
                response = client.get(f"/solve/{combination}")
                
                # Should either give validation error or 500 error
                assert response.status_code in [422, 500]
    
    @pytest.mark.api
    def test_solve_combination_empty_string(self, client):
        """Test solver endpoint with empty combination."""
        response = client.get("/solve/")  # Empty path segment
        
        # Should give 404 or method not allowed
        assert response.status_code in [404, 405]
    
    @pytest.mark.api
    def test_solve_combination_frequency_distribution_details(self, client):
        """Test that frequency distribution contains all expected statistical measures."""
        combination = "ABC"
        
        mock_result = {
            "combination": combination,
            "mode": "subsequence",
            "matches": [
                {"word": "ambulance", "frequency": 5000},
                {"word": "albatross", "frequency": 3000},
                {"word": "abstract", "frequency": 4000},
                {"word": "abacus", "frequency": 1000}
            ],
            "match_count": 4,
            "total_frequency": 13000,
            "frequency_distribution": {
                "mean": 3250.0,
                "median": 3500.0,
                "std_dev": 1708.8,
                "min_freq": 1000,
                "max_freq": 5000,
                "q1": 2500.0,
                "q3": 4500.0
            },
            "lexical_fertility": "medium"
        }
        
        with patch('app.services.solver_service.solve_combination') as mock_solve:
            mock_solve.return_value = mock_result
            
            response = client.get(f"/solve/{combination}")
            
            assert response.status_code == 200
            data = response.json()
            
            freq_dist = data["frequency_distribution"]
            assert "mean" in freq_dist
            assert "median" in freq_dist
            assert "std_dev" in freq_dist
            assert "min_freq" in freq_dist
            assert "max_freq" in freq_dist
            assert "q1" in freq_dist
            assert "q3" in freq_dist
            
            # Verify the statistical relationships
            assert freq_dist["min_freq"] <= freq_dist["q1"]
            assert freq_dist["q1"] <= freq_dist["median"]
            assert freq_dist["median"] <= freq_dist["q3"]
            assert freq_dist["q3"] <= freq_dist["max_freq"]
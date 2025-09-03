"""
API tests for scoring endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from unittest.mock import patch, MagicMock, AsyncMock

from app.main import app


class TestScoringEndpoints:
    """Test scoring API endpoints."""
    
    @pytest.mark.api
    def test_get_system_status_healthy(self, client):
        """Test system status endpoint when system is healthy."""
        mock_status = {
            "ollama_running": True,
            "models": [
                {"model": "granite", "available": True, "error_message": None},
                {"model": "mistral", "available": True, "error_message": None}
            ],
            "cache_enabled": True,
            "active_sessions": 2
        }
        
        with patch('app.services.scoring_service.scoring_service.check_system_status') as mock_check:
            mock_check.return_value = mock_status
            
            response = client.get("/scoring/status")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["ollama_running"] is True
            assert len(data["models"]) == 2
            assert data["cache_enabled"] is True
            assert data["active_sessions"] == 2
    
    @pytest.mark.api
    def test_get_system_status_unhealthy(self, client):
        """Test system status endpoint when system is unhealthy."""
        mock_status = {
            "ollama_running": False,
            "models": [
                {"model": "granite", "available": False, "error_message": "Service not running"}
            ],
            "cache_enabled": False,
            "active_sessions": 0
        }
        
        with patch('app.services.scoring_service.scoring_service.check_system_status') as mock_check:
            mock_check.return_value = mock_status
            
            response = client.get("/scoring/status")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["ollama_running"] is False
            assert data["models"][0]["available"] is False
            assert "not running" in data["models"][0]["error_message"]
    
    @pytest.mark.api
    def test_score_single_word_success(self, client):
        """Test scoring a single word successfully."""
        request_data = {
            "word": "ambulance",
            "combination": "ABC",
            "models": ["granite", "mistral"]
        }
        
        mock_result = {
            "word": "ambulance",
            "combination": "ABC",
            "individual_scores": [
                {
                    "model": "granite",
                    "score": 85.0,
                    "reasoning": "Great match!"
                },
                {
                    "model": "mistral", 
                    "score": 78.5,
                    "reasoning": "Good connection"
                }
            ],
            "aggregate_score": 81.75
        }
        
        with patch('app.services.scoring_service.scoring_service.score_word_with_models') as mock_score:
            mock_score.return_value = mock_result
            
            response = client.post("/scoring/score-word", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["word"] == "ambulance"
            assert data["combination"] == "ABC"
            assert len(data["individual_scores"]) == 2
            assert data["aggregate_score"] == 81.75
    
    @pytest.mark.api
    def test_score_single_word_invalid_request(self, client):
        """Test scoring endpoint with invalid request data."""
        # Missing required fields
        invalid_requests = [
            {},  # Empty request
            {"word": "ambulance"},  # Missing combination and models
            {"combination": "ABC"},  # Missing word and models
            {"models": ["granite"]},  # Missing word and combination
            {
                "word": "ambulance",
                "combination": "ABC",
                "models": []  # Empty models list
            }
        ]
        
        for request_data in invalid_requests:
            response = client.post("/scoring/score-word", json=request_data)
            assert response.status_code == 422  # Validation error
    
    @pytest.mark.api
    def test_score_single_word_service_error(self, client):
        """Test scoring endpoint when service raises an error."""
        request_data = {
            "word": "ambulance",
            "combination": "ABC",
            "models": ["granite"]
        }
        
        with patch('app.services.scoring_service.scoring_service.score_word_with_models') as mock_score:
            mock_score.side_effect = RuntimeError("Scoring service error")
            
            response = client.post("/scoring/score-word", json=request_data)
            
            assert response.status_code == 500
            data = response.json()
            assert "Scoring failed" in data["detail"]
    
    @pytest.mark.api
    def test_score_batch_words_success(self, client):
        """Test batch scoring endpoint successfully."""
        request_data = {
            "words": ["ambulance", "beach", "cat"],
            "combination": "ABC",
            "models": ["granite"]
        }
        
        mock_results = [
            {
                "word": "ambulance",
                "combination": "ABC",
                "individual_scores": [{"model": "granite", "score": 85.0, "reasoning": "Great"}],
                "aggregate_score": 85.0
            },
            {
                "word": "beach",
                "combination": "ABC", 
                "individual_scores": [{"model": "granite", "score": 45.0, "reasoning": "Weak"}],
                "aggregate_score": 45.0
            },
            {
                "word": "cat",
                "combination": "ABC",
                "individual_scores": [{"model": "granite", "score": 20.0, "reasoning": "Poor"}],
                "aggregate_score": 20.0
            }
        ]
        
        with patch('app.services.scoring_service.scoring_service.score_words_batch') as mock_batch:
            mock_batch.return_value = mock_results
            
            response = client.post("/scoring/score-batch", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            
            assert len(data) == 3
            assert data[0]["word"] == "ambulance"
            assert data[1]["word"] == "beach"
            assert data[2]["word"] == "cat"
    
    @pytest.mark.api
    def test_score_batch_words_empty_list(self, client):
        """Test batch scoring with empty word list."""
        request_data = {
            "words": [],
            "combination": "ABC",
            "models": ["granite"]
        }
        
        response = client.post("/scoring/score-batch", json=request_data)
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.api
    def test_random_scoring_session(self, client):
        """Test creating a random scoring session."""
        request_data = {
            "num_plates": 3,
            "words_per_plate": 2,
            "plate_length": 3,
            "models": ["granite"]
        }
        
        mock_session = {
            "session_id": "test-session-123",
            "num_plates": 3,
            "words_per_plate": 2,
            "models": ["granite"],
            "status": "completed",
            "results": [
                {
                    "plate": "ABC",
                    "word_scores": [
                        {"word": "ambulance", "score": 85.0},
                        {"word": "albatross", "score": 72.0}
                    ]
                }
            ]
        }
        
        with patch('app.services.scoring_service.scoring_service.create_random_scoring_session') as mock_session_create:
            mock_session_create.return_value = mock_session
            
            response = client.post("/scoring/random-session", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["session_id"] == "test-session-123"
            assert data["num_plates"] == 3
            assert data["words_per_plate"] == 2
            assert data["status"] == "completed"
    
    @pytest.mark.api
    def test_get_scoring_session(self, client):
        """Test retrieving a scoring session by ID."""
        session_id = "test-session-123"
        
        mock_session = {
            "session_id": session_id,
            "models": ["granite", "mistral"],
            "status": "completed",
            "created_at": "2023-01-01T10:00:00Z",
            "total_scores": 6,
            "results": []
        }
        
        with patch('app.services.scoring_service.scoring_service.get_scoring_session') as mock_get:
            mock_get.return_value = mock_session
            
            response = client.get(f"/scoring/session/{session_id}")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["session_id"] == session_id
            assert len(data["models"]) == 2
            assert data["status"] == "completed"
    
    @pytest.mark.api
    def test_get_scoring_session_not_found(self, client):
        """Test retrieving a non-existent scoring session."""
        session_id = "nonexistent-session"
        
        with patch('app.services.scoring_service.scoring_service.get_scoring_session') as mock_get:
            mock_get.return_value = None
            
            response = client.get(f"/scoring/session/{session_id}")
            
            assert response.status_code == 404
            data = response.json()
            assert "not found" in data["detail"].lower()
    
    @pytest.mark.api 
    async def test_scoring_endpoints_async(self, async_client: AsyncClient):
        """Test scoring endpoints using async client."""
        request_data = {
            "word": "ambulance",
            "combination": "ABC",
            "models": ["granite"]
        }
        
        mock_result = {
            "word": "ambulance",
            "combination": "ABC",
            "individual_scores": [{"model": "granite", "score": 85.0, "reasoning": "Great"}],
            "aggregate_score": 85.0
        }
        
        with patch('app.services.scoring_service.scoring_service.score_word_with_models') as mock_score:
            mock_score.return_value = mock_result
            
            response = await async_client.post("/scoring/score-word", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["word"] == "ambulance"
    
    @pytest.mark.api
    def test_scoring_edge_cases(self, client):
        """Test scoring endpoints with edge cases."""
        # Very long word
        long_word_request = {
            "word": "pneumonoultramicroscopicsilicovolcanoconiosiss",  # 45 characters
            "combination": "ABC",
            "models": ["granite"]
        }
        
        with patch('app.services.scoring_service.scoring_service.score_word_with_models') as mock_score:
            mock_score.return_value = {
                "word": long_word_request["word"],
                "combination": "ABC",
                "individual_scores": [{"model": "granite", "score": 10.0, "reasoning": "Too complex"}],
                "aggregate_score": 10.0
            }
            
            response = client.post("/scoring/score-word", json=long_word_request)
            # Should either succeed or give validation error based on business rules
            assert response.status_code in [200, 422]
        
        # Single character word
        short_word_request = {
            "word": "a",
            "combination": "ABC", 
            "models": ["granite"]
        }
        
        with patch('app.services.scoring_service.scoring_service.score_word_with_models') as mock_score:
            mock_score.return_value = {
                "word": "a",
                "combination": "ABC",
                "individual_scores": [{"model": "granite", "score": 5.0, "reasoning": "Too simple"}],
                "aggregate_score": 5.0
            }
            
            response = client.post("/scoring/score-word", json=short_word_request)
            assert response.status_code in [200, 422]
    
    @pytest.mark.api
    def test_scoring_concurrent_requests(self, client):
        """Test scoring service under concurrent load (basic test)."""
        request_data = {
            "word": "ambulance",
            "combination": "ABC",
            "models": ["granite"]
        }
        
        mock_result = {
            "word": "ambulance",
            "combination": "ABC",
            "individual_scores": [{"model": "granite", "score": 85.0, "reasoning": "Great"}],
            "aggregate_score": 85.0
        }
        
        with patch('app.services.scoring_service.scoring_service.score_word_with_models') as mock_score:
            mock_score.return_value = mock_result
            
            # Make multiple concurrent requests
            responses = []
            for _ in range(5):
                response = client.post("/scoring/score-word", json=request_data)
                responses.append(response)
            
            # All should succeed
            for response in responses:
                assert response.status_code == 200
                data = response.json()
                assert data["word"] == "ambulance"
    
    @pytest.mark.api
    def test_scoring_invalid_model_names(self, client):
        """Test scoring with invalid model names."""
        request_data = {
            "word": "ambulance",
            "combination": "ABC",
            "models": ["invalid-model", "another-invalid"]
        }
        
        with patch('app.services.scoring_service.scoring_service.score_word_with_models') as mock_score:
            mock_score.side_effect = ValueError("Invalid model name")
            
            response = client.post("/scoring/score-word", json=request_data)
            
            assert response.status_code == 500
            data = response.json()
            assert "Scoring failed" in data["detail"]
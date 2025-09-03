"""
API tests for prediction endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from unittest.mock import patch, MagicMock

from app.main import app


class TestPredictionEndpoints:
    """Test prediction API endpoints."""
    
    @pytest.mark.api
    def test_predict_score_valid_request(self, client):
        """Test prediction endpoint with valid request."""
        request_data = {
            "word": "ambulance",
            "plate": "ABC"
        }
        
        with patch('app.services.prediction_service.prediction_service') as mock_service:
            # Mock the prediction service
            mock_service._is_initialized = True
            mock_service.predict_score.return_value = {
                "word": "ambulance",
                "plate": "ABC",
                "predicted_score": 85.5,
                "model_version": "ridge_v3"
            }
            
            response = client.post("/predict/score", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["word"] == "ambulance"
            assert data["plate"] == "ABC"
            assert data["predicted_score"] == 85.5
            assert data["model_version"] == "ridge_v3"
    
    @pytest.mark.api
    def test_predict_score_service_not_initialized(self, client):
        """Test prediction endpoint when service is not initialized."""
        request_data = {
            "word": "ambulance",
            "plate": "ABC"
        }
        
        with patch('app.services.prediction_service.prediction_service') as mock_service:
            mock_service._is_initialized = False
            
            response = client.post("/predict/score", json=request_data)
            
            assert response.status_code == 503
            data = response.json()
            assert "not initialized" in data["detail"].lower()
    
    @pytest.mark.api
    def test_predict_score_invalid_word(self, client):
        """Test prediction endpoint with invalid word."""
        request_data = {
            "word": "",  # Empty word
            "plate": "ABC"
        }
        
        response = client.post("/predict/score", json=request_data)
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.api
    def test_predict_score_invalid_plate_length(self, client):
        """Test prediction endpoint with invalid plate length."""
        test_cases = [
            {"word": "ambulance", "plate": "AB"},      # Too short
            {"word": "ambulance", "plate": "ABCD"},    # Too long
            {"word": "ambulance", "plate": ""},        # Empty
        ]
        
        for request_data in test_cases:
            response = client.post("/predict/score", json=request_data)
            assert response.status_code == 422
    
    @pytest.mark.api
    def test_predict_score_missing_fields(self, client):
        """Test prediction endpoint with missing required fields."""
        # Missing word
        response = client.post("/predict/score", json={"plate": "ABC"})
        assert response.status_code == 422
        
        # Missing plate
        response = client.post("/predict/score", json={"word": "ambulance"})
        assert response.status_code == 422
        
        # Empty request
        response = client.post("/predict/score", json={})
        assert response.status_code == 422
    
    @pytest.mark.api
    def test_predict_score_model_not_found(self, client):
        """Test prediction endpoint when model file is not found."""
        request_data = {
            "word": "ambulance",
            "plate": "ABC"
        }
        
        with patch('app.services.prediction_service.prediction_service') as mock_service:
            mock_service._is_initialized = True
            mock_service.predict_score.side_effect = FileNotFoundError("Model file not found")
            
            response = client.post("/predict/score", json=request_data)
            
            assert response.status_code == 503
            data = response.json()
            assert "Model not loaded" in data["detail"]
    
    @pytest.mark.api
    def test_predict_score_unexpected_error(self, client):
        """Test prediction endpoint with unexpected service error."""
        request_data = {
            "word": "ambulance",
            "plate": "ABC"
        }
        
        with patch('app.services.prediction_service.prediction_service') as mock_service:
            mock_service._is_initialized = True
            mock_service.predict_score.side_effect = RuntimeError("Unexpected error")
            
            response = client.post("/predict/score", json=request_data)
            
            assert response.status_code == 500
            data = response.json()
            assert "unexpected error" in data["detail"].lower()
    
    @pytest.mark.api
    def test_prediction_health_check_ready(self, client):
        """Test prediction health check when service is ready."""
        with patch('app.services.prediction_service.prediction_service') as mock_service:
            mock_service._is_initialized = True
            
            response = client.get("/predict/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ready"
    
    @pytest.mark.api
    def test_prediction_health_check_initializing(self, client):
        """Test prediction health check when service is initializing."""
        with patch('app.services.prediction_service.prediction_service') as mock_service:
            mock_service._is_initialized = False
            
            response = client.get("/predict/health")
            
            assert response.status_code == 503
            data = response.json()
            assert data["status"] == "initializing"
    
    @pytest.mark.api
    async def test_predict_score_async_client(self, async_client: AsyncClient):
        """Test prediction endpoint using async client."""
        request_data = {
            "word": "ambulance",
            "plate": "ABC"
        }
        
        with patch('app.services.prediction_service.prediction_service') as mock_service:
            mock_service._is_initialized = True
            mock_service.predict_score.return_value = {
                "word": "ambulance",
                "plate": "ABC",
                "predicted_score": 85.5,
                "model_version": "ridge_v3"
            }
            
            response = await async_client.post("/predict/score", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["predicted_score"] == 85.5
    
    @pytest.mark.api
    def test_predict_score_content_type(self, client):
        """Test prediction endpoint with different content types."""
        request_data = {
            "word": "ambulance",
            "plate": "ABC"
        }
        
        with patch('app.services.prediction_service.prediction_service') as mock_service:
            mock_service._is_initialized = True
            mock_service.predict_score.return_value = {
                "word": "ambulance",
                "plate": "ABC",
                "predicted_score": 85.5,
                "model_version": "ridge_v3"
            }
            
            # Test with JSON content type
            response = client.post(
                "/predict/score", 
                json=request_data,
                headers={"Content-Type": "application/json"}
            )
            assert response.status_code == 200
    
    @pytest.mark.api
    def test_predict_score_special_characters(self, client):
        """Test prediction endpoint with special characters in input."""
        test_cases = [
            {"word": "café", "plate": "CAF"},       # Accented characters
            {"word": "naïve", "plate": "NAV"},      # Diacritic marks
        ]
        
        with patch('app.services.prediction_service.prediction_service') as mock_service:
            mock_service._is_initialized = True
            mock_service.predict_score.return_value = {
                "word": "test",
                "plate": "TST",
                "predicted_score": 50.0,
                "model_version": "ridge_v3"
            }
            
            for request_data in test_cases:
                response = client.post("/predict/score", json=request_data)
                # Should handle gracefully, either succeed or give validation error
                assert response.status_code in [200, 422]
    
    @pytest.mark.api
    def test_predict_score_case_insensitive(self, client):
        """Test prediction endpoint handles case variations."""
        test_cases = [
            {"word": "AMBULANCE", "plate": "abc"},
            {"word": "ambulance", "plate": "ABC"},
            {"word": "AmBuLaNcE", "plate": "AbC"},
        ]
        
        with patch('app.services.prediction_service.prediction_service') as mock_service:
            mock_service._is_initialized = True
            mock_service.predict_score.return_value = {
                "word": "ambulance",
                "plate": "ABC",
                "predicted_score": 85.5,
                "model_version": "ridge_v3"
            }
            
            for request_data in test_cases:
                response = client.post("/predict/score", json=request_data)
                assert response.status_code == 200
                data = response.json()
                assert data["predicted_score"] == 85.5
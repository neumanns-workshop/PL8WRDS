"""
End-to-end tests for complete word scoring user journeys.
"""

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from unittest.mock import patch, MagicMock

from app.main import app


class TestWordScoringJourney:
    """Test complete word scoring user journeys."""
    
    @pytest.mark.e2e
    def test_complete_word_scoring_workflow(self, client):
        """Test the complete workflow: check status -> find words -> score word -> predict."""
        
        # Step 1: Check system status
        mock_status = {
            "ollama_running": True,
            "models": [
                {"model": "granite", "available": True, "error_message": None}
            ],
            "cache_enabled": True,
            "active_sessions": 0
        }
        
        with patch('app.services.scoring_service.scoring_service.check_system_status') as mock_check:
            mock_check.return_value = mock_status
            
            status_response = client.get("/scoring/status")
            assert status_response.status_code == 200
            
            status_data = status_response.json()
            assert status_data["ollama_running"] is True
            available_models = [m["model"] for m in status_data["models"] if m["available"]]
            assert "granite" in available_models
        
        # Step 2: Find words for a plate combination
        combination = "ABC"
        mock_solver_result = {
            "combination": combination,
            "mode": "subsequence",
            "matches": [
                {"word": "ambulance", "frequency": 5000},
                {"word": "albatross", "frequency": 3000}
            ],
            "match_count": 2,
            "total_frequency": 8000,
            "frequency_distribution": {
                "mean": 4000.0,
                "median": 4000.0,
                "std_dev": 1000.0,
                "min_freq": 3000,
                "max_freq": 5000,
                "q1": 3500.0,
                "q3": 4500.0
            },
            "lexical_fertility": "medium"
        }
        
        with patch('app.services.solver_service.solve_combination') as mock_solve:
            mock_solve.return_value = mock_solver_result
            
            solver_response = client.get(f"/solve/{combination}")
            assert solver_response.status_code == 200
            
            solver_data = solver_response.json()
            assert len(solver_data["matches"]) >= 1
            
            # Pick the first word for scoring
            selected_word = solver_data["matches"][0]["word"]
        
        # Step 3: Score the selected word using LLM models
        score_request = {
            "word": selected_word,
            "combination": combination,
            "models": ["granite"]
        }
        
        mock_score_result = {
            "word": selected_word,
            "combination": combination,
            "individual_scores": [
                {
                    "model": "granite",
                    "score": 85.0,
                    "reasoning": f"The word '{selected_word}' excellently represents the combination '{combination}' with high creativity and satisfaction."
                }
            ],
            "aggregate_score": 85.0
        }
        
        with patch('app.services.scoring_service.scoring_service.score_word_with_models') as mock_score_word:
            mock_score_word.return_value = mock_score_result
            
            score_response = client.post("/scoring/score-word", json=score_request)
            assert score_response.status_code == 200
            
            score_data = score_response.json()
            assert score_data["word"] == selected_word
            assert score_data["combination"] == combination
            assert score_data["aggregate_score"] > 0
        
        # Step 4: Get ML model prediction for comparison
        predict_request = {
            "word": selected_word,
            "plate": combination
        }
        
        mock_predict_result = {
            "word": selected_word,
            "plate": combination,
            "predicted_score": 82.5,
            "model_version": "ridge_v3"
        }
        
        with patch('app.services.prediction_service.prediction_service') as mock_prediction_service:
            mock_prediction_service._is_initialized = True
            mock_prediction_service.predict_score.return_value = mock_predict_result
            
            predict_response = client.post("/predict/score", json=predict_request)
            assert predict_response.status_code == 200
            
            predict_data = predict_response.json()
            assert predict_data["word"] == selected_word
            assert predict_data["predicted_score"] > 0
        
        # Verify the complete workflow produced consistent results
        llm_score = score_data["aggregate_score"]
        ml_score = predict_data["predicted_score"]
        
        # Scores should be reasonably close (within 50 points for this test)
        score_difference = abs(llm_score - ml_score)
        assert score_difference < 50, f"LLM score ({llm_score}) and ML score ({ml_score}) too different"
    
    @pytest.mark.e2e
    def test_batch_scoring_workflow(self, client):
        """Test batch scoring workflow for multiple words."""
        
        combination = "ABC"
        
        # Step 1: Find multiple words
        mock_solver_result = {
            "combination": combination,
            "mode": "subsequence",
            "matches": [
                {"word": "ambulance", "frequency": 5000},
                {"word": "albatross", "frequency": 3000},
                {"word": "abstract", "frequency": 4000}
            ],
            "match_count": 3,
            "total_frequency": 12000,
            "frequency_distribution": {
                "mean": 4000.0,
                "median": 4000.0,
                "std_dev": 1000.0,
                "min_freq": 3000,
                "max_freq": 5000,
                "q1": 3500.0,
                "q3": 4500.0
            },
            "lexical_fertility": "medium"
        }
        
        with patch('app.services.solver_service.solve_combination') as mock_solve:
            mock_solve.return_value = mock_solver_result
            
            solver_response = client.get(f"/solve/{combination}")
            assert solver_response.status_code == 200
            
            solver_data = solver_response.json()
            words_to_score = [match["word"] for match in solver_data["matches"]]
        
        # Step 2: Batch score all found words
        batch_request = {
            "words": words_to_score,
            "combination": combination,
            "models": ["granite"]
        }
        
        mock_batch_results = [
            {
                "word": word,
                "combination": combination,
                "individual_scores": [
                    {
                        "model": "granite",
                        "score": 80.0 + i * 5,  # Vary scores
                        "reasoning": f"Good match for {word}"
                    }
                ],
                "aggregate_score": 80.0 + i * 5
            }
            for i, word in enumerate(words_to_score)
        ]
        
        with patch('app.services.scoring_service.scoring_service.score_words_batch') as mock_batch:
            mock_batch.return_value = mock_batch_results
            
            batch_response = client.post("/scoring/score-batch", json=batch_request)
            assert batch_response.status_code == 200
            
            batch_data = batch_response.json()
            assert len(batch_data) == len(words_to_score)
            
            # Verify all words were scored
            scored_words = [result["word"] for result in batch_data]
            assert set(scored_words) == set(words_to_score)
            
            # Verify scores are reasonable
            for result in batch_data:
                assert 0 <= result["aggregate_score"] <= 100
    
    @pytest.mark.e2e
    def test_random_scoring_session_workflow(self, client):
        """Test creating and managing a random scoring session."""
        
        # Step 1: Create a random scoring session
        session_request = {
            "num_plates": 2,
            "words_per_plate": 3,
            "plate_length": 3,
            "models": ["granite"]
        }
        
        mock_session_result = {
            "session_id": "session-12345",
            "num_plates": 2,
            "words_per_plate": 3,
            "models": ["granite"],
            "status": "completed",
            "created_at": "2023-01-01T10:00:00Z",
            "total_scores": 6,
            "results": [
                {
                    "plate": "ABC",
                    "word_scores": [
                        {"word": "ambulance", "score": 85.0},
                        {"word": "albatross", "score": 75.0},
                        {"word": "abstract", "score": 70.0}
                    ]
                },
                {
                    "plate": "DEF",
                    "word_scores": [
                        {"word": "defeat", "score": 80.0},
                        {"word": "defend", "score": 78.0},
                        {"word": "define", "score": 76.0}
                    ]
                }
            ]
        }
        
        with patch('app.services.scoring_service.scoring_service.create_random_scoring_session') as mock_create:
            mock_create.return_value = mock_session_result
            
            session_response = client.post("/scoring/random-session", json=session_request)
            assert session_response.status_code == 200
            
            session_data = session_response.json()
            session_id = session_data["session_id"]
            assert session_data["status"] == "completed"
            assert session_data["total_scores"] == 6
        
        # Step 2: Retrieve the session
        with patch('app.services.scoring_service.scoring_service.get_scoring_session') as mock_get:
            mock_get.return_value = mock_session_result
            
            get_response = client.get(f"/scoring/session/{session_id}")
            assert get_response.status_code == 200
            
            retrieved_data = get_response.json()
            assert retrieved_data["session_id"] == session_id
            assert retrieved_data["status"] == "completed"
    
    @pytest.mark.e2e
    def test_error_recovery_workflow(self, client):
        """Test error handling and recovery in the workflow."""
        
        combination = "ABC"
        
        # Step 1: Start with system status check that shows issues
        mock_unhealthy_status = {
            "ollama_running": False,
            "models": [
                {"model": "granite", "available": False, "error_message": "Service not running"}
            ],
            "cache_enabled": False,
            "active_sessions": 0
        }
        
        with patch('app.services.scoring_service.scoring_service.check_system_status') as mock_check:
            mock_check.return_value = mock_unhealthy_status
            
            status_response = client.get("/scoring/status")
            assert status_response.status_code == 200
            
            status_data = status_response.json()
            assert status_data["ollama_running"] is False
        
        # Step 2: Try to score a word when system is unhealthy
        score_request = {
            "word": "ambulance",
            "combination": combination,
            "models": ["granite"]
        }
        
        with patch('app.services.scoring_service.scoring_service.score_word_with_models') as mock_score:
            # Service should fail due to unhealthy system
            mock_score.side_effect = RuntimeError("Ollama service not available")
            
            score_response = client.post("/scoring/score-word", json=score_request)
            assert score_response.status_code == 500
        
        # Step 3: Fall back to ML prediction when LLM scoring fails
        predict_request = {
            "word": "ambulance",
            "plate": combination
        }
        
        mock_predict_result = {
            "word": "ambulance",
            "plate": combination,
            "predicted_score": 75.0,
            "model_version": "ridge_v3"
        }
        
        with patch('app.services.prediction_service.prediction_service') as mock_prediction_service:
            mock_prediction_service._is_initialized = True
            mock_prediction_service.predict_score.return_value = mock_predict_result
            
            predict_response = client.post("/predict/score", json=predict_request)
            assert predict_response.status_code == 200
            
            # Should still get a prediction even when LLM scoring fails
            predict_data = predict_response.json()
            assert predict_data["predicted_score"] == 75.0
    
    @pytest.mark.e2e
    async def test_async_workflow(self, async_client: AsyncClient):
        """Test complete workflow using async client."""
        
        combination = "ABC"
        
        # Step 1: Check status
        mock_status = {
            "ollama_running": True,
            "models": [
                {"model": "granite", "available": True, "error_message": None}
            ],
            "cache_enabled": True,
            "active_sessions": 0
        }
        
        with patch('app.services.scoring_service.scoring_service.check_system_status') as mock_check:
            mock_check.return_value = mock_status
            
            status_response = await async_client.get("/scoring/status")
            assert status_response.status_code == 200
        
        # Step 2: Find words
        mock_solver_result = {
            "combination": combination,
            "mode": "subsequence",
            "matches": [
                {"word": "ambulance", "frequency": 5000}
            ],
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
            mock_solve.return_value = mock_solver_result
            
            solver_response = await async_client.get(f"/solve/{combination}")
            assert solver_response.status_code == 200
        
        # Step 3: Score word
        score_request = {
            "word": "ambulance",
            "combination": combination,
            "models": ["granite"]
        }
        
        mock_score_result = {
            "word": "ambulance",
            "combination": combination,
            "individual_scores": [
                {
                    "model": "granite",
                    "score": 85.0,
                    "reasoning": "Great match!"
                }
            ],
            "aggregate_score": 85.0
        }
        
        with patch('app.services.scoring_service.scoring_service.score_word_with_models') as mock_score_word:
            mock_score_word.return_value = mock_score_result
            
            score_response = await async_client.post("/scoring/score-word", json=score_request)
            assert score_response.status_code == 200
        
        # Step 4: Get prediction
        predict_request = {
            "word": "ambulance",
            "plate": combination
        }
        
        mock_predict_result = {
            "word": "ambulance",
            "plate": combination,
            "predicted_score": 82.5,
            "model_version": "ridge_v3"
        }
        
        with patch('app.services.prediction_service.prediction_service') as mock_prediction_service:
            mock_prediction_service._is_initialized = True
            mock_prediction_service.predict_score.return_value = mock_predict_result
            
            predict_response = await async_client.post("/predict/score", json=predict_request)
            assert predict_response.status_code == 200
    
    @pytest.mark.e2e
    def test_cross_endpoint_data_consistency(self, client):
        """Test that data is consistent across different endpoints."""
        
        combination = "ABC"
        word = "ambulance"
        
        # Get the word from solver
        mock_solver_result = {
            "combination": combination,
            "mode": "subsequence",
            "matches": [
                {"word": word, "frequency": 5000}
            ],
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
            mock_solve.return_value = mock_solver_result
            
            solver_response = client.get(f"/solve/{combination}")
            solver_data = solver_response.json()
            
            found_word = solver_data["matches"][0]["word"]
            found_frequency = solver_data["matches"][0]["frequency"]
        
        # Score the same word
        score_request = {
            "word": found_word,
            "combination": combination,
            "models": ["granite"]
        }
        
        mock_score_result = {
            "word": found_word,
            "combination": combination,
            "individual_scores": [
                {
                    "model": "granite",
                    "score": 85.0,
                    "reasoning": "Great match!"
                }
            ],
            "aggregate_score": 85.0
        }
        
        with patch('app.services.scoring_service.scoring_service.score_word_with_models') as mock_score_word:
            mock_score_word.return_value = mock_score_result
            
            score_response = client.post("/scoring/score-word", json=score_request)
            score_data = score_response.json()
            
            scored_word = score_data["word"]
            scored_combination = score_data["combination"]
        
        # Predict score for the same word
        predict_request = {
            "word": found_word,
            "plate": combination
        }
        
        mock_predict_result = {
            "word": found_word,
            "plate": combination,
            "predicted_score": 82.5,
            "model_version": "ridge_v3"
        }
        
        with patch('app.services.prediction_service.prediction_service') as mock_prediction_service:
            mock_prediction_service._is_initialized = True
            mock_prediction_service.predict_score.return_value = mock_predict_result
            
            predict_response = client.post("/predict/score", json=predict_request)
            predict_data = predict_response.json()
            
            predicted_word = predict_data["word"]
            predicted_plate = predict_data["plate"]
        
        # Verify consistency across all endpoints
        assert found_word == scored_word == predicted_word == word
        assert combination == scored_combination == predicted_plate
"""
Performance tests for API endpoints.
"""

import pytest
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app


class TestAPIPerformance:
    """Test API endpoint performance."""
    
    @pytest.mark.performance
    @pytest.mark.benchmark
    def test_prediction_endpoint_response_time(self, client, benchmark):
        """Benchmark prediction endpoint response time."""
        
        request_data = {
            "word": "ambulance",
            "plate": "ABC"
        }
        
        mock_result = {
            "word": "ambulance",
            "plate": "ABC",
            "predicted_score": 85.5,
            "model_version": "ridge_v3"
        }
        
        def make_prediction_request():
            with patch('app.services.prediction_service.prediction_service') as mock_service:
                mock_service._is_initialized = True
                mock_service.predict_score.return_value = mock_result
                
                response = client.post("/predict/score", json=request_data)
                assert response.status_code == 200
                return response.json()
        
        # Benchmark the request
        result = benchmark(make_prediction_request)
        assert result["predicted_score"] == 85.5
    
    @pytest.mark.performance
    @pytest.mark.benchmark
    def test_solver_endpoint_response_time(self, client, benchmark):
        """Benchmark solver endpoint response time."""
        
        combination = "ABC"
        mock_result = {
            "combination": combination,
            "mode": "subsequence",
            "matches": [
                {"word": f"word{i}", "frequency": 1000 - i}
                for i in range(100)  # 100 matches
            ],
            "match_count": 100,
            "total_frequency": 95050,
            "frequency_distribution": {
                "mean": 950.5,
                "median": 950.5,
                "std_dev": 29.0,
                "min_freq": 901,
                "max_freq": 1000,
                "q1": 925.75,
                "q3": 975.25
            },
            "lexical_fertility": "high"
        }
        
        def make_solver_request():
            with patch('app.services.solver_service.solve_combination') as mock_solve:
                mock_solve.return_value = mock_result
                
                response = client.get(f"/solve/{combination}")
                assert response.status_code == 200
                return response.json()
        
        result = benchmark(make_solver_request)
        assert result["match_count"] == 100
    
    @pytest.mark.performance
    @pytest.mark.benchmark
    def test_scoring_endpoint_response_time(self, client, benchmark):
        """Benchmark scoring endpoint response time."""
        
        request_data = {
            "word": "ambulance",
            "combination": "ABC",
            "models": ["granite"]
        }
        
        mock_result = {
            "word": "ambulance",
            "combination": "ABC",
            "individual_scores": [
                {
                    "model": "granite",
                    "score": 85.0,
                    "reasoning": "Great match!"
                }
            ],
            "aggregate_score": 85.0
        }
        
        def make_scoring_request():
            with patch('app.services.scoring_service.scoring_service.score_word_with_models') as mock_score:
                mock_score.return_value = mock_result
                
                response = client.post("/scoring/score-word", json=request_data)
                assert response.status_code == 200
                return response.json()
        
        result = benchmark(make_scoring_request)
        assert result["aggregate_score"] == 85.0
    
    @pytest.mark.performance
    def test_concurrent_prediction_requests(self, client):
        """Test prediction endpoint under concurrent load."""
        
        request_data = {
            "word": "ambulance",
            "plate": "ABC"
        }
        
        mock_result = {
            "word": "ambulance",
            "plate": "ABC",
            "predicted_score": 85.5,
            "model_version": "ridge_v3"
        }
        
        def make_request():
            with patch('app.services.prediction_service.prediction_service') as mock_service:
                mock_service._is_initialized = True
                mock_service.predict_score.return_value = mock_result
                
                start_time = time.time()
                response = client.post("/predict/score", json=request_data)
                end_time = time.time()
                
                return {
                    "status_code": response.status_code,
                    "response_time": end_time - start_time,
                    "data": response.json() if response.status_code == 200 else None
                }
        
        # Test with 10 concurrent requests
        num_requests = 10
        results = []
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(num_requests)]
            
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
        
        # Verify all requests succeeded
        assert len(results) == num_requests
        for result in results:
            assert result["status_code"] == 200
            assert result["data"]["predicted_score"] == 85.5
        
        # Check response times
        response_times = [result["response_time"] for result in results]
        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)
        
        # Response times should be reasonable (adjust thresholds as needed)
        assert avg_response_time < 1.0, f"Average response time too high: {avg_response_time:.3f}s"
        assert max_response_time < 2.0, f"Max response time too high: {max_response_time:.3f}s"
    
    @pytest.mark.performance
    def test_batch_scoring_performance(self, client):
        """Test batch scoring performance with increasing load."""
        
        combination = "ABC"
        
        # Test with different batch sizes
        batch_sizes = [1, 5, 10, 25, 50]
        performance_results = {}
        
        for batch_size in batch_sizes:
            words = [f"word{i:03d}" for i in range(batch_size)]
            
            request_data = {
                "words": words,
                "combination": combination,
                "models": ["granite"]
            }
            
            mock_results = [
                {
                    "word": word,
                    "combination": combination,
                    "individual_scores": [
                        {"model": "granite", "score": 80.0, "reasoning": "Good match"}
                    ],
                    "aggregate_score": 80.0
                }
                for word in words
            ]
            
            with patch('app.services.scoring_service.scoring_service.score_words_batch') as mock_batch:
                mock_batch.return_value = mock_results
                
                start_time = time.time()
                response = client.post("/scoring/score-batch", json=request_data)
                end_time = time.time()
                
                assert response.status_code == 200
                data = response.json()
                assert len(data) == batch_size
                
                response_time = end_time - start_time
                performance_results[batch_size] = response_time
        
        # Verify performance scales reasonably with batch size
        # Response time should not grow exponentially
        for i in range(1, len(batch_sizes)):
            prev_size = batch_sizes[i-1]
            curr_size = batch_sizes[i]
            prev_time = performance_results[prev_size]
            curr_time = performance_results[curr_size]
            
            # Time should not increase more than proportionally to batch size increase
            size_ratio = curr_size / prev_size
            time_ratio = curr_time / prev_time
            
            # Allow some overhead, but not exponential growth
            assert time_ratio < size_ratio * 2, f"Performance degraded too much: batch {curr_size} took {time_ratio:.2f}x longer than proportional"
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_memory_usage_large_responses(self, client):
        """Test memory usage with large response payloads."""
        
        combination = "ABC"
        
        # Create a large result set (1000 matches)
        large_matches = [
            {"word": f"word{i:04d}", "frequency": 10000 - i}
            for i in range(1000)
        ]
        
        mock_large_result = {
            "combination": combination,
            "mode": "subsequence",
            "matches": large_matches,
            "match_count": 1000,
            "total_frequency": sum(match["frequency"] for match in large_matches),
            "frequency_distribution": {
                "mean": 9500.5,
                "median": 9500.5,
                "std_dev": 288.67,
                "min_freq": 9001,
                "max_freq": 10000,
                "q1": 9250.75,
                "q3": 9750.25
            },
            "lexical_fertility": "extremely_high"
        }
        
        with patch('app.services.solver_service.solve_combination') as mock_solve:
            mock_solve.return_value = mock_large_result
            
            start_time = time.time()
            response = client.get(f"/solve/{combination}")
            end_time = time.time()
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["matches"]) == 1000
            
            response_time = end_time - start_time
            
            # Should handle large responses within reasonable time
            assert response_time < 5.0, f"Large response took too long: {response_time:.3f}s"
    
    @pytest.mark.performance
    def test_api_health_check_performance(self, client):
        """Test health check endpoints are fast."""
        
        endpoints = [
            "/health",
            "/predict/health"
        ]
        
        with patch('app.services.prediction_service.prediction_service') as mock_service:
            mock_service._is_initialized = True
            
            for endpoint in endpoints:
                start_time = time.time()
                response = client.get(endpoint)
                end_time = time.time()
                
                response_time = end_time - start_time
                
                # Health checks should be very fast
                assert response_time < 0.1, f"Health check {endpoint} too slow: {response_time:.3f}s"
                assert response.status_code in [200, 503]  # Either healthy or not
    
    @pytest.mark.performance
    def test_error_response_performance(self, client):
        """Test that error responses are also fast."""
        
        # Test various error conditions
        error_cases = [
            # Invalid prediction request
            ("/predict/score", {"word": "", "plate": "ABC"}),
            # Invalid scoring request 
            ("/scoring/score-word", {"word": "ambulance", "combination": "ABC", "models": []}),
            # Non-existent session
            ("/scoring/session/nonexistent", None),
        ]
        
        for endpoint, payload in error_cases:
            start_time = time.time()
            
            if payload is None:
                response = client.get(endpoint)
            else:
                response = client.post(endpoint, json=payload)
            
            end_time = time.time()
            response_time = end_time - start_time
            
            # Error responses should also be fast
            assert response_time < 0.5, f"Error response for {endpoint} too slow: {response_time:.3f}s"
            assert response.status_code in [404, 422, 500]
    
    @pytest.mark.performance
    @pytest.mark.benchmark
    def test_json_serialization_performance(self, client, benchmark):
        """Benchmark JSON serialization/deserialization performance."""
        
        # Create a complex request with nested data
        complex_request = {
            "words": [f"word{i}" for i in range(50)],
            "combination": "ABC",
            "models": ["granite", "mistral", "deepseek"]
        }
        
        # Mock a complex response
        mock_results = [
            {
                "word": word,
                "combination": "ABC",
                "individual_scores": [
                    {
                        "model": model,
                        "score": 80.0 + i,
                        "reasoning": f"Score for {word} using {model} with detailed reasoning that could be quite long..."
                    }
                    for model in ["granite", "mistral", "deepseek"]
                ],
                "aggregate_score": 82.0 + i,
                "metadata": {
                    "word_length": len(word),
                    "frequency": 5000 - i * 10,
                    "categories": ["noun", "common", "english"],
                    "patterns": [f"pattern{j}" for j in range(5)]
                }
            }
            for i, word in enumerate(complex_request["words"])
        ]
        
        def make_complex_request():
            with patch('app.services.scoring_service.scoring_service.score_words_batch') as mock_batch:
                mock_batch.return_value = mock_results
                
                response = client.post("/scoring/score-batch", json=complex_request)
                assert response.status_code == 200
                return response.json()
        
        result = benchmark(make_complex_request)
        assert len(result) == 50
        
        # Verify the complex nested structure was handled correctly
        first_result = result[0]
        assert len(first_result["individual_scores"]) == 3
        assert "metadata" in first_result
        assert len(first_result["metadata"]["patterns"]) == 5
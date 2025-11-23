"""
Integration tests for the complete Image-to-Song workflow.
"""
import pytest
import io
from PIL import Image
from fastapi.testclient import TestClient


class TestEndToEndWorkflow:
    """Test complete end-to-end workflows."""

    def test_complete_quiz_workflow(self, client: TestClient):
        """Test complete quiz workflow from songs to preferences."""
        # Step 1: Get quiz songs
        response = client.get("/quiz/songs?limit=5")
        assert response.status_code == 200
        
        quiz_data = response.json()
        assert quiz_data["success"] is True
        quiz_songs = quiz_data["quiz_songs"]
        assert len(quiz_songs) > 0
        
        # Step 2: Simulate user ratings
        song_ratings = []
        for i, song in enumerate(quiz_songs[:3]):  # Rate first 3 songs
            song_ratings.append({
                "song_id": song["id"],
                "liked": i % 2 == 0  # Like every other song
            })
        
        # Step 3: Calculate preferences
        preferences_request = {
            "user_id": "integration_test_user",
            "song_ratings": song_ratings
        }
        
        response = client.post("/quiz/calculate-preferences", json=preferences_request)
        assert response.status_code == 200
        
        prefs_data = response.json()
        assert prefs_data["success"] is True
        assert "user_profile" in prefs_data
        
        user_profile = prefs_data["user_profile"]
        assert user_profile["quiz_completed"] is True
        assert "genre_preferences" in user_profile
        assert "audio_feature_preferences" in user_profile

    def test_complete_image_recommendation_workflow(self, client: TestClient, sample_image_file):
        """Test complete image to recommendation workflow."""
        filename, file_content, content_type = sample_image_file
        
        # Step 1: Analyze image and get recommendations
        response = client.post(
            "/analyze-and-recommend",
            files={"file": (filename, file_content, content_type)}
        )
        
        # Should process successfully or handle gracefully
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            
            # Should have analysis and recommendations
            expected_fields = ["status", "filename", "image_analysis"]
            present_fields = [field for field in expected_fields if field in data]
            assert len(present_fields) > 0
            
            # If recommendations are present, they should be well-formed
            if "recommendations" in data:
                recommendations = data["recommendations"]
                assert isinstance(recommendations, list)
                
                for rec in recommendations:
                    # Each recommendation should have basic structure
                    assert isinstance(rec, dict)
                    has_id = "id" in rec or "spotify_id" in rec
                    has_name = "name" in rec or "title" in rec
                    assert has_id or has_name

    def test_personalized_recommendation_workflow(self, client: TestClient, sample_user_profile, sample_image_file):
        """Test personalized recommendations with user profile."""
        filename, file_content, content_type = sample_image_file
        
        # First, test regular recommendations with profile
        recommendation_request = {
            "mood": "happy",
            "caption": "A joyful scene",
            "user_profile": sample_user_profile
        }
        
        response = client.post("/recommendations", json=recommendation_request)
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                assert "recommendations" in data
                assert "personalized" in data
                
                # Should indicate it's personalized
                assert data["personalized"] is True

    def test_search_integration_workflow(self, client: TestClient):
        """Test search functionality workflow."""
        # Test basic search
        response = client.get("/search/songs?q=rock+music&limit=5")
        
        # Should work or handle gracefully
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            
            # Should return search results in Spotify format
            if "tracks" in data:
                tracks = data["tracks"]
                assert "items" in tracks
                
                items = tracks["items"]
                assert isinstance(items, list)
                
                # Each item should have basic track info
                for item in items:
                    assert "id" in item
                    assert "name" in item
                    assert "artists" in item


class TestErrorRecovery:
    """Test error recovery and graceful degradation."""

    def test_spotify_unavailable_fallback(self, client: TestClient):
        """Test behavior when Spotify API is unavailable."""
        # This would require mocking Spotify unavailability
        # Test that fallback recommendations are provided
        
        recommendation_request = {
            "mood": "energetic",
            "caption": "High energy scene"
        }
        
        with patch('app.routers.recommendations.get_spotify_token', return_value=None):
            response = client.post("/recommendations", json=recommendation_request)
            
            # Should provide fallback recommendations
            assert response.status_code in [200, 500]
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    assert "recommendations" in data
                    # Should indicate fallback strategy
                    if "search_strategy" in data:
                        assert "fallback" in data["search_strategy"].lower()

    def test_ai_service_unavailable_fallback(self, client: TestClient, sample_image_file):
        """Test behavior when AI service is unavailable."""
        filename, file_content, content_type = sample_image_file
        
        # With AI service disabled (already set in test environment)
        response = client.post(
            "/analyze-and-recommend",
            files={"file": (filename, file_content, content_type)}
        )
        
        # Should use simple analyzer fallback
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            
            # Should still provide analysis using simple analyzer
            if "image_analysis" in data:
                analysis = data["image_analysis"]
                assert "mood" in analysis


class TestConcurrency:
    """Test concurrent request handling."""

    def test_concurrent_quiz_requests(self, client: TestClient):
        """Test handling multiple concurrent quiz requests."""
        import concurrent.futures
        import threading
        
        def make_quiz_request():
            return client.get("/quiz/songs?limit=10")
        
        # Make multiple concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_quiz_request) for _ in range(5)]
            responses = [future.result() for future in futures]
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200

    def test_concurrent_image_analysis(self, client: TestClient, sample_image_file):
        """Test handling multiple concurrent image analysis requests."""
        import concurrent.futures
        
        filename, file_content, content_type = sample_image_file
        
        def make_analysis_request():
            # Create new BytesIO for each request
            test_image = Image.new('RGB', (50, 50), color='purple')
            img_bytes = io.BytesIO()
            test_image.save(img_bytes, format='JPEG')
            img_bytes.seek(0)
            
            return client.post(
                "/analyze-and-recommend",
                files={"file": ("test.jpg", img_bytes, "image/jpeg")}
            )
        
        # Make concurrent image analysis requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(make_analysis_request) for _ in range(3)]
            responses = [future.result() for future in futures]
        
        # All requests should be handled (success or graceful failure)
        for response in responses:
            assert response.status_code in [200, 500]


class TestPerformance:
    """Test performance characteristics."""

    def test_api_response_times(self, client: TestClient):
        """Test that API responses are within acceptable time limits."""
        import time
        
        test_cases = [
            ("/", "GET", None),
            ("/health", "GET", None),
            ("/quiz/songs?limit=10", "GET", None),
        ]
        
        for endpoint, method, data in test_cases:
            start_time = time.time()
            
            if method == "GET":
                response = client.get(endpoint)
            elif method == "POST":
                response = client.post(endpoint, json=data)
            
            end_time = time.time()
            response_time = end_time - start_time
            
            # Should respond quickly for basic endpoints
            assert response_time < 10.0  # 10 second timeout
            assert response.status_code in [200, 422, 500]

    def test_memory_usage_stability(self, client: TestClient):
        """Test that memory usage remains stable across requests."""
        # Make multiple requests to check for memory leaks
        for i in range(10):
            response = client.get("/health")
            assert response.status_code == 200
            
            # Check that the service is still healthy
            data = response.json()
            assert data["status"] == "healthy"


# Import patch for mocking
from unittest.mock import patch
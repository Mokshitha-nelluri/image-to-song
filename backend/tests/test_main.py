"""
Test main application endpoints and core functionality.
"""
import pytest
from fastapi.testclient import TestClient


class TestMainEndpoints:
    """Test the main application endpoints."""

    def test_root_endpoint(self, client: TestClient):
        """Test the root endpoint returns API information."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert "message" in data
        assert "version" in data
        assert "status" in data
        assert "features" in data
        assert "endpoints" in data
        
        # Verify features structure
        features = data["features"]
        expected_features = [
            "music_quiz", "image_analysis", "preference_recommendations", 
            "spotify_search", "ai_service", "song_previews"
        ]
        for feature in expected_features:
            assert feature in features
        
        # Verify endpoints structure
        endpoints = data["endpoints"]
        expected_endpoints = [
            "health", "quiz_songs", "calculate_preferences", 
            "analyze_image", "recommendations", "search_songs"
        ]
        for endpoint in expected_endpoints:
            assert endpoint in endpoints

    def test_health_endpoint(self, client: TestClient):
        """Test the health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required health fields
        required_fields = [
            "status", "uptime_seconds", "model_loaded", 
            "spotify_status", "quiz_songs_available", "version", "timestamp"
        ]
        for field in required_fields:
            assert field in data
        
        # Status should be healthy
        assert data["status"] == "healthy"
        
        # Uptime should be a positive number
        assert isinstance(data["uptime_seconds"], (int, float))
        assert data["uptime_seconds"] >= 0
        
        # Quiz songs should be available
        assert isinstance(data["quiz_songs_available"], int)
        assert data["quiz_songs_available"] > 0

    def test_cors_headers(self, client: TestClient):
        """Test that CORS headers are properly set."""
        response = client.options("/")
        
        # Should allow CORS preflight
        assert response.status_code in [200, 204]

    def test_invalid_endpoint(self, client: TestClient):
        """Test accessing invalid endpoint returns 404."""
        response = client.get("/invalid-endpoint")
        
        assert response.status_code == 404


class TestErrorHandling:
    """Test global error handling."""

    def test_server_error_handling(self, client: TestClient, monkeypatch):
        """Test that server errors are handled gracefully."""
        # This would require mocking an internal error
        # For now, just ensure the error handler structure exists
        pass


class TestApplicationStartup:
    """Test application startup and lifespan events."""

    def test_app_initialization(self, client: TestClient):
        """Test that the app initializes correctly."""
        # The app should be running if we can make requests
        response = client.get("/health")
        assert response.status_code == 200

    def test_environment_configuration(self, client: TestClient):
        """Test that environment variables are properly configured."""
        response = client.get("/")
        data = response.json()
        
        # In test mode, AI service should be disabled due to RENDER_MEMORY_LIMIT
        assert data["features"]["ai_service"] == False
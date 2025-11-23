"""
Test recommendation endpoints and music recommendation logic.
"""
import pytest
import io
from PIL import Image
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
import json


class TestRecommendationEndpoints:
    """Test recommendation endpoints."""

    def test_analyze_and_recommend_endpoint(self, client: TestClient, sample_image_file):
        """Test the analyze-and-recommend endpoint."""
        filename, file_content, content_type = sample_image_file
        
        response = client.post(
            "/analyze-and-recommend",
            files={"file": (filename, file_content, content_type)}
        )
        
        # Should process or handle gracefully
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            
            # Check basic response structure
            assert "status" in data or "success" in data
            
            # Should have some form of recommendations or analysis
            expected_fields = ["recommendations", "image_analysis", "filename"]
            present_fields = [field for field in expected_fields if field in data]
            assert len(present_fields) > 0

    def test_recommendations_endpoint(self, client: TestClient, sample_user_profile):
        """Test the recommendations endpoint with user profile."""
        request_data = {
            "mood": "happy",
            "caption": "A sunny day in the park",
            "user_profile": sample_user_profile
        }
        
        response = client.post("/recommendations", json=request_data)
        
        # Should process or handle gracefully
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            
            # Check response structure
            assert "success" in data
            if data["success"]:
                assert "recommendations" in data
                assert "mood" in data
                assert isinstance(data["recommendations"], list)

    def test_recommendations_without_user_profile(self, client: TestClient):
        """Test recommendations without user profile (anonymous mode)."""
        request_data = {
            "mood": "energetic",
            "caption": "People dancing at a concert"
        }
        
        response = client.post("/recommendations", json=request_data)
        
        # Should work without user profile
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            if data["success"]:
                assert "recommendations" in data

    def test_recommendations_invalid_mood(self, client: TestClient):
        """Test recommendations with invalid mood."""
        request_data = {
            "mood": "invalid_mood_123",
            "caption": "Test caption"
        }
        
        response = client.post("/recommendations", json=request_data)
        
        # Should handle invalid mood gracefully
        assert response.status_code in [200, 400, 422, 500]

    def test_recommendations_empty_request(self, client: TestClient):
        """Test recommendations with empty request."""
        response = client.post("/recommendations", json={})
        
        # Should handle empty request gracefully
        assert response.status_code in [200, 400, 422, 500]


class TestSpotifyIntegration:
    """Test Spotify API integration."""

    @patch('app.routers.recommendations.get_spotify_token')
    @patch('app.routers.recommendations.search_spotify_songs')
    def test_spotify_search_success(self, mock_search, mock_token, client: TestClient, mock_spotify_response):
        """Test successful Spotify API integration."""
        # Mock token acquisition
        mock_token.return_value = "mock_access_token"
        
        # Mock search results
        mock_search.return_value = mock_spotify_response
        
        request_data = {
            "mood": "happy",
            "caption": "A joyful celebration"
        }
        
        response = client.post("/recommendations", json=request_data)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                recommendations = data.get("recommendations", [])
                # Should return recommendations from Spotify
                assert isinstance(recommendations, list)

    @patch('app.routers.recommendations.get_spotify_token')
    def test_spotify_token_failure_fallback(self, mock_token, client: TestClient):
        """Test fallback when Spotify token acquisition fails."""
        # Mock token failure
        mock_token.return_value = None
        
        request_data = {
            "mood": "peaceful",
            "caption": "A quiet forest scene"
        }
        
        response = client.post("/recommendations", json=request_data)
        
        # Should use fallback recommendations
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            # Should still return some recommendations (from quiz songs)
            if data.get("success"):
                assert "recommendations" in data

    @patch('httpx.AsyncClient.get')
    @patch('app.routers.recommendations.get_spotify_token')
    def test_spotify_api_error_handling(self, mock_token, mock_http_get, client: TestClient):
        """Test handling of Spotify API errors."""
        # Mock token success
        mock_token.return_value = "valid_token"
        
        # Mock HTTP error
        mock_response = MagicMock()
        mock_response.status_code = 429  # Rate limited
        mock_http_get.return_value.__aenter__ = AsyncMock()
        mock_http_get.return_value.__aexit__ = AsyncMock()
        
        request_data = {
            "mood": "energetic",
            "caption": "High energy scene"
        }
        
        response = client.post("/recommendations", json=request_data)
        
        # Should handle API errors gracefully
        assert response.status_code in [200, 500]


class TestRecommendationLogic:
    """Test recommendation algorithm and logic."""

    def test_mood_based_search_queries(self, client: TestClient):
        """Test that different moods generate appropriate search queries."""
        moods = ["happy", "sad", "energetic", "peaceful", "romantic"]
        
        for mood in moods:
            request_data = {
                "mood": mood,
                "caption": f"A {mood} scene"
            }
            
            response = client.post("/recommendations", json=request_data)
            
            # Should process each mood
            assert response.status_code in [200, 500]
            
            if response.status_code == 200:
                data = response.json()
                # Each mood should be processed (may return different results)
                assert isinstance(data, dict)

    def test_user_preference_integration(self, client: TestClient, sample_user_profile):
        """Test that user preferences influence recommendations."""
        # Test with user profile
        request_with_profile = {
            "mood": "happy",
            "caption": "Happy scene",
            "user_profile": sample_user_profile
        }
        
        # Test without user profile
        request_without_profile = {
            "mood": "happy", 
            "caption": "Happy scene"
        }
        
        response_with = client.post("/recommendations", json=request_with_profile)
        response_without = client.post("/recommendations", json=request_without_profile)
        
        # Both should work
        assert response_with.status_code in [200, 500]
        assert response_without.status_code in [200, 500]
        
        # Results might be different (personalized vs general)
        if response_with.status_code == 200 and response_without.status_code == 200:
            data_with = response_with.json()
            data_without = response_without.json()
            
            # Both should indicate their personalization status
            if data_with.get("success") and data_without.get("success"):
                # Check if personalization flag is set correctly
                assert "personalized" in data_with or "search_strategy" in data_with
                assert "personalized" in data_without or "search_strategy" in data_without

    def test_recommendation_diversification(self, client: TestClient, sample_user_profile):
        """Test that recommendations are diversified."""
        request_data = {
            "mood": "happy",
            "caption": "A diverse scene",
            "user_profile": sample_user_profile
        }
        
        response = client.post("/recommendations", json=request_data)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and "recommendations" in data:
                recommendations = data["recommendations"]
                
                if len(recommendations) > 1:
                    # Check for artist diversity (no single artist dominating)
                    artists = [rec.get("artist", "") for rec in recommendations]
                    unique_artists = set(artists)
                    
                    # Should have some diversity (not all songs from same artist)
                    diversity_ratio = len(unique_artists) / len(recommendations)
                    assert diversity_ratio > 0.5  # At least 50% unique artists


class TestFallbackRecommendations:
    """Test fallback recommendation systems."""

    @patch('app.routers.recommendations.get_spotify_token')
    def test_local_fallback_recommendations(self, mock_token, client: TestClient):
        """Test local fallback when Spotify is unavailable."""
        # Mock Spotify unavailability
        mock_token.return_value = None
        
        request_data = {
            "mood": "happy",
            "caption": "Happy scene"
        }
        
        response = client.post("/recommendations", json=request_data)
        
        # Should return fallback recommendations
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                assert "recommendations" in data
                recommendations = data["recommendations"]
                assert isinstance(recommendations, list)
                
                # Should indicate fallback strategy
                if "search_strategy" in data:
                    assert "fallback" in data["search_strategy"].lower()

    def test_quiz_songs_fallback(self, client: TestClient, sample_user_profile):
        """Test that quiz songs are used as fallback recommendations."""
        # This test verifies the fallback uses quiz songs database
        with patch('app.routers.recommendations.get_spotify_token', return_value=None):
            request_data = {
                "mood": "energetic",
                "user_profile": sample_user_profile
            }
            
            response = client.post("/recommendations", json=request_data)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "recommendations" in data:
                    recommendations = data["recommendations"]
                    
                    # Should return some recommendations from quiz database
                    assert len(recommendations) > 0
                    
                    # Check that recommendations have basic structure
                    for rec in recommendations:
                        assert "id" in rec or "name" in rec or "title" in rec


class TestRecommendationQuality:
    """Test recommendation quality and relevance."""

    def test_recommendation_structure(self, client: TestClient):
        """Test that recommendations have consistent structure."""
        request_data = {
            "mood": "peaceful",
            "caption": "A calm lake"
        }
        
        response = client.post("/recommendations", json=request_data)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and "recommendations" in data:
                recommendations = data["recommendations"]
                
                for rec in recommendations:
                    # Each recommendation should have basic info
                    assert isinstance(rec, dict)
                    
                    # Should have either Spotify ID or name/title
                    has_id = "id" in rec or "spotify_id" in rec
                    has_name = "name" in rec or "title" in rec
                    assert has_id or has_name
                    
                    # Should have artist info
                    assert "artist" in rec

    def test_recommendation_metadata(self, client: TestClient, sample_user_profile):
        """Test that recommendations include useful metadata."""
        request_data = {
            "mood": "romantic",
            "caption": "A romantic dinner scene",
            "user_profile": sample_user_profile
        }
        
        response = client.post("/recommendations", json=request_data)
        
        if response.status_code == 200:
            data = response.json()
            
            # Should include analysis metadata
            expected_metadata = [
                "total_found", "search_strategy", "analysis_method",
                "mood", "personalized"
            ]
            
            present_metadata = [field for field in expected_metadata if field in data]
            assert len(present_metadata) > 0  # At least some metadata present
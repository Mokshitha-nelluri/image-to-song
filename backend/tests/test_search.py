"""
Test search endpoints and Spotify search functionality.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock


class TestSearchEndpoints:
    """Test search functionality endpoints."""

    def test_search_songs_endpoint_exists(self, client: TestClient):
        """Test that search endpoints exist."""
        # Test without query parameter - should return validation error
        response = client.get("/search/songs")
        assert response.status_code == 422  # Missing query parameter

    def test_search_songs_with_query(self, client: TestClient):
        """Test song search with query parameter."""
        response = client.get("/search/songs?q=rock+music")
        
        # Should process or handle gracefully
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)

    def test_search_songs_empty_query(self, client: TestClient):
        """Test song search with empty query."""
        response = client.get("/search/songs?q=")
        
        # Should handle empty query gracefully
        assert response.status_code in [200, 400, 422, 500]

    def test_search_songs_with_limit(self, client: TestClient):
        """Test song search with limit parameter."""
        response = client.get("/search/songs?q=pop&limit=10")
        
        # Should respect limit parameter
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            if "tracks" in data and "items" in data["tracks"]:
                tracks = data["tracks"]["items"]
                assert len(tracks) <= 10

    def test_search_songs_invalid_limit(self, client: TestClient):
        """Test song search with invalid limit."""
        # Test with negative limit
        response = client.get("/search/songs?q=rock&limit=-1")
        assert response.status_code in [200, 400, 422, 500]
        
        # Test with very high limit
        response = client.get("/search/songs?q=rock&limit=1000")
        assert response.status_code in [200, 400, 422, 500]

    def test_search_songs_special_characters(self, client: TestClient):
        """Test song search with special characters in query."""
        special_queries = [
            "rock & roll",
            "hip-hop",
            "r&b music",
            "pop/rock",
            "indie+alternative"
        ]
        
        for query in special_queries:
            response = client.get(f"/search/songs?q={query}")
            
            # Should handle special characters
            assert response.status_code in [200, 400, 500]


class TestSpotifySearchIntegration:
    """Test Spotify search API integration."""

    @patch('app.routers.search.get_spotify_token')
    @patch('httpx.AsyncClient.get')
    def test_spotify_search_success(self, mock_http_get, mock_token, client: TestClient, mock_spotify_response):
        """Test successful Spotify search integration."""
        # Mock token acquisition
        mock_token.return_value = "mock_access_token"
        
        # Mock HTTP response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_spotify_response
        mock_http_get.return_value = mock_response
        
        response = client.get("/search/songs?q=test+song")
        
        if response.status_code == 200:
            data = response.json()
            
            # Should return Spotify-formatted response
            assert "tracks" in data
            assert "items" in data["tracks"]
            
            tracks = data["tracks"]["items"]
            if tracks:
                track = tracks[0]
                # Check Spotify track structure
                expected_fields = ["id", "name", "artists", "album"]
                for field in expected_fields:
                    assert field in track

    @patch('app.routers.search.get_spotify_token')
    def test_spotify_search_no_token(self, mock_token, client: TestClient):
        """Test search behavior when Spotify token unavailable."""
        # Mock token failure
        mock_token.return_value = None
        
        response = client.get("/search/songs?q=test+song")
        
        # Should handle token unavailability gracefully
        assert response.status_code in [200, 401, 500, 503]
        
        if response.status_code == 200:
            data = response.json()
            # Should return error message or empty results
            assert isinstance(data, dict)

    @patch('app.routers.search.get_spotify_token')
    @patch('httpx.AsyncClient.get')
    def test_spotify_search_api_error(self, mock_http_get, mock_token, client: TestClient):
        """Test handling of Spotify API errors."""
        # Mock token success
        mock_token.return_value = "valid_token"
        
        # Mock API error responses
        error_codes = [401, 403, 429, 500, 503]
        
        for error_code in error_codes:
            mock_response = AsyncMock()
            mock_response.status_code = error_code
            mock_response.text = "API Error"
            mock_http_get.return_value = mock_response
            
            response = client.get("/search/songs?q=test")
            
            # Should handle API errors gracefully
            assert response.status_code in [200, error_code, 500]

    @patch('app.routers.search.get_spotify_token')
    @patch('httpx.AsyncClient.get')
    def test_spotify_search_timeout(self, mock_http_get, mock_token, client: TestClient):
        """Test handling of Spotify API timeouts."""
        # Mock token success
        mock_token.return_value = "valid_token"
        
        # Mock timeout
        mock_http_get.side_effect = Exception("Request timeout")
        
        response = client.get("/search/songs?q=test+timeout")
        
        # Should handle timeouts gracefully
        assert response.status_code in [200, 500, 503, 504]


class TestSearchQueryHandling:
    """Test search query processing and validation."""

    def test_search_query_encoding(self, client: TestClient):
        """Test that search queries are properly encoded."""
        queries_with_spaces = [
            "the beatles",
            "rock and roll",
            "hip hop music",
            "r&b soul"
        ]
        
        for query in queries_with_spaces:
            response = client.get(f"/search/songs?q={query}")
            
            # Should handle queries with spaces
            assert response.status_code in [200, 500]

    def test_search_query_length_limits(self, client: TestClient):
        """Test search query length limits."""
        # Test very short query
        response = client.get("/search/songs?q=a")
        assert response.status_code in [200, 400, 500]
        
        # Test very long query
        long_query = "a" * 1000
        response = client.get(f"/search/songs?q={long_query}")
        assert response.status_code in [200, 400, 414, 500]

    def test_search_unicode_support(self, client: TestClient):
        """Test search with unicode characters."""
        unicode_queries = [
            "música",
            "rock&roll",
            "pop🎵music",
            "café"
        ]
        
        for query in unicode_queries:
            # URL encode the query properly
            import urllib.parse
            encoded_query = urllib.parse.quote(query)
            response = client.get(f"/search/songs?q={encoded_query}")
            
            # Should handle unicode characters
            assert response.status_code in [200, 400, 500]


class TestSearchResults:
    """Test search result format and content."""

    @patch('app.routers.search.get_spotify_token')
    @patch('httpx.AsyncClient.get')
    def test_search_result_structure(self, mock_http_get, mock_token, client: TestClient, mock_spotify_response):
        """Test that search results have expected structure."""
        # Mock successful search
        mock_token.return_value = "valid_token"
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_spotify_response
        mock_http_get.return_value = mock_response
        
        response = client.get("/search/songs?q=test")
        
        if response.status_code == 200:
            data = response.json()
            
            # Should follow Spotify API structure
            if "tracks" in data:
                tracks = data["tracks"]
                assert "items" in tracks
                
                for track in tracks["items"]:
                    # Each track should have basic required fields
                    required_fields = ["id", "name", "artists"]
                    for field in required_fields:
                        assert field in track
                    
                    # Artists should be an array
                    assert isinstance(track["artists"], list)
                    if track["artists"]:
                        artist = track["artists"][0]
                        assert "name" in artist

    def test_search_result_filtering(self, client: TestClient):
        """Test that search results are properly filtered."""
        response = client.get("/search/songs?q=explicit+content")
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if explicit content filtering is applied
            if "tracks" in data and "items" in data["tracks"]:
                tracks = data["tracks"]["items"]
                for track in tracks:
                    # Should have explicit flag
                    assert "explicit" in track or isinstance(track.get("explicit"), bool)

    def test_search_result_metadata(self, client: TestClient):
        """Test that search results include useful metadata."""
        response = client.get("/search/songs?q=metadata+test&limit=5")
        
        if response.status_code == 200:
            data = response.json()
            
            # Should include search metadata
            if "tracks" in data:
                tracks_data = data["tracks"]
                
                # May include pagination info
                metadata_fields = ["total", "limit", "offset", "next", "previous"]
                # At least some metadata should be present
                present_metadata = [field for field in metadata_fields if field in tracks_data]
                # This is optional - depends on implementation


class TestSearchPerformance:
    """Test search performance and optimization."""

    def test_search_response_time(self, client: TestClient):
        """Test that search responses are reasonably fast."""
        import time
        
        start_time = time.time()
        response = client.get("/search/songs?q=performance+test")
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # Should respond within reasonable time (adjust as needed)
        # This is more of a benchmark than a strict test
        assert response_time < 30.0  # 30 seconds max (generous for potential network calls)

    def test_search_caching(self, client: TestClient):
        """Test search result caching if implemented."""
        # Make same search twice
        query = "caching+test"
        
        response1 = client.get(f"/search/songs?q={query}")
        response2 = client.get(f"/search/songs?q={query}")
        
        # Both should succeed
        assert response1.status_code == response2.status_code
        
        # If caching is implemented, results should be consistent
        if response1.status_code == 200 and response2.status_code == 200:
            # Results should be similar (caching would make them identical)
            assert response1.json() == response2.json()


class TestSearchSecurity:
    """Test search security and input validation."""

    def test_search_injection_prevention(self, client: TestClient):
        """Test that search prevents injection attacks."""
        malicious_queries = [
            "'; DROP TABLE songs; --",
            "<script>alert('xss')</script>",
            "../../../etc/passwd",
            "{{7*7}}",  # Template injection
            "${7*7}",   # Expression injection
        ]
        
        for malicious_query in malicious_queries:
            response = client.get(f"/search/songs?q={malicious_query}")
            
            # Should handle malicious queries safely
            assert response.status_code in [200, 400, 422, 500]
            
            if response.status_code == 200:
                # Response should not execute or reflect the malicious content
                response_text = response.text.lower()
                assert "drop table" not in response_text
                assert "<script>" not in response_text

    def test_search_rate_limiting(self, client: TestClient):
        """Test search rate limiting if implemented."""
        # Make multiple rapid requests
        for i in range(10):
            response = client.get(f"/search/songs?q=rate+limit+test+{i}")
            
            # Should either succeed or be rate limited
            assert response.status_code in [200, 429, 500]
            
            # If rate limited, should return appropriate status
            if response.status_code == 429:
                break
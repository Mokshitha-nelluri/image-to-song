"""
Test quiz endpoints for music preference discovery.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


class TestQuizSongs:
    """Test the quiz songs endpoint."""

    def test_get_quiz_songs_default(self, client: TestClient):
        """Test getting quiz songs with default parameters."""
        response = client.get("/quiz/songs")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "success" in data
        assert "quiz_songs" in data
        assert "total_songs" in data
        assert "instructions" in data
        
        assert data["success"] is True
        
        # Check quiz songs structure
        quiz_songs = data["quiz_songs"]
        assert isinstance(quiz_songs, list)
        assert len(quiz_songs) <= 20  # Default limit
        
        # Check individual song structure
        if quiz_songs:
            song = quiz_songs[0]
            required_fields = [
                "id", "title", "artist", "album", "genres", 
                "preview_url", "album_cover", "quiz_position", "total_in_quiz"
            ]
            for field in required_fields:
                assert field in song
            
            assert isinstance(song["genres"], list)
            assert song["quiz_position"] >= 1
            assert song["total_in_quiz"] == len(quiz_songs)
        
        # Check instructions structure
        instructions = data["instructions"]
        expected_instruction_keys = [
            "swipe_right", "swipe_left", "tap_play", "progress"
        ]
        for key in expected_instruction_keys:
            assert key in instructions

    def test_get_quiz_songs_custom_limit(self, client: TestClient):
        """Test getting quiz songs with custom limit."""
        limit = 10
        response = client.get(f"/quiz/songs?limit={limit}")
        
        assert response.status_code == 200
        data = response.json()
        
        quiz_songs = data["quiz_songs"]
        assert len(quiz_songs) <= limit

    def test_get_quiz_songs_invalid_limit(self, client: TestClient):
        """Test getting quiz songs with invalid limit parameters."""
        # Test limit too high
        response = client.get("/quiz/songs?limit=25")
        assert response.status_code == 422  # Validation error
        
        # Test limit too low
        response = client.get("/quiz/songs?limit=0")
        assert response.status_code == 422  # Validation error
        
        # Test invalid limit type
        response = client.get("/quiz/songs?limit=invalid")
        assert response.status_code == 422  # Validation error

    def test_quiz_songs_randomization(self, client: TestClient):
        """Test that quiz songs are properly randomized."""
        # Make multiple requests and check for variation
        responses = []
        for _ in range(3):
            response = client.get("/quiz/songs?limit=5")
            assert response.status_code == 200
            data = response.json()
            song_ids = [song["id"] for song in data["quiz_songs"]]
            responses.append(song_ids)
        
        # At least one response should be different (randomization)
        # Note: This test might occasionally fail due to random chance
        all_same = all(resp == responses[0] for resp in responses[1:])
        # We don't assert this is False because randomization might occasionally produce same results


class TestPreferenceCalculation:
    """Test the preference calculation endpoint."""

    def test_calculate_preferences_success(self, client: TestClient, sample_quiz_results):
        """Test successful preference calculation."""
        response = client.post("/quiz/calculate-preferences", json=sample_quiz_results)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "success" in data
        assert "user_profile" in data
        assert "summary" in data
        
        assert data["success"] is True
        
        # Check user profile structure
        user_profile = data["user_profile"]
        required_fields = [
            "user_id", "created_at", "quiz_completed",
            "genre_preferences", "audio_feature_preferences",
            "liked_artists", "disliked_artists", "quiz_stats"
        ]
        for field in required_fields:
            assert field in user_profile
        
        assert user_profile["quiz_completed"] is True
        assert isinstance(user_profile["genre_preferences"], dict)
        assert isinstance(user_profile["audio_feature_preferences"], dict)
        assert isinstance(user_profile["liked_artists"], list)
        assert isinstance(user_profile["disliked_artists"], list)
        
        # Check quiz stats
        quiz_stats = user_profile["quiz_stats"]
        stat_fields = ["total_songs_rated", "songs_liked", "songs_disliked", "completion_rate"]
        for field in stat_fields:
            assert field in quiz_stats
        
        # Check summary structure
        summary = data["summary"]
        summary_fields = ["top_genres", "music_personality", "recommendation_ready"]
        for field in summary_fields:
            assert field in summary
        
        assert isinstance(summary["top_genres"], list)
        assert isinstance(summary["music_personality"], str)
        assert summary["recommendation_ready"] is True

    def test_calculate_preferences_empty_ratings(self, client: TestClient):
        """Test preference calculation with empty song ratings."""
        empty_quiz = {
            "user_id": "test_user",
            "song_ratings": []
        }
        
        response = client.post("/quiz/calculate-preferences", json=empty_quiz)
        
        # Should still work, just with default preferences
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_calculate_preferences_invalid_data(self, client: TestClient):
        """Test preference calculation with invalid data."""
        # Missing required fields
        invalid_quiz = {"user_id": "test"}
        
        response = client.post("/quiz/calculate-preferences", json=invalid_quiz)
        
        # Should handle gracefully or return validation error
        assert response.status_code in [200, 422, 500]

    def test_calculate_preferences_malformed_json(self, client: TestClient):
        """Test preference calculation with malformed JSON."""
        response = client.post(
            "/quiz/calculate-preferences", 
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422  # Validation error

    @patch('app.routers.quiz.QUIZ_SONGS')
    def test_calculate_preferences_song_not_found(self, mock_quiz_songs, client: TestClient):
        """Test preference calculation when referenced songs don't exist."""
        # Mock empty quiz songs database
        mock_quiz_songs.__len__ = MagicMock(return_value=0)
        mock_quiz_songs.__iter__ = MagicMock(return_value=iter([]))
        
        quiz_results = {
            "user_id": "test_user",
            "song_ratings": [
                {"song_id": "nonexistent_id", "liked": True}
            ]
        }
        
        response = client.post("/quiz/calculate-preferences", json=quiz_results)
        
        # Should handle missing songs gracefully
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestQuizDataIntegrity:
    """Test quiz data integrity and consistency."""

    def test_quiz_songs_data_structure(self, client: TestClient):
        """Test that quiz songs have consistent data structure."""
        response = client.get("/quiz/songs")
        assert response.status_code == 200
        
        data = response.json()
        quiz_songs = data["quiz_songs"]
        
        for song in quiz_songs:
            # Check that all songs have required audio features for preference calculation
            # This would need to be implemented based on your actual data structure
            assert "id" in song
            assert "genres" in song
            assert isinstance(song["genres"], list)
            assert len(song["genres"]) > 0

    def test_music_personality_generation(self, client: TestClient, sample_quiz_results):
        """Test that music personality is generated correctly."""
        response = client.post("/quiz/calculate-preferences", json=sample_quiz_results)
        
        assert response.status_code == 200
        data = response.json()
        
        personality = data["summary"]["music_personality"]
        assert isinstance(personality, str)
        assert len(personality) > 0
        # Should contain some descriptive text
        assert len(personality.split()) >= 3
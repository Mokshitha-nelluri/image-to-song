"""
Test configuration and fixtures for the Image-to-Song API tests.
"""
import pytest
import asyncio
from typing import AsyncGenerator
from fastapi.testclient import TestClient
from httpx import AsyncClient
import tempfile
import os
from PIL import Image
import io

# Import the main app
from main import app


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client for the FastAPI app."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sample_image_file():
    """Create a sample image file for testing."""
    # Create a simple test image
    image = Image.new('RGB', (100, 100), color='red')
    img_bytes = io.BytesIO()
    image.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    
    return ("test_image.jpg", img_bytes, "image/jpeg")


@pytest.fixture
def sample_quiz_results():
    """Sample quiz results for testing preference calculation."""
    return {
        "user_id": "test_user_123",
        "song_ratings": [
            {
                "song_id": "4iV5W9uYEdYUVa79Axb7Rh",
                "liked": True
            },
            {
                "song_id": "7qiZfU4dY1lWllzX7mkmht", 
                "liked": False
            },
            {
                "song_id": "0VjIjW4GlULA7loidkQA0z",
                "liked": True
            }
        ]
    }


@pytest.fixture
def sample_user_profile():
    """Sample user profile for testing recommendations."""
    return {
        "user_id": "test_user_123",
        "created_at": 1700000000.0,
        "quiz_completed": True,
        "genre_preferences": {
            "pop": 0.8,
            "rock": 0.6,
            "electronic": 0.4
        },
        "audio_feature_preferences": {
            "danceability": 0.7,
            "energy": 0.8,
            "valence": 0.6,
            "acousticness": 0.3
        },
        "liked_artists": ["The Killers", "Imagine Dragons"],
        "quiz_stats": {
            "total_songs_rated": 20,
            "songs_liked": 12,
            "songs_disliked": 8,
            "completion_rate": 1.0
        }
    }


@pytest.fixture
def mock_spotify_response():
    """Mock Spotify API response for testing."""
    return {
        "tracks": {
            "items": [
                {
                    "id": "4iV5W9uYEdYUVa79Axb7Rh",
                    "name": "Mr. Brightside",
                    "artists": [{"name": "The Killers"}],
                    "album": {
                        "name": "Hot Fuss",
                        "images": [{"url": "https://example.com/cover.jpg"}]
                    },
                    "preview_url": "https://example.com/preview.mp3",
                    "external_urls": {
                        "spotify": "https://open.spotify.com/track/4iV5W9uYEdYUVa79Axb7Rh"
                    },
                    "popularity": 85,
                    "explicit": False,
                    "duration_ms": 222200
                }
            ]
        }
    }


# Test environment variables
@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Set up test environment variables."""
    monkeypatch.setenv("RENDER_MEMORY_LIMIT", "true")  # Use lightweight mode
    monkeypatch.setenv("SPOTIFY_CLIENT_ID", "test_client_id")
    monkeypatch.setenv("SPOTIFY_CLIENT_SECRET", "test_client_secret")


# Utility functions for tests
def create_test_image(width=100, height=100, color='red'):
    """Create a test image for upload testing."""
    image = Image.new('RGB', (width, height), color=color)
    img_bytes = io.BytesIO()
    image.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    return img_bytes


def assert_valid_song_recommendation(recommendation):
    """Assert that a song recommendation has the required fields."""
    required_fields = ['id', 'name', 'artist', 'spotify_url']
    for field in required_fields:
        assert field in recommendation, f"Missing required field: {field}"
    
    # Optional fields that should be strings if present
    optional_string_fields = ['preview_url', 'album', 'image']
    for field in optional_string_fields:
        if field in recommendation:
            assert isinstance(recommendation[field], (str, type(None)))


def assert_valid_user_profile(profile):
    """Assert that a user profile has the required structure."""
    required_fields = ['user_id', 'created_at', 'quiz_completed']
    for field in required_fields:
        assert field in profile, f"Missing required field: {field}"
    
    if profile['quiz_completed']:
        assert 'genre_preferences' in profile
        assert 'audio_feature_preferences' in profile
        assert isinstance(profile['genre_preferences'], dict)
        assert isinstance(profile['audio_feature_preferences'], dict)
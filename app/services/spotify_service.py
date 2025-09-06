"""
Spotify Integration Service
Handles OAuth authentication and music recommendations based on image mood analysis.
"""
import asyncio
import base64
import hashlib
import logging
import secrets
import time
from typing import Dict, List, Optional, Any
from urllib.parse import urlencode

import aiohttp
from fastapi import HTTPException

from app.core.config import settings
from app.services.enhanced_mood_service import enhanced_mood_analyzer

logger = logging.getLogger(__name__)

class SpotifyService:
    """
    Spotify API integration service for OAuth and music recommendations.
    """
    
    def __init__(self):
        self.client_id = settings.SPOTIFY_CLIENT_ID
        self.client_secret = settings.SPOTIFY_CLIENT_SECRET
        self.redirect_uri = settings.SPOTIFY_REDIRECT_URI
        self.base_url = "https://api.spotify.com/v1"
        self.auth_url = "https://accounts.spotify.com"
        
        # Cache for access tokens
        self._token_cache: Dict[str, Dict] = {}
        
        logger.info("SpotifyService initialized")
    
    def generate_auth_url(self, state: Optional[str] = None) -> Dict[str, str]:
        """
        Generate Spotify OAuth authorization URL.
        
        Args:
            state: Optional state parameter for security
            
        Returns:
            Dict containing auth URL and state
        """
        if not state:
            state = secrets.token_urlsafe(32)
        
        # Required scopes for music recommendations
        scopes = [
            "user-read-private",
            "user-read-email", 
            "user-top-read",
            "user-read-recently-played",
            "playlist-modify-public",
            "playlist-modify-private"
        ]
        
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "scope": " ".join(scopes),
            "state": state,
            "show_dialog": "true"
        }
        
        auth_url = f"{self.auth_url}/authorize?{urlencode(params)}"
        
        return {
            "auth_url": auth_url,
            "state": state
        }
    
    async def exchange_code_for_token(self, authorization_code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access token.
        
        Args:
            authorization_code: Code received from Spotify OAuth callback
            
        Returns:
            Token information including access_token and refresh_token
        """
        # Prepare credentials
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {
            "grant_type": "authorization_code",
            "code": authorization_code,
            "redirect_uri": self.redirect_uri
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.auth_url}/api/token",
                headers=headers,
                data=data
            ) as response:
                if response.status == 200:
                    token_data = await response.json()
                    
                    # Cache token with expiration
                    user_id = await self._get_user_id(token_data["access_token"])
                    self._token_cache[user_id] = {
                        **token_data,
                        "expires_at": time.time() + token_data.get("expires_in", 3600)
                    }
                    
                    logger.info(f"Token exchanged successfully for user: {user_id}")
                    return token_data
                else:
                    error_text = await response.text()
                    logger.error(f"Token exchange failed: {error_text}")
                    raise HTTPException(status_code=400, detail="Failed to exchange code for token")
    
    async def _get_user_id(self, access_token: str) -> str:
        """Get Spotify user ID from access token."""
        headers = {"Authorization": f"Bearer {access_token}"}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/me",
                headers=headers
            ) as response:
                if response.status == 200:
                    user_data = await response.json()
                    return user_data["id"]
                else:
                    return "unknown_user"
    
    async def get_music_recommendations(
        self, 
        user_id: str, 
        mood_analysis: Dict[str, Any],
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Get music recommendations based on mood analysis from image.
        
        Args:
            user_id: Spotify user ID
            mood_analysis: Mood and color analysis from image
            limit: Number of recommendations to return
            
        Returns:
            Music recommendations with tracks and analysis
        """
        # Get user token
        token_info = self._token_cache.get(user_id)
        if not token_info or time.time() >= token_info.get("expires_at", 0):
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        access_token = token_info["access_token"]
        
        # Enhanced mood analysis
        enhanced_analysis = enhanced_mood_analyzer.analyze_comprehensive_mood(mood_analysis)
        
        # Get audio features from enhanced analysis
        audio_features = enhanced_analysis["audio_features"]
        
        # Get recommendations from Spotify
        recommendations = await self._fetch_spotify_recommendations(
            access_token, audio_features, limit
        )
        
        # Get user's top tracks for personalization
        user_top_tracks = await self._get_user_top_tracks(access_token, limit=5)
        
        # Get genre seeds based on mood
        genre_seeds = self._get_genre_seeds_for_mood(enhanced_analysis["primary_mood"])
        
        # Get additional recommendations with genre seeds
        genre_recommendations = await self._fetch_spotify_recommendations_with_genres(
            access_token, audio_features, genre_seeds, limit=5
        )
        
        return {
            "recommendations": recommendations,
            "genre_recommendations": genre_recommendations,
            "enhanced_mood_analysis": enhanced_analysis,
            "original_mood_analysis": mood_analysis,
            "audio_features_used": audio_features,
            "recommended_genres": enhanced_analysis["recommended_genres"],
            "mood_explanation": enhanced_analysis["mood_explanation"],
            "personalization": {
                "top_tracks": user_top_tracks,
                "recommendation_count": len(recommendations.get("tracks", [])),
                "genre_recommendation_count": len(genre_recommendations.get("tracks", []))
            },
            "generated_at": time.time()
        }
    
    def _mood_to_audio_features(self, mood_analysis: Dict[str, Any]) -> Dict[str, float]:
        """
        Convert mood analysis to Spotify audio features.
        
        Args:
            mood_analysis: Contains caption, dominant_colors, etc.
            
        Returns:
            Spotify audio features for recommendation
        """
        # Extract caption and colors
        caption = mood_analysis.get("caption", "").lower()
        colors = mood_analysis.get("dominant_colors", [])
        
        # Default neutral values
        features = {
            "valence": 0.5,      # Musical positivity (0.0 = sad, 1.0 = happy)
            "energy": 0.5,       # Energy level (0.0 = calm, 1.0 = energetic)
            "danceability": 0.5, # How danceable (0.0 = not, 1.0 = very)
            "acousticness": 0.5, # Acoustic vs electronic (0.0 = electronic, 1.0 = acoustic)
            "instrumentalness": 0.3, # Instrumental content
            "speechiness": 0.1,  # Speech content (0.0 = music, 1.0 = speech)
            "tempo": 120.0       # BPM (tempo in beats per minute)
        }
        
        # Analyze caption for mood keywords
        if any(word in caption for word in ["happy", "joy", "celebration", "party", "fun", "bright"]):
            features.update({
                "valence": 0.8,
                "energy": 0.7,
                "danceability": 0.7,
                "tempo": 130.0
            })
        elif any(word in caption for word in ["calm", "peaceful", "quiet", "serene", "relaxing"]):
            features.update({
                "valence": 0.6,
                "energy": 0.3,
                "acousticness": 0.8,
                "tempo": 80.0
            })
        elif any(word in caption for word in ["sad", "dark", "lonely", "rain", "gray", "melancholy"]):
            features.update({
                "valence": 0.2,
                "energy": 0.4,
                "acousticness": 0.6,
                "tempo": 70.0
            })
        elif any(word in caption for word in ["energy", "action", "sports", "running", "dancing"]):
            features.update({
                "valence": 0.7,
                "energy": 0.9,
                "danceability": 0.8,
                "tempo": 140.0
            })
        elif any(word in caption for word in ["nature", "outdoor", "forest", "mountain", "beach"]):
            features.update({
                "valence": 0.6,
                "energy": 0.5,
                "acousticness": 0.7,
                "tempo": 100.0
            })
        
        # Analyze colors for additional mood context
        if colors:
            primary_color = colors[0] if colors else {}
            rgb = primary_color.get("rgb", (128, 128, 128))
            
            # Color psychology mapping
            red, green, blue = rgb
            brightness = (red + green + blue) / 3
            
            # Bright colors = higher energy and valence
            if brightness > 200:
                features["valence"] = min(1.0, features["valence"] + 0.2)
                features["energy"] = min(1.0, features["energy"] + 0.1)
            elif brightness < 100:
                features["valence"] = max(0.0, features["valence"] - 0.2)
                features["energy"] = max(0.0, features["energy"] - 0.1)
            
            # Red = energy, Blue = calm, Green = balanced
            if red > green and red > blue:  # Red dominant
                features["energy"] = min(1.0, features["energy"] + 0.2)
                features["danceability"] = min(1.0, features["danceability"] + 0.1)
            elif blue > red and blue > green:  # Blue dominant
                features["valence"] = max(0.0, features["valence"] - 0.1)
                features["acousticness"] = min(1.0, features["acousticness"] + 0.2)
        
        logger.info(f"Mood analysis converted to audio features: {features}")
        return features
    
    async def _fetch_spotify_recommendations(
        self, 
        access_token: str, 
        audio_features: Dict[str, float], 
        limit: int
    ) -> Dict[str, Any]:
        """Fetch recommendations from Spotify API."""
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Build query parameters
        params = {
            "limit": limit,
            "market": "US",
            **{f"target_{key}": value for key, value in audio_features.items()}
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/recommendations",
                headers=headers,
                params=params
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    logger.error(f"Spotify recommendations failed: {error_text}")
                    raise HTTPException(status_code=400, detail="Failed to get recommendations")
    
    async def _get_user_top_tracks(self, access_token: str, limit: int = 5) -> List[Dict]:
        """Get user's top tracks for personalization."""
        headers = {"Authorization": f"Bearer {access_token}"}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/me/top/tracks",
                headers=headers,
                params={"limit": limit, "time_range": "medium_term"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("items", [])
                else:
                    logger.warning("Could not fetch user top tracks")
                    return []
    
    def _get_genre_seeds_for_mood(self, mood: str) -> List[str]:
        """Get Spotify genre seeds based on mood."""
        mood_to_genres = {
            "happy": ["pop", "funk", "dance", "reggae"],
            "peaceful": ["ambient", "classical", "acoustic", "folk"],
            "melancholic": ["blues", "indie", "alternative", "sad"],
            "energetic": ["electronic", "rock", "hip-hop", "punk"],
            "romantic": ["r-n-b", "soul", "jazz", "love"],
            "nature": ["world-music", "instrumental", "celtic"],
            "mysterious": ["dark-ambient", "gothic", "trip-hop"]
        }
        
        return mood_to_genres.get(mood, ["pop", "alternative"])[:3]  # Max 3 genre seeds
    
    async def _fetch_spotify_recommendations_with_genres(
        self, 
        access_token: str, 
        audio_features: Dict[str, float], 
        genre_seeds: List[str],
        limit: int
    ) -> Dict[str, Any]:
        """Fetch recommendations with specific genre seeds."""
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Build query parameters with genres
        params = {
            "limit": limit,
            "market": "US",
            "seed_genres": ",".join(genre_seeds),
            **{f"target_{key}": value for key, value in audio_features.items()}
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/recommendations",
                headers=headers,
                params=params
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    logger.error(f"Genre-based Spotify recommendations failed: {error_text}")
                    # Return empty result instead of raising exception
                    return {"tracks": []}
    
    def get_cached_user_data(self, user_id: str) -> Optional[Dict]:
        """Get cached user authentication data."""
        return self._token_cache.get(user_id)
    
    def revoke_user_access(self, user_id: str) -> bool:
        """Remove user from cache (logout)."""
        if user_id in self._token_cache:
            del self._token_cache[user_id]
            logger.info(f"User access revoked: {user_id}")
            return True
        return False

# Global service instance
spotify_service = SpotifyService()

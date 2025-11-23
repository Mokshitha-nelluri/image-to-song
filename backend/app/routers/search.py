"""
Song search endpoints for direct music search functionality.
Handles Spotify API integration for song discovery.
"""
import os
import time
import base64
import random
from typing import Dict, Any

import httpx
from fastapi import APIRouter, HTTPException, Query

from ..data.quiz_songs import QUIZ_SONGS

router = APIRouter(tags=["search"])

# Spotify credentials
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID', '25de944a1992453896769027a9ffe3c1')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')

# Global variables for token management
spotify_access_token = None
token_expires_at = 0


async def get_spotify_token():
    """Get Spotify access token using Client Credentials flow"""
    global spotify_access_token, token_expires_at
    
    # Check if current token is still valid
    current_time = time.time()
    if spotify_access_token and current_time < token_expires_at:
        return spotify_access_token
    
    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        print("❌ Spotify credentials not configured")
        return None
    
    try:
        # Encode credentials
        credentials = base64.b64encode(
            f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}".encode()
        ).decode()
        
        headers = {
            'Authorization': f'Basic {credentials}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {'grant_type': 'client_credentials'}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                'https://accounts.spotify.com/api/token',
                headers=headers,
                data=data
            )
            
            if response.status_code == 200:
                token_data = response.json()
                spotify_access_token = token_data['access_token']
                expires_in = token_data.get('expires_in', 3600)
                token_expires_at = current_time + expires_in - 60  # Refresh 1 min early
                
                print(f"✅ Got Spotify token, expires in {expires_in}s")
                return spotify_access_token
            else:
                print(f"❌ Spotify token request failed: {response.status_code}")
                return None
                
    except Exception as e:
        print(f"❌ Failed to get Spotify token: {e}")
        return None


@router.get("/songs")
async def search_songs(
    query: str = Query(..., description="Search query for songs"),
    limit: int = Query(10, ge=1, le=50, description="Number of results to return")
) -> Dict[str, Any]:
    """Search for songs using Spotify API"""
    
    token = await get_spotify_token()
    if not token:
        print(f"⚠️ Spotify search unavailable, using local fallback for query: {query}")
        # Fallback to searching local quiz songs
        query_lower = query.lower()
        matching_songs = []
        
        for song in QUIZ_SONGS:
            # Simple text matching
            if (query_lower in song["title"].lower() or 
                query_lower in song["artist"].lower() or
                any(query_lower in genre.lower() for genre in song["genres"])):
                matching_songs.append({
                    "id": song["id"],
                    "name": song["title"],
                    "artist": song["artist"],
                    "preview_url": song["preview_url"],
                    "spotify_url": f"https://open.spotify.com/track/{song['id']}",
                    "image": song["album_cover"],
                    "album": song["album"],
                    "genres": song["genres"]
                })
        
        # If no matches, return random songs
        if not matching_songs:
            matching_songs = [{
                "id": song["id"],
                "name": song["title"],
                "artist": song["artist"],
                "preview_url": song["preview_url"],
                "spotify_url": f"https://open.spotify.com/track/{song['id']}",
                "image": song["album_cover"],
                "album": song["album"],
                "genres": song["genres"]
            } for song in random.sample(QUIZ_SONGS, min(limit, len(QUIZ_SONGS)))]
        
        return {
            "success": True,
            "query": query,
            "results": matching_songs[:limit],
            "total_found": len(matching_songs),
            "search_type": "local_fallback",
            "note": "Using local song database (Spotify search unavailable)"
        }
    
    try:
        async with httpx.AsyncClient() as client:
            headers = {'Authorization': f'Bearer {token}'}
            
            response = await client.get(
                'https://api.spotify.com/v1/search',
                headers=headers,
                params={
                    'q': query,
                    'type': 'track',
                    'limit': limit,
                    'market': 'US'
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                tracks = data['tracks']['items']
                
                results = []
                for track in tracks:
                    results.append({
                        "id": track['id'],
                        "title": track['name'],
                        "artist": track['artists'][0]['name'],
                        "album": track['album']['name'],
                        "preview_url": track.get('preview_url'),
                        "spotify_url": track['external_urls']['spotify'],
                        "album_cover": track['album']['images'][0]['url'] if track['album']['images'] else None,
                        "popularity": track['popularity'],
                        "duration_ms": track['duration_ms'],
                        "explicit": track['explicit'],
                        "release_date": track['album']['release_date']
                    })
                
                return {
                    "success": True,
                    "query": query,
                    "results": results,
                    "total_found": len(results),
                    "has_previews": sum(1 for r in results if r["preview_url"] is not None)
                }
            else:
                raise HTTPException(status_code=response.status_code, detail="Spotify search failed")
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
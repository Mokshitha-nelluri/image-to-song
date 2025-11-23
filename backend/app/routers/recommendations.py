"""
Music recommendation endpoints.
Handles personalized recommendations based on image analysis and user preferences.
"""
import os
import time
import base64
import random
from typing import Dict, Any, List, Optional

import httpx
from fastapi import APIRouter, HTTPException, File, UploadFile

from ..core.config import settings
from ..data.quiz_songs import QUIZ_SONGS
from ..utils.image_utils import ImageProcessor

# Import services
try:
    from ..utils.image_music_mapper import image_music_mapper
except ImportError:
    image_music_mapper = None
    print("Image music mapper not available")

try:
    from ..services.hybrid_ai_service import hybrid_service
    USE_AI_SERVICE = True
except ImportError:
    try:
        from ..services.ai_service import blip2_service as hybrid_service
        USE_AI_SERVICE = True
    except ImportError:
        from ..services.simple_analyzer import simple_image_analyzer
        hybrid_service = None
        USE_AI_SERVICE = False

router = APIRouter(tags=["recommendations"])

# Spotify credentials
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
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
        print("Spotify credentials not configured")
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
                
                print(f"Got Spotify token, expires in {expires_in}s")
                return spotify_access_token
            else:
                print(f"Spotify token request failed: {response.status_code}")
                return None
                
    except Exception as e:
        print(f"Failed to get Spotify token: {e}")
        return None


@router.post("/analyze-and-recommend")
async def analyze_and_recommend(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Analyze image with BLIP + Color analysis, then generate music recommendations
    using the intelligent image-to-music mapping system.
    """
    try:
        print(f"Enhanced Analysis & Recommendation for: {file.filename}")
        
        # First, analyze the image
        image_data = await file.read()
        
        # Get image info and hash for caching/debugging
        try:
            image_info = ImageProcessor.get_image_info(image_data)
            image_hash = ImageProcessor.calculate_image_hash(image_data)
            print(f"Image info: {image_info}")
            print(f"Image hash: {image_hash[:16]}...")  # First 16 chars for logging
        except Exception as e:
            print(f"Failed to get image info: {e}")
            image_info = {}
            image_hash = "unknown"
        
        # Use hybrid service if available
        if USE_AI_SERVICE and hybrid_service:
            try:
                if hasattr(hybrid_service, 'analyze_image'):
                    # New hybrid service
                    analysis_result = await hybrid_service.analyze_image(image_data)  # type: ignore
                else:
                    # Old BLIP2 service - generate caption and combine with simple analysis
                    from ..services.simple_analyzer import simple_image_analyzer
                    caption = await hybrid_service.generate_caption(image_data)  # type: ignore
                    simple_result = simple_image_analyzer.analyze_image(image_data)
                    
                    analysis_result = {
                        "caption": caption,
                        "scene_description": caption,
                        "mood": simple_result["mood"],
                        "confidence": 0.9,
                        "colors": simple_result["colors"],
                        "size": simple_result["size"],
                        "analysis_method": "blip2_plus_color"
                    }
                
            except Exception as e:
                print(f"AI analysis failed, using simple: {e}")
                from ..services.simple_analyzer import simple_image_analyzer
                analysis_result = simple_image_analyzer.analyze_image(image_data)
        else:
            # Use simple analyzer only
            from ..services.simple_analyzer import simple_image_analyzer
            analysis_result = simple_image_analyzer.analyze_image(image_data)
        
        # Create enhanced music profile using the mapper
        if image_music_mapper and analysis_result:
            scene_description = analysis_result.get("scene_description") or analysis_result.get("caption", "")
            mood = analysis_result.get("mood", "neutral")
            colors = analysis_result.get("colors", {})
            
            music_profile = image_music_mapper.create_music_profile(scene_description, mood, colors)
            search_queries = image_music_mapper.get_search_queries(music_profile, mood)
            
            print(f"Generated music profile: {music_profile['recommended_genres']}")
            print(f"Search queries: {search_queries[:3]}")
            
            # Get Spotify token and search for songs
            token = await get_spotify_token()
            if not token:
                print("Spotify unavailable, using fallback recommendations from quiz songs")
                # Fallback to quiz songs based on mood/genre
                fallback_songs = _get_fallback_songs_for_analysis(music_profile, mood)
                return {
                    "status": "success",
                    "filename": file.filename,
                    "image_analysis": analysis_result,
                    "music_profile": music_profile,
                    "search_queries": search_queries,
                    "recommendations": fallback_songs[:15],  # Return top 15
                    "total_found": len(fallback_songs),
                    "analysis_method": "enhanced_hybrid_mapping_fallback"
                }
            
            # Search for songs using the intelligent queries
            songs = []
            all_tracks = []
            
            # Collect all tracks from different search strategies
            for query in search_queries[:6]:  # Use top 6 queries
                try:
                    search_results = await search_spotify_songs(query, limit=8)
                    if search_results and "tracks" in search_results:
                        for track in search_results["tracks"]["items"]:
                            if track["id"] not in [t.get("id") for t in all_tracks]:  # Avoid duplicates
                                all_tracks.append({
                                    "id": track["id"],
                                    "name": track["name"],
                                    "artist": ", ".join([artist["name"] for artist in track["artists"]]),
                                    "preview_url": track.get("preview_url"),
                                    "spotify_url": track["external_urls"]["spotify"],
                                    "image": track["album"]["images"][0]["url"] if track["album"]["images"] else None,
                                    "popularity": track.get("popularity", 0),
                                    "explicit": track.get("explicit", False),
                                    "duration_ms": track.get("duration_ms", 0),
                                    "query_used": query,
                                    "album": track["album"]["name"],
                                    "release_date": track["album"].get("release_date", "")
                                })
                        
                except Exception as e:
                    print(f"Search failed for query '{query}': {e}")
                    continue
            
            # Smart filtering and ranking based on musical characteristics
            filtered_songs = _rank_songs_by_characteristics(all_tracks, mood)
            
            return {
                "status": "success",
                "filename": file.filename,
                "image_analysis": analysis_result,
                "image_info": image_info,
                "image_hash": image_hash,
                "music_profile": music_profile,
                "search_queries": search_queries,
                "recommendations": filtered_songs[:15],  # Return top 15 ranked songs
                "total_found": len(all_tracks),
                "analysis_method": "intelligent_characteristic_matching"
            }
        
        else:
            # Fallback to simple recommendation
            mood = analysis_result.get("mood", "neutral")
            base_queries = _generate_mood_based_queries(mood, analysis_result.get("caption", ""))
            
            # Get basic recommendations
            token = await get_spotify_token()
            if not token:
                print("Spotify unavailable, using fallback recommendations from quiz songs")
                fallback_songs = _get_fallback_songs_by_mood(mood)
                return {
                    "status": "success", 
                    "filename": file.filename,
                    "image_analysis": analysis_result,
                    "recommendations": fallback_songs,
                    "total_found": len(fallback_songs),
                    "analysis_method": "simple_fallback"
                }
            
            songs = []
            for query in base_queries[:3]:
                try:
                    search_results = await search_spotify_songs(query, limit=5)
                    if search_results and "tracks" in search_results:
                        for track in search_results["tracks"]["items"]:
                            if track["id"] not in [s.get("id") for s in songs]:
                                songs.append({
                                    "id": track["id"],
                                    "name": track["name"],
                                    "artist": ", ".join([artist["name"] for artist in track["artists"]]),
                                    "preview_url": track.get("preview_url"),
                                    "spotify_url": track["external_urls"]["spotify"],
                                    "image": track["album"]["images"][0]["url"] if track["album"]["images"] else None
                                })
                                
                                if len(songs) >= 10:
                                    break
                except Exception as e:
                    continue
            
            return {
                "status": "success", 
                "filename": file.filename,
                "image_analysis": analysis_result,
                "recommendations": songs,
                "total_found": len(songs),
                "analysis_method": "simple_fallback"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        print(f"Enhanced analysis error: {error_msg}")
        raise HTTPException(status_code=500, detail=f"Enhanced analysis failed: {error_msg}")


@router.post("/recommendations")
async def get_recommendations(request: Dict[str, Any]) -> Dict[str, Any]:
    """Get personalized song recommendations based on image mood + user preferences"""
    try:
        mood = request.get('mood', 'neutral')
        caption = request.get('caption', '')
        user_profile = request.get('user_profile', {})
        
        print(f"Getting recommendations for mood: {mood}")
        print(f"User profile provided: {bool(user_profile)}")
        
        # Get Spotify token
        token = await get_spotify_token()
        if not token:
            return _get_fallback_recommendations(mood, user_profile)
        
        # Combine image mood with user preferences
        search_params = _build_search_parameters(mood, caption, user_profile)
        
        print(f"Search queries: {search_params['queries']}")
        print(f"Strategy: {search_params['strategy']}")
        
        # Diversified search strategy - limit tracks per search for variety
        all_tracks = []
        async with httpx.AsyncClient() as client:
            headers = {'Authorization': f'Bearer {token}'}
            
            # Search with multiple diverse parameters
            for search_query in search_params["queries"]:
                try:
                    print(f"Searching for: '{search_query}'")
                    search_response = await client.get(
                        'https://api.spotify.com/v1/search',
                        headers=headers,
                        params={
                            'q': search_query,
                            'type': 'track',
                            'limit': 8,  # Reduced limit for diversity
                            'market': 'US'
                        }
                    )
                    
                    if search_response.status_code == 200:
                        tracks = search_response.json()['tracks']['items']
                        print(f"Found {len(tracks)} tracks for '{search_query}'")
                        
                        # Limit to max 4 tracks per search for diversity
                        query_tracks = []
                        tracks_with_preview = 0
                        
                        for track in tracks[:4]:  # Max 4 per search
                            track_data = {
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
                                "search_type": search_query[:20]  # Track which search found this
                            }
                            query_tracks.append(track_data)
                            
                            if track.get('preview_url'):
                                tracks_with_preview += 1
                        
                        all_tracks.extend(query_tracks)
                        print(f"Added {len(query_tracks)} tracks ({tracks_with_preview} with previews)")
                        
                    else:
                        print(f"Spotify search failed: {search_response.status_code}")
                            
                except Exception as e:
                    print(f"Search query failed: {search_query}, error: {e}")
                    continue
        
        # Apply diversified selection algorithm
        recommendations = _diversified_track_selection(all_tracks)
        
        print(f"Diversified final recommendations: {len(recommendations)}")
        
        # Always return what we found, no minimum threshold needed
        return {
            "success": True,
            "mood": mood,
            "caption": caption,
            "recommendations": recommendations,
            "search_strategy": f"{search_params['strategy']} + diversified",
            "total_found": len(recommendations),
            "personalized": bool(user_profile)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendations failed: {str(e)}")


# Helper functions
async def search_spotify_songs(query: str, limit: int = 20) -> Optional[Dict[str, Any]]:
    """Search Spotify for songs using a query"""
    try:
        token = await get_spotify_token()
        if not token:
            return None
        
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
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Spotify search failed: {response.status_code}")
                return None
                
    except Exception as e:
        print(f"Search error for '{query}': {e}")
        return None


def _generate_mood_based_queries(mood: str, caption: str) -> List[str]:
    """Generate simple mood-based queries for fallback"""
    mood_queries = {
        "happy": ["happy songs", "upbeat music", "feel good playlist"],
        "peaceful": ["calm music", "relaxing songs", "peaceful playlist"],
        "energetic": ["energetic music", "workout songs", "high energy playlist"],
        "melancholic": ["sad songs", "emotional music", "melancholy playlist"],
        "romantic": ["love songs", "romantic music", "romantic playlist"],
        "nature": ["nature sounds", "acoustic music", "outdoor playlist"],
        "neutral": ["popular music", "top songs", "trending playlist"]
    }
    
    return mood_queries.get(mood, mood_queries["neutral"])


def _get_fallback_songs_for_analysis(music_profile: Dict[str, Any], mood: str) -> List[Dict[str, Any]]:
    """Get fallback songs for enhanced analysis when Spotify is unavailable"""
    
    if not music_profile or not music_profile.get("recommended_genres"):
        return _get_fallback_songs_by_mood(mood)
    
    # Filter songs based on the generated music profile
    recommended_genres = music_profile["recommended_genres"]
    matched_songs = []
    
    for song in QUIZ_SONGS:
        song_genres = [g.lower() for g in song["genres"]]
        if any(genre.lower() in " ".join(song_genres) for genre in recommended_genres):
            matched_songs.append({
                "id": song["id"],
                "name": song["title"],
                "artist": song["artist"],
                "preview_url": song["preview_url"],
                "spotify_url": f"https://open.spotify.com/track/{song['id']}",
                "image": song["album_cover"],
                "query_used": f"genre:{', '.join(recommended_genres)}"
            })
    
    # If not enough matches, add some random ones
    if len(matched_songs) < 10:
        remaining_songs = [s for s in QUIZ_SONGS if s["id"] not in [ms["id"] for ms in matched_songs]]
        additional = random.sample(remaining_songs, min(10 - len(matched_songs), len(remaining_songs)))
        
        for song in additional:
            matched_songs.append({
                "id": song["id"],
                "name": song["title"],
                "artist": song["artist"],
                "preview_url": song["preview_url"],
                "spotify_url": f"https://open.spotify.com/track/{song['id']}",
                "image": song["album_cover"],
                "query_used": "fallback"
            })
    
    return matched_songs


def _get_fallback_songs_by_mood(mood: str) -> List[Dict[str, Any]]:
    """Get fallback songs by mood when Spotify is unavailable"""
    
    mood_song_count = {
        "happy": 6,
        "energetic": 6,
        "peaceful": 4,
        "melancholic": 4,
        "romantic": 4,
        "nature": 4
    }
    
    count = mood_song_count.get(mood, 5)
    selected_songs = random.sample(QUIZ_SONGS, min(count, len(QUIZ_SONGS)))
    
    return [{
        "id": song["id"],
        "name": song["title"],
        "artist": song["artist"],
        "preview_url": song["preview_url"],
        "spotify_url": f"https://open.spotify.com/track/{song['id']}",
        "image": song["album_cover"]
    } for song in selected_songs]


def _get_fallback_recommendations(mood: str, user_profile: Dict[str, Any]) -> Dict[str, Any]:
    """Get fallback recommendations when Spotify is not available"""
    
    # Use our quiz songs as recommendations
    mood_songs = []
    
    if user_profile and user_profile.get("genre_preferences"):
        # Filter songs based on user preferences
        genre_prefs = user_profile["genre_preferences"]
        top_genres = [genre for genre, score in genre_prefs.items() if score > 0.5]
        
        for song in QUIZ_SONGS:
            if any(genre in song["genres"] for genre in top_genres):
                mood_songs.append({
                    "id": song["id"],
                    "title": song["title"],
                    "artist": song["artist"],
                    "album": song["album"],
                    "preview_url": song["preview_url"],
                    "spotify_url": f"https://open.spotify.com/track/{song['id']}",
                    "album_cover": song["album_cover"],
                    "popularity": 75,  # Default popularity
                    "duration_ms": 180000,  # Default 3 minutes
                    "explicit": False
                })
    else:
        # Use mood-based filtering
        mood_song_count = {
            "happy": 4,
            "energetic": 4,
            "peaceful": 3,
            "melancholic": 3,
            "romantic": 3,
            "nature": 3
        }
        
        count = mood_song_count.get(mood, 4)
        selected_songs = random.sample(QUIZ_SONGS, min(count, len(QUIZ_SONGS)))
        
        for song in selected_songs:
            mood_songs.append({
                "id": song["id"],
                "title": song["title"],
                "artist": song["artist"],
                "album": song["album"],
                "preview_url": song["preview_url"],
                "spotify_url": f"https://open.spotify.com/track/{song['id']}",
                "album_cover": song["album_cover"],
                "popularity": 75,
                "duration_ms": 180000,
                "explicit": False
            })
    
    return {
        "success": True,
        "mood": mood,
        "recommendations": mood_songs[:6],  # Limit to 6 recommendations
        "search_strategy": "fallback_local",
        "total_found": len(mood_songs),
        "personalized": bool(user_profile),
        "note": "Using local song database (Spotify search unavailable)"
    }


def _build_search_parameters(mood: str, caption: str, user_profile: Dict[str, Any]) -> Dict[str, Any]:
    """Build intelligent search parameters balancing scene context with user preferences"""
    
    # Scene-appropriate genre searches with DISTINCT mood-specific strategies
    scene_based_strategies = {
        "happy": [
            "genre:pop", "genre:dance-pop", "pop cheerful",
            "feel good hits", "upbeat popular", "sunny pop"
        ],
        "peaceful": [
            "genre:folk", "genre:acoustic", "peaceful indie",
            "calm acoustic", "folk popular", "nature acoustic"
        ],
        "energetic": [
            "genre:rock", "genre:electronic", "genre:dance",
            "high energy hits", "workout popular", "rock anthems"
        ],
        "melancholic": [
            "genre:alternative", "genre:indie-rock", "emotional indie",
            "sad alternative", "melancholic popular", "introspective hits"
        ],
        "romantic": [
            "genre:pop", "genre:r-n-b", "genre:acoustic",
            "love song hits", "romantic popular", "soul ballads"
        ],
        "nature": [
            "genre:folk", "genre:indie-folk", "acoustic nature",
            "folk popular", "organic acoustic", "nature indie"
        ]
    }
    
    scene_searches = scene_based_strategies.get(mood, scene_based_strategies["happy"])
    
    final_queries = []
    
    # 1. Prioritize SCENE-APPROPRIATE genres (most important for context)
    final_queries.extend(scene_searches[:4])  # Top 4 scene-based searches for variety
    
    # 2. Minimal user preference integration (limited influence)
    if user_profile and user_profile.get("genre_preferences"):
        genre_prefs = user_profile["genre_preferences"]
        top_user_genres = sorted(genre_prefs.items(), key=lambda x: x[1], reverse=True)[:3]
        
        # Add user genres but keep scene context dominant
        user_genre_count = 0
        for genre, score in top_user_genres:
            if score > 0.5 and user_genre_count < 1:  # Only 1 user genre max, higher threshold
                # Check if user genre is compatible with scene mood
                if _is_genre_mood_compatible(genre, mood):
                    final_queries.append(f"genre:{genre}")
                    user_genre_count += 1
        
        strategy = "scene_dominated_personalized"
    else:
        strategy = "pure_scene_based"
    
    # 3. Add mood-specific popular songs as variety
    mood_specific_queries = {
        "peaceful": ["acoustic popular", "folk hits"],
        "melancholic": ["alternative popular", "indie emotional"],
        "happy": ["pop hits", "feel good popular"],
        "energetic": ["rock popular", "electronic hits"],
        "romantic": ["love song hits", "r&b popular"]
    }
    
    specific_queries = mood_specific_queries.get(mood, ["popular music"])
    final_queries.extend(specific_queries[:2])  # Add 2 mood-specific queries
    
    return {
        "queries": final_queries[:7],  # Balanced query count
        "strategy": strategy,
        "scene_context": {
            "mood": mood,
            "caption": caption,
            "priority": "scene_over_user"  # Scene context takes priority
        }
    }


def _is_genre_mood_compatible(genre: str, mood: str) -> bool:
    """Check if a user's preferred genre is compatible with the scene mood"""
    
    # Genre-mood compatibility matrix
    compatibility = {
        "peaceful": ["folk", "acoustic", "indie", "ambient", "jazz", "classical", "new age"],
        "nature": ["folk", "acoustic", "indie-folk", "world", "ambient", "country"],
        "melancholic": ["indie", "alternative", "folk", "acoustic", "blues", "ambient"],
        "romantic": ["r&b", "soul", "acoustic", "jazz", "indie", "pop"],
        "happy": ["pop", "indie", "funk", "dance", "electronic", "reggae"],
        "energetic": ["rock", "electronic", "hip-hop", "dance", "punk", "metal"]
    }
    
    compatible_genres = compatibility.get(mood, [])
    genre_lower = genre.lower()
    
    # Check if genre matches any compatible genres
    return any(comp_genre in genre_lower for comp_genre in compatible_genres)


def _rank_songs_by_characteristics(tracks: List[Dict[str, Any]], mood: str) -> List[Dict[str, Any]]:
    """Rank songs based on musical characteristics and mood appropriateness"""
    
    # Define mood preferences for ranking
    mood_preferences = {
        "happy": {
            "min_popularity": 50,
            "prefer_recent": True,
            "avoid_explicit": True,
            "duration_range": (120000, 300000)  # 2-5 minutes
        },
        "melancholic": {
            "min_popularity": 40,
            "prefer_recent": False,
            "avoid_explicit": False,
            "duration_range": (180000, 360000)  # 3-6 minutes
        },
        "energetic": {
            "min_popularity": 60,
            "prefer_recent": True,
            "avoid_explicit": False,
            "duration_range": (150000, 300000)  # 2.5-5 minutes
        },
        "peaceful": {
            "min_popularity": 45,
            "prefer_recent": False,
            "avoid_explicit": True,
            "duration_range": (180000, 420000)  # 3-7 minutes
        },
        "romantic": {
            "min_popularity": 50,
            "prefer_recent": False,
            "avoid_explicit": True,
            "duration_range": (200000, 360000)  # 3-6 minutes
        }
    }
    
    preferences = mood_preferences.get(mood, mood_preferences["happy"])
    scored_tracks = []
    
    for track in tracks:
        score = 0
        
        # POPULARITY SCORE - Much more important now (0-60 points instead of 40)
        popularity = track.get("popularity", 0)
        if popularity >= preferences["min_popularity"]:
            score += min(popularity * 0.6, 60)  # Increased weight
        elif popularity >= 30:  # Give partial credit for moderately popular
            score += popularity * 0.3
        else:
            score -= 20  # Penalty for very low popularity
        
        # Duration score (0-20 points)
        duration = track.get("duration_ms", 0)
        if preferences["duration_range"][0] <= duration <= preferences["duration_range"][1]:
            score += 20
        elif duration > 0:
            score += 10  # Partial points for any duration
        
        # Explicit content penalty
        if preferences["avoid_explicit"] and track.get("explicit", False):
            score -= 15
        
        # Recent release bonus
        release_date = track.get("release_date", "")
        if preferences["prefer_recent"] and release_date:
            try:
                year = int(release_date[:4])
                if year >= 2020:
                    score += 15
                elif year >= 2015:
                    score += 8
            except (ValueError, IndexError):
                pass
        
        scored_tracks.append((score, track))
    
    # Sort by score descending and return the tracks
    scored_tracks.sort(key=lambda x: x[0], reverse=True)
    
    # Convert back to list of tracks with enhanced info
    ranked_tracks = []
    for score, track in scored_tracks:
        enhanced_track = track.copy()
        enhanced_track["ranking_score"] = score
        ranked_tracks.append(enhanced_track)
    
    return ranked_tracks


def _diversified_track_selection(all_tracks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Select diverse tracks from multiple search results to prevent duplicates.
    Ensures variety across different search types and artists.
    """
    if not all_tracks:
        return []
    
    # Remove exact duplicates by track ID
    seen_ids = set()
    unique_tracks = []
    for track in all_tracks:
        if track["id"] not in seen_ids:
            seen_ids.add(track["id"])
            unique_tracks.append(track)
    
    # Group tracks by search type for balanced selection
    search_type_groups = {}
    for track in unique_tracks:
        search_type = track.get("search_type", "unknown")
        if search_type not in search_type_groups:
            search_type_groups[search_type] = []
        search_type_groups[search_type].append(track)
    
    # Select tracks with artist diversity
    final_recommendations = []
    seen_artists = set()
    max_per_artist = 2  # Limit tracks per artist
    
    # Round-robin selection from different search types
    search_types = list(search_type_groups.keys())
    search_index = 0
    
    while len(final_recommendations) < 8 and any(search_type_groups.values()):
        # Get current search type
        current_search_type = search_types[search_index % len(search_types)]
        tracks_for_type = search_type_groups[current_search_type]
        
        if tracks_for_type:
            # Find a track from a new artist or one we haven't overused
            track_added = False
            for track in tracks_for_type[:]:  # Copy list to modify during iteration
                artist = track["artist"].lower()
                artist_count = sum(1 for t in final_recommendations if t["artist"].lower() == artist)
                
                if artist_count < max_per_artist:
                    final_recommendations.append(track)
                    tracks_for_type.remove(track)
                    track_added = True
                    break
            
            # If no suitable track found, move to next search type
            if not track_added:
                search_type_groups[current_search_type] = []  # Mark as exhausted
        
        search_index += 1
    
    print(f"Diversified selection: {len(final_recommendations)} tracks from {len(search_type_groups)} search types")
    
    # Sort by popularity for better user experience
    final_recommendations.sort(key=lambda x: x.get("popularity", 0), reverse=True)
    
    return final_recommendations[:8]  # Return max 8 tracks
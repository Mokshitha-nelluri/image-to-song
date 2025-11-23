"""
Quiz system endpoints for music preference discovery.
Handles quiz song delivery and preference calculation.
"""
import time
import random
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Query

from ..data.quiz_songs import QUIZ_SONGS

router = APIRouter(tags=["quiz"])


@router.get("/songs")
async def get_quiz_songs(limit: int = Query(20, ge=1, le=20)) -> Dict[str, Any]:
    """Get randomized songs for the quiz"""
    try:
        # Shuffle and limit songs
        shuffled_songs = random.sample(QUIZ_SONGS, min(limit, len(QUIZ_SONGS)))
        
        # Format for mobile app
        quiz_songs = []
        for i, song in enumerate(shuffled_songs):
            quiz_songs.append({
                "id": song["id"],
                "title": song["title"],
                "artist": song["artist"],
                "album": song["album"],
                "genres": song["genres"],
                "preview_url": song["preview_url"],
                "album_cover": song["album_cover"],
                "quiz_position": i + 1,
                "total_in_quiz": len(shuffled_songs)
            })
        
        return {
            "success": True,
            "quiz_songs": quiz_songs,
            "total_songs": len(quiz_songs),
            "instructions": {
                "swipe_right": "Like this song",
                "swipe_left": "Pass on this song",
                "tap_play": "Play 30-second preview",
                "progress": f"Rate {len(quiz_songs)} songs to build your music profile"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get quiz songs: {str(e)}")


@router.post("/calculate-preferences")
async def calculate_preferences(quiz_results: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate user music preferences from quiz results"""
    try:
        print(f"🧮 Calculating preferences from quiz results: {quiz_results}")
        
        # Extract liked and disliked songs
        liked_songs = []
        disliked_songs = []
        
        for song_rating in quiz_results.get("song_ratings", []):
            song_id = song_rating.get("song_id")
            user_liked = song_rating.get("liked")
            
            # Find the song in our database
            song_data = next((s for s in QUIZ_SONGS if s["id"] == song_id), None)
            if song_data:
                if user_liked:
                    liked_songs.append(song_data)
                else:
                    disliked_songs.append(song_data)
        
        print(f"👍 Liked songs: {len(liked_songs)}")
        print(f"👎 Disliked songs: {len(disliked_songs)}")
        
        # Calculate genre preferences
        genre_scores = {}
        for song in liked_songs:
            for genre in song["genres"]:
                genre_scores[genre] = genre_scores.get(genre, 0) + 1
        
        for song in disliked_songs:
            for genre in song["genres"]:
                genre_scores[genre] = genre_scores.get(genre, 0) - 0.5
        
        # Normalize genre preferences to 0-1 scale
        max_score = max(genre_scores.values()) if genre_scores else 1.0
        genre_preferences = {
            genre: float(max(0, score / max_score)) 
            for genre, score in genre_scores.items()
        }
        
        # Calculate audio feature preferences
        feature_preferences = {}
        audio_features = ['danceability', 'energy', 'valence', 'acousticness', 'instrumentalness']
        
        for feature in audio_features:
            liked_values = [song["audio_features"][feature] for song in liked_songs]
            disliked_values = [song["audio_features"][feature] for song in disliked_songs]
            
            if liked_values:
                liked_avg = sum(liked_values) / len(liked_values)
                
                if disliked_values:
                    disliked_avg = sum(disliked_values) / len(disliked_values)
                    # Adjust preference away from disliked average
                    preference = liked_avg + 0.1 * (liked_avg - disliked_avg)
                else:
                    preference = liked_avg
                
                feature_preferences[feature] = max(0, min(1, preference))
            else:
                feature_preferences[feature] = 0.5  # Default neutral
        
        # Generate user profile
        user_profile = {
            "user_id": quiz_results.get("user_id", f"user_{int(time.time())}"),
            "created_at": time.time(),
            "quiz_completed": True,
            "genre_preferences": genre_preferences,
            "audio_feature_preferences": feature_preferences,
            "liked_artists": list(set([song["artist"] for song in liked_songs])),
            "disliked_artists": list(set([song["artist"] for song in disliked_songs])),
            "quiz_stats": {
                "total_songs_rated": len(liked_songs) + len(disliked_songs),
                "songs_liked": len(liked_songs),
                "songs_disliked": len(disliked_songs),
                "completion_rate": (len(liked_songs) + len(disliked_songs)) / len(QUIZ_SONGS)
            }
        }
        
        print(f"✅ User profile generated: {user_profile}")
        
        return {
            "success": True,
            "user_profile": user_profile,
            "summary": {
                "top_genres": sorted(genre_preferences.items(), key=lambda x: x[1], reverse=True)[:3],
                "music_personality": _generate_music_personality(genre_preferences, feature_preferences),
                "recommendation_ready": True
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate preferences: {str(e)}")


def _generate_music_personality(genre_prefs: Dict[str, float], feature_prefs: Dict[str, float]) -> str:
    """Generate a fun music personality description"""
    top_genre = max(genre_prefs.items(), key=lambda x: x[1])[0] if genre_prefs else "eclectic"
    
    energy_level = feature_prefs.get("energy", 0.5)
    valence_level = feature_prefs.get("valence", 0.5)
    danceability = feature_prefs.get("danceability", 0.5)
    
    personalities = {
        ("pop", "high_energy", "positive"): "Pop Enthusiast - You love catchy, upbeat songs that make you smile!",
        ("rock", "high_energy", "positive"): "Rock Warrior - You crave powerful, energetic anthems!",
        ("hip hop", "high_energy", "positive"): "Hip-Hop Head - You vibe with rhythmic beats and clever lyrics!",
        ("electronic", "high_energy", "positive"): "Electronic Explorer - You're drawn to digital soundscapes and dance beats!",
        ("indie", "medium_energy", "positive"): "Indie Soul - You appreciate artistic, alternative sounds!",
        ("r&b", "medium_energy", "positive"): "R&B Lover - You're into smooth, soulful melodies!",
        ("country", "medium_energy", "positive"): "Country Heart - You enjoy storytelling and authentic vibes!",
        ("alternative", "medium_energy", "neutral"): "Alternative Spirit - You march to your own musical beat!"
    }
    
    # Classify energy and mood
    energy_cat = "high_energy" if energy_level > 0.6 else "medium_energy"
    mood_cat = "positive" if valence_level > 0.6 else "neutral"
    
    personality_key = (top_genre, energy_cat, mood_cat)
    return personalities.get(personality_key, f"Eclectic Listener - You have diverse taste in {top_genre} and beyond!")
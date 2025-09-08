"""
Image-to-Song App: Quiz-Based Music Preference System
Complete rewrite focusing on music quiz and preference-driven recommendations
"""
import asyncio
import io
import time
import base64
import os
import hashlib
import json
import random
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import existing services if available, otherwise use fallbacks
try:
    # Check if we're in a memory-constrained environment
    import os
    MEMORY_LIMIT = os.getenv('RENDER_MEMORY_LIMIT', '').lower() == 'true'
    
    if MEMORY_LIMIT:
        # Lightweight mode for free hosting
        from app.core.config import settings
        from app.utils.image_music_mapper import image_music_mapper
        hybrid_service = None  # Skip heavy AI model
        USE_AI_SERVICE = False
        print("⚡ Using Lightweight Mode (No AI model - optimized for free hosting)")
    else:
        # Full mode with AI
        from app.core.config import settings
        from app.services.hybrid_ai_service import hybrid_service
        from app.utils.image_music_mapper import image_music_mapper
        USE_AI_SERVICE = True
        print("✅ Using HybridImageService (BLIP + Color Analysis + Enhanced Mapping)")
except ImportError:
    try:
        from app.core.config import settings
        from app.services.ai_service import blip2_service as hybrid_service
        from app.utils.image_music_mapper import image_music_mapper
        USE_AI_SERVICE = True
        print("✅ Using BLIP2Service + Enhanced Mapping (fallback)")
    except ImportError:
        # Final fallback configuration
        class Settings:
            APP_NAME = "Image-to-Song Quiz App"
            APP_VERSION = "3.0.0"
            DEBUG = True
            HOST = "0.0.0.0"
            PORT = 8000
            LOG_LEVEL = "INFO"
            MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
            ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/jpg", "image/webp"]
            USE_GPU = False
        
        settings = Settings()
        hybrid_service = None
        image_music_mapper = None
        USE_AI_SERVICE = False
        print("ℹ️ Using SimpleImageAnalyzer only (no AI models)")

# Environment variables for Spotify Client Credentials (no user auth needed)
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID', '25de944a1992453896769027a9ffe3c1')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')

# Global variables
app_startup_time = None
spotify_access_token = None
token_expires_at = 0

class SimpleImageAnalyzer:
    """Simple image analyzer for mood detection"""
    
    def analyze_image(self, image_data: bytes) -> Dict[str, Any]:
        """Analyze image and extract mood"""
        try:
            print(f"🔍 SimpleImageAnalyzer: Starting analysis of {len(image_data)} bytes")
            
            # Open and analyze image
            image = Image.open(io.BytesIO(image_data))
            width, height = image.size
            print(f"📏 Image size: {width}x{height}")
            
            # Get dominant colors
            image_rgb = image.convert('RGB')
            colors = image_rgb.getcolors(maxcolors=256*256*256)
            
            if colors:
                dominant_color = max(colors, key=lambda x: x[0])[1]
                # Ensure we have a tuple of RGB values
                if isinstance(dominant_color, (tuple, list)) and len(dominant_color) >= 3:
                    r, g, b = dominant_color[:3]
                else:
                    # Fallback if color format is unexpected
                    r, g, b = 128, 128, 128
                
                # Color-based mood detection
                brightness = (r + g + b) / 3
                saturation = max(r, g, b) - min(r, g, b)
                
                mood = self._determine_mood_from_colors(r, g, b, brightness, saturation)
                color_info = {"dominant": f"rgb({r},{g},{b})", "brightness": brightness}
            else:
                mood = "neutral"
                r, g, b = 128, 128, 128
                brightness = 128
                color_info = {"dominant": f"rgb({r},{g},{b})", "brightness": brightness}
            
            # Generate caption
            caption = self._generate_caption(width, height, mood)
            
            result = {
                "caption": caption,
                "mood": mood,
                "confidence": 0.85,
                "colors": color_info,
                "size": f"{width}x{height}",
                "analysis_method": "color_based"
            }
            
            print(f"✅ Analysis complete: {result}")
            return result
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ SimpleImageAnalyzer error: {error_msg}")
            return {
                "caption": "a beautiful scene captured in an image",
                "mood": "neutral",
                "confidence": 0.5,
                "error": error_msg,
                "analysis_method": "fallback"
            }
    
    def _determine_mood_from_colors(self, r: int, g: int, b: int, brightness: float, saturation: float) -> str:
        """Determine mood based on color analysis"""
        if brightness > 200 and saturation > 100:
            return "energetic"
        elif brightness > 180:
            return "happy"
        elif brightness < 80:
            return "melancholic"
        elif g > r and g > b:  # Green dominant
            return "nature"
        elif b > 150:  # Blue dominant
            return "peaceful"
        elif r > 150 and brightness > 100:  # Red/warm
            return "romantic"
        else:
            return "neutral"
    
    def _generate_caption(self, width: int, height: int, mood: str) -> str:
        """Generate a realistic caption based on image properties"""
        captions = {
            "energetic": [
                "dynamic scene with vibrant colors and movement",
                "action-packed moment with bright lighting",
                "energetic composition with bold visual elements"
            ],
            "happy": [
                "bright and cheerful scene with warm lighting",
                "joyful moment captured with vivid colors",
                "uplifting image with positive atmosphere"
            ],
            "peaceful": [
                "serene landscape with calm atmosphere",
                "tranquil scene with soft lighting",
                "peaceful moment in natural setting"
            ],
            "melancholic": [
                "moody scene with atmospheric lighting",
                "contemplative moment with subtle tones",
                "reflective composition with muted colors"
            ],
            "nature": [
                "beautiful natural landscape with greenery",
                "outdoor scene with natural elements",
                "scenic view of nature with organic forms"
            ],
            "romantic": [
                "romantic scene with warm ambient lighting",
                "intimate moment with soft color palette",
                "beautiful composition with romantic atmosphere"
            ]
        }
        
        mood_captions = captions.get(mood, ["scenic image with artistic composition"])
        return random.choice(mood_captions)

# Initialize image analyzer
image_analyzer = SimpleImageAnalyzer()

# Quiz song database - curated songs with preview URLs
QUIZ_SONGS = [
    # Pop (4 songs)
    {
        "id": "4uLU6hMCjMI75M1A2tKUQC",
        "title": "Anti-Hero",
        "artist": "Taylor Swift",
        "album": "Midnights",
        "genres": ["pop", "indie pop"],
        "preview_url": "https://p.scdn.co/mp3-preview/...",  # Will be updated with real URLs
        "album_cover": "https://i.scdn.co/image/ab67616d0000b273bb54dde68cd23e2a268ae0f5",
        "audio_features": {
            "danceability": 0.579,
            "energy": 0.513,
            "valence": 0.321,
            "acousticness": 0.257,
            "instrumentalness": 0.000001,
            "tempo": 96.881,
            "loudness": -8.6
        }
    },
    {
        "id": "1BxfuPKGuaTgP7aM0Bbdwr",
        "title": "Cruel Summer",
        "artist": "Taylor Swift",
        "album": "Lover",
        "genres": ["pop", "synth-pop"],
        "preview_url": "https://p.scdn.co/mp3-preview/...",
        "album_cover": "https://i.scdn.co/image/ab67616d0000b273e787cffec20aa2a396a61647",
        "audio_features": {
            "danceability": 0.552,
            "energy": 0.702,
            "valence": 0.564,
            "acousticness": 0.117,
            "instrumentalness": 0.000096,
            "tempo": 169.994,
            "loudness": -5.707
        }
    },
    {
        "id": "4Dvkj6JhhA12EX05fT7y2e",
        "title": "As It Was",
        "artist": "Harry Styles",
        "album": "Harry's House",
        "genres": ["pop", "art pop"],
        "preview_url": "https://p.scdn.co/mp3-preview/...",
        "album_cover": "https://i.scdn.co/image/ab67616d0000b2732e8ed79e177ff6011076f5f0",
        "audio_features": {
            "danceability": 0.685,
            "energy": 0.549,
            "valence": 0.359,
            "acousticness": 0.361,
            "instrumentalness": 0.000003,
            "tempo": 108.009,
            "loudness": -7.667
        }
    },
    {
        "id": "7qiZfU4dY1lWllzX7mPBI3",
        "title": "Shape of You",
        "artist": "Ed Sheeran",
        "album": "÷ (Divide)",
        "genres": ["pop", "dance pop"],
        "preview_url": "https://p.scdn.co/mp3-preview/...",
        "album_cover": "https://i.scdn.co/image/ab67616d0000b273ba5db46f4b838ef6027e6f96",
        "audio_features": {
            "danceability": 0.825,
            "energy": 0.652,
            "valence": 0.931,
            "acousticness": 0.581,
            "instrumentalness": 0.000002,
            "tempo": 95.977,
            "loudness": -3.183
        }
    },
    
    # Rock (3 songs)
    {
        "id": "0VjIjW4GlULA4LGy1nby9d",
        "title": "Bohemian Rhapsody",
        "artist": "Queen",
        "album": "A Night at the Opera",
        "genres": ["rock", "classic rock"],
        "preview_url": "https://p.scdn.co/mp3-preview/...",
        "album_cover": "https://i.scdn.co/image/ab67616d0000b273e319baafd16e84f0408af2a0",
        "audio_features": {
            "danceability": 0.495,
            "energy": 0.618,
            "valence": 0.579,
            "acousticness": 0.213,
            "instrumentalness": 0.001,
            "tempo": 144.077,
            "loudness": -8.235
        }
    },
    {
        "id": "4VqPOruhp5EdPBeR92t6lQ",
        "title": "Stairway to Heaven",
        "artist": "Led Zeppelin",
        "album": "Led Zeppelin IV",
        "genres": ["rock", "hard rock"],
        "preview_url": "https://p.scdn.co/mp3-preview/...",
        "album_cover": "https://i.scdn.co/image/ab67616d0000b2732ac77543e4dd391bfb3a93b6",
        "audio_features": {
            "danceability": 0.378,
            "energy": 0.541,
            "valence": 0.446,
            "acousticness": 0.309,
            "instrumentalness": 0.274,
            "tempo": 81.995,
            "loudness": -14.123
        }
    },
    {
        "id": "0JiV5NKJP0vC8hOJKWMJ7y",
        "title": "Don't Stop Believin'",
        "artist": "Journey",
        "album": "Escape",
        "genres": ["rock", "arena rock"],
        "preview_url": "https://p.scdn.co/mp3-preview/...",
        "album_cover": "https://i.scdn.co/image/ab67616d0000b2732e77e624a0225686f4e62af6",
        "audio_features": {
            "danceability": 0.563,
            "energy": 0.736,
            "valence": 0.899,
            "acousticness": 0.00131,
            "instrumentalness": 0.000014,
            "tempo": 119.069,
            "loudness": -6.011
        }
    },
    
    # Hip-Hop (3 songs)
    {
        "id": "6DCZcSspjsKoFjzjrWoCdn",
        "title": "God's Plan",
        "artist": "Drake",
        "album": "Scorpion",
        "genres": ["hip hop", "pop rap"],
        "preview_url": "https://p.scdn.co/mp3-preview/...",
        "album_cover": "https://i.scdn.co/image/ab67616d0000b273f907de96b9a4fbc04accc0d5",
        "audio_features": {
            "danceability": 0.754,
            "energy": 0.449,
            "valence": 0.357,
            "acousticness": 0.00685,
            "instrumentalness": 0.000001,
            "tempo": 77.169,
            "loudness": -9.211
        }
    },
    {
        "id": "7ouMYWpwJ422jRcDASZB7P",
        "title": "HUMBLE.",
        "artist": "Kendrick Lamar",
        "album": "DAMN.",
        "genres": ["hip hop", "conscious rap"],
        "preview_url": "https://p.scdn.co/mp3-preview/...",
        "album_cover": "https://i.scdn.co/image/ab67616d0000b2738b52c6b9bc4e43d873869699",
        "audio_features": {
            "danceability": 0.904,
            "energy": 0.621,
            "valence": 0.421,
            "acousticness": 0.000548,
            "instrumentalness": 0.000024,
            "tempo": 150.020,
            "loudness": -6.842
        }
    },
    {
        "id": "5W3cjX2J3tjhG8zb6u0qHn",
        "title": "Old Town Road",
        "artist": "Lil Nas X",
        "album": "7 EP",
        "genres": ["hip hop", "country rap"],
        "preview_url": "https://p.scdn.co/mp3-preview/...",
        "album_cover": "https://i.scdn.co/image/ab67616d0000b273a5c40298ab23da2ac819f9ab",
        "audio_features": {
            "danceability": 0.876,
            "energy": 0.555,
            "valence": 0.687,
            "acousticness": 0.132,
            "instrumentalness": 0.000003,
            "tempo": 136.041,
            "loudness": -8.871
        }
    },
    
    # Electronic (2 songs)
    {
        "id": "4Y7KDMX07MCuZo10LPW60s",
        "title": "Clarity",
        "artist": "Zedd",
        "album": "Clarity",
        "genres": ["electronic", "progressive house"],
        "preview_url": "https://p.scdn.co/mp3-preview/...",
        "album_cover": "https://i.scdn.co/image/ab67616d0000b27331c35347e0ec535429c0addc",
        "audio_features": {
            "danceability": 0.473,
            "energy": 0.793,
            "valence": 0.394,
            "acousticness": 0.000234,
            "instrumentalness": 0.000001,
            "tempo": 128.026,
            "loudness": -4.669
        }
    },
    {
        "id": "1vYXt7VSjH9JIM5oewBZNF",
        "title": "Midnight City",
        "artist": "M83",
        "album": "Hurry Up, We're Dreaming",
        "genres": ["electronic", "synthwave"],
        "preview_url": "https://p.scdn.co/mp3-preview/...",
        "album_cover": "https://i.scdn.co/image/ab67616d0000b273bb0e9b14abea7d52e3f7ad58",
        "audio_features": {
            "danceability": 0.511,
            "energy": 0.789,
            "valence": 0.749,
            "acousticness": 0.000069,
            "instrumentalness": 0.893,
            "tempo": 104.896,
            "loudness": -6.398
        }
    },
    
    # Indie (2 songs)
    {
        "id": "2Z8WuEywRWYTKe1NybPQEW",
        "title": "Somebody That I Used to Know",
        "artist": "Gotye",
        "album": "Making Mirrors",
        "genres": ["indie", "alternative"],
        "preview_url": "https://p.scdn.co/mp3-preview/...",
        "album_cover": "https://i.scdn.co/image/ab67616d0000b273f9c35bd8b2fbb68b90b7bbc6",
        "audio_features": {
            "danceability": 0.684,
            "energy": 0.449,
            "valence": 0.425,
            "acousticness": 0.102,
            "instrumentalness": 0.000063,
            "tempo": 129.874,
            "loudness": -7.883
        }
    },
    {
        "id": "0VE4kBnHJEhHWW8nnB2OAJ",
        "title": "Young Folks",
        "artist": "Peter Bjorn and John",
        "album": "Writer's Block",
        "genres": ["indie", "indie pop"],
        "preview_url": "https://p.scdn.co/mp3-preview/...",
        "album_cover": "https://i.scdn.co/image/ab67616d0000b273abc34a5e2c52ec8f3b5ddd35",
        "audio_features": {
            "danceability": 0.728,
            "energy": 0.712,
            "valence": 0.819,
            "acousticness": 0.186,
            "instrumentalness": 0.105,
            "tempo": 120.047,
            "loudness": -6.895
        }
    },
    
    # R&B (2 songs)
    {
        "id": "7dt6x5M1jzdTEt8oCbisTK",
        "title": "Redbone",
        "artist": "Childish Gambino",
        "album": "Awaken, My Love!",
        "genres": ["r&b", "funk"],
        "preview_url": "https://p.scdn.co/mp3-preview/...",
        "album_cover": "https://i.scdn.co/image/ab67616d0000b2733b5e11ca1b063583df9492db",
        "audio_features": {
            "danceability": 0.738,
            "energy": 0.345,
            "valence": 0.467,
            "acousticness": 0.423,
            "instrumentalness": 0.000017,
            "tempo": 158.784,
            "loudness": -14.558
        }
    },
    {
        "id": "4rXVn5n57hCcKXJ5ZQeaB9",
        "title": "Blinding Lights",
        "artist": "The Weeknd",
        "album": "After Hours",
        "genres": ["r&b", "synthwave"],
        "preview_url": "https://p.scdn.co/mp3-preview/...",
        "album_cover": "https://i.scdn.co/image/ab67616d0000b2738863bc11d2aa12b54f5aeb36",
        "audio_features": {
            "danceability": 0.514,
            "energy": 0.73,
            "valence": 0.334,
            "acousticness": 0.00146,
            "instrumentalness": 0.000002,
            "tempo": 171.009,
            "loudness": -5.934
        }
    },
    
    # Country (2 songs)
    {
        "id": "1Je1IMUlBXcx1Fz0WE7oPT",
        "title": "Cruise",
        "artist": "Florida Georgia Line",
        "album": "Here's to the Good Times",
        "genres": ["country", "country pop"],
        "preview_url": "https://p.scdn.co/mp3-preview/...",
        "album_cover": "https://i.scdn.co/image/ab67616d0000b273f9b8b5f60b6b2bb5f9b8b5f6",
        "audio_features": {
            "danceability": 0.648,
            "energy": 0.693,
            "valence": 0.959,
            "acousticness": 0.0851,
            "instrumentalness": 0.000000,
            "tempo": 120.043,
            "loudness": -4.359
        }
    },
    {
        "id": "1zHlj4dQ8ZAtrayhuDDmkY",
        "title": "Need You Now",
        "artist": "Lady Antebellum",
        "album": "Need You Now",
        "genres": ["country", "country pop"],
        "preview_url": "https://p.scdn.co/mp3-preview/...",
        "album_cover": "https://i.scdn.co/image/ab67616d0000b273f9b8b5f60b6b2bb5f9b8b5f6",
        "audio_features": {
            "danceability": 0.567,
            "energy": 0.506,
            "valence": 0.284,
            "acousticness": 0.372,
            "instrumentalness": 0.000000,
            "tempo": 132.013,
            "loudness": -7.965
        }
    },
    
    # Alternative (2 songs)
    {
        "id": "7GhIk7Il098yCjg4BQjzvb",
        "title": "Radioactive",
        "artist": "Imagine Dragons",
        "album": "Night Visions",
        "genres": ["alternative", "rock"],
        "preview_url": "https://p.scdn.co/mp3-preview/...",
        "album_cover": "https://i.scdn.co/image/ab67616d0000b273b83b446d40addb05b033e3ad",
        "audio_features": {
            "danceability": 0.593,
            "energy": 0.867,
            "valence": 0.334,
            "acousticness": 0.000081,
            "instrumentalness": 0.000002,
            "tempo": 136.040,
            "loudness": -4.464
        }
    },
    {
        "id": "1mea3bSkSGXuIRvnydlB5b",
        "title": "Pumped Up Kicks",
        "artist": "Foster the People",
        "album": "Torches",
        "genres": ["alternative", "indie pop"],
        "preview_url": "https://p.scdn.co/mp3-preview/...",
        "album_cover": "https://i.scdn.co/image/ab67616d0000b273f9b8b5f60b6b2bb5f9b8b5f6",
        "audio_features": {
            "danceability": 0.703,
            "energy": 0.622,
            "valence": 0.686,
            "acousticness": 0.011,
            "instrumentalness": 0.000105,
            "tempo": 127.851,
            "loudness": -6.958
        }
    }
]

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

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global app_startup_time
    
    # Startup
    print("🚀 Starting Image-to-Song Quiz App...")
    app_startup_time = time.time()
    
    # Load AI model if available
    if USE_AI_SERVICE and hybrid_service:
        try:
            print("Loading Hybrid AI model...")
            await hybrid_service.load_model()
            print("✅ Hybrid AI model loaded successfully")
        except Exception as e:
            print(f"❌ Failed to load Hybrid AI model: {e}")
            print("🔄 Falling back to simple analyzer")
    else:
        print("📝 Using simple image analyzer (no AI dependencies)")
    
    # Get initial Spotify token
    token = await get_spotify_token()
    if token:
        print("✅ Spotify Client Credentials obtained")
    else:
        print("⚠️ Spotify integration not available")
    
    startup_duration = time.time() - app_startup_time
    print(f"✅ API started in {startup_duration:.2f} seconds")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Image-to-Song Quiz App...")
    if USE_AI_SERVICE and hybrid_service:
        try:
            await hybrid_service.cleanup()
        except:
            pass
    print("✅ Cleanup completed")

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Quiz-based music preference system with image analysis",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint with API information"""
    return {
        "message": "Image-to-Song Quiz App API",
        "version": settings.APP_VERSION,
        "status": "running",
        "features": {
            "music_quiz": True,
            "image_analysis": True,
            "preference_recommendations": True,
            "spotify_search": bool(SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET),
            "ai_service": USE_AI_SERVICE,
            "song_previews": True
        },
        "endpoints": {
            "health": "/health",
            "quiz_songs": "/quiz/songs",
            "calculate_preferences": "/quiz/calculate-preferences",
            "analyze_image": "/analyze-image",
            "recommendations": "/recommendations",
            "search_songs": "/search/songs"
        }
    }

@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint with detailed status"""
    global app_startup_time
    
    uptime = time.time() - app_startup_time if app_startup_time else 0
    
    # Check if AI model is loaded (if using AI service)
    model_loaded = False
    if USE_AI_SERVICE and hybrid_service:
        try:
            model_info = await hybrid_service.get_model_info()
            model_loaded = model_info.get("status") == "loaded"
        except:
            model_loaded = False
    
    # Check Spotify token status
    spotify_status = "available" if spotify_access_token else "not_available"
    
    return {
        "status": "healthy",
        "uptime_seconds": round(uptime, 2),
        "model_loaded": model_loaded if USE_AI_SERVICE else "using_simple_analyzer",
        "spotify_status": spotify_status,
        "quiz_songs_available": len(QUIZ_SONGS),
        "version": settings.APP_VERSION,
        "timestamp": time.time()
    }

# Quiz system endpoints
@app.get("/quiz/songs")
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

@app.post("/quiz/calculate-preferences")
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

# Image analysis endpoint
@app.post("/analyze-image")
async def analyze_image(file: UploadFile = File(...)):
    """Analyze uploaded image for mood and context"""
    print(f"🖼️ === ANALYZE IMAGE ===")
    print(f"📁 File: {file.filename}")
    print(f"📄 Content-Type: {file.content_type}")
    
    try:
        # Read file data
        image_data = await file.read()
        print(f"📏 File size: {len(image_data)} bytes")
        
        if len(image_data) == 0:
            raise HTTPException(status_code=400, detail="Empty file received")
        
        # Use AI service if available, otherwise use simple analyzer
        if USE_AI_SERVICE and hybrid_service:
            try:
                # Check if this is the hybrid service or old service
                if hasattr(hybrid_service, 'analyze_image'):
                    # New hybrid service
                    result = await hybrid_service.analyze_image(image_data)  # type: ignore
                    result["filename"] = file.filename or "image.jpg"
                else:
                    # Old BLIP2 service - generate caption and combine with simple analysis
                    caption = await hybrid_service.generate_caption(image_data)  # type: ignore
                    simple_result = image_analyzer.analyze_image(image_data)
                    
                    result = {
                        "status": "success",
                        "filename": file.filename or "image.jpg",
                        "caption": caption,
                        "mood": simple_result["mood"],
                        "confidence": 0.9,
                        "colors": simple_result["colors"],
                        "size": simple_result["size"],
                        "analysis_method": "blip2_plus_color"
                    }
                
            except Exception as e:
                print(f"AI analysis failed, falling back to simple: {e}")
                result = image_analyzer.analyze_image(image_data)
                result["status"] = "success"
                result["filename"] = file.filename or "image.jpg"
        else:
            # Use simple analyzer only
            result = image_analyzer.analyze_image(image_data)
            result["status"] = "success"
            result["filename"] = file.filename or "image.jpg"
        
        print(f"✅ Image analysis result: {result}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Image analysis error: {error_msg}")
        raise HTTPException(status_code=500, detail=f"Image processing failed: {error_msg}")

@app.post("/analyze-and-recommend")
async def analyze_and_recommend(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Enhanced endpoint: Analyze image with BLIP + Color analysis, then generate music recommendations
    using the intelligent image-to-music mapping system.
    """
    try:
        print(f"🎵 Enhanced Analysis & Recommendation for: {file.filename}")
        
        # First, analyze the image
        image_data = await file.read()
        
        # Use hybrid service if available
        if USE_AI_SERVICE and hybrid_service:
            try:
                if hasattr(hybrid_service, 'analyze_image'):
                    # New hybrid service
                    analysis_result = await hybrid_service.analyze_image(image_data)  # type: ignore
                else:
                    # Old BLIP2 service - generate caption and combine with simple analysis
                    caption = await hybrid_service.generate_caption(image_data)  # type: ignore
                    simple_result = image_analyzer.analyze_image(image_data)
                    
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
                analysis_result = image_analyzer.analyze_image(image_data)
        else:
            # Use simple analyzer only
            analysis_result = image_analyzer.analyze_image(image_data)
        
        # Create enhanced music profile using the mapper
        if image_music_mapper and analysis_result:
            scene_description = analysis_result.get("scene_description") or analysis_result.get("caption", "")
            mood = analysis_result.get("mood", "neutral")
            colors = analysis_result.get("colors", {})
            
            music_profile = image_music_mapper.create_music_profile(scene_description, mood, colors)
            search_queries = image_music_mapper.get_search_queries(music_profile, mood)
            
            print(f"🎼 Generated music profile: {music_profile['recommended_genres']}")
            print(f"🔍 Search queries: {search_queries[:3]}")
            
            # Get Spotify token and search for songs
            token = await get_spotify_token()
            if not token:
                print("⚠️ Spotify unavailable, using fallback recommendations from quiz songs")
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
                print("⚠️ Spotify unavailable, using fallback recommendations from quiz songs")
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
        print(f"❌ Enhanced analysis error: {error_msg}")
        raise HTTPException(status_code=500, detail=f"Enhanced analysis failed: {error_msg}")

# Recommendation system
@app.post("/recommendations")
async def get_recommendations(request: Dict[str, Any]) -> Dict[str, Any]:
    """Get personalized song recommendations based on image mood + user preferences"""
    try:
        mood = request.get('mood', 'neutral')
        caption = request.get('caption', '')
        user_profile = request.get('user_profile', {})
        
        print(f"🎵 Getting recommendations for mood: {mood}")
        print(f"👤 User profile provided: {bool(user_profile)}")
        
        # Get Spotify token
        token = await get_spotify_token()
        if not token:
            return _get_fallback_recommendations(mood, user_profile)
        
        # Combine image mood with user preferences
        search_params = _build_search_parameters(mood, caption, user_profile)
        
        print(f"🔍 Search queries: {search_params['queries']}")
        print(f"📋 Strategy: {search_params['strategy']}")
        
        recommendations = []
        async with httpx.AsyncClient() as client:
            headers = {'Authorization': f'Bearer {token}'}
            
            # Search for songs based on combined preferences
            for search_query in search_params["queries"]:
                try:
                    print(f"🎯 Searching for: '{search_query}'")
                    search_response = await client.get(
                        'https://api.spotify.com/v1/search',
                        headers=headers,
                        params={
                            'q': search_query,
                            'type': 'track',
                            'limit': 20,
                            'market': 'US'
                        }
                    )
                    
                    if search_response.status_code == 200:
                        tracks = search_response.json()['tracks']['items']
                        print(f"📀 Found {len(tracks)} tracks for '{search_query}'")
                        
                        tracks_with_preview = 0
                        tracks_added = 0
                        for track in tracks:
                            # Add all tracks, not just those with previews
                            recommendations.append({
                                "id": track['id'],
                                "title": track['name'],
                                "artist": track['artists'][0]['name'],
                                "album": track['album']['name'],
                                "preview_url": track.get('preview_url'),  # Optional now
                                "spotify_url": track['external_urls']['spotify'],
                                "album_cover": track['album']['images'][0]['url'] if track['album']['images'] else None,
                                "popularity": track['popularity'],
                                "duration_ms": track['duration_ms'],
                                "explicit": track['explicit']
                            })
                            tracks_added += 1
                            
                            if track.get('preview_url'):
                                tracks_with_preview += 1
                        
                        print(f"🎵 Added {tracks_added} tracks ({tracks_with_preview} with previews)")
                        
                        if len(recommendations) >= 10:  # Got enough recommendations
                            break
                    else:
                        print(f"❌ Spotify search failed: {search_response.status_code}")
                            
                except Exception as e:
                    print(f"❌ Search query failed: {search_query}, error: {e}")
                    continue
        
        # Remove duplicates and limit results
        seen_ids = set()
        unique_recommendations = []
        for rec in recommendations:
            if rec["id"] not in seen_ids:
                seen_ids.add(rec["id"])
                unique_recommendations.append(rec)
                if len(unique_recommendations) >= 8:
                    break
        
        print(f"✅ Final recommendations: {len(unique_recommendations)}")
        
        # Always return what we found, no minimum threshold needed
        return {
            "success": True,
            "mood": mood,
            "caption": caption,
            "recommendations": unique_recommendations,
            "search_strategy": search_params["strategy"],
            "total_found": len(unique_recommendations),
            "personalized": bool(user_profile)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendations failed: {str(e)}")

def _build_search_parameters(mood: str, caption: str, user_profile: Dict[str, Any]) -> Dict[str, Any]:
    """Build intelligent search parameters mapping moods to musical characteristics and popular songs"""
    
    # Smart mood-to-music mapping focusing on ARTISTS, GENRES, and MUSICAL FEATURES
    mood_search_strategies = {
        "happy": {
            "artists": ["Pharrell Williams", "Bruno Mars", "Dua Lipa", "Justin Timberlake", "Lizzo"],
            "genres": ["pop", "funk", "dance pop", "upbeat rock"],
            "characteristics": ["major key", "upbeat tempo", "energetic"],
            "popular_songs": ["Happy", "Uptown Funk", "Can't Stop the Feeling", "Good as Hell"]
        },
        "peaceful": {
            "artists": ["Bon Iver", "Norah Jones", "James Blake", "Billie Eilish", "Lana Del Rey"],
            "genres": ["indie folk", "ambient", "soft rock", "chillout"],
            "characteristics": ["slow tempo", "acoustic", "soft vocals"],
            "popular_songs": ["Holocene", "Come Away With Me", "ocean eyes", "Video Games"]
        },
        "energetic": {
            "artists": ["The Weeknd", "Daft Punk", "Calvin Harris", "Eminem", "Imagine Dragons"],
            "genres": ["electronic", "hip hop", "rock", "dance"],
            "characteristics": ["high energy", "driving beat", "powerful vocals"],
            "popular_songs": ["Blinding Lights", "One More Time", "Thunder", "Lose Yourself"]
        },
        "melancholic": {
            "artists": ["Radiohead", "Adele", "Johnny Cash", "The National", "Sufjan Stevens"],
            "genres": ["alternative rock", "indie", "folk", "soul"],
            "characteristics": ["minor key", "emotional vocals", "introspective"],
            "popular_songs": ["Creep", "Someone Like You", "Hurt", "Mad World"]
        },
        "romantic": {
            "artists": ["John Legend", "Ed Sheeran", "Alicia Keys", "Sam Smith", "H.E.R."],
            "genres": ["R&B", "soul", "acoustic pop", "ballad"],
            "characteristics": ["love theme", "tender vocals", "intimate"],
            "popular_songs": ["All of Me", "Perfect", "Stay With Me", "Best Part"]
        },
        "nature": {
            "artists": ["Fleet Foxes", "Iron & Wine", "Kings of Leon", "Mumford & Sons"],
            "genres": ["folk", "indie folk", "acoustic", "country"],
            "characteristics": ["organic sounds", "acoustic guitar", "natural themes"],
            "popular_songs": ["White Winter Hymnal", "Boy with a Coin", "Use Somebody"]
        },
        "neutral": {
            "artists": ["Taylor Swift", "Drake", "Billie Eilish", "Post Malone", "Ariana Grande"],
            "genres": ["pop", "hip hop", "alternative"],
            "characteristics": ["mainstream appeal", "current trends"],
            "popular_songs": ["Anti-Hero", "God's Plan", "thank u, next", "Circles"]
        }
    }
    
    strategy_data = mood_search_strategies.get(mood, mood_search_strategies["neutral"])
    final_queries = []
    
    # 1. Search by POPULAR ARTISTS known for this mood
    artists = strategy_data["artists"][:3]  # Top 3 artists
    for artist in artists:
        final_queries.append(f"artist:{artist}")
    
    # 2. Search by GENRE combinations
    genres = strategy_data["genres"][:2]  # Top 2 genres
    for genre in genres:
        final_queries.append(f"genre:{genre}")
    
    # 3. Add user preference integration if available
    if user_profile and user_profile.get("genre_preferences"):
        genre_prefs = user_profile["genre_preferences"]
        top_user_genres = sorted(genre_prefs.items(), key=lambda x: x[1], reverse=True)[:2]
        
        # Combine user preferences with mood-appropriate artists
        for genre, score in top_user_genres:
            if score > 0.3:
                # Find artists from user's preferred genre that match the mood
                final_queries.append(f"genre:{genre}")
        
        strategy = "intelligent_personalized"
    else:
        strategy = "intelligent_mood_based"
    
    # 4. Add popular songs as backup (without explicit mood words)
    final_queries.extend(["year:2020-2024", "popularity:70..100"])
    
    return {
        "queries": final_queries[:8],  # More diverse queries
        "strategy": strategy,
        "mood_context": strategy_data
    }

def _rank_songs_by_characteristics(tracks: List[Dict[str, Any]], mood: str) -> List[Dict[str, Any]]:
    """Rank songs based on musical characteristics and mood appropriateness"""
    
    # Define mood preferences for ranking
    mood_preferences = {
        "happy": {
            "min_popularity": 30,
            "prefer_recent": True,
            "avoid_explicit": True,
            "duration_range": (120000, 300000)  # 2-5 minutes
        },
        "melancholic": {
            "min_popularity": 20,
            "prefer_recent": False,
            "avoid_explicit": False,
            "duration_range": (180000, 360000)  # 3-6 minutes
        },
        "energetic": {
            "min_popularity": 40,
            "prefer_recent": True,
            "avoid_explicit": False,
            "duration_range": (150000, 300000)  # 2.5-5 minutes
        },
        "peaceful": {
            "min_popularity": 15,
            "prefer_recent": False,
            "avoid_explicit": True,
            "duration_range": (180000, 420000)  # 3-7 minutes
        },
        "romantic": {
            "min_popularity": 25,
            "prefer_recent": False,
            "avoid_explicit": True,
            "duration_range": (200000, 360000)  # 3-6 minutes
        }
    }
    
    preferences = mood_preferences.get(mood, mood_preferences["happy"])
    scored_tracks = []
    
    for track in tracks:
        score = 0
        
        # Popularity score (0-40 points)
        popularity = track.get("popularity", 0)
        if popularity >= preferences["min_popularity"]:
            score += min(popularity * 0.4, 40)
        
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
        
        # Avoid songs with obvious mood words in title (too literal)
        title_lower = track.get("name", "").lower()
        literal_mood_words = ["sad", "happy", "emotional", "melancholic", "depressed", "joyful"]
        if any(word in title_lower for word in literal_mood_words):
            score -= 25  # Heavy penalty for literal mood words
        
        # Bonus for real artists (not generic background music)
        artist_name = track.get("artist", "").lower()
        generic_terms = ["background", "instrumental", "meditation", "royalty free", "stock"]
        if not any(term in artist_name for term in generic_terms):
            score += 10
        
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

# Search endpoint for additional functionality
@app.get("/search/songs")
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

# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc) if settings.DEBUG else "An unexpected error occurred"
        }
    )

if __name__ == "__main__":
    import uvicorn
    
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"Debug mode: {settings.DEBUG}")
    print(f"AI Service: {USE_AI_SERVICE}")
    print(f"Spotify Client Credentials: {bool(SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET)}")
    print(f"Quiz songs available: {len(QUIZ_SONGS)}")
    
    uvicorn.run(
        "main_quiz:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower() if hasattr(settings, 'LOG_LEVEL') else "info"
    )

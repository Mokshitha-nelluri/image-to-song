"""
Complete Image-to-Song Pipeline
OAuth + AI Image Analysis + Mixed Personalized Recommendations
This is the main backend entry point with full functionality.
"""
import asyncio
import io
import time
import base64
import secrets
import os
import hashlib
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional
from urllib.parse import urlencode

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from PIL import Image
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import existing services if available, otherwise use fallbacks
try:
    from app.core.config import settings
    from app.services.ai_service import blip2_service
    from app.utils.image_utils import ImageProcessor
    USE_AI_SERVICE = True
except ImportError:
    # Fallback configuration
    class Settings:
        APP_NAME = "Image-to-Song Complete Pipeline"
        APP_VERSION = "2.0.0"
        DEBUG = True
        HOST = "0.0.0.0"
        PORT = 8000
        LOG_LEVEL = "INFO"
        MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
        ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/jpg", "image/webp"]
        USE_GPU = False
    
    settings = Settings()
    USE_AI_SERVICE = False

# Environment variables
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID', '25de944a1992453896769027a9ffe3c1')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
SPOTIFY_REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI', 'https://image-to-song.onrender.com/spotify/callback')

# In-memory storage for demo (use Redis/DB in production)
auth_sessions = {}
user_tokens = {}  # Store user tokens by session

class SimpleImageAnalyzer:
    """Simple image analyzer without heavy AI dependencies for cloud deployment"""
    
    def analyze_image(self, image_data: bytes) -> Dict[str, Any]:
        """Analyze image and extract mood - simplified version for deployment"""
        try:
            print(f"SimpleImageAnalyzer: Starting analysis of {len(image_data)} bytes")
            
            # Open and analyze image
            try:
                image = Image.open(io.BytesIO(image_data))
                print(f"SimpleImageAnalyzer: Successfully opened image")
            except Exception as e:
                print(f"SimpleImageAnalyzer: Failed to open image: {e}")
                raise Exception(f"Failed to open image: {e}")
            
            try:
                width, height = image.size
                print(f"SimpleImageAnalyzer: Image size: {width}x{height}")
            except Exception as e:
                print(f"SimpleImageAnalyzer: Failed to get image size: {e}")
                raise Exception(f"Failed to get image size: {e}")
            
            # Get dominant colors (simplified)
            try:
                image_rgb = image.convert('RGB')
                print(f"SimpleImageAnalyzer: Converted to RGB")
                colors = image_rgb.getcolors(maxcolors=256*256*256)
                print(f"SimpleImageAnalyzer: Got {len(colors) if colors else 0} colors")
            except Exception as e:
                print(f"SimpleImageAnalyzer: Failed to get colors: {e}")
                raise Exception(f"Failed to analyze colors: {e}")
            
            if colors:
                try:
                    dominant_color = max(colors, key=lambda x: x[0])[1]
                    r, g, b = dominant_color
                    
                    # Simple mood detection based on color analysis
                    brightness = (r + g + b) / 3
                    saturation = max(r, g, b) - min(r, g, b)
                    
                    mood = self._determine_mood_from_colors(r, g, b, brightness, saturation)
                    
                    color_info = {"dominant": f"rgb({r},{g},{b})", "brightness": brightness}
                    print(f"SimpleImageAnalyzer: Color analysis successful - mood: {mood}")
                except Exception as e:
                    print(f"SimpleImageAnalyzer: Failed to analyze dominant color: {e}")
                    raise Exception(f"Failed to analyze dominant color: {e}")
            else:
                mood = "neutral"
                r, g, b = 128, 128, 128  # Default gray
                brightness = 128
                color_info = {"dominant": f"rgb({r},{g},{b})", "brightness": brightness}
                print(f"SimpleImageAnalyzer: No colors found, using defaults")
            
            # Generate a realistic caption based on image properties
            try:
                caption = self._generate_caption(width, height, mood)
                print(f"SimpleImageAnalyzer: Generated caption: {caption}")
            except Exception as e:
                print(f"SimpleImageAnalyzer: Failed to generate caption: {e}")
                caption = "a beautiful scene"
            
            result = {
                "caption": caption,
                "mood": mood,
                "confidence": 0.85,
                "colors": color_info,
                "size": f"{width}x{height}",
                "analysis_method": "color_based"
            }
            
            print(f"SimpleImageAnalyzer: Analysis complete: {result}")
            return result
            
        except Exception as e:
            error_msg = str(e) if str(e) else f"Unknown SimpleImageAnalyzer error of type {type(e).__name__}"
            print(f"SimpleImageAnalyzer: Exception occurred: {error_msg}")
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
        import random
        return random.choice(mood_captions)

# Initialize image analyzer
image_analyzer = SimpleImageAnalyzer()

# Global variables for tracking
app_startup_time = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global app_startup_time
    
    # Startup
    print("🚀 Starting Image-to-Song Complete Pipeline...")
    app_startup_time = time.time()
    
    # Load AI model if available
    if USE_AI_SERVICE:
        try:
            print("Loading BLIP-2 model...")
            await blip2_service.load_model()
            print("✅ BLIP-2 model loaded successfully")
        except Exception as e:
            print(f"❌ Failed to load BLIP-2 model: {e}")
            print("🔄 Falling back to simple analyzer")
    else:
        print("📝 Using simple image analyzer (no AI dependencies)")
    
    startup_duration = time.time() - app_startup_time
    print(f"✅ API started in {startup_duration:.2f} seconds")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Image-to-Song API...")
    if USE_AI_SERVICE:
        try:
            await blip2_service.cleanup()
        except:
            pass
    print("✅ Cleanup completed")

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Complete Image-to-Song pipeline with OAuth and AI analysis",
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
    """Root endpoint with API information."""
    return {
        "message": "Image-to-Song Complete Pipeline API",
        "version": settings.APP_VERSION,
        "status": "running",
        "features": {
            "spotify_oauth": bool(SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET),
            "image_analysis": True,
            "mixed_recommendations": True,
            "ai_service": USE_AI_SERVICE
        },
        "endpoints": {
            "health": "/health",
            "spotify_login": "/spotify/login",
            "spotify_callback": "/spotify/callback",
            "analyze_image": "/analyze-image",
            "mixed_recommendations": "/mixed-recommendations",
            "model_info": "/model/info" if USE_AI_SERVICE else None,
            "generate_caption": "/caption/generate" if USE_AI_SERVICE else None
        }
    }

@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint with detailed status."""
    global app_startup_time
    
    uptime = time.time() - app_startup_time if app_startup_time else 0
    
    # Check if AI model is loaded (if using AI service)
    model_loaded = False
    if USE_AI_SERVICE:
        try:
            model_info = await blip2_service.get_model_info()
            model_loaded = model_info.get("status") == "loaded"
        except:
            model_loaded = False
    
    return {
        "status": "healthy",
        "uptime_seconds": round(uptime, 2),
        "model_loaded": model_loaded if USE_AI_SERVICE else "Not using AI service",
        "user_authenticated": len(user_tokens) > 0,
        "version": settings.APP_VERSION,
        "features": {
            "spotify_oauth": bool(SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET),
            "image_analysis": True,
            "ai_service": USE_AI_SERVICE
        },
        "timestamp": time.time()
    }

@app.get("/model/info")
async def get_model_info() -> Dict[str, Any]:
    """Get information about the loaded AI model."""
    if not USE_AI_SERVICE:
        return {
            "success": True,
            "model_info": {
                "status": "using_simple_analyzer",
                "type": "Simple Image Analyzer",
                "description": "Color-based mood detection"
            }
        }
    
    try:
        model_info = await blip2_service.get_model_info()
        return {
            "success": True,
            "model_info": model_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get model info: {str(e)}")

# Spotify OAuth endpoints
@app.get("/spotify/login")
async def spotify_login():
    """Start Spotify OAuth flow"""
    if not SPOTIFY_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Spotify client ID not configured")
    
    state = secrets.token_urlsafe(32)
    
    params = {
        'client_id': SPOTIFY_CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': SPOTIFY_REDIRECT_URI,
        'scope': 'user-read-private user-read-email user-library-read user-top-read playlist-read-private',
        'state': state
    }
    
    auth_sessions[state] = {'pending': True}
    
    auth_url = f"https://accounts.spotify.com/authorize?{urlencode(params)}"
    
    return {
        "auth_url": auth_url,
        "state": state,
        "message": "Visit the auth_url to authorize with Spotify"
    }

@app.get("/spotify/callback")
async def spotify_callback(
    code: str = Query(...),
    state: str = Query(...),
    error: str = Query(None)
):
    """Handle Spotify OAuth callback"""
    
    if error:
        # Redirect to mobile app with error
        return HTMLResponse(f"""
        <html>
        <body>
        <h2>❌ Authorization Failed</h2>
        <p>Error: {error}</p>
        <p>You can close this window and try again in the app.</p>
        <script>
        setTimeout(() => window.close(), 3000);
        </script>
        </body>
        </html>
        """)
    
    if state not in auth_sessions:
        return HTMLResponse("""
        <html>
        <body>
        <h2>❌ Invalid Session</h2>
        <p>Session expired or invalid. Please try again.</p>
        <script>
        setTimeout(() => window.close(), 3000);
        </script>
        </body>
        </html>
        """)
    
    try:
        token_data = await exchange_code_for_token(code)
        
        if 'access_token' in token_data:
            # Store token
            user_tokens[state] = {
                'access_token': token_data['access_token'],
                'refresh_token': token_data.get('refresh_token'),
                'expires_in': token_data.get('expires_in')
            }
            
            # Return success page that closes automatically
            return HTMLResponse("""
            <html>
            <body>
            <h2>✅ Authorization Successful!</h2>
            <p>You can now close this window and return to the app.</p>
            <script>
            setTimeout(() => window.close(), 2000);
            </script>
            </body>
            </html>
            """)
            
        else:
            raise HTTPException(status_code=400, detail="Failed to get access token")
            
    except Exception as e:
        return HTMLResponse(f"""
        <html>
        <body>
        <h2>❌ Token Exchange Failed</h2>
        <p>Error: {str(e)}</p>
        <script>
        setTimeout(() => window.close(), 3000);
        </script>
        </body>
        </html>
        """)

async def exchange_code_for_token(authorization_code: str):
    """Exchange authorization code for access token"""
    credentials = base64.b64encode(f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}".encode()).decode()
    
    headers = {
        'Authorization': f'Basic {credentials}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    data = {
        'grant_type': 'authorization_code',
        'code': authorization_code,
        'redirect_uri': SPOTIFY_REDIRECT_URI
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post('https://accounts.spotify.com/api/token', headers=headers, data=data)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=response.status_code, detail=f"Token exchange failed: {response.text}")

@app.get("/spotify/status")
async def spotify_status():
    """Check Spotify authentication status"""
    
    valid_tokens = 0
    has_token = False
    
    for token_data in user_tokens.values():
        if 'access_token' in token_data:
            valid_tokens += 1
            has_token = True
    
    return {
        "has_token": has_token,
        "user_count": valid_tokens,
        "total_users": len(user_tokens)
    }

# Main pipeline endpoints
@app.post("/analyze-image")
async def analyze_image(file: UploadFile = File(...)):
    """Analyze uploaded image using AI or simple analyzer"""
    
    print(f"🔍 === ANALYZE IMAGE ===")
    print(f"📁 File: {file.filename}")
    print(f"📄 Content-Type: {file.content_type}")
    
    try:
        # Read file data
        image_data = await file.read()
        print(f"📏 File size: {len(image_data)} bytes")
        
        if len(image_data) == 0:
            print("❌ Empty file")
            raise HTTPException(status_code=400, detail="Empty file received")
        
        # File signature check
        if len(image_data) >= 4:
            signature = ' '.join([f'{b:02x}' for b in image_data[:4]])
            print(f"🔍 File signature: {signature}")
        
        # Use AI service if available, otherwise use simple analyzer
        if USE_AI_SERVICE:
            try:
                # Validate image format using ImageProcessor
                if not ImageProcessor.validate_image(image_data):
                    raise HTTPException(status_code=400, detail="Invalid image format")
                
                # Get image information
                image_info = ImageProcessor.get_image_info(image_data)
                image_hash = ImageProcessor.calculate_image_hash(image_data)
                
                # Generate caption using AI
                caption = await blip2_service.generate_caption(image_data)
                
                # Use simple analyzer for mood detection (combining with AI caption)
                simple_result = image_analyzer.analyze_image(image_data)
                
                result = {
                    "status": "success",
                    "filename": file.filename or "image.jpg",
                    "caption": caption,
                    "mood": simple_result["mood"],
                    "confidence": 0.9,
                    "colors": simple_result["colors"],
                    "size": f"{image_info.get('size', 'unknown')}",
                    "analysis_method": "ai_plus_color",
                    "hash": image_hash[:16] + "..." if image_hash else None
                }
            except Exception as e:
                print(f"AI analysis failed, falling back to simple: {e}")
                result = image_analyzer.analyze_image(image_data)
                result["status"] = "success"
                result["filename"] = file.filename or "image.jpg"
        else:
            # Use simple analyzer
            result = image_analyzer.analyze_image(image_data)
            result["status"] = "success"
            result["filename"] = file.filename or "image.jpg"
        
        print(f"✅ SUCCESS: {result}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e) if str(e) else f"Unknown error of type {type(e).__name__}"
        print(f"❌ Error: {error_msg}")
        raise HTTPException(status_code=500, detail=f"Processing error: {error_msg}")

@app.post("/mixed-recommendations")
async def get_mixed_recommendations(request: Dict[str, str]):
    """Get mixed recommendations: personalized + mood-based + discovery"""
    
    mood = request.get('mood', 'neutral')
    caption = request.get('caption', '')
    
    try:
        # Get user token (find any valid token for demo)
        user_token = None
        print(f"🔍 DEBUG: Checking {len(user_tokens)} stored token sessions...")
        
        for state_id, token_data in user_tokens.items():
            print(f"🔑 Token session {state_id}: {list(token_data.keys())}")
            if 'access_token' in token_data:
                user_token = token_data['access_token']
                print(f"✅ Found token: {user_token[:20]}..." if user_token else "❌ Empty token")
                break
        
        print(f"🎵 Final token status: {'✅ Authenticated' if user_token else '❌ Anonymous mode'}")
        
        results = {
            "mood": mood,
            "caption": caption,
            "personalized": [],
            "mood_based": [],
            "discovery": [],
            "mode": "authenticated" if user_token else "anonymous"
        }
        
        # If no token, provide fallback recommendations
        if not user_token:
            print("📱 Using anonymous fallback recommendations...")
            anon_tracks = get_anonymous_recommendations(mood)
            print(f"🎵 Anonymous tracks returned: {anon_tracks}")
            print(f"📊 Number of tracks: {len(anon_tracks) if anon_tracks else 0}")
            
            # Ensure we always have arrays, not None
            results["mood_based"] = anon_tracks if anon_tracks else []
            results["discovery"] = [{"name": f"Discover {mood.title()} Music", "artist": "Mood Radio", "preview": None, "external_url": "#"}]
            results["summary"] = {
                "total_recommendations": len(results["mood_based"]) + len(results["discovery"]),
                "breakdown": {
                    "personalized": 0,
                    "mood_based": len(results["mood_based"]),
                    "discovery": len(results["discovery"])
                }
            }
            print(f"📊 Final anonymous results: {results}")
            return results
            
        async with httpx.AsyncClient() as client:
            headers = {'Authorization': f'Bearer {user_token}'} if user_token else {}
            
            # 1. Personalized recommendations (if user is authenticated)
            if user_token:
                try:
                    top_tracks_response = await client.get('https://api.spotify.com/v1/me/top/tracks?limit=3', headers=headers)
                    if top_tracks_response.status_code == 200:
                        top_tracks = top_tracks_response.json()['items']
                        if top_tracks:
                            # Use user's top tracks for personalized recommendations
                            seed_tracks = ','.join([track['id'] for track in top_tracks[:2]])
                            
                            # Get mood-adjusted audio features
                            mood_features = get_mood_audio_features(mood)
                            
                            rec_params = {
                                'seed_tracks': seed_tracks,
                                'limit': 6,
                                **mood_features
                            }
                            
                            rec_response = await client.get('https://api.spotify.com/v1/recommendations', headers=headers, params=rec_params)
                            
                            if rec_response.status_code == 200:
                                recommendations = rec_response.json()['tracks']
                                results["personalized"] = [
                                    {
                                        "name": track['name'],
                                        "artist": track['artists'][0]['name'],
                                        "popularity": track['popularity'],
                                        "spotify_url": track['external_urls']['spotify']
                                    }
                                    for track in recommendations[:4]  # 60% of recommendations
                                ]
                except Exception as e:
                    print(f"Personalized recommendations failed: {e}")
            
            # 2. Mood-based general search (30%)
            mood_queries = {
                "happy": "happy upbeat positive feel good",
                "peaceful": "peaceful calm relaxing ambient",
                "energetic": "energetic pump up workout motivation",
                "melancholic": "sad melancholic emotional introspective",
                "romantic": "romantic love ballad tender",
                "nature": "nature peaceful acoustic organic"
            }
            
            mood_query = mood_queries.get(mood, "popular trending")
            
            # Search for mood-based tracks
            search_params = {
                'q': mood_query,
                'type': 'track',
                'limit': 15,
                'market': 'US'
            }
            
            search_response = await client.get('https://api.spotify.com/v1/search', params=search_params)
            
            if search_response.status_code == 200:
                search_results = search_response.json()['tracks']['items']
                results["mood_based"] = [
                    {
                        "name": track['name'],
                        "artist": track['artists'][0]['name'],
                        "popularity": track['popularity'],
                        "spotify_url": track['external_urls']['spotify']
                    }
                    for track in search_results[:3]  # 30% of recommendations
                ]
            
            # 3. Discovery (10%) - Popular tracks from different genres
            discovery_queries = ["top hits 2024", "viral songs", "trending now"]
            
            for query in discovery_queries[:1]:  # Just one discovery search
                discovery_params = {
                    'q': query,
                    'type': 'track',
                    'limit': 10,
                    'market': 'US'
                }
                
                discovery_response = await client.get('https://api.spotify.com/v1/search', params=discovery_params)
                
                if discovery_response.status_code == 200:
                    discovery_results = discovery_response.json()['tracks']['items']
                    results["discovery"] = [
                        {
                            "name": track['name'],
                            "artist": track['artists'][0]['name'],
                            "popularity": track['popularity'],
                            "spotify_url": track['external_urls']['spotify']
                        }
                        for track in discovery_results[:1]  # 10% of recommendations
                    ]
                    break
        
        # Add recommendation counts
        results["summary"] = {
            "total_recommendations": len(results["personalized"]) + len(results["mood_based"]) + len(results["discovery"]),
            "breakdown": {
                "personalized": len(results["personalized"]),
                "mood_based": len(results["mood_based"]),
                "discovery": len(results["discovery"])
            }
        }
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Mixed recommendations failed: {str(e)}")

def get_mood_audio_features(mood: str) -> Dict[str, float]:
    """Get Spotify audio features based on mood"""
    mood_features = {
        "happy": {"target_valence": 0.8, "target_energy": 0.7, "target_danceability": 0.8},
        "peaceful": {"target_valence": 0.4, "target_energy": 0.3, "target_acousticness": 0.7},
        "energetic": {"target_valence": 0.7, "target_energy": 0.9, "target_danceability": 0.8},
        "melancholic": {"target_valence": 0.2, "target_energy": 0.4, "target_acousticness": 0.6},
        "romantic": {"target_valence": 0.6, "target_energy": 0.5, "target_acousticness": 0.5},
        "nature": {"target_valence": 0.5, "target_energy": 0.4, "target_acousticness": 0.8}
    }
    
    return mood_features.get(mood, {"target_valence": 0.5, "target_energy": 0.5})

def get_anonymous_recommendations(mood: str):
    """Get fallback recommendations when user is not authenticated"""
    
    print(f"🔍 Getting anonymous recommendations for mood: '{mood}'")
    
    mood_recommendations = {
        "happy": [
            {"name": "Happy", "artist": "Pharrell Williams", "preview": None, "external_url": "https://open.spotify.com/track/60nZcImufyMA1MKQY3dcCH"},
            {"name": "Good as Hell", "artist": "Lizzo", "preview": None, "external_url": "https://open.spotify.com/track/1LLXZFeAHK9R4xUramtUKw"},
            {"name": "Can't Stop the Feeling!", "artist": "Justin Timberlake", "preview": None, "external_url": "https://open.spotify.com/track/4bHsxqR3GMrXTxEPLuK5ue"}
        ],
        "melancholic": [
            {"name": "The Night We Met", "artist": "Lord Huron", "preview": None, "external_url": "https://open.spotify.com/track/0NdTUS4UiNYCNn5FgVqKQY"},
            {"name": "Skinny Love", "artist": "Bon Iver", "preview": None, "external_url": "https://open.spotify.com/track/2Ek2iSEoDv7IwKxhWXNShN"},
            {"name": "Mad World", "artist": "Gary Jules", "preview": None, "external_url": "https://open.spotify.com/track/3JOVTQ5h8HGFnDdp4VT3MP"}
        ],
        "energetic": [
            {"name": "Uptown Funk", "artist": "Mark Ronson ft. Bruno Mars", "preview": None, "external_url": "https://open.spotify.com/track/32OlwWuMpZ6b0aN2RZOeMS"},
            {"name": "Don't Stop Me Now", "artist": "Queen", "preview": None, "external_url": "https://open.spotify.com/track/5T8EDUDqKcs6OSOwEsfqG7"},
            {"name": "Can't Hold Us", "artist": "Macklemore", "preview": None, "external_url": "https://open.spotify.com/track/3DK6m7It6Pw857FcQftMds"}
        ],
        "peaceful": [
            {"name": "Weightless", "artist": "Marconi Union", "preview": None, "external_url": "https://open.spotify.com/track/3rCLsaUhdI5nIQdHWo8dOJ"},
            {"name": "Claire de Lune", "artist": "Claude Debussy", "preview": None, "external_url": "https://open.spotify.com/track/1Awsqv8AQfhOXsafRDf3HV"},
            {"name": "Holocene", "artist": "Bon Iver", "preview": None, "external_url": "https://open.spotify.com/track/6wAFjJlNSz2zd6ER3vz7MD"}
        ],
        "nature": [
            {"name": "River", "artist": "Leon Bridges", "preview": None, "external_url": "https://open.spotify.com/track/4Qa4GnP6gLVpL5DZqsKGHC"},
            {"name": "Forest", "artist": "System of a Down", "preview": None, "external_url": "https://open.spotify.com/track/31TvWB4wf0iBDyVsMLOFAf"},
            {"name": "Mountain", "artist": "Heartbreak on the Map", "preview": None, "external_url": "https://open.spotify.com/track/2eXVIy5ZjWgJqN9gWJn4yp"}
        ],
        "romantic": [
            {"name": "All of Me", "artist": "John Legend", "preview": None, "external_url": "https://open.spotify.com/track/3U4isOIWM3VvDubwSI3y7a"},
            {"name": "Perfect", "artist": "Ed Sheeran", "preview": None, "external_url": "https://open.spotify.com/track/0tgVpDi06FyKpA1z0VMD4v"},
            {"name": "Thinking Out Loud", "artist": "Ed Sheeran", "preview": None, "external_url": "https://open.spotify.com/track/0Qp8L0kSMXOm8jQf9Nz5H6"}
        ]
    }
    
    # Check available moods
    print(f"📋 Available moods: {list(mood_recommendations.keys())}")
    
    # Return mood-specific tracks or default to peaceful
    result = mood_recommendations.get(mood, mood_recommendations.get("peaceful", []))
    print(f"📋 Mood '{mood}' mapped to {len(result)} tracks: {[t['name'] for t in result] if result else 'None'}")
    return result

# Keep existing AI-focused endpoints for compatibility (but add fallback support)
@app.post("/caption/generate")
async def generate_caption(
    background_tasks: BackgroundTasks,
    image: UploadFile = File(..., description="Image file to generate caption for")
) -> Dict[str, Any]:
    """Generate a caption for an uploaded image (AI service or fallback)."""
    start_time = time.time()
    
    try:
        # Validate file type
        if image.content_type not in settings.ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported image type. Allowed types: {settings.ALLOWED_IMAGE_TYPES}"
            )
        
        # Read image bytes
        image_bytes = await image.read()
        
        # Validate file size
        if len(image_bytes) > settings.MAX_IMAGE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"Image too large. Maximum size: {settings.MAX_IMAGE_SIZE / (1024*1024):.1f}MB"
            )
        
        if USE_AI_SERVICE:
            # Validate image format
            if not ImageProcessor.validate_image(image_bytes):
                raise HTTPException(status_code=400, detail="Invalid image format")
            
            # Get image information
            image_info = ImageProcessor.get_image_info(image_bytes)
            image_hash = ImageProcessor.calculate_image_hash(image_bytes)
            
            # Generate caption
            caption_start_time = time.time()
            caption = await blip2_service.generate_caption(image_bytes)
            caption_time = time.time() - caption_start_time
        else:
            # Use simple analyzer for caption
            analysis = image_analyzer.analyze_image(image_bytes)
            caption = analysis.get("caption", "a beautiful scene")
            caption_time = 0.1
            image_info = {"size": "unknown", "format": "unknown"}
            image_hash = hashlib.md5(image_bytes).hexdigest()
        
        total_time = time.time() - start_time
        
        # Prepare response
        response_data = {
            "success": True,
            "caption": caption,
            "image_info": {
                "filename": image.filename,
                "size": image_info.get("size"),
                "format": image_info.get("format"),
                "file_size": len(image_bytes),
                "hash": image_hash[:16] + "..." if image_hash else "unknown"
            },
            "processing_time": {
                "total_seconds": round(total_time, 3),
                "caption_generation_seconds": round(caption_time, 3)
            },
            "timestamp": time.time(),
            "service_used": "ai" if USE_AI_SERVICE else "simple"
        }
        
        # Log processing metrics (background task)
        background_tasks.add_task(
            log_processing_metrics,
            image_hash if image_hash else "unknown",
            caption_time,
            total_time,
            len(image_bytes)
        )
        
        return response_data
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Caption generation failed: {str(e)}")

@app.post("/image/process")
async def process_image(
    image: UploadFile = File(..., description="Image file to process")
) -> Dict[str, Any]:
    """Process an image and return detailed analysis (AI service or fallback)."""
    start_time = time.time()
    
    try:
        # Read image bytes
        image_bytes = await image.read()
        
        if USE_AI_SERVICE:
            # Validate image
            if not ImageProcessor.validate_image(image_bytes):
                raise HTTPException(status_code=400, detail="Invalid image format")
            
            # Get image information
            image_info = ImageProcessor.get_image_info(image_bytes)
            image_hash = ImageProcessor.calculate_image_hash(image_bytes)
            
            # Preprocess for BLIP-2
            processed_bytes = ImageProcessor.preprocess_for_blip2(image_bytes)
            
            # Extract dominant colors
            try:
                dominant_colors = ImageProcessor.extract_dominant_colors(image_bytes)
            except Exception as e:
                dominant_colors = {"error": f"Color extraction failed: {str(e)}"}
        else:
            # Use simple analyzer
            analysis = image_analyzer.analyze_image(image_bytes)
            image_info = {"size": "unknown", "format": "unknown"}
            image_hash = hashlib.md5(image_bytes).hexdigest()
            processed_bytes = image_bytes  # No preprocessing
            dominant_colors = analysis.get("colors", {})
        
        processing_time = time.time() - start_time
        
        return {
            "success": True,
            "original_image": {
                "filename": image.filename,
                "size": image_info.get("size"),
                "format": image_info.get("format"),
                "file_size": len(image_bytes),
                "hash": image_hash
            },
            "processed_image": {
                "file_size": len(processed_bytes),
                "compression_ratio": round(len(processed_bytes) / len(image_bytes), 3) if image_bytes else 1.0
            },
            "dominant_colors": dominant_colors,
            "processing_time_seconds": round(processing_time, 3),
            "timestamp": time.time(),
            "service_used": "ai" if USE_AI_SERVICE else "simple"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image processing failed: {str(e)}")

@app.post("/caption/batch")
async def generate_batch_captions(
    images: list[UploadFile] = File(..., description="List of image files")
) -> Dict[str, Any]:
    """Generate captions for multiple images in batch (AI service or fallback)."""
    if len(images) > 10:  # Limit batch size
        raise HTTPException(status_code=400, detail="Maximum 10 images per batch")
    
    start_time = time.time()
    results = []
    
    try:
        # Read all images
        image_bytes_list = []
        for img in images:
            if img.content_type not in settings.ALLOWED_IMAGE_TYPES:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported image type in {img.filename}"
                )
            
            bytes_data = await img.read()
            if len(bytes_data) > settings.MAX_IMAGE_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail=f"Image {img.filename} too large"
                )
            
            image_bytes_list.append(bytes_data)
        
        # Generate captions
        if USE_AI_SERVICE:
            # Use AI service for batch processing
            captions = await blip2_service.batch_generate_captions(image_bytes_list)
        else:
            # Use simple analyzer for each image
            captions = []
            for image_bytes in image_bytes_list:
                analysis = image_analyzer.analyze_image(image_bytes)
                captions.append(analysis.get("caption", "a beautiful scene"))
        
        # Prepare results
        for i, (img, caption) in enumerate(zip(images, captions)):
            results.append({
                "filename": img.filename,
                "caption": caption,
                "index": i
            })
        
        total_time = time.time() - start_time
        
        return {
            "success": True,
            "results": results,
            "batch_info": {
                "total_images": len(images),
                "total_time_seconds": round(total_time, 3),
                "average_time_per_image": round(total_time / len(images), 3)
            },
            "timestamp": time.time(),
            "service_used": "ai" if USE_AI_SERVICE else "simple"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch processing failed: {str(e)}")

async def log_processing_metrics(
    image_hash: str,
    caption_time: float,
    total_time: float,
    file_size: int
):
    """Background task to log processing metrics."""
    # This would typically log to a database or monitoring system
    print(f"METRICS: hash={image_hash[:8]}, caption_time={caption_time:.3f}s, "
          f"total_time={total_time:.3f}s, file_size={file_size}")

# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
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
    print(f"GPU enabled: {getattr(settings, 'USE_GPU', False)}")
    print(f"AI Service: {USE_AI_SERVICE}")
    print(f"Spotify OAuth: {bool(SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET)}")
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower() if hasattr(settings, 'LOG_LEVEL') else "info"
    )

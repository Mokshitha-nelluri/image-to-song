"""
Image-to-Song App: Quiz-Based Music Preference System
Main application entry point with proper FastAPI structure.
"""
import asyncio
import time
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.routers import quiz, image, recommendations, search

# Global variables
app_startup_time = None

# Import services for initialization
try:
    MEMORY_LIMIT = os.getenv('RENDER_MEMORY_LIMIT', '').lower() == 'true'
    
    if MEMORY_LIMIT:
        # Lightweight mode for free hosting
        hybrid_service = None
        USE_AI_SERVICE = False
        print("⚡ Using Lightweight Mode (No AI model - optimized for free hosting)")
    else:
        # Full mode with AI
        from app.services.hybrid_ai_service import hybrid_service
        USE_AI_SERVICE = True
        print("✅ Using HybridImageService (BLIP + Color Analysis + Enhanced Mapping)")
except ImportError:
    try:
        from app.services.ai_service import blip2_service as hybrid_service
        USE_AI_SERVICE = True
        print("✅ Using BLIP2Service + Enhanced Mapping (fallback)")
    except ImportError:
        hybrid_service = None
        USE_AI_SERVICE = False
        print("ℹ️ Using SimpleImageAnalyzer only (no AI models)")


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
            print("Loading AI model...")
            await hybrid_service.load_model()
            
            # Verify the model loaded properly
            if hasattr(hybrid_service, 'verify_startup_status'):
                verification = await hybrid_service.verify_startup_status()  # type: ignore
                print(f"✅ AI model loaded successfully: {verification}")
            else:
                print("✅ AI model loaded successfully")
        except Exception as e:
            print(f"❌ Failed to load AI model: {e}")
            print("🔄 Falling back to simple analyzer")
    else:
        print("📝 Using simple image analyzer (no AI dependencies)")
    
    # Initialize Spotify token (from recommendations router)
    try:
        from app.routers.recommendations import get_spotify_token
        token = await get_spotify_token()
        if token:
            print("✅ Spotify Client Credentials obtained")
        else:
            print("⚠️ Spotify integration not available")
    except Exception as e:
        print(f"⚠️ Could not initialize Spotify: {e}")
    
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

# Include routers
app.include_router(quiz.router, prefix="/quiz", tags=["quiz"])
app.include_router(image.router, tags=["image"])
app.include_router(recommendations.router, tags=["recommendations"])
app.include_router(search.router, prefix="/search", tags=["search"])


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Image-to-Song Quiz App API",
        "version": settings.APP_VERSION,
        "status": "running",
        "features": {
            "music_quiz": True,
            "image_analysis": True,
            "preference_recommendations": True,
            "spotify_search": bool(os.getenv('SPOTIFY_CLIENT_ID', '') and os.getenv('SPOTIFY_CLIENT_SECRET', '')),
            "ai_service": USE_AI_SERVICE,
            "song_previews": True
        },
        "endpoints": {
            "health": "/health",
            "quiz_songs": "/quiz/songs",
            "calculate_preferences": "/quiz/calculate-preferences",
            "analyze_image": "/analyze-image",
            "recommendations": "/analyze-and-recommend",
            "search_songs": "/search/songs"
        }
    }


@app.get("/health")
async def health_check():
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
    
    # Check Spotify token status (from recommendations router)
    spotify_status = "not_available"
    try:
        from app.routers.recommendations import spotify_access_token
        spotify_status = "available" if spotify_access_token else "not_available"
    except:
        pass
    
    # Get quiz songs count
    try:
        from app.data.quiz_songs import QUIZ_SONGS
        quiz_songs_count = len(QUIZ_SONGS)
    except:
        quiz_songs_count = 0
    
    return {
        "status": "healthy",
        "uptime_seconds": round(uptime, 2),
        "model_loaded": model_loaded if USE_AI_SERVICE else "using_simple_analyzer",
        "spotify_status": spotify_status,
        "quiz_songs_available": quiz_songs_count,
        "version": settings.APP_VERSION,
        "timestamp": time.time()
    }


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
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower() if hasattr(settings, 'LOG_LEVEL') else "info"
    )
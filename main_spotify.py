"""
Extended FastAPI application with Spotify integration.
Adds music recommendation endpoints to the existing image processing API.
"""
import asyncio
import io
import time
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse

from app.core.config import settings
from app.services.cpu_ai_service import cpu_caption_service
from app.services.spotify_service import spotify_service
from app.utils.image_utils import ImageProcessor

# Global variables for tracking
app_startup_time = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global app_startup_time
    
    # Startup
    print("🚀 Starting Image-to-Song API (CPU-Optimized + Spotify)...")
    app_startup_time = time.time()
    
    # Load AI model
    try:
        print("Loading CPU-optimized BLIP model...")
        await cpu_caption_service.load_model()
        print("✅ CPU-optimized BLIP model loaded successfully")
    except Exception as e:
        print(f"❌ Failed to load CPU-optimized BLIP model: {e}")
    
    startup_duration = time.time() - app_startup_time
    print(f"✅ API started in {startup_duration:.2f} seconds")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Image-to-Song API...")
    await cpu_caption_service.cleanup()
    print("✅ Cleanup completed")

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME + " (Full Stack)",
    version=settings.APP_VERSION,
    description="Complete Image-to-Song pipeline with AI captioning and Spotify integration",
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
        "features": [
            "AI Image Captioning (BLIP)",
            "Color Analysis & Mood Detection", 
            "Spotify Music Recommendations",
            "OAuth Authentication"
        ],
        "endpoints": {
            "health": "/health",
            "model_info": "/model/info",
            "generate_caption": "/caption/generate",
            "process_image": "/image/process",
            "spotify_auth": "/spotify/auth",
            "music_recommendations": "/spotify/recommendations"
        }
    }

@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint."""
    global app_startup_time
    
    uptime = time.time() - app_startup_time if app_startup_time else 0
    
    # Check if model is loaded
    model_info = await cpu_caption_service.get_model_info()
    model_loaded = model_info.get("status") == "loaded"
    
    # Check Spotify configuration
    spotify_configured = bool(settings.SPOTIFY_CLIENT_ID and settings.SPOTIFY_CLIENT_SECRET)
    
    return {
        "status": "healthy" if model_loaded else "starting",
        "uptime_seconds": round(uptime, 2),
        "ai_model_loaded": model_loaded,
        "spotify_configured": spotify_configured,
        "optimization": "CPU-optimized",
        "timestamp": time.time()
    }

@app.get("/model/info")
async def get_model_info() -> Dict[str, Any]:
    """Get information about the loaded AI model."""
    try:
        model_info = await cpu_caption_service.get_model_info()
        return {
            "success": True,
            "model_info": model_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get model info: {str(e)}")

@app.post("/caption/generate")
async def generate_caption(
    background_tasks: BackgroundTasks,
    image: UploadFile = File(..., description="Image file to generate caption for")
) -> Dict[str, Any]:
    """Generate a caption for an uploaded image."""
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
        
        # Validate image format
        if not ImageProcessor.validate_image(image_bytes):
            raise HTTPException(status_code=400, detail="Invalid image format")
        
        # Get image information
        image_info = ImageProcessor.get_image_info(image_bytes)
        image_hash = ImageProcessor.calculate_image_hash(image_bytes)
        
        # Generate caption
        caption_start_time = time.time()
        caption = await cpu_caption_service.generate_caption(image_bytes)
        caption_time = time.time() - caption_start_time
        
        # Extract colors for mood analysis
        try:
            dominant_colors = ImageProcessor.extract_dominant_colors(image_bytes)
        except Exception as e:
            dominant_colors = []
        
        total_time = time.time() - start_time
        
        # Prepare response with mood analysis
        response_data = {
            "success": True,
            "caption": caption,
            "mood_analysis": {
                "caption": caption,
                "dominant_colors": dominant_colors,
                "image_info": image_info
            },
            "image_info": {
                "filename": image.filename,
                "size": image_info.get("size"),
                "format": image_info.get("format"),
                "file_size": len(image_bytes),
                "hash": image_hash[:16] + "..."
            },
            "processing_time": {
                "total_seconds": round(total_time, 3),
                "caption_generation_seconds": round(caption_time, 3)
            },
            "optimization": "CPU-optimized BLIP model",
            "timestamp": time.time()
        }
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Caption generation failed: {str(e)}")

# Spotify Integration Endpoints

@app.get("/spotify/auth")
async def spotify_auth(state: Optional[str] = None) -> Dict[str, str]:
    """
    Generate Spotify OAuth authorization URL.
    
    Args:
        state: Optional state parameter for security
    
    Returns:
        Authorization URL and state for OAuth flow
    """
    if not settings.SPOTIFY_CLIENT_ID:
        raise HTTPException(
            status_code=503, 
            detail="Spotify integration not configured. Please set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET"
        )
    
    auth_data = spotify_service.generate_auth_url(state)
    return {
        "auth_url": auth_data["auth_url"],
        "state": auth_data["state"],
        "message": "Visit auth_url to authorize Spotify access"
    }

@app.get("/spotify/callback")
async def spotify_callback(
    code: str = Query(..., description="Authorization code from Spotify"),
    state: Optional[str] = Query(None, description="State parameter for validation")
) -> Dict[str, Any]:
    """
    Handle Spotify OAuth callback.
    
    Args:
        code: Authorization code from Spotify
        state: State parameter for validation
    
    Returns:
        Authentication success confirmation and user info
    """
    try:
        # Exchange code for token
        token_data = await spotify_service.exchange_code_for_token(code)
        
        # Get user ID
        user_id = await spotify_service._get_user_id(token_data["access_token"])
        
        return {
            "success": True,
            "message": "Spotify authentication successful",
            "user_id": user_id,
            "expires_in": token_data.get("expires_in", 3600),
            "timestamp": time.time()
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Authentication failed: {str(e)}")

@app.post("/spotify/recommendations")
async def get_music_recommendations(
    background_tasks: BackgroundTasks,
    user_id: str = Query(..., description="Spotify user ID"),
    image: UploadFile = File(..., description="Image for mood analysis")
) -> Dict[str, Any]:
    """
    Get music recommendations based on image mood analysis.
    
    Args:
        user_id: Spotify user ID (from authentication)
        image: Image file for mood analysis
    
    Returns:
        Music recommendations based on image mood
    """
    start_time = time.time()
    
    try:
        # Validate Spotify configuration
        if not settings.SPOTIFY_CLIENT_ID:
            raise HTTPException(status_code=503, detail="Spotify integration not configured")
        
        # Process image for mood analysis
        image_bytes = await image.read()
        
        # Validate image
        if not ImageProcessor.validate_image(image_bytes):
            raise HTTPException(status_code=400, detail="Invalid image format")
        
        # Generate caption and analyze mood
        caption_start = time.time()
        caption = await cpu_caption_service.generate_caption(image_bytes)
        caption_time = time.time() - caption_start
        
        # Extract colors
        color_start = time.time()
        try:
            dominant_colors = ImageProcessor.extract_dominant_colors(image_bytes)
        except Exception as e:
            dominant_colors = []
        color_time = time.time() - color_start
        
        # Prepare mood analysis
        mood_analysis = {
            "caption": caption,
            "dominant_colors": dominant_colors,
            "image_info": ImageProcessor.get_image_info(image_bytes)
        }
        
        # Get Spotify recommendations
        spotify_start = time.time()
        recommendations = await spotify_service.get_music_recommendations(
            user_id, mood_analysis, limit=10
        )
        spotify_time = time.time() - spotify_start
        
        total_time = time.time() - start_time
        
        # Prepare response
        response_data = {
            "success": True,
            "user_id": user_id,
            "mood_analysis": mood_analysis,
            "recommendations": recommendations,
            "processing_time": {
                "total_seconds": round(total_time, 3),
                "caption_generation": round(caption_time, 3),
                "color_analysis": round(color_time, 3),
                "spotify_recommendations": round(spotify_time, 3)
            },
            "timestamp": time.time()
        }
        
        # Log metrics in background
        background_tasks.add_task(
            log_recommendation_metrics,
            user_id,
            caption,
            len(dominant_colors),
            len(recommendations.get("recommendations", {}).get("tracks", [])),
            total_time
        )
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendation generation failed: {str(e)}")

@app.get("/spotify/user/{user_id}")
async def get_user_spotify_data(user_id: str) -> Dict[str, Any]:
    """Get cached Spotify user data."""
    user_data = spotify_service.get_cached_user_data(user_id)
    
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found or not authenticated")
    
    return {
        "user_id": user_id,
        "authenticated": True,
        "expires_at": user_data.get("expires_at", 0),
        "is_expired": time.time() >= user_data.get("expires_at", 0)
    }

@app.delete("/spotify/user/{user_id}")
async def logout_user(user_id: str) -> Dict[str, Any]:
    """Logout user (remove from cache)."""
    success = spotify_service.revoke_user_access(user_id)
    
    return {
        "success": success,
        "message": "User logged out successfully" if success else "User not found"
    }

# Background task functions
async def log_recommendation_metrics(
    user_id: str,
    caption: str,
    color_count: int,
    track_count: int,
    processing_time: float
):
    """Background task to log recommendation metrics."""
    print(f"RECOMMENDATION_METRICS: user={user_id[:8]}, caption_length={len(caption)}, "
          f"colors={color_count}, tracks={track_count}, time={processing_time:.3f}s")

# Legacy endpoints (keeping for compatibility)
@app.post("/image/process")
async def process_image(
    image: UploadFile = File(..., description="Image file to process")
) -> Dict[str, Any]:
    """Process an image and return detailed analysis."""
    start_time = time.time()
    
    try:
        image_bytes = await image.read()
        
        if not ImageProcessor.validate_image(image_bytes):
            raise HTTPException(status_code=400, detail="Invalid image format")
        
        image_info = ImageProcessor.get_image_info(image_bytes)
        image_hash = ImageProcessor.calculate_image_hash(image_bytes)
        processed_bytes = ImageProcessor.preprocess_for_blip2(image_bytes)
        
        try:
            dominant_colors = ImageProcessor.extract_dominant_colors(image_bytes)
        except Exception as e:
            dominant_colors = {"error": f"Color extraction failed: {str(e)}"}
        
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
                "compression_ratio": round(len(processed_bytes) / len(image_bytes), 3)
            },
            "dominant_colors": dominant_colors,
            "processing_time_seconds": round(processing_time, 3),
            "optimization": "CPU-optimized processing",
            "timestamp": time.time()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image processing failed: {str(e)}")

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
    
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION} (Full Stack)")
    print(f"Debug mode: {settings.DEBUG}")
    print(f"Features: AI Image Processing + Spotify Integration")
    
    uvicorn.run(
        "main_spotify:app",
        host=settings.HOST,
        port=8002,  # Different port for full-stack version
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )

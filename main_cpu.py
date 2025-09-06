"""
FastAPI application for the Image-to-Song backend - CPU Optimized Version.
Uses the faster CPU-optimized AI service for immediate testing.
"""
import asyncio
import io
import time
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.services.cpu_ai_service import cpu_caption_service
from app.utils.image_utils import ImageProcessor

# Global variables for tracking
app_startup_time = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global app_startup_time
    
    # Startup
    print("🚀 Starting Image-to-Song API (CPU-Optimized)...")
    app_startup_time = time.time()
    
    # Load AI model
    try:
        print("Loading CPU-optimized BLIP model...")
        await cpu_caption_service.load_model()
        print("✅ CPU-optimized BLIP model loaded successfully")
    except Exception as e:
        print(f"❌ Failed to load CPU-optimized BLIP model: {e}")
        # Don't crash the app, allow it to start and handle errors gracefully
    
    startup_duration = time.time() - app_startup_time
    print(f"✅ API started in {startup_duration:.2f} seconds")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Image-to-Song API...")
    await cpu_caption_service.cleanup()
    print("✅ Cleanup completed")

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME + " (CPU-Optimized)",
    version=settings.APP_VERSION,
    description="AI-powered image captioning service for music recommendations - CPU Optimized",
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
        "message": "Image-to-Song AI Pipeline API (CPU-Optimized)",
        "version": settings.APP_VERSION,
        "status": "running",
        "optimization": "CPU-optimized with smaller BLIP model",
        "endpoints": {
            "health": "/health",
            "model_info": "/model/info",
            "generate_caption": "/caption/generate",
            "process_image": "/image/process"
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
    
    return {
        "status": "healthy" if model_loaded else "starting",
        "uptime_seconds": round(uptime, 2),
        "model_loaded": model_loaded,
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
    """
    Generate a caption for an uploaded image.
    
    Args:
        image: Uploaded image file
        
    Returns:
        Dict containing the generated caption and metadata
    """
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
                "hash": image_hash[:16] + "..."  # Truncated hash for privacy
            },
            "processing_time": {
                "total_seconds": round(total_time, 3),
                "caption_generation_seconds": round(caption_time, 3)
            },
            "optimization": "CPU-optimized BLIP model",
            "timestamp": time.time()
        }
        
        # Log processing metrics (background task)
        background_tasks.add_task(
            log_processing_metrics,
            image_hash,
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
    """
    Process an image and return detailed analysis including preprocessing results.
    
    Args:
        image: Uploaded image file
        
    Returns:
        Dict containing image analysis and processing results
    """
    start_time = time.time()
    
    try:
        # Read image bytes
        image_bytes = await image.read()
        
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
    
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION} (CPU-Optimized)")
    print(f"Debug mode: {settings.DEBUG}")
    print(f"Using CPU-optimized AI service")
    
    uvicorn.run(
        "main_cpu:app",
        host=settings.HOST,
        port=8001,  # Use different port to avoid conflict
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )

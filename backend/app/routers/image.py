"""
Image analysis endpoints for mood detection and scene understanding.
Handles image upload, analysis, and recommendation generation.
"""
import os
from typing import Dict, Any

from fastapi import APIRouter, File, UploadFile, HTTPException

from ..core.config import settings
from ..utils.image_utils import ImageProcessor

# Import services with fallback handling
try:
    MEMORY_LIMIT = os.getenv('RENDER_MEMORY_LIMIT', '').lower() == 'true'
    
    if MEMORY_LIMIT:
        # Lightweight mode for free hosting
        from ..services.simple_analyzer import simple_image_analyzer as image_analyzer
        hybrid_service = None
        USE_AI_SERVICE = False
        print("Using Lightweight Mode (No AI model - optimized for free hosting)")
    else:
        # Full mode with AI
        from ..services.hybrid_ai_service import hybrid_service
        from ..services.simple_analyzer import simple_image_analyzer as image_analyzer
        USE_AI_SERVICE = True
        print("Using HybridImageService (BLIP + Color Analysis + Enhanced Mapping)")
except ImportError:
    try:
        from ..services.ai_service import blip2_service as hybrid_service
        from ..services.simple_analyzer import simple_image_analyzer as image_analyzer
        USE_AI_SERVICE = True
        print("Using BLIP2Service + Enhanced Mapping (fallback)")
    except ImportError:
        from ..services.simple_analyzer import simple_image_analyzer as image_analyzer
        hybrid_service = None
        USE_AI_SERVICE = False
        print("Using SimpleImageAnalyzer only (no AI models)")

router = APIRouter(tags=["image"])


@router.post("/analyze-image")
async def analyze_image(file: UploadFile = File(...)):
    """Analyze uploaded image for mood and context"""
    print(f"File: {file.filename}")
    print(f"Content-Type: {file.content_type}")
    
    try:
        # Read file data
        image_data = await file.read()
        print(f"File size: {len(image_data)} bytes")
        
        if len(image_data) == 0:
            raise HTTPException(status_code=400, detail="Empty file received")
        
        # Validate file size
        if len(image_data) > settings.MAX_IMAGE_SIZE:
            raise HTTPException(status_code=413, detail=f"File too large. Maximum size is {settings.MAX_IMAGE_SIZE / (1024*1024):.1f}MB")
        
        # Validate image format
        if not ImageProcessor.validate_image(image_data):
            raise HTTPException(status_code=400, detail="Invalid image format. Please upload a valid image file.")
        
        # Compress image if needed (keep under 2MB for faster processing)
        if len(image_data) > 2 * 1024 * 1024:  # 2MB
            try:
                image_data = ImageProcessor.compress_image(image_data, max_size_mb=2.0)
                print(f"Image compressed to: {len(image_data)} bytes")
            except Exception as e:
                print(f"Image compression failed: {e}")
                # Continue with original image if compression fails
        
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
        
        print(f"Image analysis result: {result}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        print(f"Image analysis error: {error_msg}")
        raise HTTPException(status_code=500, detail=f"Image processing failed: {error_msg}")
"""
Basic FastAPI server test without AI models.
This will verify our API setup is working correctly.
"""
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(
    title="Image-to-Song API Test",
    description="Basic API test without AI models",
    version="1.0.0"
)

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Image-to-Song API Test Server",
        "status": "running",
        "endpoints": ["/", "/health", "/test"]
    }

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "message": "API is running correctly"
    }

@app.get("/test")
async def test():
    """Test endpoint to verify functionality."""
    try:
        # Test basic imports
        import torch
        import numpy as np
        from PIL import Image
        
        return {
            "success": True,
            "torch_version": torch.__version__,
            "cuda_available": torch.cuda.is_available(),
            "message": "All basic dependencies are working"
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "message": "Dependency test failed"
            }
        )

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting basic API test server...")
    print("📍 Server will be available at: http://localhost:8000")
    print("📖 Docs will be available at: http://localhost:8000/docs")
    
    uvicorn.run(
        "basic_api_test:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

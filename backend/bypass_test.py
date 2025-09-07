"""
Simple bypass version of analyze-image endpoint for testing
"""
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse

app = FastAPI()

@app.post("/analyze-image")
async def analyze_image_bypass(file: UploadFile = File(...)):
    """Bypass version that always returns success without actual analysis"""
    
    # Just return a successful response without doing any processing
    return JSONResponse(content={
        "status": "success",
        "filename": file.filename or "unknown.jpg",
        "size": "1000x1000",
        "caption": "a beautiful scene captured in an image",
        "mood": "neutral",
        "confidence": 0.8,
        "colors": {"dominant": "rgb(128,128,128)", "brightness": 128},
        "analysis_method": "bypass_test"
    })

@app.get("/health")
async def health():
    return {"status": "healthy", "version": "bypass_test"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Image-to-Song AI Pipeline Backend

This is the backend service for the Image-to-Song application, featuring BLIP-2 image captioning with production-ready optimizations.

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- CUDA-compatible GPU (recommended) or CPU
- At least 8GB RAM (16GB recommended for GPU)

### Installation

1. **Clone and navigate to backend directory:**
```bash
cd backend
```

2. **Create virtual environment (recommended):**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. **Run the setup script:**
```bash
python setup.py
```

Or install manually:
```bash
pip install -r requirements.txt
```

### 🧪 Testing the AI Pipeline

Test the core AI functionality:
```bash
python test_ai_pipeline.py
```

This will:
- ✅ Test image processing utilities
- ✅ Load and test BLIP-2 model
- ✅ Generate captions for test images
- ✅ Benchmark performance

### 🌐 Starting the API Server

```bash
python main.py
```

The API will be available at: `http://localhost:8000`

## 📡 API Endpoints

### Core Endpoints

- **GET /** - API information and available endpoints
- **GET /health** - Health check and model status
- **GET /model/info** - Detailed model information

### Image Processing

- **POST /caption/generate** - Generate caption for a single image
- **POST /caption/batch** - Generate captions for multiple images
- **POST /image/process** - Process image and extract detailed analysis

### Example Usage

```bash
# Test with curl
curl -X POST "http://localhost:8000/caption/generate" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "image=@your_image.jpg"
```

## 🏗️ Architecture

```
backend/
├── app/
│   ├── core/           # Configuration and settings
│   ├── services/       # AI services (BLIP-2)
│   ├── utils/          # Image processing utilities
│   └── __init__.py
├── tests/              # Test files
├── main.py            # FastAPI application
├── test_ai_pipeline.py # AI pipeline testing
├── setup.py           # Setup script
├── requirements.txt   # Dependencies
└── .env              # Environment configuration
```

## ⚡ Performance Features

### AI Model Optimizations
- **Memory Efficient**: FP16 precision, 8-bit quantization
- **GPU Optimized**: CUDA memory management and caching
- **Batch Processing**: Efficient multi-image processing
- **Model Warm-up**: Consistent performance after startup

### Image Processing
- **Smart Compression**: Automatic size optimization for BLIP-2
- **Format Validation**: Robust image format handling
- **Dominant Colors**: Color extraction for mood analysis
- **Hash-based Caching**: Avoid reprocessing identical images

### API Features
- **Async Processing**: Non-blocking request handling
- **Background Tasks**: Metrics logging and cleanup
- **Error Handling**: Graceful degradation and informative errors
- **CORS Support**: Cross-origin requests for web apps

## 🔧 Configuration

Edit `.env` file to customize settings:

```env
# AI Model Settings
USE_GPU=true
MAX_BATCH_SIZE=4
MODEL_CACHE_DIR=./models

# Image Processing
MAX_IMAGE_SIZE=10485760  # 10MB
TARGET_IMAGE_WIDTH=384
TARGET_IMAGE_HEIGHT=384

# Performance
MAX_WORKERS=2
REQUEST_TIMEOUT=30

# Logging
LOG_LEVEL=INFO
DEBUG=false
```

## 📊 Performance Benchmarks

### Expected Performance (RTX 3080, 12GB VRAM):
- **Model Loading**: ~15-30 seconds
- **Single Image Caption**: ~0.8-1.5 seconds
- **Batch Processing (4 images)**: ~2-3 seconds
- **Image Preprocessing**: ~10-50ms

### CPU Performance (Intel i7):
- **Single Image Caption**: ~8-15 seconds
- **Model Loading**: ~45-60 seconds

## 🐛 Troubleshooting

### Common Issues

**1. CUDA Out of Memory**
```bash
# Reduce batch size in .env
MAX_BATCH_SIZE=1
```

**2. Model Download Fails**
```bash
# Set custom cache directory
MODEL_CACHE_DIR=/path/to/large/storage
```

**3. Slow CPU Performance**
```bash
# Force CPU mode for testing
USE_GPU=false
```

**4. Import Errors**
```bash
# Reinstall dependencies
pip install --force-reinstall -r requirements.txt
```

### Debug Mode

Enable debug logging:
```bash
export DEBUG=true
export LOG_LEVEL=DEBUG
python main.py
```

## 🧪 Testing

### Unit Tests
```bash
cd tests
python -m pytest
```

### Performance Testing
```bash
python test_ai_pipeline.py
```

### Load Testing
```bash
# Install locust
pip install locust

# Run load test (future feature)
locust -f tests/locustfile.py
```

## 📈 Monitoring

The API provides metrics endpoints for monitoring:
- Response times
- Model inference duration
- Memory usage
- Error rates

### Logs
All operations are logged with structured JSON for easy parsing:
```json
{
  "timestamp": "2025-09-05T10:30:00Z",
  "level": "INFO",
  "message": "Caption generated",
  "duration_ms": 1250,
  "image_hash": "abc123...",
  "caption_length": 45
}
```

## 🚀 Production Deployment

### Docker (Recommended)
```dockerfile
FROM python:3.11-slim
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["python", "main.py"]
```

### Environment Variables
```bash
export HOST=0.0.0.0
export PORT=8000
export USE_GPU=true
export MODEL_CACHE_DIR=/models
```

### Scaling Considerations
- **Memory**: 8-16GB RAM per instance
- **GPU**: 6-12GB VRAM for optimal performance
- **Storage**: 10-20GB for model cache
- **CPU**: 4+ cores recommended

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📄 License

This project is part of the Image-to-Song application suite.

---

**Next Steps**: After testing the AI pipeline, proceed to implement Spotify integration and the Flutter mobile app!

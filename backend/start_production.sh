#!/bin/bash
# Production start script for Image-to-Song API

echo "🚀 Starting Image-to-Song API (Production Mode)"
echo "=============================================="

# Production server with optimized settings
python -m uvicorn main:app \
    --host 0.0.0.0 \
    --port ${PORT:-8000} \
    --workers 1 \
    --timeout-keep-alive 65 \
    --timeout-graceful-shutdown 30 \
    --access-log \
    --no-reload

echo "✅ Production server started successfully!"

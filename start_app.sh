#!/bin/bash
echo "Starting Image-to-Song Complete Pipeline..."
echo "Available Python files:"
ls -la *.py | head -10
echo "Starting main_complete_pipeline..."
python -m uvicorn main_complete_pipeline:app --host 0.0.0.0 --port $PORT

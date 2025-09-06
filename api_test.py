"""
Quick API endpoint test using CPU-optimized service.
"""
import asyncio
import io
import time
from PIL import Image
import requests
import json

# Test if server is running
def test_server_connection():
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running!")
            print(f"📄 Response: {response.json()}")
            return True
        else:
            print(f"❌ Server returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to server: {e}")
        return False

def test_health_endpoint():
    try:
        response = requests.get("http://localhost:8000/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ Health check passed!")
            print(f"📊 Status: {data.get('status')}")
            print(f"⏱️ Uptime: {data.get('uptime_seconds')}s")
            print(f"🤖 Model loaded: {data.get('model_loaded')}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def create_test_image():
    """Create a simple test image."""
    image = Image.new('RGB', (100, 100), color='blue')
    img_bytes = io.BytesIO()
    image.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    return img_bytes.getvalue()

def test_caption_endpoint():
    try:
        print("🖼️ Testing caption generation...")
        image_data = create_test_image()
        
        files = {
            'image': ('test.jpg', image_data, 'image/jpeg')
        }
        
        start_time = time.time()
        response = requests.post(
            "http://localhost:8000/caption/generate", 
            files=files,
            timeout=30
        )
        request_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Caption generation successful!")
            print(f"📝 Caption: '{data.get('caption')}'")
            print(f"⏱️ Request time: {request_time:.2f}s")
            print(f"🔧 Processing time: {data.get('processing_time', {}).get('total_seconds')}s")
            return True
        else:
            print(f"❌ Caption generation failed: {response.status_code}")
            print(f"📄 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Caption test error: {e}")
        return False

def main():
    print("🚀 API Testing Suite")
    print("=" * 50)
    
    # Test 1: Server connection
    print("\n1️⃣ Testing server connection...")
    if not test_server_connection():
        print("❌ Server is not running. Please start it with: python main.py")
        return
    
    # Test 2: Health check
    print("\n2️⃣ Testing health endpoint...")
    if not test_health_endpoint():
        print("⚠️ Health check failed, but continuing tests...")
    
    # Test 3: Caption generation
    print("\n3️⃣ Testing caption generation...")
    if test_caption_endpoint():
        print("\n🎉 All API tests passed!")
    else:
        print("\n❌ Caption generation test failed")
    
    print("\n🌐 API Documentation available at: http://localhost:8000/docs")

if __name__ == "__main__":
    main()

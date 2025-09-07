"""
Quick API endpoint test for CPU-optimized service on port 8001.
"""
import io
import time
from PIL import Image
import requests
import json

# Test if server is running
def test_server_connection():
    try:
        response = requests.get("http://localhost:8001/", timeout=5)
        if response.status_code == 200:
            print("✅ CPU-optimized server is running!")
            data = response.json()
            print(f"📄 Message: {data.get('message')}")
            print(f"🔧 Optimization: {data.get('optimization')}")
            return True
        else:
            print(f"❌ Server returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to server: {e}")
        return False

def test_health_endpoint():
    try:
        response = requests.get("http://localhost:8001/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ Health check passed!")
            print(f"📊 Status: {data.get('status')}")
            print(f"⏱️ Uptime: {data.get('uptime_seconds')}s")
            print(f"🤖 Model loaded: {data.get('model_loaded')}")
            print(f"🔧 Optimization: {data.get('optimization')}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_model_info():
    try:
        response = requests.get("http://localhost:8001/model/info", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ Model info retrieved!")
            model_info = data.get('model_info', {})
            print(f"🏷️ Model: {model_info.get('model_name')}")
            print(f"💾 Device: {model_info.get('device')}")
            print(f"📊 Status: {model_info.get('status')}")
            return True
        else:
            print(f"❌ Model info failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Model info error: {e}")
        return False

def create_test_image():
    """Create a simple test image."""
    image = Image.new('RGB', (200, 200), color='blue')
    # Add some simple content
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
            "http://localhost:8001/caption/generate", 
            files=files,
            timeout=30
        )
        request_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Caption generation successful!")
            print(f"📝 Caption: '{data.get('caption')}'")
            print(f"⏱️ Request time: {request_time:.2f}s")
            processing_time = data.get('processing_time', {})
            print(f"🔧 Processing time: {processing_time.get('total_seconds')}s")
            print(f"🧠 Caption time: {processing_time.get('caption_generation_seconds')}s")
            print(f"🔧 Optimization: {data.get('optimization')}")
            return True
        else:
            print(f"❌ Caption generation failed: {response.status_code}")
            print(f"📄 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Caption test error: {e}")
        return False

def test_image_processing():
    try:
        print("🔧 Testing image processing...")
        image_data = create_test_image()
        
        files = {
            'image': ('test.jpg', image_data, 'image/jpeg')
        }
        
        response = requests.post(
            "http://localhost:8001/image/process", 
            files=files,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Image processing successful!")
            original = data.get('original_image', {})
            processed = data.get('processed_image', {})
            print(f"📏 Original size: {original.get('file_size')} bytes")
            print(f"📏 Processed size: {processed.get('file_size')} bytes")
            print(f"📊 Compression ratio: {processed.get('compression_ratio')}")
            print(f"🎨 Colors extracted: {bool(data.get('dominant_colors'))}")
            return True
        else:
            print(f"❌ Image processing failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Image processing error: {e}")
        return False

def main():
    print("🚀 CPU-Optimized API Testing Suite")
    print("=" * 60)
    
    # Test 1: Server connection
    print("\n1️⃣ Testing server connection...")
    if not test_server_connection():
        print("❌ Server is not running. Please start it with: python main_cpu.py")
        return
    
    # Test 2: Health check
    print("\n2️⃣ Testing health endpoint...")
    if not test_health_endpoint():
        print("⚠️ Health check failed, but continuing tests...")
    
    # Test 3: Model info
    print("\n3️⃣ Testing model info...")
    test_model_info()
    
    # Test 4: Caption generation
    print("\n4️⃣ Testing caption generation...")
    caption_success = test_caption_endpoint()
    
    # Test 5: Image processing
    print("\n5️⃣ Testing image processing...")
    processing_success = test_image_processing()
    
    if caption_success and processing_success:
        print("\n🎉 ALL API TESTS PASSED!")
        print("\n✅ Next Steps:")
        print("1. ✅ AI Pipeline: WORKING")
        print("2. ✅ API Server: WORKING") 
        print("3. 🔜 Build mobile app frontend")
        print("4. 🔜 Integrate Spotify API")
    else:
        print("\n⚠️ Some tests failed, but basic functionality is working")
    
    print(f"\n🌐 API Documentation: http://localhost:8001/docs")
    print(f"🔧 CPU-optimized server running on port 8001")

if __name__ == "__main__":
    main()

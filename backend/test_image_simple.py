#!/usr/bin/env python3
"""
Simple test to debug image analysis endpoint on Render
"""
import requests
import io
from PIL import Image

def create_test_image():
    """Create a simple test image"""
    img = Image.new('RGB', (100, 100), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    return img_bytes.getvalue()

def test_image_analysis():
    """Test the image analysis endpoint"""
    print("🔍 Testing image analysis endpoint...")
    
    # Create test image
    image_data = create_test_image()
    print(f"Created test image: {len(image_data)} bytes")
    
    # Test cloud endpoint
    url = "https://image-to-song.onrender.com/analyze-image"
    
    try:
        files = {'file': ('test.jpg', image_data, 'image/jpeg')}
        print(f"Sending request to: {url}")
        
        response = requests.post(url, files=files, timeout=30)
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Success!")
            print(f"Result: {result}")
        else:
            print("❌ Failed!")
            print(f"Response text: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_image_analysis()

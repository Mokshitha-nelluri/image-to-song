#!/usr/bin/env python3
"""
Test to match mobile app's exact request format
"""
import requests
import io
from PIL import Image

def create_test_image_file():
    """Create a test image file on disk like mobile app would have"""
    img = Image.new('RGB', (100, 100), color='red')
    img.save('test_mobile.jpg', format='JPEG')
    return 'test_mobile.jpg'

def test_mobile_app_format():
    """Test using file from disk like mobile app does"""
    print("🔍 Testing mobile app format...")
    
    # Create test image file
    image_path = create_test_image_file()
    print(f"Created test image file: {image_path}")
    
    # Test cloud endpoint with file from disk
    url = "https://image-to-song.onrender.com/analyze-image"
    
    try:
        with open(image_path, 'rb') as f:
            files = {'file': (image_path, f, 'image/jpeg')}
            print(f"Sending file from disk to: {url}")
            
            response = requests.post(url, files=files, timeout=30)
            
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Success with file from disk!")
                print(f"Result: {result}")
            else:
                print("❌ Failed with file from disk!")
                print(f"Response text: {response.text}")
                
    except Exception as e:
        print(f"❌ Exception with file from disk: {e}")

def test_large_image():
    """Test with a larger image like mobile camera would produce"""
    print("\n🔍 Testing larger image...")
    
    # Create larger test image
    img = Image.new('RGB', (1000, 1000), color='blue')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG', quality=85)
    img_bytes.seek(0)
    image_data = img_bytes.getvalue()
    
    print(f"Created larger test image: {len(image_data)} bytes")
    
    url = "https://image-to-song.onrender.com/analyze-image"
    
    try:
        files = {'file': ('large_test.jpg', image_data, 'image/jpeg')}
        print(f"Sending large image to: {url}")
        
        response = requests.post(url, files=files, timeout=30)
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Success with large image!")
            print(f"Result: {result}")
        else:
            print("❌ Failed with large image!")
            print(f"Response text: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception with large image: {e}")

if __name__ == "__main__":
    test_mobile_app_format()
    test_large_image()

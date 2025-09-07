#!/usr/bin/env python3
"""
Test with various image formats that might match what mobile app sends
"""
import requests
import io
from PIL import Image

def test_various_formats():
    """Test different image formats and processing"""
    print("🔍 Testing various image formats...")
    
    url = "https://image-to-song.onrender.com/analyze-image"
    
    # Test 1: JPEG with different quality settings (like mobile scaling)
    formats_to_test = [
        {"format": "JPEG", "quality": 95, "size": (1920, 1080), "color": "blue"},
        {"format": "JPEG", "quality": 80, "size": (1000, 1000), "color": "green"},
        {"format": "JPEG", "quality": 60, "size": (800, 600), "color": "red"},
        {"format": "PNG", "quality": None, "size": (500, 500), "color": "purple"},
    ]
    
    for i, test_config in enumerate(formats_to_test):
        try:
            print(f"\n--- Test {i+1}: {test_config['format']} ---")
            
            # Create test image with specific format
            img = Image.new('RGB', test_config['size'], color=test_config['color'])
            img_bytes = io.BytesIO()
            
            if test_config['format'] == 'JPEG':
                img.save(img_bytes, format='JPEG', quality=test_config['quality'])
                content_type = 'image/jpeg'
            else:
                img.save(img_bytes, format='PNG')
                content_type = 'image/png'
            
            img_bytes.seek(0)
            image_data = img_bytes.getvalue()
            
            print(f"Created {test_config['format']} image: {len(image_data)} bytes, {test_config['size']}")
            
            # Send to server
            files = {'file': (f'test_{i+1}.jpg', image_data, content_type)}
            response = requests.post(url, files=files, timeout=30)
            
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Success: {result.get('mood', 'N/A')} mood detected")
            else:
                print(f"❌ Failed: {response.text}")
                
        except Exception as e:
            print(f"❌ Exception in test {i+1}: {e}")

if __name__ == "__main__":
    test_various_formats()

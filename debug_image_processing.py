"""
Debug the image processing endpoint error.
"""
import io
import requests
from PIL import Image

def create_test_image():
    """Create a simple test image."""
    image = Image.new('RGB', (100, 100), color='red')
    img_bytes = io.BytesIO()
    image.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    return img_bytes.getvalue()

def test_image_processing_debug():
    try:
        print("🔍 Debugging image processing endpoint...")
        image_data = create_test_image()
        
        files = {
            'image': ('test.jpg', image_data, 'image/jpeg')
        }
        
        response = requests.post(
            "http://localhost:8001/image/process", 
            files=files,
            timeout=30
        )
        
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Success!")
            print(f"Data: {data}")
        else:
            print(f"❌ Failed with status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_image_processing_debug()

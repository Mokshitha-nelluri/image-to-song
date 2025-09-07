"""
Diagnostic script to test all backend endpoints and identify issues
"""
import requests
import json
from pathlib import Path

def test_backend():
    base_url = "http://192.168.1.131:8002"
    
    print("🔍 Backend Diagnostic Report")
    print("=" * 50)
    
    # Test 1: Health Check
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"✅ Health Check: {response.status_code}")
        if response.status_code == 200:
            health_data = response.json()
            print(f"   Features: {health_data.get('features', {})}")
            print(f"   Components: {health_data.get('components', {})}")
    except Exception as e:
        print(f"❌ Health Check Failed: {e}")
    
    # Test 2: Spotify Login Endpoint
    try:
        response = requests.get(f"{base_url}/spotify/login", timeout=5)
        print(f"✅ Spotify Login: {response.status_code}")
        if response.status_code == 200:
            login_data = response.json()
            print(f"   Has auth_url: {'auth_url' in login_data}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Spotify Login Failed: {e}")
    
    # Test 3: Image Analysis (with test image)
    try:
        # Create a simple test image
        from PIL import Image
        import io
        
        # Create a simple red square test image
        test_image = Image.new('RGB', (100, 100), color='red')
        img_bytes = io.BytesIO()
        test_image.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        files = {'file': ('test.png', img_bytes, 'image/png')}
        response = requests.post(f"{base_url}/analyze-image", files=files, timeout=10)
        
        print(f"✅ Image Analysis: {response.status_code}")
        if response.status_code == 200:
            analysis_data = response.json()
            print(f"   Caption: {analysis_data.get('caption', 'N/A')}")
            print(f"   Mood: {analysis_data.get('mood', 'N/A')}")
        else:
            print(f"   Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Image Analysis Failed: {e}")
    
    # Test 4: Mixed Recommendations
    try:
        test_request = {
            "mood": "happy",
            "caption": "a bright colorful scene"
        }
        response = requests.post(
            f"{base_url}/mixed-recommendations", 
            json=test_request,
            timeout=15
        )
        print(f"✅ Mixed Recommendations: {response.status_code}")
        if response.status_code == 200:
            rec_data = response.json()
            print(f"   Personalized: {len(rec_data.get('personalized', []))} tracks")
            print(f"   Mood-based: {len(rec_data.get('mood_based', []))} tracks")
            print(f"   Discovery: {len(rec_data.get('discovery', []))} tracks")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Mixed Recommendations Failed: {e}")
    
    print("=" * 50)
    print("🔧 Recommendations:")
    print("1. Check terminal logs for detailed error messages")
    print("2. Ensure Spotify credentials are set in .env")
    print("3. Verify PIL/Pillow is installed correctly")
    print("4. Check network connectivity between phone and computer")

if __name__ == "__main__":
    test_backend()

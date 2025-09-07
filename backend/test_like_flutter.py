#!/usr/bin/env python3
"""
Test that exactly mimics Flutter's http.MultipartFile.fromPath behavior
"""
import requests
import os
from pathlib import Path

def test_like_flutter():
    """Test using real file exactly like Flutter MultipartFile.fromPath"""
    print("🔍 Testing exactly like Flutter mobile app...")
    
    # Find a real image file
    current_dir = Path.cwd()
    test_files = list(current_dir.glob("test_mobile.jpg"))
    
    if not test_files:
        print("❌ No test image found")
        return
    
    test_file = test_files[0]
    print(f"Using file: {test_file}")
    print(f"File size: {test_file.stat().st_size} bytes")
    
    url = "https://image-to-song.onrender.com/analyze-image"
    
    try:
        # Mimic exactly what Flutter MultipartFile.fromPath does
        with open(test_file, 'rb') as f:
            # This is exactly how Flutter sends it
            files = {
                'file': (
                    test_file.name,  # filename
                    f,               # file object
                    'image/jpeg'     # content type
                )
            }
            
            print("📤 Sending request exactly like Flutter...")
            print(f"  - URL: {url}")
            print(f"  - File: {test_file.name}")
            print(f"  - Content-Type: image/jpeg")
            print(f"  - Size: {test_file.stat().st_size} bytes")
            
            # Add headers that mobile app might send
            headers = {
                'User-Agent': 'Dart/3.0 (dart:io)',  # Flutter's default user agent
                'Accept': 'application/json',
                'Connection': 'keep-alive'
            }
            
            response = requests.post(
                url, 
                files=files, 
                headers=headers,
                timeout=60
            )
            
            print(f"📥 Response received:")
            print(f"  - Status: {response.status_code}")
            print(f"  - Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ SUCCESS - Exactly like Flutter!")
                print(f"Result: {result}")
            else:
                print("❌ FAILED - Same as mobile app!")
                print(f"Response text: {response.text}")
                print(f"Response content: {response.content}")
                
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_like_flutter()

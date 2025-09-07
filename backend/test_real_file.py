#!/usr/bin/env python3
"""
Test that mimics exactly what the mobile app does
"""
import requests
import os

def test_with_real_mobile_image():
    """Test with a real image file"""
    print("🔍 Testing with real mobile image format...")
    
    # Look for any jpg files that might be test images
    test_files = []
    current_dir = os.getcwd()
    
    # Check current directory and parent for test images
    for root, dirs, files in os.walk(current_dir):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.png')) and 'test' in file.lower():
                test_files.append(os.path.join(root, file))
        if len(test_files) > 0:
            break  # Found some, don't search too deep
    
    if not test_files:
        print("No test image files found, skipping real file test")
        return
    
    test_file = test_files[0]
    print(f"Using test file: {test_file}")
    
    url = "https://image-to-song.onrender.com/analyze-image"
    
    try:
        # Open and send the file exactly like mobile app would
        with open(test_file, 'rb') as f:
            files = {'file': (os.path.basename(test_file), f, 'image/jpeg')}
            
            print(f"Sending real file: {os.path.basename(test_file)}")
            print(f"File size: {os.path.getsize(test_file)} bytes")
            
            response = requests.post(url, files=files, timeout=60)
            
            print(f"Response status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Success with real file!")
                print(f"Result: {result}")
            else:
                print("❌ Failed with real file!")
                print(f"Response text: {response.text}")
                
    except Exception as e:
        print(f"❌ Exception with real file: {e}")

if __name__ == "__main__":
    test_with_real_mobile_image()

#!/usr/bin/env python3
"""
Test script to simulate mobile app API calls
"""
import requests
import json

BASE_URL = "https://image-to-song.onrender.com"

def test_health():
    """Test health endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=30)
        print(f"✅ Health Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"❌ Health Error: {e}")

def test_quiz_songs():
    """Test quiz songs endpoint"""
    print("\n🔍 Testing quiz songs endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/quiz/songs?limit=10", timeout=30)
        print(f"✅ Quiz Songs Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Found {len(data['quiz_songs'])} songs")
            print(f"   First song: {data['quiz_songs'][0]['title']} by {data['quiz_songs'][0]['artist']}")
        else:
            print(f"   Error response: {response.text}")
    except Exception as e:
        print(f"❌ Quiz Songs Error: {e}")

def test_user_profile():
    """Test user profile endpoint"""
    print("\n🔍 Testing user profile endpoint...")
    try:
        test_user_id = "test_mobile_user"
        response = requests.get(f"{BASE_URL}/user/{test_user_id}/profile", timeout=30)
        print(f"✅ User Profile Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   User: {data['user_id']}")
            print(f"   Quiz completed: {data['quiz_completed']}")
        else:
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ User Profile Error: {e}")

def main():
    print("🚀 Testing Mobile App Connection to Production Backend")
    print(f"🌐 Backend URL: {BASE_URL}")
    print("=" * 60)
    
    test_health()
    test_quiz_songs()
    test_user_profile()
    
    print("\n" + "=" * 60)
    print("✅ Test Complete!")

if __name__ == "__main__":
    main()

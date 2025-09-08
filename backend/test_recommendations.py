#!/usr/bin/env python3
"""
Test script to debug the recommendations endpoint
"""
import requests
import json

def test_recommendations():
    """Test the recommendations endpoint with melancholic mood"""
    url = "https://image-to-song.onrender.com/recommendations"
    
    # Test payload similar to what the mobile app sends
    payload = {
        "mood": "melancholic",
        "caption": "reflective composition with muted colors",
        "user_profile": {
            "user_id": "test_user",
            "quiz_completed": True,
            "genre_preferences": {
                "pop": 0.7,
                "indie": 0.8,
                "rock": 0.6
            },
            "audio_features": {
                "energy": 0.4,
                "valence": 0.3,
                "danceability": 0.4
            }
        }
    }
    
    try:
        print("🎵 Testing recommendations endpoint...")
        print(f"📝 Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(
            url,
            headers={'Content-Type': 'application/json'},
            json=payload,
            timeout=30
        )
        
        print(f"📡 Status Code: {response.status_code}")
        print(f"📦 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Got {len(data.get('recommendations', []))} recommendations")
            print(f"🎯 Strategy: {data.get('search_strategy', 'unknown')}")
            print(f"👤 Personalized: {data.get('personalized', False)}")
            
            # Show first few recommendations
            for i, rec in enumerate(data.get('recommendations', [])[:3], 1):
                print(f"  {i}. {rec['title']} by {rec['artist']}")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"💥 Exception: {e}")

if __name__ == "__main__":
    test_recommendations()

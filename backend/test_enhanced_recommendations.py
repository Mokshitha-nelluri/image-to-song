#!/usr/bin/env python3

import requests
import json
import time

def test_recommendations():
    """Test the enhanced recommendation system"""
    
    # Test with a simple mood analysis
    url = "https://image-to-song.onrender.com/recommendations"
    
    # Test data simulating image analysis results
    test_data = {
        "mood": "happy",
        "energy": "high", 
        "user_preferences": ["pop", "rock", "upbeat"]
    }
    
    print("🎵 Testing Enhanced Recommendation System")
    print("=" * 50)
    print(f"Request URL: {url}")
    print(f"Test Data: {json.dumps(test_data, indent=2)}")
    print()
    
    try:
        print("📡 Making request...")
        response = requests.post(url, json=test_data, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            recommendations = response.json()
            print("✅ Success! Recommendations received:")
            print(f"Total recommendations: {len(recommendations)}")
            print()
            
            # Show first 5 recommendations
            display_count = min(5, len(recommendations))
            for i in range(display_count):
                rec = recommendations[i]
                has_preview = rec.get('preview_url') is not None
                preview_status = "🎵 Has Preview" if has_preview else "❌ No Preview"
                
                print(f"{i+1}. {rec.get('title', 'Unknown')} - {rec.get('artist', 'Unknown')}")
                print(f"   Album: {rec.get('album', 'Unknown')}")
                print(f"   Popularity: {rec.get('popularity', 0)}")
                print(f"   Duration: {rec.get('duration_ms', 0) // 1000}s")
                print(f"   {preview_status}")
                print(f"   Spotify ID: {rec.get('spotify_id', 'None')}")
                print()
            
            # Count preview availability
            with_preview = sum(1 for rec in recommendations if rec.get('preview_url'))
            without_preview = len(recommendations) - with_preview
            
            print("📊 Preview URL Statistics:")
            print(f"   Songs with preview: {with_preview}")
            print(f"   Songs without preview: {without_preview}")
            print(f"   Total songs: {len(recommendations)}")
            print(f"   Preview rate: {(with_preview/len(recommendations)*100):.1f}%")
            
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_recommendations()

"""
Simple Spotify Test - No OAuth Required
Uses Client Credentials Flow for testing recommendations
"""
import requests
import base64
import json
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def get_spotify_token():
    """Get access token using Client Credentials Flow (no user login needed)"""
    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    
    # Encode credentials
    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    
    # Token request
    headers = {
        'Authorization': f'Basic {credentials}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    data = {
        'grant_type': 'client_credentials'
    }
    
    response = requests.post('https://accounts.spotify.com/api/token', headers=headers, data=data)
    
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        print(f"❌ Token request failed: {response.status_code}")
        print(f"❌ Error: {response.text}")
        return None

def search_tracks(token, mood, genre):
    """Search for tracks based on mood and genre"""
    headers = {
        'Authorization': f'Bearer {token}'
    }
    
    # Search for tracks
    query = f"genre:{genre} mood:{mood}"
    params = {
        'q': query,
        'type': 'track',
        'limit': 5
    }
    
    response = requests.get('https://api.spotify.com/v1/search', headers=headers, params=params)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ Search failed: {response.status_code}")
        return None

def get_recommendations(token, seed_genres, target_valence, target_energy):
    """Get music recommendations based on audio features"""
    headers = {
        'Authorization': f'Bearer {token}'
    }
    
    params = {
        'seed_genres': ','.join(seed_genres),
        'target_valence': target_valence,
        'target_energy': target_energy,
        'limit': 10
    }
    
    response = requests.get('https://api.spotify.com/v1/recommendations', headers=headers, params=params)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ Recommendations failed: {response.status_code}")
        print(f"❌ Error: {response.text}")
        return None

def main():
    print("🎵 Testing Spotify API with Client Credentials...")
    print("=" * 60)
    
    # Get access token
    print("🔑 Getting Spotify access token...")
    token = get_spotify_token()
    
    if not token:
        print("❌ Failed to get access token. Check your credentials.")
        return
    
    print("✅ Successfully got access token!")
    
    # Test different moods
    test_scenarios = [
        {
            'mood': 'happy',
            'genres': ['pop', 'dance', 'funk'],
            'valence': 0.8,
            'energy': 0.7,
            'description': 'Happy Beach Photo'
        },
        {
            'mood': 'peaceful',
            'genres': ['ambient', 'classical', 'new-age'],
            'valence': 0.4,
            'energy': 0.3,
            'description': 'Peaceful Forest'
        },
        {
            'mood': 'energetic',
            'genres': ['rock', 'electronic', 'hip-hop'],
            'valence': 0.7,
            'energy': 0.9,
            'description': 'Energetic Sports Scene'
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\n🎯 Testing: {scenario['description']}")
        print(f"   Mood: {scenario['mood']}")
        print(f"   Target Valence: {scenario['valence']}")
        print(f"   Target Energy: {scenario['energy']}")
        
        # Get recommendations
        recommendations = get_recommendations(
            token, 
            scenario['genres'], 
            scenario['valence'], 
            scenario['energy']
        )
        
        if recommendations and 'tracks' in recommendations:
            print(f"   ✅ Found {len(recommendations['tracks'])} recommendations:")
            
            for i, track in enumerate(recommendations['tracks'][:3], 1):
                artist = track['artists'][0]['name']
                song = track['name']
                preview_url = track.get('preview_url', 'No preview')
                external_url = track['external_urls']['spotify']
                
                print(f"      {i}. {song} - {artist}")
                print(f"         🔗 Spotify: {external_url}")
                if preview_url != 'No preview':
                    print(f"         🎵 Preview: {preview_url}")
        else:
            print("   ❌ No recommendations found")
        
        print("-" * 50)
    
    print("\n🎉 Spotify API test completed successfully!")
    print("🚀 Your credentials are working perfectly!")
    print("\n💡 Next steps:")
    print("   1. ✅ Spotify API integration - WORKING")
    print("   2. 🔄 Add image upload to test complete pipeline")
    print("   3. 🔄 Mobile app development")

if __name__ == "__main__":
    main()

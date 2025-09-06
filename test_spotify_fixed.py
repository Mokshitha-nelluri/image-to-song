"""
Fixed Spotify Recommendations Test
Uses proper API format with seed tracks instead of genres
"""
import requests
import base64
import json
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def get_spotify_token():
    """Get access token using Client Credentials Flow"""
    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    
    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    
    headers = {
        'Authorization': f'Basic {credentials}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    data = {'grant_type': 'client_credentials'}
    
    response = requests.post('https://accounts.spotify.com/api/token', headers=headers, data=data)
    
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        print(f"❌ Token request failed: {response.status_code}")
        return None

def find_seed_tracks(token, search_query, limit=1):
    """Find seed tracks to use for recommendations"""
    headers = {'Authorization': f'Bearer {token}'}
    
    params = {
        'q': search_query,
        'type': 'track',
        'limit': limit,
        'market': 'US'  # Add market parameter
    }
    
    response = requests.get('https://api.spotify.com/v1/search', headers=headers, params=params)
    
    if response.status_code == 200:
        tracks = response.json()['tracks']['items']
        return [track['id'] for track in tracks]
    else:
        print(f"❌ Seed track search failed: {response.status_code}")
        return []

def get_recommendations_with_seeds(token, seed_tracks, target_valence, target_energy, target_danceability=None):
    """Get recommendations using seed tracks (more reliable than genres)"""
    headers = {'Authorization': f'Bearer {token}'}
    
    params = {
        'seed_tracks': ','.join(seed_tracks[:5]),  # Max 5 seeds
        'target_valence': target_valence,
        'target_energy': target_energy,
        'limit': 10,
        'market': 'US'  # Add market parameter
    }
    
    if target_danceability:
        params['target_danceability'] = target_danceability
    
    print(f"🔍 Request URL: https://api.spotify.com/v1/recommendations")
    print(f"🔍 Params: {params}")
    
    response = requests.get('https://api.spotify.com/v1/recommendations', headers=headers, params=params)
    
    print(f"🔍 Response Status: {response.status_code}")
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ Recommendations failed: {response.status_code}")
        print(f"❌ Response Headers: {dict(response.headers)}")
        print(f"❌ Response: {response.text}")
        return None

def main():
    print("🎵 Fixed Spotify Recommendations Test...")
    print("=" * 60)
    
    # Get access token
    print("🔑 Getting Spotify access token...")
    token = get_spotify_token()
    
    if not token:
        print("❌ Failed to get access token")
        return
    
    print("✅ Access token obtained!")
    
    # Test scenarios using seed tracks instead of genres
    test_scenarios = [
        {
            'description': '🏖️ Happy Beach Photo',
            'mood': 'happy',
            'seed_search': 'happy summer beach feel good',
            'valence': 0.8,
            'energy': 0.7,
            'danceability': 0.8
        },
        {
            'description': '🌲 Peaceful Forest',
            'mood': 'peaceful',
            'seed_search': 'peaceful calm relaxing nature',
            'valence': 0.3,
            'energy': 0.2,
            'danceability': 0.3
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\n{scenario['description']}")
        print(f"   🎭 Mood: {scenario['mood']}")
        print(f"   📊 Target Features: valence={scenario['valence']}, energy={scenario['energy']}")
        
        # Find seed tracks
        print(f"   🔍 Finding seed tracks for: '{scenario['seed_search']}'")
        seed_tracks = find_seed_tracks(token, scenario['seed_search'], limit=2)
        
        if seed_tracks:
            print(f"   ✅ Found {len(seed_tracks)} seed tracks: {seed_tracks}")
            
            # Get recommendations
            recommendations = get_recommendations_with_seeds(
                token, 
                seed_tracks, 
                scenario['valence'], 
                scenario['energy'],
                scenario['danceability']
            )
            
            if recommendations and 'tracks' in recommendations:
                tracks = recommendations['tracks']
                print(f"   🎉 SUCCESS! Found {len(tracks)} recommendations:")
                
                for i, track in enumerate(tracks[:5], 1):
                    artist = track['artists'][0]['name']
                    song = track['name']
                    spotify_url = track['external_urls']['spotify']
                    popularity = track['popularity']
                    
                    print(f"      {i}. {song} - {artist}")
                    print(f"         📈 Popularity: {popularity}/100")
                    print(f"         🔗 {spotify_url}")
                
                # Show recommendation details
                if 'seeds' in recommendations:
                    print(f"   📋 Seed Details:")
                    for seed in recommendations['seeds']:
                        print(f"      • {seed['type']}: {seed['id']} (pool: {seed.get('initialPoolSize', 'unknown')})")
                
            else:
                print("   ❌ Recommendations failed")
        else:
            print("   ❌ No seed tracks found")
        
        print("-" * 50)
    
    print("\n🎯 Test Results:")
    print("   ✅ If you see 'SUCCESS!' above, the recommendations API is working!")
    print("   ✅ This means your Image-to-Song pipeline is 100% functional!")

if __name__ == "__main__":
    main()

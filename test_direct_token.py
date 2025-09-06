"""
Direct Token Test for Spotify
Uses access token directly (from implicit flow) to test personalized recommendations
"""
import requests
import json

def test_user_recommendations(access_token):
    """Test getting personalized recommendations with user token"""
    headers = {'Authorization': f'Bearer {access_token}'}
    
    print("🔍 Testing access token validity...")
    
    # Test 1: Get user profile
    profile_response = requests.get('https://api.spotify.com/v1/me', headers=headers)
    
    if profile_response.status_code == 200:
        profile = profile_response.json()
        print(f"✅ Token valid! User: {profile.get('display_name', 'Unknown')}")
        print(f"   📧 Email: {profile.get('email', 'N/A')}")
        print(f"   🌍 Country: {profile.get('country', 'N/A')}")
    else:
        print(f"❌ Token invalid: {profile_response.status_code}")
        print(f"❌ Error: {profile_response.text}")
        return False
    
    # Test 2: Get user's top tracks
    print("\n🎵 Getting user's top tracks...")
    top_tracks_response = requests.get('https://api.spotify.com/v1/me/top/tracks?limit=5&time_range=medium_term', headers=headers)
    
    if top_tracks_response.status_code == 200:
        top_tracks = top_tracks_response.json()['items']
        print(f"✅ Found {len(top_tracks)} top tracks:")
        
        for i, track in enumerate(top_tracks, 1):
            print(f"   {i}. {track['name']} - {track['artists'][0]['name']}")
        
        # Use top tracks as seeds
        if len(top_tracks) >= 2:
            seed_tracks = [track['id'] for track in top_tracks[:2]]
            
            # Test 3: Get personalized recommendations for different moods
            test_scenarios = [
                {
                    'name': '🏖️ Happy Beach Vibes',
                    'valence': 0.8,
                    'energy': 0.7,
                    'danceability': 0.8
                },
                {
                    'name': '🌙 Chill Evening',
                    'valence': 0.4,
                    'energy': 0.3,
                    'danceability': 0.4
                },
                {
                    'name': '💪 Workout Energy',
                    'valence': 0.7,
                    'energy': 0.9,
                    'danceability': 0.8
                }
            ]
            
            for scenario in test_scenarios:
                print(f"\n{scenario['name']}")
                print(f"   🎭 Target: valence={scenario['valence']}, energy={scenario['energy']}")
                
                params = {
                    'seed_tracks': ','.join(seed_tracks),
                    'target_valence': scenario['valence'],
                    'target_energy': scenario['energy'],
                    'target_danceability': scenario['danceability'],
                    'limit': 5,
                    'market': profile.get('country', 'US')
                }
                
                rec_response = requests.get('https://api.spotify.com/v1/recommendations', headers=headers, params=params)
                
                if rec_response.status_code == 200:
                    recommendations = rec_response.json()
                    print(f"   🎉 SUCCESS! Got {len(recommendations['tracks'])} personalized recommendations:")
                    
                    for i, track in enumerate(recommendations['tracks'], 1):
                        artist = track['artists'][0]['name']
                        song = track['name']
                        popularity = track['popularity']
                        preview = track.get('preview_url', 'No preview')
                        
                        print(f"      {i}. {song} - {artist} (popularity: {popularity})")
                        print(f"         🔗 {track['external_urls']['spotify']}")
                        if preview != 'No preview':
                            print(f"         🎵 Preview: {preview}")
                    
                else:
                    print(f"   ❌ Recommendations failed: {rec_response.status_code}")
                    print(f"   ❌ Error: {rec_response.text}")
        
        else:
            print("⚠️ Need at least 2 top tracks for recommendations")
    
    else:
        print(f"❌ Failed to get top tracks: {top_tracks_response.status_code}")
        print(f"❌ Error: {top_tracks_response.text}")
        return False
    
    return True

def main():
    print("🎵 Direct Access Token Test for Personalized Recommendations")
    print("=" * 70)
    
    print("📋 Instructions:")
    print("1. Open 'spotify_oauth_helper.html' in your browser")
    print("2. Click 'Authorize with Spotify'")
    print("3. Copy the access token that appears")
    print("4. Paste it below")
    print()
    
    access_token = input("📝 Enter your Spotify access token: ").strip()
    
    if access_token:
        print(f"\n🔄 Testing with token (first 20 chars): {access_token[:20]}...")
        
        if test_user_recommendations(access_token):
            print("\n🎉 PERSONALIZED RECOMMENDATIONS WORKING!")
            print("✅ OAuth flow successful!")
            print("✅ Your Image-to-Song app can now get personalized music!")
            print("\n🚀 Ready to integrate into the full pipeline!")
        else:
            print("\n❌ Something went wrong with the recommendations")
    else:
        print("❌ No access token provided")

if __name__ == "__main__":
    main()

"""
Manual OAuth Test for Spotify
Step-by-step process to get user authorization without HTTPS tunnel
"""
import requests
import base64
import json
from dotenv import load_dotenv
import os
import urllib.parse

# Load environment variables
load_dotenv()

def get_client_token():
    """Get client credentials token"""
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

def generate_auth_url():
    """Generate the Spotify authorization URL"""
    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    
    # Using a dummy redirect URI for manual testing
    redirect_uri = "http://localhost:8002/spotify/callback"
    
    params = {
        'client_id': client_id,
        'response_type': 'code',
        'redirect_uri': redirect_uri,
        'scope': 'user-read-private user-read-email user-library-read user-top-read playlist-read-private',
        'state': 'test123'
    }
    
    auth_url = 'https://accounts.spotify.com/authorize?' + urllib.parse.urlencode(params)
    return auth_url

def exchange_code_for_token(authorization_code):
    """Exchange authorization code for access token"""
    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    redirect_uri = "http://localhost:8002/spotify/callback"
    
    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    
    headers = {
        'Authorization': f'Basic {credentials}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    data = {
        'grant_type': 'authorization_code',
        'code': authorization_code,
        'redirect_uri': redirect_uri
    }
    
    response = requests.post('https://accounts.spotify.com/api/token', headers=headers, data=data)
    
    print(f"🔍 Token exchange response: {response.status_code}")
    print(f"🔍 Response: {response.text}")
    
    if response.status_code == 200:
        return response.json()
    else:
        return None

def test_user_recommendations(access_token):
    """Test getting personalized recommendations with user token"""
    headers = {'Authorization': f'Bearer {access_token}'}
    
    # First, get user's top tracks to use as seeds
    top_tracks_response = requests.get('https://api.spotify.com/v1/me/top/tracks?limit=3', headers=headers)
    
    if top_tracks_response.status_code == 200:
        top_tracks = top_tracks_response.json()['items']
        seed_tracks = [track['id'] for track in top_tracks[:2]]
        
        print(f"✅ Found user's top tracks as seeds: {[t['name'] for t in top_tracks[:2]]}")
        
        # Get personalized recommendations
        params = {
            'seed_tracks': ','.join(seed_tracks),
            'target_valence': 0.8,
            'target_energy': 0.7,
            'limit': 5,
            'market': 'US'
        }
        
        rec_response = requests.get('https://api.spotify.com/v1/recommendations', headers=headers, params=params)
        
        if rec_response.status_code == 200:
            recommendations = rec_response.json()
            print(f"🎉 SUCCESS! Got {len(recommendations['tracks'])} personalized recommendations:")
            
            for i, track in enumerate(recommendations['tracks'], 1):
                print(f"   {i}. {track['name']} - {track['artists'][0]['name']}")
                print(f"      🔗 {track['external_urls']['spotify']}")
            
            return True
        else:
            print(f"❌ Recommendations failed: {rec_response.status_code}")
            print(f"❌ Error: {rec_response.text}")
            return False
    else:
        print(f"❌ Failed to get user's top tracks: {top_tracks_response.status_code}")
        return False

def main():
    print("🎵 Manual OAuth Test for Personalized Recommendations")
    print("=" * 60)
    
    # Test 1: Client credentials (should work)
    print("🔑 Testing client credentials...")
    client_token = get_client_token()
    if client_token:
        print("✅ Client credentials working!")
    else:
        print("❌ Client credentials failed!")
        return
    
    # Test 2: Generate auth URL
    print("\n🌐 Generating authorization URL...")
    auth_url = generate_auth_url()
    print(f"✅ Authorization URL: {auth_url}")
    
    print("\n📋 MANUAL STEPS:")
    print("1. Copy the URL above and paste it in your browser")
    print("2. Log in to Spotify and authorize the app")
    print("3. You'll be redirected to a page that doesn't load (that's normal)")
    print("4. Copy the 'code' parameter from the URL in your browser")
    print("5. Enter that code below")
    
    # Get authorization code from user
    auth_code = input("\n📝 Enter the authorization code from the redirect URL: ").strip()
    
    if auth_code:
        print(f"\n🔄 Exchanging code for access token...")
        token_data = exchange_code_for_token(auth_code)
        
        if token_data and 'access_token' in token_data:
            print("🎉 SUCCESS! Got user access token!")
            
            # Test personalized recommendations
            print("\n🎵 Testing personalized recommendations...")
            if test_user_recommendations(token_data['access_token']):
                print("\n🚀 OAUTH FLOW COMPLETE!")
                print("✅ Personalized recommendations are working!")
                print("🎯 Ready to integrate into the full pipeline!")
            else:
                print("\n⚠️ OAuth worked but recommendations failed")
        else:
            print("❌ Failed to exchange code for token")
    else:
        print("❌ No authorization code provided")

if __name__ == "__main__":
    main()

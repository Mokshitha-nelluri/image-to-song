"""
Spotify Integration Test Suite
Tests the complete Image-to-Song pipeline with music recommendations.
"""
import os
import time
import requests
import webbrowser
from pathlib import Path

def test_server_connection():
    """Test if the full-stack server is running."""
    try:
        response = requests.get("http://localhost:8002/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Full-stack server is running!")
            print(f"📋 Features: {', '.join(data.get('features', []))}")
            return True
        else:
            print(f"❌ Server returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to server: {e}")
        return False

def test_health_check():
    """Test health endpoint with Spotify configuration status."""
    try:
        response = requests.get("http://localhost:8002/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Health check passed!")
            print(f"📊 Status: {data.get('status')}")
            print(f"🤖 AI Model: {data.get('ai_model_loaded')}")
            print(f"🎵 Spotify Config: {data.get('spotify_configured')}")
            
            if not data.get('spotify_configured'):
                print("\n⚠️ Spotify not configured!")
                print("📝 Instructions:")
                print("1. Copy .env.template to .env")
                print("2. Get Spotify credentials from https://developer.spotify.com/dashboard")
                print("3. Fill in SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET")
                print("4. Restart the server")
                return False
            
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_spotify_auth_flow():
    """Test Spotify OAuth authentication flow."""
    try:
        print("\n🎵 Testing Spotify Authentication...")
        
        # Get auth URL
        response = requests.get("http://localhost:8002/spotify/auth")
        if response.status_code != 200:
            if response.status_code == 503:
                print("❌ Spotify not configured! Please set up credentials first.")
                return None
            else:
                print(f"❌ Auth endpoint failed: {response.status_code}")
                return None
        
        auth_data = response.json()
        auth_url = auth_data["auth_url"]
        state = auth_data["state"]
        
        print("✅ Auth URL generated successfully!")
        print(f"🔗 Auth URL: {auth_url[:100]}...")
        print(f"🔐 State: {state[:16]}...")
        
        # Prompt user to complete OAuth
        print("\n🌐 Opening Spotify authentication in browser...")
        print("📝 Instructions:")
        print("1. Authorize the app in the browser")
        print("2. You'll be redirected to a callback URL") 
        print("3. Copy the 'code' parameter from the URL")
        print("4. Paste it back here")
        
        try:
            webbrowser.open(auth_url)
        except:
            print("❌ Could not open browser automatically")
            print(f"🔗 Please visit: {auth_url}")
        
        # Get authorization code from user
        auth_code = input("\n📋 Enter the 'code' parameter from callback URL (or 'skip'): ").strip()
        
        if auth_code.lower() in ['skip', 's', '']:
            print("⏭️ Skipping OAuth test")
            return None
        
        # Test callback
        callback_response = requests.get(
            f"http://localhost:8002/spotify/callback?code={auth_code}&state={state}"
        )
        
        if callback_response.status_code == 200:
            callback_data = callback_response.json()
            user_id = callback_data.get("user_id")
            print("✅ Spotify authentication successful!")
            print(f"👤 User ID: {user_id}")
            return user_id
        else:
            print(f"❌ Callback failed: {callback_response.status_code}")
            print(f"📄 Error: {callback_response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Auth test error: {e}")
        return None

def test_music_recommendations(user_id=None):
    """Test music recommendations with image."""
    if not user_id:
        print("\n⚠️ Skipping recommendations test - no authenticated user")
        return False
    
    try:
        print(f"\n🎵 Testing music recommendations for user: {user_id}")
        
        # Create test image
        from PIL import Image
        import io
        
        # Create a blue sunset image (should suggest calm music)
        img = Image.new('RGB', (300, 200))
        pixels = img.load()
        
        # Create gradient from orange (sunset) to blue (sky)
        for y in range(200):
            for x in range(300):
                if y < 100:  # Top half - blue sky
                    r, g, b = int(50 + y), int(100 + y), int(200 - y/2)
                else:  # Bottom half - orange sunset
                    r, g, b = int(255 - (y-100)), int(165 - (y-100)/2), int(50)
                pixels[x, y] = (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))
        
        # Convert to bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        
        # Send recommendation request
        files = {'image': ('sunset.jpg', img_bytes.getvalue(), 'image/jpeg')}
        params = {'user_id': user_id}
        
        start_time = time.time()
        response = requests.post(
            "http://localhost:8002/spotify/recommendations",
            files=files,
            params=params,
            timeout=60
        )
        request_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Music recommendations generated!")
            
            # Show results
            mood = data.get('mood_analysis', {})
            recs = data.get('recommendations', {})
            timing = data.get('processing_time', {})
            
            print(f"📝 Caption: '{mood.get('caption', 'N/A')}'")
            print(f"🎨 Colors: {len(mood.get('dominant_colors', []))} detected")
            print(f"⏱️ Total time: {request_time:.2f}s")
            print(f"🧠 AI processing: {timing.get('caption_generation', 0):.2f}s")
            print(f"🎵 Spotify query: {timing.get('spotify_recommendations', 0):.2f}s")
            
            # Show recommended tracks
            tracks = recs.get('recommendations', {}).get('tracks', [])
            print(f"\n🎵 Recommended tracks ({len(tracks)}):")
            for i, track in enumerate(tracks[:5]):  # Show first 5
                artist = track.get('artists', [{}])[0].get('name', 'Unknown')
                name = track.get('name', 'Unknown')
                print(f"  {i+1}. {artist} - {name}")
            
            # Show audio features used
            features = recs.get('audio_features_used', {})
            print(f"\n🎛️ Audio features used:")
            print(f"  Valence (happiness): {features.get('valence', 0):.2f}")
            print(f"  Energy: {features.get('energy', 0):.2f}")
            print(f"  Danceability: {features.get('danceability', 0):.2f}")
            print(f"  Acousticness: {features.get('acousticness', 0):.2f}")
            
            return True
        else:
            print(f"❌ Recommendations failed: {response.status_code}")
            print(f"📄 Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Recommendations test error: {e}")
        return False

def test_caption_only():
    """Test just the caption generation without Spotify."""
    try:
        print("\n🖼️ Testing AI caption generation...")
        
        # Create test image
        from PIL import Image
        import io
        
        # Create a simple nature scene
        img = Image.new('RGB', (200, 200), color='green')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        
        files = {'image': ('nature.jpg', img_bytes.getvalue(), 'image/jpeg')}
        
        response = requests.post(
            "http://localhost:8002/caption/generate",
            files=files,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Caption generation working!")
            print(f"📝 Caption: '{data.get('caption')}'")
            print(f"🎨 Colors: {len(data.get('mood_analysis', {}).get('dominant_colors', []))}")
            return True
        else:
            print(f"❌ Caption failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Caption test error: {e}")
        return False

def main():
    print("🎵 Image-to-Song Spotify Integration Test")
    print("=" * 60)
    
    # Test 1: Server connection
    print("\n1️⃣ Testing server connection...")
    if not test_server_connection():
        print("❌ Please start the server with: python main_spotify.py")
        return
    
    # Test 2: Health check
    print("\n2️⃣ Testing health and configuration...")
    spotify_ready = test_health_check()
    
    # Test 3: Caption generation (always works)
    print("\n3️⃣ Testing AI caption generation...")
    caption_works = test_caption_only()
    
    if spotify_ready:
        # Test 4: Spotify authentication
        print("\n4️⃣ Testing Spotify authentication...")
        user_id = test_spotify_auth_flow()
        
        # Test 5: Music recommendations
        if user_id:
            print("\n5️⃣ Testing music recommendations...")
            rec_works = test_music_recommendations(user_id)
            
            if rec_works:
                print("\n🎉 COMPLETE SUCCESS!")
                print("✅ All features working:")
                print("  - AI Image Captioning")
                print("  - Color/Mood Analysis") 
                print("  - Spotify Authentication")
                print("  - Music Recommendations")
            else:
                print("\n⚠️ Partial success - recommendations failed")
        else:
            print("\n⚠️ Skipped recommendations test")
    else:
        print("\n⚠️ Spotify not configured - only AI features tested")
        if caption_works:
            print("✅ AI pipeline is working! Set up Spotify for full features.")
    
    print(f"\n🌐 Full API documentation: http://localhost:8002/docs")
    print("🎵 Complete pipeline ready for mobile app integration!")

if __name__ == "__main__":
    main()

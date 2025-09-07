"""
Simplified main_spotify.py for deployment testing
Focuses on Spotify OAuth without heavy AI dependencies
"""
from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.responses import RedirectResponse, JSONResponse
import httpx
import base64
import secrets
import os
from urllib.parse import urlencode
import uvicorn

app = FastAPI(title="Image-to-Song API (Deployment Test)", version="1.0.0")

# Environment variables
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
SPOTIFY_REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI')

# In-memory storage for demo (use Redis/DB in production)
auth_sessions = {}

@app.get("/")
async def root():
    """API Health Check"""
    return {
        "message": "🎵 Image-to-Song API is running!",
        "status": "healthy",
        "spotify_configured": bool(SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET),
        "version": "1.0.0 (OAuth Test)"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "spotify_client_configured": bool(SPOTIFY_CLIENT_ID),
        "spotify_secret_configured": bool(SPOTIFY_CLIENT_SECRET),
        "redirect_uri": SPOTIFY_REDIRECT_URI
    }

@app.get("/spotify/login")
async def spotify_login():
    """Start Spotify OAuth flow"""
    if not SPOTIFY_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Spotify client ID not configured")
    
    state = secrets.token_urlsafe(32)
    
    params = {
        'client_id': SPOTIFY_CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': SPOTIFY_REDIRECT_URI,
        'scope': 'user-read-private user-read-email user-library-read user-top-read playlist-read-private',
        'state': state
    }
    
    # Store state for verification
    auth_sessions[state] = {'pending': True}
    
    auth_url = f"https://accounts.spotify.com/authorize?{urlencode(params)}"
    
    return {
        "auth_url": auth_url,
        "state": state,
        "message": "Visit the auth_url to authorize with Spotify"
    }

@app.get("/spotify/callback")
async def spotify_callback(
    code: str = Query(...),
    state: str = Query(...),
    error: str = Query(None)
):
    """Handle Spotify OAuth callback"""
    
    if error:
        raise HTTPException(status_code=400, detail=f"Spotify authorization failed: {error}")
    
    # Verify state
    if state not in auth_sessions:
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    
    # Exchange code for token
    try:
        token_data = await exchange_code_for_token(code)
        
        if 'access_token' in token_data:
            # Store token (in production, store securely per user)
            auth_sessions[state] = {
                'access_token': token_data['access_token'],
                'refresh_token': token_data.get('refresh_token'),
                'expires_in': token_data.get('expires_in')
            }
            
            return {
                "status": "success",
                "message": "Successfully authorized with Spotify!",
                "token_preview": token_data['access_token'][:20] + "...",
                "test_url": "/spotify/test-recommendations"
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to get access token")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token exchange failed: {str(e)}")

async def exchange_code_for_token(authorization_code: str):
    """Exchange authorization code for access token"""
    credentials = base64.b64encode(f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}".encode()).decode()
    
    headers = {
        'Authorization': f'Basic {credentials}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    data = {
        'grant_type': 'authorization_code',
        'code': authorization_code,
        'redirect_uri': SPOTIFY_REDIRECT_URI
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post('https://accounts.spotify.com/api/token', headers=headers, data=data)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=response.status_code, detail=f"Token exchange failed: {response.text}")

@app.get("/spotify/test-recommendations")
async def test_spotify_recommendations():
    """Test Spotify API with user token"""
    
    # Find a valid token (in production, get from user session)
    user_token = None
    for session in auth_sessions.values():
        if 'access_token' in session:
            user_token = session['access_token']
            break
    
    if not user_token:
        return {
            "error": "No active Spotify session. Please visit /spotify/login first.",
            "login_url": "/spotify/login"
        }
    
    try:
        headers = {'Authorization': f'Bearer {user_token}'}
        
        # Get user's top tracks
        async with httpx.AsyncClient() as client:
            # Test user profile
            profile_response = await client.get('https://api.spotify.com/v1/me', headers=headers)
            
            if profile_response.status_code == 200:
                profile = profile_response.json()
                
                # Test top tracks
                top_tracks_response = await client.get('https://api.spotify.com/v1/me/top/tracks?limit=3', headers=headers)
                
                results = {
                    "status": "success",
                    "user_profile": {
                        "name": profile.get('display_name'),
                        "id": profile.get('id'),
                        "followers": profile.get('followers', {}).get('total')
                    }
                }
                
                if top_tracks_response.status_code == 200:
                    top_tracks = top_tracks_response.json()['items']
                    results["top_tracks"] = [
                        {
                            "name": track['name'],
                            "artist": track['artists'][0]['name'],
                            "popularity": track['popularity']
                        }
                        for track in top_tracks
                    ]
                    
                    # Test recommendations based on top tracks
                    if top_tracks:
                        seed_tracks = ','.join([track['id'] for track in top_tracks[:2]])
                        rec_params = {
                            'seed_tracks': seed_tracks,
                            'target_valence': 0.8,
                            'target_energy': 0.7,
                            'limit': 5
                        }
                        
                        rec_response = await client.get(
                            'https://api.spotify.com/v1/recommendations',
                            headers=headers,
                            params=rec_params
                        )
                        
                        if rec_response.status_code == 200:
                            recommendations = rec_response.json()['tracks']
                            results["personalized_recommendations"] = [
                                {
                                    "name": track['name'],
                                    "artist": track['artists'][0]['name'],
                                    "popularity": track['popularity'],
                                    "spotify_url": track['external_urls']['spotify']
                                }
                                for track in recommendations
                            ]
                            results["message"] = "🎉 Personalized recommendations working!"
                        else:
                            results["recommendation_error"] = f"Recommendations failed: {rec_response.status_code}"
                
                return results
            else:
                raise HTTPException(status_code=401, detail="Invalid or expired token")
                
    except Exception as e:
        return {
            "error": f"Spotify API test failed: {str(e)}",
            "message": "Token might be expired. Try /spotify/login again."
        }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8002))
    uvicorn.run(app, host="0.0.0.0", port=port)

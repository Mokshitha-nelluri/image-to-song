# Image-to-Song Backend Deployment

This service provides the complete Image-to-Song pipeline with:
- AI-powered image analysis
- Spotify OAuth integration  
- Personalized music recommendations

## Deployment Configuration

- **Service Name**: `image-to-song-api`
- **Environment**: Python 3.11+
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn main_complete_pipeline:app --host 0.0.0.0 --port $PORT`

## Environment Variables Required

```
SPOTIFY_CLIENT_ID=25de944a1992453896769027a9ffe3c1
SPOTIFY_CLIENT_SECRET=[Your Spotify App Secret]
SPOTIFY_REDIRECT_URI=https://image-to-song-api.onrender.com/spotify/callback
```

## Endpoints

- **Health Check**: `/health`
- **Image Analysis**: `/analyze-image` 
- **Spotify Login**: `/spotify/login`
- **Recommendations**: `/mixed-recommendations`

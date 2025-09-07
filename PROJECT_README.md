# 🎵 Image-to-Song AI Pipeline

**Turn your photos into personalized music recommendations using AI image analysis and Spotify integration.**

## 🚀 Features

### Complete Authentication Flow
- **Login Screen**: Users can choose to login with Spotify or continue without authentication
- **Spotify OAuth**: Seamless in-app authentication with WebView
- **Anonymous Mode**: Full functionality without requiring Spotify login

### AI-Powered Image Analysis
- **BLIP-2 Integration**: Advanced AI image captioning (when available)
- **Fallback Analyzer**: Simple color-based mood detection for deployment environments
- **Smart Processing**: Automatic image preprocessing and validation

### Personalized Music Recommendations
- **Authenticated Users**: Personalized recommendations based on user's Spotify listening history + mood analysis
- **Anonymous Users**: General mood-based recommendations using curated fallback playlists
- **Mixed Strategy**: Combines personalized, mood-based, and discovery recommendations

## 🏗️ Architecture

```
image-to-song/
├── backend/                    # FastAPI backend
│   ├── main.py                # Complete pipeline with OAuth + AI + Spotify
│   ├── app/
│   │   ├── core/              # Configuration
│   │   ├── services/          # AI and Spotify services
│   │   └── utils/             # Image processing utilities
│   ├── requirements.txt       # Python dependencies
│   ├── Procfile              # Deployment configuration
│   └── render.yaml           # Render.com deployment
│
├── mobile_app/                # Flutter mobile application
│   ├── lib/
│   │   ├── main.dart         # App entry point
│   │   ├── config.dart       # Configuration
│   │   ├── screens/
│   │   │   ├── login_screen.dart     # Initial login/skip screen
│   │   │   └── home_screen.dart      # Main app functionality
│   │   └── spotify_auth_screen.dart  # OAuth WebView
│   └── pubspec.yaml          # Flutter dependencies
│
└── README.md                 # This file
```

## 🔄 User Flow

### 1. App Launch
- User opens the app and sees a beautiful login screen
- Options: "🎵 Login with Spotify" or "Continue without login"

### 2. Authentication (Optional)
- **With Login**: OAuth flow opens in WebView → User authenticates → Returns to app
- **Without Login**: Direct access to main functionality

### 3. Image Analysis
- User uploads an image from gallery
- AI analyzes the image for mood and content
- Returns caption, mood, and confidence score

### 4. Music Recommendations
- **Authenticated**: Mixed recommendations (personalized + mood + discovery)
- **Anonymous**: Curated mood-based recommendations
- Results are categorized and displayed with Spotify links

## 🛠️ Setup & Installation

### Backend Setup

1. **Navigate to backend directory:**
```bash
cd backend
```

2. **Create virtual environment:**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Set environment variables:**
```bash
# Create .env file
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
SPOTIFY_REDIRECT_URI=http://localhost:8000/spotify/callback
```

5. **Run the server:**
```bash
python main.py
```

### Mobile App Setup

1. **Navigate to mobile app directory:**
```bash
cd mobile_app
```

2. **Install Flutter dependencies:**
```bash
flutter pub get
```

3. **Update configuration** (if using local backend):
```dart
// In lib/config.dart
static const String baseUrl = 'http://localhost:8000';
```

4. **Run the app:**
```bash
flutter run
```

## 🔧 Configuration

### Backend Configuration

The backend automatically detects available services:
- **AI Service**: Uses BLIP-2 if available, falls back to simple color analysis
- **Spotify Integration**: Handles OAuth and API calls
- **Image Processing**: Smart preprocessing and validation

### Mobile App Configuration

**Environment Selection** in `lib/config.dart`:
```dart
// Production (default)
static const String baseUrl = 'https://image-to-song.onrender.com';

// Local development
// static const String baseUrl = 'http://localhost:8000';
```

## 📡 API Endpoints

### Core Endpoints
- `GET /` - API information
- `GET /health` - Health check with detailed status
- `POST /analyze-image` - Image analysis (AI or fallback)
- `POST /mixed-recommendations` - Get recommendations

### Spotify Integration
- `GET /spotify/login` - Start OAuth flow
- `GET /spotify/callback` - OAuth callback handler
- `GET /spotify/status` - Check authentication status

### Legacy Endpoints (for compatibility)
- `POST /caption/generate` - Generate image caption
- `POST /image/process` - Detailed image processing

## 🚀 Deployment

### Backend Deployment (Render.com)

The backend is configured for automatic deployment:
- **Service**: `render.yaml` configuration
- **Build**: `pip install -r requirements.txt`
- **Start**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Mobile App Deployment

**Android:**
```bash
flutter build apk --release
```

**iOS:**
```bash
flutter build ios --release
```

## 🎯 Key Features Implemented

### ✅ Fixed Issues

1. **Authentication Flow**: 
   - ✅ Proper login screen as entry point
   - ✅ Option to skip login and use anonymous mode
   - ✅ Spotify OAuth integration with WebView

2. **Backend Integration**:
   - ✅ Complete pipeline in single main.py file
   - ✅ Fallback systems for deployment environments
   - ✅ Proper error handling and logging

3. **Mobile App Structure**:
   - ✅ Clean separation of screens
   - ✅ State management for authentication
   - ✅ Proper navigation flow

4. **Configuration Management**:
   - ✅ Environment-based configuration
   - ✅ Production vs development settings
   - ✅ Proper deployment configuration

### 🎵 Recommendation Strategy

**Authenticated Users (Spotify Connected):**
- 60% Personalized (based on user's top tracks + mood)
- 30% Mood-based (search API with mood keywords)
- 10% Discovery (trending/popular tracks)

**Anonymous Users:**
- 100% Curated mood-based recommendations
- Fallback playlists for all moods
- No external API dependency

## 🐛 Troubleshooting

### Backend Issues
```bash
# Check if AI service is working
curl http://localhost:8000/health

# Test image analysis
curl -X POST -F "file=@test.jpg" http://localhost:8000/analyze-image
```

### Mobile App Issues
```bash
# Clean and rebuild
flutter clean
flutter pub get
flutter run

# Check debug output
flutter logs
```

### Common Problems

1. **Backend Connection Failed**: Check Config.baseUrl in mobile app
2. **Spotify Auth Fails**: Verify SPOTIFY_CLIENT_ID and redirect URI
3. **Image Analysis Errors**: Check file size and format (max 10MB)

## 📝 Development Notes

### Architecture Decisions

1. **Fallback Systems**: Backend gracefully degrades when AI services aren't available
2. **OAuth in WebView**: Better user experience than external browser redirect
3. **Anonymous Mode**: Full functionality without requiring Spotify account
4. **Mixed Recommendations**: Combines multiple strategies for better results

### Future Enhancements

- [ ] User preference learning
- [ ] Playlist creation functionality
- [ ] Social sharing features
- [ ] Advanced mood detection
- [ ] Offline mode support

## 📄 License

This project is part of the Image-to-Song application suite.

---

**🎵 Ready to turn your images into music? Get started now!**

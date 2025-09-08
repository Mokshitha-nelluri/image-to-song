# Image-to-Song App: Music Quiz & Preference-Based Recommendations

## 📖 Overview
A mobile app that learns user music preferences through a Tinder-style quiz on first launch, then provides personalized song recommendations based on uploaded images combined with stored user preferences.

## 🎯 Core Features
- **First-time Music Quiz**: Swipeable song preview cards to build user profile
- **Image Analysis**: BLIP-2 powered mood and context extraction
- **Smart Recommendations**: Spotify search combining image mood + user preferences
- **No Authentication**: Pure search-based, no user accounts needed
- **Local Storage**: All user data stored privately on device

---

## 🔄 User Flow

### First Launch Experience
```
📱 App Launch
    ↓
🎵 Welcome Screen
    "Discover Your Musical DNA"
    ↓
📋 Quiz Instructions
    "Swipe ❤️ for love, ❌ for pass"
    ↓
🎧 Music Quiz (15-20 songs)
    - Auto-play 30s previews
    - Swipe interactions
    - Progress tracking
    ↓
🧬 Preference Analysis
    - Calculate genre preferences
    - Build audio feature profile
    - Store locally
    ↓
✅ Quiz Complete
    "Your music taste saved!"
    ↓
📷 Main App Interface
```

### Regular Usage Flow
```
📱 App Launch
    ↓
📷 Home Screen
    - Upload image button
    - Camera/Gallery options
    ↓
🔍 Image Analysis
    - BLIP-2 caption generation
    - Mood extraction
    - Context analysis
    ↓
🎵 Smart Recommendations
    - Combine image mood + user preferences
    - Spotify search with weighted criteria
    - Rank results by relevance
    ↓
📋 Results Display
    - Song cards with previews
    - Spotify deep links
    - Save/share options
```

---

## 🏗️ Technical Architecture

### Backend Stack
```
FastAPI Server
├── Image Analysis
│   ├── BLIP-2 (Salesforce/blip2-opt-2.7b)
│   ├── Mood extraction from captions
│   └── Color analysis fallback
├── Spotify Integration
│   ├── Client Credentials Flow (no user auth)
│   ├── Search API for recommendations
│   └── Audio features analysis
└── Quiz System
    ├── Curated song database
    ├── Preference calculation algorithms
    └── Recommendation engine
```

### Mobile App Stack
```
Flutter App
├── Screens
│   ├── WelcomeScreen
│   ├── QuizScreen (Tinder-style cards)
│   ├── HomeScreen (Image upload)
│   └── ResultsScreen (Recommendations)
├── Services
│   ├── QuizService (Manage quiz flow)
│   ├── ProfileService (Local storage)
│   ├── ApiService (Backend communication)
│   └── AudioService (Preview playback)
├── Models
│   ├── QuizSong
│   ├── UserMusicProfile
│   └── Recommendation
└── Local Storage
    ├── SharedPreferences (Profile data)
    ├── Hive/SQLite (Quiz history)
    └── File Storage (Cached images)
```

---

## 💾 Local Data Storage

### User Music Profile Structure
```dart
class UserMusicProfile {
  // Basic Info
  String userId;                    // Generated UUID
  DateTime createdAt;
  DateTime lastUpdated;
  bool quizCompleted;
  
  // Genre Preferences (0.0 - 1.0 scale)
  Map<String, double> genrePreferences;
  /*
  Example:
  {
    "pop": 0.8,
    "rock": 0.6,
    "hip-hop": 0.9,
    "classical": 0.2,
    "electronic": 0.7,
    "country": 0.1,
    "jazz": 0.4,
    "indie": 0.8
  }
  */
  
  // Audio Feature Preferences (0.0 - 1.0 scale)
  Map<String, double> audioFeaturePreferences;
  /*
  Spotify Audio Features:
  {
    "danceability": 0.7,     // How danceable
    "energy": 0.8,           // Intensity and power
    "valence": 0.6,          // Positivity/happiness
    "acousticness": 0.3,     // Acoustic vs electronic
    "instrumentalness": 0.1, // Vocal vs instrumental
    "tempo": 0.7,            // Speed preference (normalized)
    "loudness": 0.6          // Volume preference (normalized)
  }
  */
  
  // Artist & Track Insights
  List<String> likedArtists;        // Artists from liked songs
  List<String> dislikedArtists;     // Artists from disliked songs
  List<String> likedTrackIds;       // Spotify IDs of liked songs
  List<String> dislikedTrackIds;    // Spotify IDs of disliked songs
  
  // Quiz Statistics
  int totalSongsRated;
  int songsLiked;
  int songsDisliked;
  double completionRate;
}
```

### Quiz Song Data Structure
```dart
class QuizSong {
  // Spotify Data
  String spotifyId;
  String title;
  String artist;
  String album;
  List<String> genres;
  
  // Audio Preview
  String? previewUrl;               // 30-second preview URL
  bool hasPreview;
  
  // Visual Assets
  String albumCoverUrl;
  String? albumCoverLarge;          // High-res version
  
  // Audio Features (from Spotify API)
  Map<String, double> audioFeatures;
  /*
  {
    "danceability": 0.735,
    "energy": 0.578,
    "valence": 0.624,
    "acousticness": 0.00242,
    "instrumentalness": 0.000006,
    "tempo": 150.062,
    "loudness": -5.883
  }
  */
  
  // Quiz Metadata
  int quizPosition;                 // Order in quiz (1-20)
  DateTime? ratedAt;                // When user rated
  bool? userLiked;                  // User's rating (null = not rated)
}
```

### Storage Implementation

#### SharedPreferences (Simple Key-Value)
```dart
// Store serialized profile
await prefs.setString('user_music_profile', jsonEncode(profile.toJson()));

// Store quiz completion status
await prefs.setBool('quiz_completed', true);

// Store app version for migration handling
await prefs.setString('app_version', '1.0.0');
```

#### Hive Database (Structured Local Storage)
```dart
// User Profile Box
@HiveType(typeId: 0)
class UserMusicProfile extends HiveObject {
  @HiveField(0) String userId;
  @HiveField(1) DateTime createdAt;
  @HiveField(2) Map<String, double> genrePreferences;
  @HiveField(3) Map<String, double> audioFeaturePreferences;
  // ... other fields
}

// Quiz Songs Box
@HiveType(typeId: 1)
class QuizSong extends HiveObject {
  @HiveField(0) String spotifyId;
  @HiveField(1) String title;
  @HiveField(2) bool? userLiked;
  // ... other fields
}
```

### Data Privacy & Security
```dart
class PrivacySettings {
  // No cloud storage - everything local
  static const bool SEND_ANALYTICS = false;
  static const bool CLOUD_BACKUP = false;
  
  // Data retention
  static const int PROFILE_RETENTION_DAYS = 365;
  static const int QUIZ_HISTORY_RETENTION_DAYS = 90;
  
  // Export/Delete options
  static Future<void> exportUserData() async { /* ... */ }
  static Future<void> deleteAllUserData() async { /* ... */ }
}
```

---

## 🎵 Quiz System Design

### Song Selection Criteria
```yaml
Total Quiz Songs: 20

Genre Distribution:
  - Pop: 4 songs (20%)
  - Rock: 3 songs (15%)
  - Hip-Hop: 3 songs (15%)
  - Electronic: 2 songs (10%)
  - Indie: 2 songs (10%)
  - R&B: 2 songs (10%)
  - Country: 2 songs (10%)
  - Alternative: 2 songs (10%)

Audio Feature Diversity:
  High Energy (0.7-1.0): 6 songs
  Medium Energy (0.4-0.7): 8 songs
  Low Energy (0.0-0.4): 6 songs
  
  High Valence (Happy): 7 songs
  Medium Valence: 6 songs
  Low Valence (Sad): 7 songs
  
  High Danceability: 6 songs
  Medium Danceability: 8 songs
  Low Danceability: 6 songs

Preview Requirements:
  - Must have 30-second preview URL
  - Preview quality > 128kbps
  - Working/accessible URLs only
```

### Preference Calculation Algorithm
```python
def calculate_user_preferences(quiz_results):
    liked_songs = [song for song in quiz_results if song.user_liked]
    disliked_songs = [song for song in quiz_results if not song.user_liked]
    
    # Genre Preferences
    genre_scores = {}
    for song in liked_songs:
        for genre in song.genres:
            genre_scores[genre] = genre_scores.get(genre, 0) + 1
    
    for song in disliked_songs:
        for genre in song.genres:
            genre_scores[genre] = genre_scores.get(genre, 0) - 0.5
    
    # Normalize to 0-1 scale
    max_score = max(genre_scores.values()) if genre_scores else 1
    genre_preferences = {
        genre: max(0, score / max_score) 
        for genre, score in genre_scores.items()
    }
    
    # Audio Feature Preferences
    feature_preferences = {}
    audio_features = ['danceability', 'energy', 'valence', 'acousticness']
    
    for feature in audio_features:
        liked_values = [song.audio_features[feature] for song in liked_songs]
        disliked_values = [song.audio_features[feature] for song in disliked_songs]
        
        if liked_values:
            # Calculate weighted average preference
            liked_avg = sum(liked_values) / len(liked_values)
            
            if disliked_values:
                disliked_avg = sum(disliked_values) / len(disliked_values)
                # Adjust preference away from disliked average
                preference = liked_avg + 0.1 * (liked_avg - disliked_avg)
            else:
                preference = liked_avg
            
            feature_preferences[feature] = max(0, min(1, preference))
    
    return genre_preferences, feature_preferences
```

---

## 🔍 Recommendation Engine

### Image Analysis to Music Mapping
```python
# Mood to Audio Features Mapping
MOOD_MAPPINGS = {
    "happy": {
        "valence": 0.8,
        "energy": 0.7,
        "danceability": 0.6
    },
    "sad": {
        "valence": 0.2,
        "energy": 0.3,
        "acousticness": 0.6
    },
    "energetic": {
        "energy": 0.9,
        "danceability": 0.8,
        "tempo": 0.8
    },
    "calm": {
        "energy": 0.2,
        "acousticness": 0.7,
        "instrumentalness": 0.4
    },
    "romantic": {
        "valence": 0.6,
        "acousticness": 0.5,
        "energy": 0.4
    }
}

def generate_recommendations(image_analysis, user_profile):
    # Extract mood from image
    detected_mood = extract_mood_from_caption(image_analysis.caption)
    mood_features = MOOD_MAPPINGS.get(detected_mood, {})
    
    # Combine with user preferences (weighted 60% user, 40% mood)
    combined_features = {}
    for feature in ['danceability', 'energy', 'valence', 'acousticness']:
        user_pref = user_profile.audio_feature_preferences.get(feature, 0.5)
        mood_pref = mood_features.get(feature, 0.5)
        
        combined_features[feature] = (0.6 * user_pref) + (0.4 * mood_pref)
    
    # Get preferred genres
    top_genres = sorted(
        user_profile.genre_preferences.items(), 
        key=lambda x: x[1], 
        reverse=True
    )[:3]
    
    # Search Spotify
    recommendations = spotify_search(
        genres=[genre for genre, _ in top_genres],
        target_features=combined_features,
        limit=10
    )
    
    return rank_recommendations(recommendations, user_profile)
```

---

## 📱 Implementation Timeline

### Phase 1: Backend Overhaul (Week 1)
- [ ] Remove OAuth system completely
- [ ] Implement Spotify Client Credentials
- [ ] Create quiz song database endpoint
- [ ] Build preference calculation algorithms
- [ ] Update recommendation engine

### Phase 2: Mobile App Quiz System (Week 2)
- [ ] Design welcome and quiz screens
- [ ] Implement swipeable card interface
- [ ] Add audio preview functionality
- [ ] Create local storage system
- [ ] Build preference calculation

### Phase 3: Enhanced Recommendations (Week 3)
- [ ] Integrate user preferences with image analysis
- [ ] Improve recommendation ranking
- [ ] Add song preview in results
- [ ] Implement Spotify deep linking

### Phase 4: Polish & Testing (Week 4)
- [ ] UI/UX improvements
- [ ] Error handling and edge cases
- [ ] Performance optimization
- [ ] Beta testing and feedback

---

## 🛠️ Development Dependencies

### Backend Requirements
```python
# requirements.txt
fastapi==0.104.1
uvicorn==0.24.0
spotipy==2.22.1          # Spotify API client
python-multipart==0.0.6
pillow==10.0.1
torch==2.1.0
transformers==4.35.0
httpx==0.25.0
python-dotenv==1.0.0
```

### Mobile App Requirements
```yaml
# pubspec.yaml
dependencies:
  flutter:
    sdk: flutter
  
  # UI & Navigation
  cupertino_icons: ^1.0.8
  
  # HTTP & API
  http: ^1.1.0
  dio: ^5.3.2              # Advanced HTTP client
  
  # Local Storage
  shared_preferences: ^2.2.2
  hive: ^2.2.3
  hive_flutter: ^1.1.0
  
  # Audio Playback
  audioplayers: ^5.2.1
  
  # Image Handling
  image_picker: ^1.0.4
  cached_network_image: ^3.3.0
  
  # State Management
  provider: ^6.1.1
  
  # Utils
  uuid: ^4.1.0
  intl: ^0.18.1

dev_dependencies:
  hive_generator: ^2.0.1
  build_runner: ^2.4.7
```

---

## 🔒 Privacy & Data Protection

### Local-First Approach
- **No Cloud Storage**: All user data remains on device
- **No Analytics**: No tracking or usage data collection
- **No Accounts**: No user registration or profiles
- **Minimal Permissions**: Only camera/gallery access needed

### Data Management
- **Export Option**: Users can export their music profile
- **Delete Option**: Complete data deletion available
- **Migration Handling**: Safe app updates without data loss
- **Storage Optimization**: Automatic cleanup of old data

### Compliance
- **GDPR Ready**: No personal data collection
- **CCPA Compliant**: No data sale or sharing
- **Kids Safe**: No data collection from minors
- **Transparent**: Clear privacy policy about local storage

---

This document serves as the complete technical specification for implementing the quiz-based, preference-driven Image-to-Song application. The focus on local storage and privacy-first design ensures user trust while delivering personalized music recommendations.

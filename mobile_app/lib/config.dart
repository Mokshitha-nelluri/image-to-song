/// Application Configuration
/// Contains app-wide constants and configuration values
class AppConfig {
  // App Information
  static const String appName = '🎵 Image-to-Song';
  static const String appVersion = '1.0.0';

  // API Configuration
  static const String apiBaseUrl = 'https://image-to-song.onrender.com';
  static const String apiBaseUrlDev = 'http://localhost:8000';

  // Timeouts
  static const Duration apiTimeout = Duration(seconds: 30);
  static const Duration audioPreviewLength = Duration(seconds: 30);

  // Quiz Configuration
  static const int maxQuizSongs = 20;
  static const int recommendationsLimit = 15;
  static const int searchResultsLimit = 10;

  // Theme Colors
  static const int spotifyGreenPrimary = 0xFF1DB954;
  static const int spotifyGreenSecondary = 0xFF1ed760;
  static const int spotifyDark = 0xFF191414;

  // Storage Keys
  static const String userProfileKey = 'user_music_profile';
  static const String quizCompletedKey = 'quiz_completed';
  static const String quizSongsKey = 'quiz_songs';
  static const String appVersionKey = 'app_version';

  // Feature Flags
  static const bool enableDarkMode = true;
  static const bool enableOfflineMode = true;
  static const bool enableAnalytics = false;

  // Environment Detection
  static bool get isProduction => apiBaseUrl.contains('onrender');
  static bool get isDevelopment => !isProduction;

  // Get API base URL based on environment
  static String get currentApiBaseUrl =>
      isProduction ? apiBaseUrl : apiBaseUrlDev;
}

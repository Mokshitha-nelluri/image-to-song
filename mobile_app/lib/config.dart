class Config {
  // Backend URL configuration
  // For production deployment, use cloud backend
  static const String baseUrl = 'https://image-to-song.onrender.com';

  // For local development, uncomment the line below and comment the line above:
  // static const String baseUrl = 'http://192.168.1.131:8000';
  // static const String baseUrl = 'http://localhost:8000';

  // App configuration
  static const String appName = 'Image-to-Song';
  static const String appVersion = '1.0.0';

  // Timeouts
  static const Duration requestTimeout = Duration(seconds: 30);
  static const Duration authTimeout = Duration(seconds: 60);

  // Image constraints
  static const int maxImageSizeBytes = 10 * 1024 * 1024; // 10MB
  static const int imageQuality = 80;
  static const double maxImageWidth = 1920;
  static const double maxImageHeight = 1080;
}

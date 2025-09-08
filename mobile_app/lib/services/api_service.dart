import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/quiz_song.dart';
import '../models/user_music_profile.dart';
import '../models/song_recommendation.dart';

class ApiService {
  static const String baseUrl =
      'https://image-to-song.onrender.com'; // Production URL
  // static const String baseUrl = 'http://localhost:8000'; // Development URL

  static const Duration timeout = Duration(seconds: 30);

  // Health check
  Future<Map<String, dynamic>> healthCheck() async {
    try {
      final response = await http
          .get(Uri.parse('$baseUrl/health'))
          .timeout(timeout);

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Health check failed: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Health check error: $e');
    }
  }

  // Get quiz songs
  Future<List<QuizSong>> getQuizSongs({int limit = 20}) async {
    try {
      final response = await http
          .get(Uri.parse('$baseUrl/quiz/songs?limit=$limit'))
          .timeout(timeout);

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        final List<dynamic> songsJson = data['quiz_songs'];

        return songsJson
            .map((songJson) => QuizSong.fromJson(songJson))
            .toList();
      } else {
        throw Exception('Failed to get quiz songs: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Quiz songs error: $e');
    }
  }

  // Calculate user preferences from quiz results
  Future<UserMusicProfile> calculatePreferences({
    required String userId,
    required List<Map<String, dynamic>> songRatings,
  }) async {
    try {
      final body = json.encode({
        'user_id': userId,
        'song_ratings': songRatings,
      });

      final response = await http
          .post(
            Uri.parse('$baseUrl/quiz/calculate-preferences'),
            headers: {'Content-Type': 'application/json'},
            body: body,
          )
          .timeout(timeout);

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        // The backend returns the profile in data['user_profile']
        final profileData = data['user_profile'];

        // Convert to our expected format
        return UserMusicProfile.fromJson({
          'user_id': profileData['user_id'],
          'created_at': DateTime.fromMillisecondsSinceEpoch(
            (profileData['created_at'] * 1000).toInt(),
          ).toIso8601String(),
          'quiz_completed': profileData['quiz_completed'],
          'total_songs': profileData['quiz_stats']['total_songs_rated'],
          'songs_liked': profileData['quiz_stats']['songs_liked'],
          'preference_percentage':
              (profileData['quiz_stats']['songs_liked'] /
              profileData['quiz_stats']['total_songs_rated'] *
              100),
          'top_genres':
              (profileData['genre_preferences'] as Map<String, dynamic>).entries
                  .map((e) => {'genre': e.key, 'score': e.value})
                  .toList(),
          'audio_features': profileData['audio_feature_preferences'],
          'music_personality': data['summary']['music_personality'],
        });
      } else {
        throw Exception(
          'Failed to calculate preferences: ${response.statusCode}',
        );
      }
    } catch (e) {
      throw Exception('Calculate preferences error: $e');
    }
  }

  // Analyze image
  Future<Map<String, dynamic>> analyzeImage(
    List<int> imageBytes,
    String filename,
  ) async {
    try {
      var request = http.MultipartRequest(
        'POST',
        Uri.parse('$baseUrl/analyze-image'),
      );

      request.files.add(
        http.MultipartFile.fromBytes('file', imageBytes, filename: filename),
      );

      final streamedResponse = await request.send().timeout(timeout);
      final response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed to analyze image: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Image analysis error: $e');
    }
  }

  // Get recommendations
  Future<List<SongRecommendation>> getRecommendations({
    required String mood,
    required String caption,
    UserMusicProfile? userProfile,
  }) async {
    try {
      final body = json.encode({
        'mood': mood,
        'caption': caption,
        'user_profile': userProfile?.toJson(),
      });

      final response = await http
          .post(
            Uri.parse('$baseUrl/recommendations'),
            headers: {'Content-Type': 'application/json'},
            body: body,
          )
          .timeout(timeout);

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        final List<dynamic> recommendationsJson = data['recommendations'];

        return recommendationsJson
            .map((recJson) => SongRecommendation.fromJson(recJson))
            .toList();
      } else {
        throw Exception(
          'Failed to get recommendations: ${response.statusCode}',
        );
      }
    } catch (e) {
      throw Exception('Recommendations error: $e');
    }
  }

  // Search songs
  Future<List<SongRecommendation>> searchSongs({
    required String query,
    int limit = 10,
  }) async {
    try {
      final response = await http
          .get(
            Uri.parse(
              '$baseUrl/search/songs?query=${Uri.encodeComponent(query)}&limit=$limit',
            ),
          )
          .timeout(timeout);

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        final List<dynamic> resultsJson = data['results'];

        return resultsJson
            .map((resultJson) => SongRecommendation.fromJson(resultJson))
            .toList();
      } else {
        throw Exception('Failed to search songs: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Song search error: $e');
    }
  }

  // Test connection
  Future<bool> testConnection() async {
    try {
      final response = await http
          .get(Uri.parse('$baseUrl/'))
          .timeout(const Duration(seconds: 10));

      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }
}
